
"""
Agent supervisor.

Monitors agent execution and determines whether the workflow
should continue, stop, retry, or wait for user confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.agent.state import AgentState
from backend.app.agent.workflow import WorkflowResult


@dataclass
class SupervisorDecision:
    """Decision made by the supervisor."""

    action: str
    reason: str
    should_continue: bool
    requires_user_action: bool = False
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary."""

        return {
            "action": self.action,
            "reason": self.reason,
            "should_continue": self.should_continue,
            "requires_user_action": (
                self.requires_user_action
            ),
            "metadata": self.metadata or {},
        }


class AgentSupervisor:
    """Supervises agent workflow execution."""

    def __init__(
        self,
        max_retries: int = 2,
    ):
        self.max_retries = max(
            0,
            max_retries,
        )

    def evaluate(
        self,
        state: AgentState,
        workflow_result: WorkflowResult,
    ) -> SupervisorDecision:
        """Evaluate the current workflow state."""

        if workflow_result.status == "completed":
            return SupervisorDecision(
                action="finish",
                reason="All planned tasks completed.",
                should_continue=False,
            )

        if workflow_result.status == "waiting_confirmation":
            return SupervisorDecision(
                action="wait_for_confirmation",
                reason=(
                    workflow_result.error
                    or "User confirmation is required."
                ),
                should_continue=False,
                requires_user_action=True,
            )

        if workflow_result.status == "failed":
            retry_count = int(
                state.metadata.get(
                    "retry_count",
                    0,
                )
            )

            if retry_count < self.max_retries:
                state.metadata["retry_count"] = (
                    retry_count + 1
                )

                return SupervisorDecision(
                    action="retry",
                    reason=(
                        "The workflow failed and the "
                        "maximum retry count has not "
                        "been reached."
                    ),
                    should_continue=True,
                    metadata={
                        "retry_count": retry_count + 1,
                        "max_retries": self.max_retries,
                    },
                )

            return SupervisorDecision(
                action="stop",
                reason=(
                    "The workflow failed and the maximum "
                    "retry count has been reached."
                ),
                should_continue=False,
            )

        if workflow_result.status == "blocked":
            return SupervisorDecision(
                action="stop",
                reason=(
                    "The workflow is blocked because "
                    "no executable next step exists."
                ),
                should_continue=False,
            )

        return SupervisorDecision(
            action="continue",
            reason="Workflow can continue.",
            should_continue=True,
        )

    def validate_state(
        self,
        state: AgentState,
    ) -> tuple[bool, str | None]:
        """Validate basic state consistency."""

        if not state.user_id:
            return False, "User ID is missing."

        if not state.user_message.strip():
            return False, "User message is empty."

        if state.current_step < 0:
            return False, "Invalid current step."

        if state.total_steps < 0:
            return False, "Invalid total step count."

        return True, None
