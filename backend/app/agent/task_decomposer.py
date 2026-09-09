"""
Task decomposition.

Breaks a complex user request into smaller executable tasks.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.llm.client import GeminiClient
from backend.app.llm.parser import parse_json_response
from backend.app.llm.prompts import build_planning_prompt


# ============================================================
# TASK MODEL
# ============================================================

@dataclass
class Task:
    """
    Represents one executable agent task.
    """

    id: str
    description: str
    task_type: str = "general"
    priority: int = 1
    dependencies: list[str] = field(default_factory=list)
    tool: str | None = None
    status: str = "pending"
    requires_confirmation: bool = False
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert task to dictionary.
        """

        return {
            "id": self.id,
            "description": self.description,
            "task_type": self.task_type,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "tool": self.tool,
            "status": self.status,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "metadata": self.metadata,
        }


# ============================================================
# TASK DECOMPOSER
# ============================================================

class TaskDecomposer:
    """
    Decomposes a user request into executable tasks.

    Gemini is used for high-level task planning, while
    deterministic routing ensures government-document
    questions use the RAG tool.
    """

    VALID_TOOLS = {
        "rag",
        "search",
        "document",
        "verification",
        "application",
        "notification",
    }

    GOVERNMENT_KEYWORDS = {
        "government",
        "govt",
        "scholarship",
        "pension",
        "housing scheme",
        "certificate",
        "income certificate",
        "caste certificate",
        "domicile",
        "residence certificate",
        "pm yasasvi",
        "yasasvi",
        "pm kisan",
        "ujjwala",
        "ayushman",
        "pmjay",
        "jan dhan",
        "sukanya",
        "svanidhi",
        "nsap",
        "pmay",
        "national scholarship",
        "post matric",
        "central sector scholarship",
        "eligibility",
        "scheme",
        "guidelines",
        "government pdf",
    }

    # Consequential task types always require confirmation.
    CONFIRMATION_TASK_TYPES = {
        "submission",
        "application_submission",
        "external_submission",
        "final_submission",
        "payment",
        "external_action",
    }

    CONFIRMATION_KEYWORDS = {
        "submit application",
        "submit the application",
        "final submit",
        "final submission",
        "send application",
        "apply now",
        "complete application",
        "make payment",
        "pay fee",
        "external submission",
    }

    def __init__(
        self,
        llm_client: GeminiClient | None = None,
    ) -> None:
        self.llm = llm_client or GeminiClient()

    # ========================================================
    # DECOMPOSE
    # ========================================================

    async def decompose(
        self,
        user_message: str,
        language: str = "en",
        context: list[dict[str, Any]] | None = None,
    ) -> list[Task]:
        """
        Decompose a user request into executable tasks.
        """

        if not user_message or not user_message.strip():
            return []

        user_message = user_message.strip()
        context = context or []

        # ----------------------------------------------------
        # Deterministic government-document routing.
        # ----------------------------------------------------

        if self._is_government_document_question(
            user_message
        ):
            return [
                self._create_rag_task(
                    user_message=user_message,
                    language=language,
                    routing="deterministic_rag",
                )
            ]

        # ----------------------------------------------------
        # Available tools.
        # ----------------------------------------------------

        available_tools = (
            "rag, "
            "search, "
            "document, "
            "verification, "
            "application, "
            "notification"
        )

        context_text = ""

        if context:
            context_text = "\n\nAdditional context:\n"

            for item in context:
                if isinstance(item, dict):
                    context_text += f"{item}\n"
                else:
                    context_text += f"{str(item)}\n"

        available_tools_text = (
            f"Available tools: {available_tools}\n"
            "\nTool usage rules:\n"
            "- rag: search official government PDFs and "
            "authoritative retrieved documents.\n"
            "- search: perform general web/search operations "
            "when appropriate.\n"
            "- document: process user-uploaded documents.\n"
            "- verification: compare user information/documents "
            "against requirements.\n"
            "- application: assist with application workflows.\n"
            "- notification: send notifications when required.\n"
            "- Do not use browser automation for local "
            "government-PDF retrieval.\n"
            "- Government scheme eligibility questions should "
            "use rag.\n"
            "- Information retrieval does not require "
            "confirmation.\n"
            "- Consequential external actions require explicit "
            "user confirmation.\n"
            "- Never claim an external action is completed "
            "unless execution is actually confirmed.\n"
            f"{context_text}"
            f"\nUser language: {language}"
        )

        prompt = build_planning_prompt(
            user_request=user_message,
            available_tools=available_tools_text,
        )

        try:
            response = await self.llm.generate_json_async(
                prompt=prompt,
            )

            parsed = parse_json_response(response)

            tasks = self._parse_tasks(parsed)

            if tasks:
                return tasks

        except Exception as exc:
            print("=" * 60)
            print("TASK DECOMPOSITION ERROR")
            print("=" * 60)
            print(f"Error type: {type(exc).__name__}")
            print(f"Error: {exc}")
            print("=" * 60)

        return self._fallback_decomposition(
            user_message
        )

    # ========================================================
    # PARSE TASKS
    # ========================================================

    def _parse_tasks(
        self,
        data: Any,
    ) -> list[Task]:
        """
        Convert LLM planning output into Task objects.
        """

        if isinstance(data, dict):
            raw_tasks = data.get(
                "tasks",
                [],
            )

            if not raw_tasks:
                raw_tasks = data.get(
                    "plan",
                    [],
                )

        elif isinstance(data, list):
            raw_tasks = data

        else:
            return []

        if not isinstance(raw_tasks, list):
            return []

        tasks: list[Task] = []

        for index, raw_task in enumerate(
            raw_tasks,
            start=1,
        ):
            # ------------------------------------------------
            # String task
            # ------------------------------------------------

            if isinstance(raw_task, str):
                description = raw_task.strip()

                if not description:
                    continue

                task = Task(
                    id=f"task_{uuid.uuid4().hex[:8]}",
                    description=description,
                    priority=index,
                )

                self._apply_deterministic_rules(task)

                tasks.append(task)

                continue

            # ------------------------------------------------
            # Dictionary task
            # ------------------------------------------------

            if not isinstance(raw_task, dict):
                continue

            description = str(
                raw_task.get(
                    "description",
                    raw_task.get(
                        "task",
                        "",
                    ),
                )
            ).strip()

            if not description:
                continue

            dependencies = raw_task.get(
                "dependencies",
                [],
            )

            if not isinstance(
                dependencies,
                list,
            ):
                dependencies = []

            task_type = str(
                raw_task.get(
                    "task_type",
                    raw_task.get(
                        "type",
                        "general",
                    ),
                )
            ).strip().lower()

            if not task_type:
                task_type = "general"

            tool = self._normalize_tool(
                raw_task.get("tool")
            )

            requires_confirmation = bool(
                raw_task.get(
                    "requires_confirmation",
                    False,
                )
            )

            metadata = {
                key: value
                for key, value in raw_task.items()
                if key not in {
                    "id",
                    "description",
                    "task",
                    "task_type",
                    "type",
                    "dependencies",
                    "tool",
                    "requires_confirmation",
                }
            }

            task = Task(
                id=str(
                    raw_task.get(
                        "id",
                        f"task_{uuid.uuid4().hex[:8]}",
                    )
                ),
                description=description,
                task_type=task_type,
                priority=index,
                dependencies=[
                    str(item)
                    for item in dependencies
                    if item
                ],
                tool=tool,
                status="pending",
                requires_confirmation=(
                    requires_confirmation
                ),
                metadata=metadata,
            )

            self._apply_deterministic_rules(task)

            tasks.append(task)

        return tasks

    # ========================================================
    # DETERMINISTIC SAFETY RULES
    # ========================================================

    def _apply_deterministic_rules(
        self,
        task: Task,
    ) -> None:
        """
        Apply deterministic routing and safety rules.

        These rules override unsafe or inconsistent LLM output.
        """

        # ----------------------------------------------------
        # Government questions always use RAG.
        # ----------------------------------------------------

        if self._is_government_document_question(
            task.description
        ):
            task.tool = "rag"
            task.requires_confirmation = False

            task.metadata["routing"] = (
                "deterministic_rag"
            )

        # ----------------------------------------------------
        # RAG is informational and does not require
        # confirmation.
        # ----------------------------------------------------

        if task.tool == "rag":
            task.requires_confirmation = False

        # ----------------------------------------------------
        # Consequential task types require confirmation.
        # ----------------------------------------------------

        normalized_type = task.task_type.lower()

        if normalized_type in self.CONFIRMATION_TASK_TYPES:
            task.requires_confirmation = True

        # ----------------------------------------------------
        # Consequential submission phrases require
        # confirmation even if Gemini selected another type.
        # ----------------------------------------------------

        if self._requires_confirmation_by_description(
            task.description
        ):
            task.requires_confirmation = True

        # ----------------------------------------------------
        # Browser/application assistance itself does not
        # automatically mean submission.
        # ----------------------------------------------------

        if (
            task.tool == "application"
            and self._requires_confirmation_by_description(
                task.description
            )
        ):
            task.requires_confirmation = True

    # ========================================================
    # TOOL NORMALIZATION
    # ========================================================

    def _normalize_tool(
        self,
        raw_tool: Any,
    ) -> str | None:
        """
        Normalize the tool returned by Gemini to one of the
        registered tool names.
        """

        if raw_tool is None:
            return None

        tool = str(raw_tool).strip().lower()

        if not tool:
            return None

        if tool in self.VALID_TOOLS:
            return tool

        aliases = {
            "rag/document retrieval": "rag",
            "rag retrieval": "rag",
            "document retrieval": "rag",
            "government document retrieval": "rag",
            "government pdf retrieval": "rag",
            "pdf retrieval": "rag",
            "retrieval": "rag",
            "web search": "search",
            "browser search": "search",
            "document processing": "document",
            "document processing tool": "document",
            "verification tool": "verification",
            "application assistance": "application",
            "application tool": "application",
            "browser": "application",
            "browser automation": "application",
            "notification tool": "notification",
        }

        if tool in aliases:
            return aliases[tool]

        # Safe partial matching for RAG.
        if (
            "government" in tool
            and (
                "pdf" in tool
                or "document" in tool
                or "retriev" in tool
                or "rag" in tool
            )
        ):
            return "rag"

        if "rag" in tool:
            return "rag"

        return None

    # ========================================================
    # GOVERNMENT QUESTION DETECTION
    # ========================================================

    def _is_government_document_question(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether a request should be routed to
        the local government-PDF RAG knowledge base.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            text.lower().strip(),
        )

        return any(
            keyword in normalized
            for keyword in self.GOVERNMENT_KEYWORDS
        )

    # ========================================================
    # CONFIRMATION DETECTION
    # ========================================================

    def _requires_confirmation_by_description(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether a task description represents
        a consequential external action.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            text.lower().strip(),
        )

        return any(
            keyword in normalized
            for keyword in self.CONFIRMATION_KEYWORDS
        )

    # ========================================================
    # RAG TASK CREATION
    # ========================================================

    @staticmethod
    def _create_rag_task(
        user_message: str,
        language: str,
        routing: str,
    ) -> Task:
        """
        Create a deterministic government RAG task.
        """

        return Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            description=(
                "Retrieve and verify the relevant official "
                "government scheme information from the "
                "local government PDF knowledge base."
            ),
            task_type="information_retrieval",
            priority=1,
            tool="rag",
            requires_confirmation=False,
            metadata={
                "source": "government_pdfs",
                "routing": routing,
                "user_request": user_message,
                "language": language,
            },
        )

    # ========================================================
    # FALLBACK
    # ========================================================

    def _fallback_decomposition(
        self,
        user_message: str,
    ) -> list[Task]:
        """
        Deterministic fallback when Gemini cannot produce
        a valid plan.
        """

        if self._is_government_document_question(
            user_message
        ):
            return [
                self._create_rag_task(
                    user_message=user_message,
                    language="en",
                    routing="fallback_rag",
                )
            ]

        task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            description=user_message,
            task_type="general",
            priority=1,
        )

        self._apply_deterministic_rules(task)

        return [task]