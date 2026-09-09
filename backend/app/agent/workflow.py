
"""
Agent workflow execution.

Executes planned tasks sequentially and records their results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from backend.app.agent.planner import (
    AgentPlanner,
    Plan,
    PlanStep,
)
from backend.app.agent.state import AgentState


ToolExecutor = Callable[
    [PlanStep, AgentState],
    Awaitable[Any],
]


@dataclass
class WorkflowResult:
    """Result returned after workflow execution."""

    success: bool
    status: str
    completed_steps: int
    failed_steps: int
    results: dict[str, Any] = field(
        default_factory=dict
    )
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "success": self.success,
            "status": self.status,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "results": self.results,
            "error": self.error,
        }


class Workflow:
    """Executes an agent plan."""

    def __init__(
        self,
        planner: AgentPlanner | None = None,
    ):
        self.planner = planner or AgentPlanner()
        self._executors: dict[
            str,
            ToolExecutor,
        ] = {}

    def register_executor(
        self,
        tool_name: str,
        executor: ToolExecutor,
    ) -> None:
        """Register an executor for a tool."""

        self._executors[tool_name] = executor

    async def execute(
        self,
        plan: Plan,
        state: AgentState,
    ) -> WorkflowResult:
        """Execute a complete plan."""

        plan.status = "running"
        state.status = "running"

        completed_task_ids: set[str] = {
            task.get("id")
            for task in state.completed_tasks
            if task.get("id")
        }

        results: dict[str, Any] = {}

        while True:
            step = self.planner.get_next_step(
                plan,
                completed_task_ids,
            )

            if step is None:
                break

            if step.requires_confirmation:
                plan.status = "waiting_confirmation"
                state.status = "waiting_confirmation"

                return WorkflowResult(
                    success=False,
                    status="waiting_confirmation",
                    completed_steps=len(
                        completed_task_ids
                    ),
                    failed_steps=len(
                        state.failed_tasks
                    ),
                    results=results,
                    error=(
                        "User confirmation is required "
                        "before executing: "
                        f"{step.description}"
                    ),
                )

            try:
                result = await self._execute_step(
                    step,
                    state,
                )

                results[step.task_id] = result

                self.planner.mark_step_completed(
                    plan,
                    step.step_id,
                )

                state.mark_task_completed(
                    step.task_id,
                    result,
                )

                completed_task_ids.add(
                    step.task_id
                )

            except Exception as exc:
                error_message = str(exc)

                self.planner.mark_step_failed(
                    plan,
                    step.step_id,
                )

                state.mark_task_failed(
                    step.task_id,
                    error_message,
                )

                plan.status = "failed"
                state.status = "failed"
                state.error = error_message

                return WorkflowResult(
                    success=False,
                    status="failed",
                    completed_steps=len(
                        completed_task_ids
                    ),
                    failed_steps=len(
                        state.failed_tasks
                    ),
                    results=results,
                    error=error_message,
                )

        if self.planner.is_complete(plan):
            plan.status = "completed"
            state.status = "completed"

            return WorkflowResult(
                success=True,
                status="completed",
                completed_steps=len(
                    completed_task_ids
                ),
                failed_steps=len(
                    state.failed_tasks
                ),
                results=results,
            )

        plan.status = "blocked"
        state.status = "blocked"

        return WorkflowResult(
            success=False,
            status="blocked",
            completed_steps=len(
                completed_task_ids
            ),
            failed_steps=len(
                state.failed_tasks
            ),
            results=results,
            error=(
                "The workflow could not determine "
                "a next executable step."
            ),
        )

    async def _execute_step(
        self,
        step: PlanStep,
        state: AgentState,
    ) -> Any:
        """
        Execute one workflow step.

        Registered tools perform the actual operation.
        If no tool is registered, the step is only
        acknowledged and no external action is performed.
        """

        if step.tool:
            executor = self._executors.get(
                step.tool
            )

            if executor is None:
                raise RuntimeError(
                    f"No executor registered for tool "
                    f"'{step.tool}'."
                )

            result = await executor(
                step,
                state,
            )

            state.add_tool_result(
                step.tool,
                result,
            )

            return result

        return {
            "success": True,
            "status": "acknowledged",
            "executed": False,
            "task_id": step.task_id,
            "description": step.description,
            "message": (
                "Task identified, but no external "
                "tool is connected. No external action "
                "was performed."
            ),
        }
