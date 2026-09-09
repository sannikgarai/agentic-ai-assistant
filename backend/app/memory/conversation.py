"""
Conversation management.

Maintains the structure of conversations and messages before they
are persisted to long-term storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ConversationMessage:
    """Represents one conversation message."""

    role: str
    content: str
    message_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    language: str | None = None
    message_type: str = "text"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""

        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "language": self.language,
            "message_type": self.message_type,
            "metadata": self.metadata,
        }


@dataclass
class Conversation:
    """Represents a complete conversation."""

    conversation_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    user_id: str | None = None
    title: str = "New Conversation"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    messages: list[ConversationMessage] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_message(
        self,
        message: ConversationMessage,
    ) -> ConversationMessage:
        """Add a message to the conversation."""

        self.messages.append(message)

        self.updated_at = datetime.now(
            timezone.utc
        )

        return message

    def clear_messages(self) -> None:
        """Remove all messages."""

        self.messages.clear()

        self.updated_at = datetime.now(
            timezone.utc
        )

    def get_recent_messages(
        self,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """Return the most recent messages."""

        if limit <= 0:
            return []

        return self.messages[-limit:]

    def to_dict(self) -> dict[str, Any]:
        """Convert conversation to dictionary."""

        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [
                message.to_dict()
                for message in self.messages
            ],
            "metadata": self.metadata,
        }


class ConversationManager:
    """Manage conversations in application memory."""

    def __init__(self):
        self._conversations: dict[
            str,
            Conversation,
        ] = {}

    def create(
        self,
        user_id: str | None = None,
        title: str = "New Conversation",
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """Create a new conversation."""

        conversation = Conversation(
            user_id=user_id,
            title=title,
            metadata=metadata or {},
        )

        self._conversations[
            conversation.conversation_id
        ] = conversation

        return conversation

    def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        """Get a conversation."""

        return self._conversations.get(
            conversation_id
        )

    def get_or_create(
        self,
        conversation_id: str | None = None,
        user_id: str | None = None,
    ) -> Conversation:
        """Get existing conversation or create one."""

        if conversation_id:
            existing = self.get(
                conversation_id
            )

            if existing:
                return existing

        return self.create(
            user_id=user_id
        )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        language: str | None = None,
        message_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """Add a message to a conversation."""

        conversation = self.get(
            conversation_id
        )

        if conversation is None:
            raise ValueError(
                f"Conversation not found: "
                f"{conversation_id}"
            )

        message = ConversationMessage(
            role=role,
            content=content,
            language=language,
            message_type=message_type,
            metadata=metadata or {},
        )

        conversation.add_message(
            message
        )

        return message

    def delete(
        self,
        conversation_id: str,
    ) -> bool:
        """Delete an in-memory conversation."""

        if conversation_id not in self._conversations:
            return False

        del self._conversations[
            conversation_id
        ]

        return True

    def list_for_user(
        self,
        user_id: str,
    ) -> list[Conversation]:
        """Return conversations belonging to a user."""

        conversations = [
            conversation
            for conversation in self._conversations.values()
            if conversation.user_id == user_id
        ]

        return sorted(
            conversations,
            key=lambda item: item.updated_at,
            reverse=True,
        )