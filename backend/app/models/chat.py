"""
Chat and conversation models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


MessageRole = Literal[
    "user",
    "assistant",
    "system",
    "tool",
]

MessageType = Literal[
    "text",
    "voice",
    "image",
    "document",
    "tool",
]


class ChatMessage(BaseModel):
    """A single conversation message."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: str | None = None

    conversation_id: str | None = None

    role: MessageRole

    content: str = Field(
        min_length=1,
        max_length=100000,
    )

    message_type: MessageType = "text"

    language: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime | None = None


class ConversationCreate(BaseModel):
    """Create a new conversation."""

    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=200,
    )

    language: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class Conversation(BaseModel):
    """Conversation record."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: str

    user_id: str

    title: str

    language: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


class ChatRequest(BaseModel):
    """Request sent to the chat API."""

    message: str = Field(
        min_length=1,
        max_length=100000,
    )

    conversation_id: str | None = None

    language: str | None = None

    include_history: bool = True

    use_rag: bool = True

    use_agent: bool = True

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ChatResponse(BaseModel):
    """Response returned by the chat API."""

    message: ChatMessage

    conversation_id: str

    task_id: str | None = None

    sources: list[dict[str, Any]] = Field(
        default_factory=list
    )

    tasks: list[dict[str, Any]] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )