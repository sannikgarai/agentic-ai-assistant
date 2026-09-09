
"""
Application repository.

Stores government application workflow state.
"""

from __future__ import annotations

from typing import Any

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)


class ApplicationRepository:
    """Database operations for applications."""

    TABLE = "applications"

    VALID_STATUSES = {
        "draft",
        "preparing",
        "verification_pending",
        "waiting_approval",
        "submitted",
        "under_review",
        "approved",
        "rejected",
        "failed",
        "cancelled",
    }

    def __init__(
        self,
        database: SupabaseDatabase | None = None,
    ):
        self.database = database or get_database()

    def create(
        self,
        user_id: str,
        scheme_name: str,
        portal_url: str | None = None,
        status: str = "draft",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an application."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if not scheme_name or not scheme_name.strip():
            raise ValueError(
                "scheme_name cannot be empty."
            )

        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid application status: {status}"
            )

        payload: dict[str, Any] = {
            "user_id": user_id,
            "scheme_name": scheme_name,
            "status": status,
        }

        if portal_url:
            payload["portal_url"] = portal_url

        if metadata is not None:
            payload["metadata"] = metadata

        response = (
            self.database
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to create application."
            )

        return response.data[0]

    def get(
        self,
        application_id: str,
    ) -> dict[str, Any] | None:
        """Get an application."""

        if not application_id:
            raise ValueError(
                "application_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq(
                "id",
                application_id,
            )
            .limit(1)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def list_for_user(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List applications belonging to a user."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0."
            )

        if status is not None and status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid application status: {status}"
            )

        query = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
        )

        if status:
            query = query.eq(
                "status",
                status,
            )

        response = (
            query
            .order(
                "created_at",
                desc=True,
            )
            .limit(limit)
            .execute()
        )

        return response.data or []

    def update_status(
        self,
        application_id: str,
        status: str,
        confirmation_number: str | None = None,
    ) -> dict[str, Any] | None:
        """Update application status."""

        if not application_id:
            raise ValueError(
                "application_id is required."
            )

        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid application status: {status}"
            )

        payload: dict[str, Any] = {
            "status": status,
        }

        if confirmation_number:
            payload["confirmation_number"] = (
                confirmation_number
            )

        response = (
            self.database
            .table(self.TABLE)
            .update(payload)
            .eq(
                "id",
                application_id,
            )
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def update(
        self,
        application_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update application data."""

        if not application_id:
            raise ValueError(
                "application_id is required."
            )

        if not data:
            raise ValueError(
                "Update data cannot be empty."
            )

        response = (
            self.database
            .table(self.TABLE)
            .update(data)
            .eq(
                "id",
                application_id,
            )
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def delete(
        self,
        application_id: str,
    ) -> bool:
        """Delete an application."""

        if not application_id:
            raise ValueError(
                "application_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .delete()
            .eq(
                "id",
                application_id,
            )
            .execute()
        )

        return bool(response.data)
