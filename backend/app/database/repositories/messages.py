
"""
Message repository.
"""

from __future__ import annotations

from typing import Any

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)


class MessageRepository:
    """Database operations for conversation messages."""

    TABLE = "messages"

    def __init__(
        self,
        database: SupabaseDatabase | None = None,
    ):
        self.database = database or get_database()

    def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
        language: str | None = None,
        message_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a message."""

        if not conversation_id:
            raise ValueError(
                "conversation_id is required."
            )

        if role not in {
            "user",
            "assistant",
            "system",
            "tool",
        }:
            raise ValueError(
                f"Invalid message role: {role}"
            )

        if not content or not content.strip():
            raise ValueError(
                "Message content cannot be empty."
            )

        if not message_type:
            raise ValueError(
                "message_type is required."
            )

        payload: dict[str, Any] = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "message_type": message_type,
        }

        if language is not None:
            payload["language"] = language

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
                "Failed to create message."
            )

        return response.data[0]

    def get(
        self,
        message_id: str,
    ) -> dict[str, Any] | None:
        """Get one message."""

        if not message_id:
            raise ValueError(
                "message_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("id", message_id)
            .limit(1)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def list_for_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return conversation messages."""

        if not conversation_id:
            raise ValueError(
                "conversation_id is required."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq(
                "conversation_id",
                conversation_id,
            )
            .order(
                "created_at",
                desc=False,
            )
            .limit(limit)
            .execute()
        )

        return response.data or []

    def delete(
        self,
        message_id: str,
    ) -> bool:
        """Delete a message."""

        if not message_id:
            raise ValueError(
                "message_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .delete()
            .eq("id", message_id)
            .execute()
        )

        return bool(response.data)
