"""
Verification models.
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


class VerificationStatus(str, Enum):
    """Verification result states."""

    PENDING = "pending"

    VERIFIED = "verified"

    MISMATCH = "mismatch"

    FAILED = "failed"

    INELIGIBLE = "ineligible"

    MANUAL_REVIEW = "manual_review"


class VerificationRequest(BaseModel):
    """Request to verify information."""

    verification_type: str = Field(
        min_length=1,
        max_length=100,
    )

    document_ids: list[str] = Field(
        default_factory=list
    )

    application_id: str | None = None

    expected_fields: dict[str, Any] = Field(
        default_factory=dict
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class VerificationResult(BaseModel):
    """Individual verification result."""

    field_name: str

    expected_value: Any | None = None

    actual_value: Any | None = None

    matched: bool

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    source_document_id: str | None = None

    message: str = ""


class VerificationResponse(BaseModel):
    """Complete verification response."""

    id: str | None = None

    user_id: str | None = None

    verification_type: str

    status: VerificationStatus

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    results: list[
        VerificationResult
    ] = Field(
        default_factory=list
    )

    mismatches: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    eligibility: dict[str, Any] = Field(
        default_factory=dict
    )

    message: str = ""

    created_at: datetime | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )