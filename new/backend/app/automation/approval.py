"""
Human approval workflow.

Provides explicit approval before irreversible application actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class ApprovalStatus(str, Enum):
    """Approval states."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Represents an approval request."""

    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    user_id: str = ""

    application_id: str | None = None

    description: str = ""

    status: ApprovalStatus = (
        ApprovalStatus.PENDING
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    resolved_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": (
                self.resolved_at.isoformat()
                if self.resolved_at
                else None
            ),
            "metadata": self.metadata,
        }


class ApprovalManager:
    """Manage human approval requests."""

    def __init__(self):
        self._requests: dict[
            str,
            ApprovalRequest,
        ] = {}

    def create_request(
        self,
        user_id: str,
        description: str,
        application_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        """Create a pending approval request."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if not description.strip():
            raise ValueError(
                "Approval description is required."
            )

        request = ApprovalRequest(
            user_id=user_id,
            application_id=application_id,
            description=description.strip(),
            metadata=metadata or {},
        )

        self._requests[
            request.request_id
        ] = request

        return request

    def get(
        self,
        request_id: str,
    ) -> ApprovalRequest | None:
        """Get an approval request."""

        return self._requests.get(
            request_id
        )

    def approve(
        self,
        request_id: str,
        user_id: str,
    ) -> ApprovalRequest:
        """Approve a pending request."""

        request = self._get_owned_request(
            request_id,
            user_id,
        )

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                "Only pending requests can be approved."
            )

        request.status = (
            ApprovalStatus.APPROVED
        )

        request.resolved_at = (
            datetime.now(timezone.utc)
        )

        return request

    def reject(
        self,
        request_id: str,
        user_id: str,
    ) -> ApprovalRequest:
        """Reject a pending request."""

        request = self._get_owned_request(
            request_id,
            user_id,
        )

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                "Only pending requests can be rejected."
            )

        request.status = (
            ApprovalStatus.REJECTED
        )

        request.resolved_at = (
            datetime.now(timezone.utc)
        )

        return request

    def is_approved(
        self,
        request_id: str,
        user_id: str,
    ) -> bool:
        """Check whether a request is approved."""

        request = self._get_owned_request(
            request_id,
            user_id,
        )

        return (
            request.status
            == ApprovalStatus.APPROVED
        )

    def list_pending(
        self,
        user_id: str,
    ) -> list[ApprovalRequest]:
        """List pending requests for a user."""

        return [
            request
            for request in self._requests.values()
            if request.user_id == user_id
            and request.status
            == ApprovalStatus.PENDING
        ]

    def _get_owned_request(
        self,
        request_id: str,
        user_id: str,
    ) -> ApprovalRequest:
        """Get request and verify ownership."""

        request = self.get(
            request_id
        )

        if request is None:
            raise ValueError(
                "Approval request not found."
            )

        if request.user_id != user_id:
            raise PermissionError(
                "User does not own this approval request."
            )

        return request