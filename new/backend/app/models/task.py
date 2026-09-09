"""
Agent task models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class TaskStatus(str, Enum):
    """Possible task states."""

    PENDING = "pending"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    WAITING_APPROVAL = (
        "waiting_approval"
    )


class TaskCreate(BaseModel):
    """Create an Agent task."""

    task_type: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        min_length=1,
        max_length=10000,
    )

    conversation_id: str | None = None

    parent_task_id: str | None = None

    dependencies: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class TaskUpdate(BaseModel):
    """Update an Agent task."""

    status: TaskStatus | None = None

    description: str | None = None

    result: Any | None = None

    error_message: str | None = None

    metadata: dict[str, Any] | None = None


class Task(BaseModel):
    """Agent task record."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: str

    user_id: str

    task_type: str

    description: str

    status: TaskStatus = TaskStatus.PENDING

    conversation_id: str | None = None

    parent_task_id: str | None = None

    dependencies: list[str] = Field(
        default_factory=list
    )

    result: Any | None = None

    error_message: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime | None = None

    started_at: datetime | None = None

    completed_at: datetime | None = None

    updated_at: datetime | None = None