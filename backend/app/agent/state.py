"""
Agent state management.

Stores all information required during an agent execution,
including user input, tasks, results, retrieved context,
verification results, and execution status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================
# TIME HELPER
# ============================================================

def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


# ============================================================
# AGENT STATE
# ============================================================

@dataclass
class AgentState:
    """
    Runtime state of an Agentic AI task.

    The state is intentionally framework-independent so that
    it can later be connected to LangGraph or another workflow
    engine if required.
    """

    user_id: str

    user_message: str

    conversation_id: str | None = None

    language: str = "en"

    session_id: str | None = None

    status: str = "initialized"

    current_step: int = 0

    total_steps: int = 0

    tasks: list[dict[str, Any]] = field(default_factory=list)

    completed_tasks: list[dict[str, Any]] = field(
        default_factory=list
    )

    failed_tasks: list[dict[str, Any]] = field(
        default_factory=list
    )

    task_results: dict[str, Any] = field(
        default_factory=dict
    )

    retrieved_context: list[dict[str, Any]] = field(
        default_factory=list
    )

    documents: list[dict[str, Any]] = field(
        default_factory=list
    )

    verification_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    application_data: dict[str, Any] = field(
        default_factory=dict
    )

    tool_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    messages: list[dict[str, Any]] = field(
        default_factory=list
    )

    final_response: str | None = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=utc_now
    )

    updated_at: datetime = field(
        default_factory=utc_now
    )

    # ========================================================
    # UPDATE STATE
    # ========================================================

    def update(self, **kwargs: Any) -> None:
        """
        Update state fields and refresh the timestamp.
        """

        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(
                    f"AgentState has no field named '{key}'."
                )

            setattr(self, key, value)

        self.updated_at = utc_now()

    # ========================================================
    # TASK MANAGEMENT
    # ========================================================

    def add_task(
        self,
        task: dict[str, Any],
    ) -> None:
        """
        Add a task to the execution plan.
        """

        if not isinstance(task, dict):
            raise TypeError(
                "Task must be a dictionary."
            )

        self.tasks.append(task)

        self.total_steps = len(self.tasks)

        if self.status == "initialized":
            self.status = "planning"

        self.updated_at = utc_now()

    def mark_task_completed(
        self,
        task_id: str,
        result: Any = None,
    ) -> None:
        """
        Mark a task as successfully completed.
        """

        task = self._find_task(task_id)

        if task is None:
            raise ValueError(
                f"Task '{task_id}' was not found."
            )

        # Prevent duplicate completion records.
        already_completed = any(
            item.get("id") == task_id
            for item in self.completed_tasks
        )

        task["status"] = "completed"

        if result is not None:
            task["result"] = result

        if not already_completed:
            self.completed_tasks.append(
                task.copy()
            )

        self.task_results[task_id] = result

        self.current_step = min(
            self.current_step + 1,
            self.total_steps,
        )

        if self.is_complete():
            self.status = "completed"
        else:
            self.status = "running"

        self.updated_at = utc_now()

    def mark_task_failed(
        self,
        task_id: str,
        error: str,
    ) -> None:
        """
        Mark a task as failed.
        """

        if not error:
            raise ValueError(
                "Task error cannot be empty."
            )

        task = self._find_task(task_id)

        if task is None:
            raise ValueError(
                f"Task '{task_id}' was not found."
            )

        already_failed = any(
            item.get("id") == task_id
            for item in self.failed_tasks
        )

        task["status"] = "failed"
        task["error"] = error

        if not already_failed:
            self.failed_tasks.append(
                task.copy()
            )

        self.task_results[task_id] = {
            "success": False,
            "error": error,
        }

        self.status = "failed"
        self.error = error

        self.updated_at = utc_now()

    # ========================================================
    # MESSAGE MANAGEMENT
    # ========================================================

    def add_message(
        self,
        role: str,
        content: str,
        **metadata: Any,
    ) -> None:
        """
        Add a conversation message to the state.
        """

        if not role:
            raise ValueError(
                "Message role cannot be empty."
            )

        if not content:
            raise ValueError(
                "Message content cannot be empty."
            )

        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": utc_now().isoformat(),
                "metadata": metadata,
            }
        )

        self.updated_at = utc_now()

    # ========================================================
    # RAG CONTEXT
    # ========================================================

    def add_context(
        self,
        context: dict[str, Any],
    ) -> None:
        """
        Add retrieved RAG context.
        """

        if not isinstance(context, dict):
            raise TypeError(
                "Context must be a dictionary."
            )

        self.retrieved_context.append(
            context
        )

        self.updated_at = utc_now()

    # ========================================================
    # TOOL RESULTS
    # ========================================================

    def add_tool_result(
        self,
        tool_name: str,
        result: Any,
    ) -> None:
        """
        Store the result of a tool execution.
        """

        if not tool_name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        self.tool_results.append(
            {
                "tool": tool_name,
                "result": result,
                "timestamp": utc_now().isoformat(),
            }
        )

        self.updated_at = utc_now()

    # ========================================================
    # STATE CHECKS
    # ========================================================

    def is_complete(self) -> bool:
        """
        Return True when all planned tasks are completed.
        """

        if not self.tasks:
            return False

        completed_ids = {
            task.get("id")
            for task in self.completed_tasks
        }

        task_ids = {
            task.get("id")
            for task in self.tasks
        }

        return task_ids.issubset(completed_ids)

    def has_failed(self) -> bool:
        """
        Return True if at least one task has failed.
        """

        return bool(self.failed_tasks)

    # ========================================================
    # TASK LOOKUP
    # ========================================================

    def _find_task(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        """
        Find a task by ID.
        """

        for task in self.tasks:
            if task.get("id") == task_id:
                return task

        return None

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize state into a dictionary.
        """

        return {
            "user_id": self.user_id,
            "user_message": self.user_message,
            "conversation_id": self.conversation_id,
            "language": self.language,
            "session_id": self.session_id,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "tasks": self.tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "task_results": self.task_results,
            "retrieved_context": self.retrieved_context,
            "documents": self.documents,
            "verification_results": self.verification_results,
            "application_data": self.application_data,
            "tool_results": self.tool_results,
            "messages": self.messages,
            "final_response": self.final_response,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }