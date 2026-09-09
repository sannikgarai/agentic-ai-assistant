"""
Agent planning system.

Creates an ordered execution plan from decomposed tasks.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.agent.task_decomposer import Task


# ============================================================
# PLAN STEP
# ============================================================

@dataclass
class PlanStep:
    """One step in an agent execution plan."""

    step_id: str

    task_id: str

    description: str

    order: int

    tool: str | None = None

    dependencies: list[str] = field(
        default_factory=list
    )

    requires_confirmation: bool = False

    status: str = "pending"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert plan step to dictionary."""

        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "description": self.description,
            "order": self.order,
            "tool": self.tool,
            "dependencies": self.dependencies,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "status": self.status,
            "metadata": self.metadata,
        }


# ============================================================
# PLAN
# ============================================================

@dataclass
class Plan:
    """Complete execution plan."""

    plan_id: str

    goal: str

    steps: list[PlanStep] = field(
        default_factory=list
    )

    status: str = "created"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary."""

        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "status": self.status,
            "metadata": self.metadata,
        }


# ============================================================
# AGENT PLANNER
# ============================================================

class AgentPlanner:
    """Builds executable plans from tasks."""

    # ========================================================
    # CREATE PLAN
    # ========================================================

    def create_plan(
        self,
        goal: str,
        tasks: list[Task],
    ) -> Plan:
        """
        Create an ordered execution plan.

        Tasks are ordered according to their dependencies.
        Consequential external actions require confirmation.
        """

        plan = Plan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            goal=goal,
        )

        if not tasks:
            plan.status = "empty"
            return plan

        # ----------------------------------------------------
        # Validate task IDs.
        # ----------------------------------------------------

        task_ids = [task.id for task in tasks]

        if len(task_ids) != len(set(task_ids)):
            plan.status = "invalid"

            plan.metadata["error"] = (
                "Duplicate task IDs detected."
            )

            return plan

        # ----------------------------------------------------
        # Order tasks.
        # ----------------------------------------------------

        ordered_tasks = self._order_tasks(tasks)

        # ----------------------------------------------------
        # Create plan steps.
        # ----------------------------------------------------

        for index, task in enumerate(
            ordered_tasks,
            start=1,
        ):
            plan.steps.append(
                PlanStep(
                    step_id=(
                        f"step_"
                        f"{uuid.uuid4().hex[:8]}"
                    ),
                    task_id=task.id,
                    description=task.description,
                    order=index,
                    tool=task.tool,
                    dependencies=list(
                        task.dependencies
                    ),
                    requires_confirmation=(
                        self._requires_confirmation(task)
                    ),
                    status="pending",
                    metadata=dict(
                        task.metadata
                    ),
                )
            )

        plan.status = "ready"

        return plan

    # ========================================================
    # CONFIRMATION
    # ========================================================

    def _requires_confirmation(
        self,
        task: Task,
    ) -> bool:
        """
        Determine whether a task requires user confirmation.

        Retrieval, planning, searching, document analysis,
        and eligibility checking do not require confirmation.

        Consequential external actions do.
        """

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

        # ----------------------------------------------------
        # Explicit task flag.
        # ----------------------------------------------------

        if task.requires_confirmation:
            return True

        # ----------------------------------------------------
        # Consequential task types.
        # ----------------------------------------------------

        confirmation_types = {
            "submit",
            "submission",
            "application_submission",
            "submit_application",
            "external_action",
            "final_submission",
            "finalize_application",
            "finalise_application",
            "payment",
        }

        if task_type in confirmation_types:
            return True

        # ----------------------------------------------------
        # Consequential tools.
        # ----------------------------------------------------

        confirmation_tools = {
            "application_submission",
            "submit_application",
            "browser_submit",
            "submission",
        }

        if tool_name in confirmation_tools:
            return True

        # ----------------------------------------------------
        # Explicit final-submission language.
        # ----------------------------------------------------

        submission_phrases = {
            "submit application",
            "submit the application",
            "final submit",
            "final submission",
            "confirm submission",
            "submit form",
            "submit the form",
            "finalize application",
            "finalise application",
            "send application",
            "make payment",
            "pay fee",
        }

        return any(
            phrase in description
            for phrase in submission_phrases
        )

    # ========================================================
    # TASK ORDERING
    # ========================================================

    def _order_tasks(
        self,
        tasks: list[Task],
    ) -> list[Task]:
        """
        Order tasks while respecting dependencies.

        Uses topological ordering. Missing dependencies do not
        remove a task from the plan.
        """

        task_map = {
            task.id: task
            for task in tasks
        }

        result: list[Task] = []

        visited: set[str] = set()

        visiting: set[str] = set()

        def visit(task: Task) -> None:
            """Visit a task and its dependencies."""

            if task.id in visited:
                return

            # ------------------------------------------------
            # Circular dependency protection.
            # ------------------------------------------------

            if task.id in visiting:
                return

            visiting.add(task.id)

            for dependency_id in task.dependencies:
                dependency = task_map.get(
                    dependency_id
                )

                if dependency is not None:
                    visit(dependency)

            visiting.remove(task.id)

            visited.add(task.id)

            result.append(task)

        sorted_tasks = sorted(
            tasks,
            key=lambda item: (
                item.priority,
                item.id,
            ),
        )

        for task in sorted_tasks:
            visit(task)

        return result

    # ========================================================
    # GET NEXT STEP
    # ========================================================

    def get_next_step(
        self,
        plan: Plan,
        completed_task_ids: set[str],
    ) -> PlanStep | None:
        """
        Return the next executable plan step.

        A step is executable when:
        - it is still pending
        - all dependencies are completed
        """

        for step in sorted(
            plan.steps,
            key=lambda item: item.order,
        ):
            if step.status != "pending":
                continue

            dependencies_completed = all(
                dependency in completed_task_ids
                for dependency in step.dependencies
            )

            if dependencies_completed:
                return step

        return None

    # ========================================================
    # STEP STATUS
    # ========================================================

    def mark_step_completed(
        self,
        plan: Plan,
        step_id: str,
    ) -> bool:
        """Mark a plan step as completed."""

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = "completed"

                if self.is_complete(plan):
                    plan.status = "completed"

                return True

        return False

    def mark_step_failed(
        self,
        plan: Plan,
        step_id: str,
    ) -> bool:
        """Mark a plan step as failed."""

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = "failed"
                plan.status = "failed"
                return True

        return False

    # ========================================================
    # PLAN COMPLETION
    # ========================================================

    def is_complete(
        self,
        plan: Plan,
    ) -> bool:
        """
        Check whether every step in the plan is completed.
        """

        return bool(plan.steps) and all(
            step.status == "completed"
            for step in plan.steps
        )