
"""
Conversation repository.
"""

from __future__ import annotations

from typing import Any

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)


class ConversationRepository:
    """Database operations for conversations."""

    TABLE = "conversations"

    def __init__(
        self,
        database: SupabaseDatabase | None = None,
    ):
        self.database = database or get_database()

    def create(
        self,
        user_id: str,
        title: str = "New Conversation",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a conversation."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        payload: dict[str, Any] = {
            "user_id": user_id,
            "title": title,
        }

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
                "Failed to create conversation."
            )

        return response.data[0]

    def get(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        """Get a conversation."""

        if not conversation_id:
            raise ValueError(
                "conversation_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("id", conversation_id)
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
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List conversations belonging to a user."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order(
                "updated_at",
                desc=True,
            )
            .limit(limit)
            .execute()
        )

        return response.data or []

    def update(
        self,
        conversation_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update a conversation."""

        if not conversation_id:
            raise ValueError(
                "conversation_id is required."
            )

        if not data:
            raise ValueError(
                "Update data cannot be empty."
            )

        response = (
            self.database
            .table(self.TABLE)
            .update(data)
            .eq("id", conversation_id)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def delete(
        self,
        conversation_id: str,
    ) -> bool:
        """Delete a conversation."""

        if not conversation_id:
            raise ValueError(
                "conversation_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .delete()
            .eq("id", conversation_id)
            .execute()
        )

        return bool(response.data)
