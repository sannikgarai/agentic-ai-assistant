"""
Government application models.
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


class ApplicationStatus(str, Enum):
    """Application workflow states."""

    DRAFT = "draft"

    PREPARING = "preparing"

    VERIFICATION_PENDING = (
        "verification_pending"
    )

    WAITING_APPROVAL = (
        "waiting_approval"
    )

    SUBMITTED = "submitted"

    UNDER_REVIEW = "under_review"

    APPROVED = "approved"

    REJECTED = "rejected"

    FAILED = "failed"

    CANCELLED = "cancelled"


class ApplicationCreate(BaseModel):
    """Create a government application."""

    scheme_name: str = Field(
        min_length=1,
        max_length=300,
    )

    portal_url: str | None = None

    description: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ApplicationUpdate(BaseModel):
    """Update application information."""

    status: ApplicationStatus | None = None

    portal_url: str | None = None

    description: str | None = None

    confirmation_number: str | None = None

    metadata: dict[str, Any] | None = None


class Application(BaseModel):
    """Government application record."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: str

    user_id: str

    scheme_name: str

    portal_url: str | None = None

    description: str | None = None

    status: ApplicationStatus = (
        ApplicationStatus.DRAFT
    )

    confirmation_number: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None

    submitted_at: datetime | None = None