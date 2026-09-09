"""
Main Agent implementation.

Coordinates:
    User request
        ↓
    Conversation memory
        ↓
    Task decomposition
        ↓
    Planning
        ↓
    Tool registration
        ↓
    Workflow execution
        ↓
    Supervision
        ↓
    Final response

The Agent maintains in-memory conversation history so that
information provided in earlier turns can be reused in later turns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.agent.planner import AgentPlanner
from backend.app.agent.state import AgentState
from backend.app.agent.supervisor import AgentSupervisor
from backend.app.agent.task_decomposer import (
    Task,
    TaskDecomposer,
)
from backend.app.agent.workflow import Workflow
from backend.app.llm.client import GeminiClient
from backend.app.llm.prompts import build_chat_prompt
from backend.app.memory.conversation import (
    ConversationManager,
)
from backend.app.memory.short_term import (
    ShortTermMemory,
)
from backend.app.tools.registry import default_registry


@dataclass
class AgentResult:
    """Final result returned by the Agent."""

    success: bool
    response: str
    status: str
    state: AgentState

    plan: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "success": self.success,
            "response": self.response,
            "status": self.status,
            "state": self.state.to_dict(),
            "plan": self.plan,
            "metadata": self.metadata,
        }


class Agent:
    """
    Main autonomous Agent.

    Coordinates task decomposition, planning,
    tool execution, workflow execution,
    supervision, memory, and final response generation.
    """

    # ----------------------------------------------------------
    # Gemini/RAG context limits
    # ----------------------------------------------------------

    MAX_RETRIEVED_CONTEXT_CHARS = 8000
    MAX_CHUNK_CHARS = 1800
    MAX_RETRIEVED_RESULTS = 5

    # ----------------------------------------------------------
    # Conversation memory limits
    # ----------------------------------------------------------

    MAX_CONVERSATION_MESSAGES = 20
    MAX_CONVERSATION_CONTEXT_CHARS = 12000

    def __init__(
        self,
        llm_client: GeminiClient | None = None,
        task_decomposer: TaskDecomposer | None = None,
        planner: AgentPlanner | None = None,
        workflow: Workflow | None = None,
        supervisor: AgentSupervisor | None = None,
        conversation_manager: ConversationManager | None = None,
    ):
        self.llm = llm_client or GeminiClient()

        self.decomposer = (
            task_decomposer
            or TaskDecomposer(
                llm_client=self.llm,
            )
        )

        self.planner = (
            planner
            or AgentPlanner()
        )

        self.workflow = (
            workflow
            or Workflow(
                planner=self.planner,
            )
        )

        self.supervisor = (
            supervisor
            or AgentSupervisor()
        )

        # ------------------------------------------------------
        # Conversation memory
        # ------------------------------------------------------

        self.conversations = (
            conversation_manager
            or ConversationManager()
        )

        # ------------------------------------------------------
        # Short-term memories.
        #
        # One memory object is maintained per conversation.
        # ------------------------------------------------------

        self._short_term_memories: dict[
            str,
            ShortTermMemory,
        ] = {}

        self._register_tools()

    # ==========================================================
    # TOOL REGISTRATION
    # ==========================================================

    def _register_tools(self) -> None:
        """
        Connect tools from the ToolRegistry to the workflow.

        Only tools actually registered in the central registry
        are made available to the workflow.
        """

        for tool in default_registry.list_tools():
            tool_name = tool["name"]

            async def executor(
                step,
                state,
                tool_name=tool_name,
            ):
                """
                Execute a registered tool.

                The user's original request is preferred as the
                tool query. This prevents the RAG tool from
                receiving only a generic planning description.
                """

                query = ""

                if getattr(
                    step,
                    "metadata",
                    None,
                ):
                    query = step.metadata.get(
                        "user_request",
                        "",
                    )

                if not query:
                    query = getattr(
                        state,
                        "user_message",
                        "",
                    )

                if not query:
                    query = step.description

                query = str(
                    query
                ).strip()

                result = await default_registry.execute(
                    tool_name,
                    query=query,
                )

                if not result.success:
                    raise RuntimeError(
                        result.error
                        or result.message
                        or (
                            f"Tool '{tool_name}' "
                            "execution failed."
                        )
                    )

                result_dict = result.to_dict()

                # --------------------------------------------------
                # Preserve only the RAG results needed by the
                # final response generator.
                # --------------------------------------------------

                if tool_name == "rag":
                    data = result_dict.get(
                        "data",
                        {},
                    )

                    if isinstance(
                        data,
                        dict,
                    ):
                        rag_results = data.get(
                            "results",
                            [],
                        )

                        if isinstance(
                            rag_results,
                            list,
                        ):
                            state.retrieved_context = (
                                rag_results[
                                    : self.MAX_RETRIEVED_RESULTS
                                ]
                            )

                return result_dict

            self.workflow.register_executor(
                tool_name=tool_name,
                executor=executor,
            )

    # ==========================================================
    # CONVERSATION MEMORY
    # ==========================================================

    def _get_conversation(
        self,
        user_id: str,
        conversation_id: str | None,
    ):
        """
        Get an existing conversation or create a new one.

        Conversations are isolated by user ID.
        """

        if conversation_id:
            conversation = self.conversations.get(
                conversation_id
            )

            # --------------------------------------------------
            # Never allow one user's conversation memory to be
            # reused for another user.
            # --------------------------------------------------

            if (
                conversation
                and conversation.user_id == user_id
            ):
                return conversation

        return self.conversations.create(
            user_id=user_id
        )

    def _get_short_term_memory(
        self,
        conversation_id: str,
    ) -> ShortTermMemory:
        """
        Get or create short-term memory for a conversation.
        """

        memory = self._short_term_memories.get(
            conversation_id
        )

        if memory is None:
            memory = ShortTermMemory(
                max_messages=self.MAX_CONVERSATION_MESSAGES
            )

            self._short_term_memories[
                conversation_id
            ] = memory

        return memory

    def _load_conversation_into_memory(
        self,
        conversation,
    ) -> ShortTermMemory:
        """
        Synchronize ConversationManager history into the
        short-term memory object.

        This is especially important when a conversation was
        created in a previous Agent request.
        """

        conversation_id = (
            conversation.conversation_id
        )

        memory = self._get_short_term_memory(
            conversation_id
        )

        # ------------------------------------------------------
        # Rebuild the short-term memory from the conversation.
        #
        # This avoids stale memory when the conversation manager
        # already contains previous messages.
        # ------------------------------------------------------

        memory.clear()

        recent_messages = (
            conversation.get_recent_messages(
                self.MAX_CONVERSATION_MESSAGES
            )
        )

        for message in recent_messages:
            memory.add(
                role=message.role,
                content=message.content,
                language=message.language,
                message_type=message.message_type,
                timestamp=message.timestamp.isoformat(),
                **(
                    message.metadata
                    if isinstance(
                        message.metadata,
                        dict,
                    )
                    else {}
                ),
            )

        return memory

    def _add_user_message_to_memory(
        self,
        conversation,
        short_term: ShortTermMemory,
        content: str,
        language: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store the current user message in both conversation
        memory and short-term memory.
        """

        clean_content = (
            content.strip()
            if content
            else ""
        )

        if not clean_content:
            return

        message_metadata = dict(
            metadata or {}
        )

        conversation_message = (
            self.conversations.add_message(
                conversation_id=(
                    conversation.conversation_id
                ),
                role="user",
                content=clean_content,
                language=language,
                message_type="text",
                metadata=message_metadata,
            )
        )

        short_term.add(
            role="user",
            content=clean_content,
            language=language,
            message_id=(
                conversation_message.message_id
            ),
            **message_metadata,
        )

    def _add_assistant_message_to_memory(
        self,
        conversation,
        short_term: ShortTermMemory,
        content: str,
        language: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store the assistant response in both conversation
        memory and short-term memory.
        """

        clean_content = (
            content.strip()
            if content
            else ""
        )

        if not clean_content:
            return

        message_metadata = dict(
            metadata or {}
        )

        conversation_message = (
            self.conversations.add_message(
                conversation_id=(
                    conversation.conversation_id
                ),
                role="assistant",
                content=clean_content,
                language=language,
                message_type="text",
                metadata=message_metadata,
            )
        )

        short_term.add(
            role="assistant",
            content=clean_content,
            language=language,
            message_id=(
                conversation_message.message_id
            ),
            **message_metadata,
        )

    def _build_conversation_context(
        self,
        short_term: ShortTermMemory,
        include_current_user_message: bool = True,
    ) -> str:
        """
        Build explicit conversational context for Gemini.

        Previous turns are included directly rather than relying
        only on lexical memory retrieval.

        This is important for facts such as:

            Turn 1:
            My family income is ₹2.5 lakh.

            Turn 2:
            I am a B.Tech student.

            Turn 3:
            Am I eligible?

        The final model receives all relevant recent turns.
        """

        messages = short_term.get_messages(
            self.MAX_CONVERSATION_MESSAGES
        )

        if not messages:
            return ""

        lines = [
            "RECENT CONVERSATION HISTORY:"
        ]

        total_chars = len(
            lines[0]
        )

        for message in messages:
            if not isinstance(
                message,
                dict,
            ):
                continue

            role = str(
                message.get(
                    "role",
                    "unknown",
                )
            ).strip()

            content = str(
                message.get(
                    "content",
                    "",
                )
            ).strip()

            if not content:
                continue

            # --------------------------------------------------
            # Do not duplicate the current message when the
            # caller specifically asks for previous context only.
            # --------------------------------------------------

            if (
                not include_current_user_message
                and role == "user"
                and message is messages[-1]
            ):
                continue

            block = (
                f"\n{role.upper()}: "
                f"{content}"
            )

            remaining = (
                self.MAX_CONVERSATION_CONTEXT_CHARS
                - total_chars
            )

            if remaining <= 0:
                break

            if len(block) > remaining:
                block = (
                    block[
                        :remaining
                    ].rstrip()
                    + "..."
                )

            lines.append(block)

            total_chars += len(block)

            if total_chars >= (
                self.MAX_CONVERSATION_CONTEXT_CHARS
            ):
                break

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    # ==========================================================
    # MAIN PIPELINE
    # ==========================================================

    async def run(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        language: str = "en",
        context: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> AgentResult:
        """
        Run the complete agent pipeline.

        Supports:

        - normal text requests
        - image requests
        - text + image requests
        - multi-turn conversational memory
        """

        # ------------------------------------------------------
        # Normalize image input.
        # ------------------------------------------------------

        has_image = bool(
            image_bytes
            and image_mime_type
        )

        if image_bytes and not image_mime_type:
            raise ValueError(
                "image_mime_type is required when image_bytes "
                "is provided."
            )

        if image_mime_type and not image_bytes:
            raise ValueError(
                "image_bytes is required when image_mime_type "
                "is provided."
            )

        clean_message = (
            message.strip()
            if message
            else ""
        )

        state_metadata = dict(
            metadata or {}
        )

        if has_image:
            state_metadata[
                "has_image"
            ] = True

            state_metadata[
                "image_mime_type"
            ] = image_mime_type

        # ------------------------------------------------------
        # Get/create conversation.
        # ------------------------------------------------------

        conversation = (
            self._get_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
            )
        )

        actual_conversation_id = (
            conversation.conversation_id
        )

        # ------------------------------------------------------
        # Load existing conversation into short-term memory.
        # ------------------------------------------------------

        short_term = (
            self._load_conversation_into_memory(
                conversation
            )
        )

        # ------------------------------------------------------
        # Build previous context BEFORE adding the current
        # message.
        #
        # This gives us clean previous-turn context for task
        # decomposition.
        # ------------------------------------------------------

        previous_conversation_context = (
            self._build_conversation_context(
                short_term=short_term,
                include_current_user_message=True,
            )
        )

        # ------------------------------------------------------
        # Add current user message to persistent in-memory
        # conversation.
        # ------------------------------------------------------

        memory_message = clean_message

        if not memory_message and has_image:
            memory_message = (
                "User uploaded an image for analysis."
            )

        if memory_message:
            self._add_user_message_to_memory(
                conversation=conversation,
                short_term=short_term,
                content=memory_message,
                language=language,
                metadata={
                    "has_image": has_image,
                    "image_mime_type": (
                        image_mime_type
                        if has_image
                        else None
                    ),
                },
            )

        # ------------------------------------------------------
        # Build complete context after adding current message.
        # ------------------------------------------------------

        conversation_context = (
            self._build_conversation_context(
                short_term=short_term,
                include_current_user_message=True,
            )
        )

        # ------------------------------------------------------
        # Create AgentState.
        # ------------------------------------------------------

        state = AgentState(
            user_id=user_id,
            user_message=clean_message,
            conversation_id=actual_conversation_id,
            language=language,
            metadata=state_metadata,
        )

        # ------------------------------------------------------
        # Add complete recent conversation into state.
        # ------------------------------------------------------

        for item in short_term.get_messages(
            self.MAX_CONVERSATION_MESSAGES
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            role = item.get(
                "role",
                "user",
            )

            content = item.get(
                "content",
                "",
            )

            if content:
                state.add_message(
                    role=role,
                    content=content,
                )

        # ------------------------------------------------------
        # Validate state.
        # ------------------------------------------------------

        valid, error = self.supervisor.validate_state(
            state
        )

        if not valid:
            state.status = "failed"
            state.error = error

            return AgentResult(
                success=False,
                response=(
                    error
                    or "Invalid request."
                ),
                status="failed",
                state=state,
                metadata={
                    "conversation_id": (
                        actual_conversation_id
                    ),
                },
            )

        # ------------------------------------------------------
        # Add external context.
        # ------------------------------------------------------

        if context:
            for item in context:
                state.add_context(item)

        try:

            # ==================================================
            # IMAGE-ONLY REQUEST
            # ==================================================

            image_only = (
                has_image
                and not clean_message
            )

            if image_only:
                print("=" * 60)
                print("IMAGE-ONLY REQUEST")
                print("Skipping task decomposition.")
                print("Sending image directly to Gemini.")
                print(
                    f"Conversation ID: "
                    f"{actual_conversation_id}"
                )
                print("=" * 60)

                state.user_message = (
                    "Please analyze the uploaded image "
                    "and answer based on what you can see."
                )

                state.status = "completed"

                response = (
                    await self._generate_final_response(
                        state=state,
                        execution_summary={
                            "image_only": True,
                        },
                        image_bytes=image_bytes,
                        image_mime_type=image_mime_type,
                    )
                )

                state.final_response = response

                response_is_error = (
                    response.startswith(
                        "I could not analyze the uploaded image"
                    )
                    or response.startswith(
                        "Gemini API rate limit or quota"
                    )
                )

                if response_is_error:
                    state.status = "failed"

                else:
                    # --------------------------------------------------
                    # Save assistant response to memory.
                    # --------------------------------------------------

                    self._add_assistant_message_to_memory(
                        conversation=conversation,
                        short_term=short_term,
                        content=response,
                        language=language,
                        metadata={
                            "has_image": True,
                            "image_only": True,
                        },
                    )

                return AgentResult(
                    success=not response_is_error,
                    response=response,
                    status=state.status,
                    state=state,
                    metadata={
                        "task_count": 0,
                        "has_image": True,
                        "image_only": True,
                        "conversation_id": (
                            actual_conversation_id
                        ),
                    },
                )

            # ==================================================
            # TASK DECOMPOSITION
            # ==================================================

            # --------------------------------------------------
            # Give the decomposer the previous conversation
            # so that it does not treat the current turn as an
            # isolated request.
            # --------------------------------------------------

            decomposition_message = (
                clean_message
            )

            if previous_conversation_context:
                decomposition_message = (
                    "CONVERSATION HISTORY:\n"
                    + previous_conversation_context
                    + "\n\n"
                    "CURRENT USER REQUEST:\n"
                    + clean_message
                )

            tasks = await self.decomposer.decompose(
                user_message=decomposition_message,
                language=language,
                context=(
                    context or []
                )
                + [
                    {
                        "type": "conversation_memory",
                        "content": conversation_context,
                    }
                ],
            )

            # ------------------------------------------------------
            # Normalize task confirmation requirements.
            # ------------------------------------------------------

            tasks = self._normalize_tasks(
                tasks
            )

            for task in tasks:
                state.add_task(
                    task.to_dict()
                )

            # ------------------------------------------------------
            # No tasks.
            # ------------------------------------------------------

            if not tasks:
                state.status = "completed"

                response = (
                    await self._generate_final_response(
                        state=state,
                        execution_summary={},
                        image_bytes=image_bytes,
                        image_mime_type=image_mime_type,
                    )
                )

                state.final_response = response

                self._add_assistant_message_to_memory(
                    conversation=conversation,
                    short_term=short_term,
                    content=response,
                    language=language,
                    metadata={
                        "task_count": 0,
                    },
                )

                return AgentResult(
                    success=True,
                    response=response,
                    status="completed",
                    state=state,
                    metadata={
                        "task_count": 0,
                        "has_image": has_image,
                        "conversation_id": (
                            actual_conversation_id
                        ),
                    },
                )

            # ==================================================
            # CREATE EXECUTION PLAN
            # ==================================================

            plan = self.planner.create_plan(
                goal=clean_message,
                tasks=tasks,
            )

            state.metadata[
                "plan_id"
            ] = plan.plan_id

            # ------------------------------------------------------
            # Safety normalization of plan.
            # ------------------------------------------------------

            self._normalize_plan_confirmation(
                plan
            )

            # ==================================================
            # EXECUTE WORKFLOW
            # ==================================================

            workflow_result = (
                await self.workflow.execute(
                    plan=plan,
                    state=state,
                )
            )

            # ==================================================
            # SUPERVISOR EVALUATION
            # ==================================================

            decision = self.supervisor.evaluate(
                state=state,
                workflow_result=workflow_result,
            )

            state.metadata[
                "supervisor"
            ] = decision.to_dict()

            # ==================================================
            # FINAL RESPONSE
            # ==================================================

            response = (
                await self._generate_final_response(
                    state=state,
                    execution_summary=(
                        workflow_result.to_dict()
                    ),
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                )
            )

            state.final_response = response

            # ------------------------------------------------------
            # Save assistant response to conversation memory.
            # ------------------------------------------------------

            self._add_assistant_message_to_memory(
                conversation=conversation,
                short_term=short_term,
                content=response,
                language=language,
                metadata={
                    "task_count": len(tasks),
                    "workflow_success": (
                        workflow_result.success
                    ),
                    "waiting_confirmation": (
                        decision.action
                        == "wait_for_confirmation"
                    ),
                },
            )

            # ==================================================
            # DETERMINE FINAL SUCCESS
            # ==================================================

            success = (
                workflow_result.success
            )

            if (
                decision.action
                == "wait_for_confirmation"
            ):
                success = False

            return AgentResult(
                success=success,
                response=response,
                status=state.status,
                state=state,
                plan=plan.to_dict(),
                metadata={
                    "workflow": (
                        workflow_result.to_dict()
                    ),
                    "supervisor": (
                        decision.to_dict()
                    ),
                    "has_image": has_image,
                    "conversation_id": (
                        actual_conversation_id
                    ),
                },
            )

        except Exception as exc:
            state.status = "failed"
            state.error = str(exc)

            print("=" * 60)
            print("AGENT ERROR")
            print("=" * 60)
            print(
                f"Error type: "
                f"{type(exc).__name__}"
            )
            print(
                f"Error: "
                f"{exc}"
            )
            print("=" * 60)

            return AgentResult(
                success=False,
                response=(
                    f"Agent error: "
                    f"{type(exc).__name__}: {exc}"
                ),
                status="failed",
                state=state,
                metadata={
                    "error": str(exc),
                    "error_type": (
                        type(exc).__name__
                    ),
                    "has_image": has_image,
                    "conversation_id": (
                        actual_conversation_id
                    ),
                },
            )

    # ==========================================================
    # TASK NORMALIZATION
    # ==========================================================

    @staticmethod
    def _is_submission_task(
        task: Task,
    ) -> bool:
        """Determine whether a task is a final submission action."""

        task_type = (
            task.task_type.strip().lower()
            if task.task_type
            else ""
        )

        tool_name = (
            task.tool.strip().lower()
            if task.tool
            else ""
        )

        description = (
            task.description.strip().lower()
            if task.description
            else ""
        )

        submission_types = {
            "submit",
            "submission",
            "application_submission",
            "submit_application",
            "final_submission",
            "finalize_application",
            "external_action",
        }

        submission_tools = {
            "application_submission",
            "submit_application",
            "browser_submit",
            "submission",
        }

        submission_phrases = (
            "submit application",
            "submit the application",
            "submit the form",
            "submit form",
            "final submission",
            "final submit",
            "confirm submission",
            "finalize application",
            "finalise application",
            "send application",
            "send the application",
        )

        if task_type in submission_types:
            return True

        if tool_name in submission_tools:
            return True

        return any(
            phrase in description
            for phrase in submission_phrases
        )

    @classmethod
    def _normalize_tasks(
        cls,
        tasks: list[Task],
    ) -> list[Task]:
        """Normalize LLM-generated tasks before planning."""

        normalized: list[Task] = []

        for task in tasks:
            if cls._is_submission_task(
                task
            ):
                task.requires_confirmation = True
            else:
                task.requires_confirmation = False

            normalized.append(task)

        return normalized

    @classmethod
    def _normalize_plan_confirmation(
        cls,
        plan,
    ) -> None:
        """Apply confirmation safety rules to the final plan."""

        for step in plan.steps:
            description = (
                step.description.strip().lower()
                if step.description
                else ""
            )

            tool_name = (
                step.tool.strip().lower()
                if step.tool
                else ""
            )

            task_type = (
                str(
                    step.metadata.get(
                        "task_type",
                        "",
                    )
                ).strip().lower()
                if step.metadata
                else ""
            )

            submission_types = {
                "submit",
                "submission",
                "application_submission",
                "submit_application",
                "final_submission",
                "finalize_application",
            }

            submission_tools = {
                "application_submission",
                "submit_application",
                "browser_submit",
                "submission",
            }

            submission_phrases = (
                "submit application",
                "submit the application",
                "submit the form",
                "submit form",
                "final submission",
                "final submit",
                "confirm submission",
                "finalize application",
                "finalise application",
                "send application",
                "send the application",
            )

            is_submission = (
                task_type in submission_types
                or tool_name in submission_tools
                or any(
                    phrase in description
                    for phrase in submission_phrases
                )
            )

            step.requires_confirmation = (
                is_submission
            )

    # ==========================================================
    # COMPACT RAG CONTEXT
    # ==========================================================

    def _build_compact_retrieved_context(
        self,
        state: AgentState,
    ) -> str:
        """
        Build a compact RAG context for Gemini.

        Only the most relevant retrieved chunks are included.
        Large metadata objects and duplicated workflow data are
        intentionally excluded.
        """

        if not state.retrieved_context:
            return ""

        results = [
            item
            for item in state.retrieved_context
            if isinstance(
                item,
                dict,
            )
        ]

        def relevance_score(
            item: dict[str, Any],
        ) -> float:
            value = item.get(
                "score",
                0,
            )

            try:
                return float(value)
            except (
                TypeError,
                ValueError,
            ):
                return 0.0

        results.sort(
            key=relevance_score,
            reverse=True,
        )

        results = results[
            : self.MAX_RETRIEVED_RESULTS
        ]

        parts: list[str] = [
            "AUTHORITATIVE RETRIEVED GOVERNMENT INFORMATION:"
        ]

        total_chars = len(
            parts[0]
        )

        for index, item in enumerate(
            results,
            start=1,
        ):
            source = str(
                item.get(
                    "source",
                    "",
                )
            ).strip()

            page = item.get(
                "page_number",
                None,
            )

            text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                continue

            if len(text) > self.MAX_CHUNK_CHARS:
                text = (
                    text[
                        : self.MAX_CHUNK_CHARS
                    ].rstrip()
                    + "..."
                )

            source_block = (
                f"\n\nSource {index}: {source}"
            )

            if page is not None:
                source_block += (
                    f"\nPage: {page}"
                )

            source_block += (
                f"\nContent:\n{text}"
            )

            remaining = (
                self.MAX_RETRIEVED_CONTEXT_CHARS
                - total_chars
            )

            if remaining <= 0:
                break

            if len(source_block) > remaining:
                source_block = (
                    source_block[
                        :remaining
                    ].rstrip()
                    + "..."
                )

            parts.append(
                source_block
            )

            total_chars += len(
                source_block
            )

            if total_chars >= (
                self.MAX_RETRIEVED_CONTEXT_CHARS
            ):
                break

        return "\n".join(parts)

    # ==========================================================
    # COMPACT WORKFLOW CONTEXT
    # ==========================================================

    @staticmethod
    def _build_compact_workflow_context(
        state: AgentState,
        execution_summary: dict[str, Any],
    ) -> str:
        """
        Build a small workflow summary.

        Do not send complete task_results or the complete
        execution_summary because these can contain large
        duplicated RAG payloads.
        """

        parts: list[str] = [
            "AGENT WORKFLOW STATUS:",
            f"Current status: {state.status}",
        ]

        if state.tasks:
            parts.append(
                "Tasks:"
            )

            for index, task in enumerate(
                state.tasks[:10],
                start=1,
            ):
                if isinstance(
                    task,
                    dict,
                ):
                    description = str(
                        task.get(
                            "description",
                            task.get(
                                "name",
                                "",
                            ),
                        )
                    ).strip()

                    if description:
                        parts.append(
                            f"{index}. {description}"
                        )

        if state.completed_tasks:
            parts.append(
                "Completed tasks:"
            )

            for item in state.completed_tasks[:10]:
                if isinstance(
                    item,
                    dict,
                ):
                    description = str(
                        item.get(
                            "description",
                            item.get(
                                "name",
                                "",
                            ),
                        )
                    ).strip()

                    if description:
                        parts.append(
                            f"- {description}"
                        )
                else:
                    parts.append(
                        f"- {str(item)}"
                    )

        if state.failed_tasks:
            parts.append(
                "Failed tasks:"
            )

            for item in state.failed_tasks[:10]:
                if isinstance(
                    item,
                    dict,
                ):
                    description = str(
                        item.get(
                            "description",
                            item.get(
                                "name",
                                "",
                            ),
                        )
                    ).strip()

                    if description:
                        parts.append(
                            f"- {description}"
                        )
                else:
                    parts.append(
                        f"- {str(item)}"
                    )

        if state.verification_results:
            parts.append(
                "Verification results available: yes"
            )
        else:
            parts.append(
                "Verification results available: no"
            )

        waiting_confirmation = (
            state.status
            == "waiting_confirmation"
        )

        parts.append(
            "Waiting for user confirmation: "
            f"{'yes' if waiting_confirmation else 'no'}"
        )

        return "\n".join(parts)

    # ==========================================================
    # FINAL RESPONSE
    # ==========================================================

    async def _generate_final_response(
        self,
        state: AgentState,
        execution_summary: dict[str, Any],
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> str:
        """Generate the final natural-language response."""

        # ------------------------------------------------------
        # Conversation context
        # ------------------------------------------------------

        conversation_context = ""

        if state.messages:
            conversation_lines = []

            for item in state.messages:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                role = item.get(
                    "role",
                    "unknown",
                )

                content = item.get(
                    "content",
                    "",
                )

                if content:
                    conversation_lines.append(
                        f"{role}: {content}"
                    )

            conversation_context = (
                "\n".join(
                    conversation_lines
                )
            )

        # ------------------------------------------------------
        # Compact RAG context
        # ------------------------------------------------------

        retrieved_context = (
            self._build_compact_retrieved_context(
                state
            )
        )

        # ------------------------------------------------------
        # Compact workflow context
        # ------------------------------------------------------

        workflow_context = (
            self._build_compact_workflow_context(
                state,
                execution_summary,
            )
        )

        if retrieved_context:
            retrieved_context = (
                retrieved_context
                + "\n\n"
                + workflow_context
            )
        else:
            retrieved_context = (
                workflow_context
            )

        # ------------------------------------------------------
        # Build Gemini prompt
        # ------------------------------------------------------

        user_message_for_prompt = (
            state.user_message.strip()
        )

        if (
            not user_message_for_prompt
            and image_bytes
        ):
            user_message_for_prompt = (
                "Please analyze the uploaded image "
                "and answer based on what you can see."
            )

        prompt = build_chat_prompt(
            user_message=user_message_for_prompt,
            language=state.language,
            conversation_context=(
                conversation_context
            ),
            retrieved_context=(
                retrieved_context
            ),
        )

        prompt += """

IMPORTANT CONVERSATIONAL MEMORY RULES:

1. Treat the RECENT CONVERSATION HISTORY as part of the
   user's current context.

2. Information explicitly provided by the user in an earlier
   turn remains available for the current conversation.

3. Do NOT ask the user again for information that is already
   explicitly present in the conversation history.

4. Combine relevant information across multiple user turns.

5. If the user supplied a value earlier, use that value when
   answering a later question unless the user has corrected it.

6. When determining eligibility, collect all relevant facts
   from the conversation history before deciding what is
   missing.

7. Only ask for genuinely missing information.

8. Do not assume that a previous assistant question was answered
   unless the user actually supplied the answer.

9. Do not treat information from retrieved government documents
   as if it were personal information supplied by the user.

10. Clearly distinguish:
    - user-provided information
    - government-source information
    - inferred information
    - missing information

11. If the user asks "based on my information", use all relevant
    information supplied throughout the current conversation.

12. If a required value was supplied earlier, do not list it as
    missing merely because it was not included in the latest
    message.

13. If two user messages contain complementary information,
    combine them before determining eligibility.

14. Never fabricate a personal detail that the user did not
    provide.

15. Do not overwrite an earlier user value with an inferred value.

IMPORTANT WORKFLOW AND RAG GROUNDING RULES:

1. The user's actual question is the primary question to answer.

2. When AUTHORITATIVE RETRIEVED GOVERNMENT INFORMATION is
   available, use it as the primary factual source for the answer.

3. Do NOT ignore relevant retrieved government information.

4. Do NOT invent information that is not supported by the
   retrieved government information.

5. If retrieved documents contain only a high-level summary,
   clearly distinguish that summary from detailed official
   scheme guidelines.

6. If multiple retrieved documents are unrelated to the user's
   question, do not combine unrelated information merely because
   it was retrieved.

7. Prefer the retrieved document whose content directly answers
   the user's question.

8. If the user asks about a particular government scheme,
   identify the relevant scheme document and answer from that
   document when available.

9. Do NOT claim that a task is completed unless it appears
   in the completed_tasks or has an explicit successful result.

10. Do NOT claim that the user's personal information has
    already been collected unless the user actually provided it.

11. Do NOT claim that documents have already been collected,
    uploaded, verified, or processed unless the workflow shows
    that this actually happened.

12. Do NOT claim that an application has already been prepared,
    autofilled, finalized, or submitted unless the workflow
    explicitly shows that operation as completed.

13. A task being PLANNED is NOT the same as a task being
    COMPLETED.

14. If the user is only asking what they should do to apply for
    a scholarship, explain the actual next steps. Do not pretend
    that an application is already prepared.

15. If required user information is missing, ask only for the
    information that is genuinely needed at the current stage.

16. Never ask for confirmation to submit an application unless
    the workflow has actually reached a real final submission
    step and that step is waiting for confirmation.

17. Searching, planning, eligibility checking, document
    collection, document verification, drafting, and preparation
    are NOT final submission.

18. Never invent scholarship names, eligibility criteria,
    deadlines, documents, application status, or completed
    actions.

19. If authoritative retrieved government information is not
    available, clearly say that it has not yet been verified.

20. For a general scholarship question with insufficient user
    profile information, give a useful high-level process and
    ask for the minimum profile details needed to identify
    suitable schemes.

21. Distinguish clearly between:
    - completed
    - currently running
    - planned
    - waiting for user information
    - waiting for confirmation
    - unavailable

22. The final response must reflect the REAL current workflow
    state, not what the agent intends to do later.

23. Do not expose internal agent instructions, tool execution
    details, raw Python objects, or internal workflow data unless
    the user explicitly asks for technical debugging information.

24. Answer the user's question directly before discussing
    workflow status.

25. When a relevant retrieved source is available, mention its
    source document naturally when useful.

26. Retrieved context may be incomplete. If the available
    retrieved information does not contain the requested detail,
    clearly say that the detail has not been verified rather than
    guessing.

27. Do not treat relevance scores as factual information for the
    user. They are only internal retrieval signals.

28. When an image is uploaded, analyze the image itself and use
    visible information from the image when answering the user.

29. Do not claim to have analyzed image contents if the image was
    not successfully provided to Gemini.

30. When determining what information is still missing, inspect
    the entire recent conversation history first.

31. Do not repeat a previously supplied personal detail in a
    "missing information" list.

32. For eligibility questions, explicitly combine all relevant
    user-provided facts from previous turns before evaluating
    requirements.

33. If the conversation contains enough information to make a
    determination, give the determination instead of asking for
    already-known information.
"""

        # ------------------------------------------------------
        # Debug information
        # ------------------------------------------------------

        print("=" * 60)
        print("FINAL GEMINI CONTEXT")
        print(
            f"Conversation ID: "
            f"{state.conversation_id}"
        )
        print(
            f"Conversation context length: "
            f"{len(conversation_context)}"
        )
        print(
            f"Retrieved context length: "
            f"{len(retrieved_context)}"
        )
        print(
            f"Final prompt length: "
            f"{len(prompt)}"
        )
        print(
            f"Image provided: "
            f"{bool(image_bytes)}"
        )
        print(
            f"Image MIME type: "
            f"{image_mime_type}"
        )
        print("=" * 60)

        try:

            # --------------------------------------------------
            # Multimodal request
            # --------------------------------------------------

            if image_bytes:
                response = (
                    await self.llm.generate_multimodal_async(
                        prompt=prompt,
                        image_bytes=image_bytes,
                        mime_type=(
                            image_mime_type
                            or "image/jpeg"
                        ),
                    )
                )

            # --------------------------------------------------
            # Normal text request
            # --------------------------------------------------

            else:
                response = (
                    await self.llm.generate_async(
                        prompt=prompt,
                    )
                )

            response = (
                response.strip()
            )

            if response:
                return response

        except Exception as exc:
            print("=" * 60)
            print(
                "FINAL RESPONSE GENERATION ERROR"
            )
            print("=" * 60)
            print(
                f"Error type: "
                f"{type(exc).__name__}"
            )
            print(
                f"Error: "
                f"{exc}"
            )
            print("=" * 60)

            if image_bytes:
                return (
                    "I could not analyze the uploaded image "
                    "because the AI image-processing request "
                    "failed. "
                    f"Error: {type(exc).__name__}: {exc}"
                )

        return self._fallback_response(
            state
        )

    # ==========================================================
    # FALLBACK RESPONSE
    # ==========================================================

    @staticmethod
    def _fallback_response(
        state: AgentState,
    ) -> str:
        """Generate a safe fallback response."""

        if (
            state.status
            == "waiting_confirmation"
        ):
            return (
                "The workflow has reached an action that requires "
                "your confirmation before it can continue."
            )

        if state.status == "completed":
            return (
                "I processed the available information successfully. "
                "No external submission was performed unless "
                "explicitly confirmed and completed."
            )

        if state.status == "failed":
            return (
                "I could not complete the requested workflow. "
                "Please review the request and try again."
            )

        if state.status == "waiting_user":
            return (
                "I need some additional information from you "
                "before I can continue."
            )

        return (
            "I understand your request. I can help you work "
            "through the required steps."
        )