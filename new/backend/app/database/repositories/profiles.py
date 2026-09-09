
"""
Profile repository.
"""

from __future__ import annotations

from typing import Any

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)


class ProfileRepository:
    """Database operations for user profiles."""

    TABLE = "profiles"

    def __init__(
        self,
        database: SupabaseDatabase | None = None,
    ):
        self.database = database or get_database()

    def create(
        self,
        user_id: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a user profile."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        payload = {
            "id": user_id,
            **(data or {}),
        }

        response = (
            self.database
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else payload
        )

    def get(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Get a profile."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def update(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update a profile."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if not data:
            raise ValueError(
                "Update data cannot be empty."
            )

        response = (
            self.database
            .table(self.TABLE)
            .update(data)
            .eq("id", user_id)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def upsert(
        self,
        user_id: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create or update a profile."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        payload = {
            "id": user_id,
            **(data or {}),
        }

        response = (
            self.database
            .table(self.TABLE)
            .upsert(payload)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def delete(
        self,
        user_id: str,
    ) -> bool:
        """Delete a profile."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .delete()
            .eq("id", user_id)
            .execute()
        )

        return bool(response.data)
