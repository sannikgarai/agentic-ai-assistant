"""
Agent package for the Agentic AI Assistant.

This package contains the core agent orchestration system:
- Agent state management
- Task decomposition
- Planning
- Workflow execution
- Supervision
- Agent coordination
"""

from backend.app.agent.agent import Agent, AgentResult
from backend.app.agent.planner import AgentPlanner, Plan, PlanStep
from backend.app.agent.state import AgentState
from backend.app.agent.supervisor import AgentSupervisor
from backend.app.agent.task_decomposer import TaskDecomposer, Task
from backend.app.agent.workflow import Workflow, WorkflowResult

__all__ = [
    "Agent",
    "AgentResult",
    "AgentPlanner",
    "Plan",
    "PlanStep",
    "AgentState",
    "AgentSupervisor",
    "TaskDecomposer",
    "Task",
    "Workflow",
    "WorkflowResult",
]