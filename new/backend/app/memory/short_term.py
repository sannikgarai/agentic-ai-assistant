"""
Short-term conversational memory.

Stores the recent conversation context used when constructing
prompts for the LLM/agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShortTermMemory:
    """
    Sliding-window memory for recent messages.
    """

    max_messages: int = 20

    messages: list[dict[str, Any]] = field(
        default_factory=list
    )

    def add(
        self,
        role: str,
        content: str,
        **metadata: Any,
    ) -> None:
        """Add a message."""

        if not content or not content.strip():
            return

        message = {
            "role": role,
            "content": content.strip(),
            "metadata": metadata,
        }

        self.messages.append(
            message
        )

        self._trim()

    def add_message(
        self,
        message: dict[str, Any],
    ) -> None:
        """Add an existing message object."""

        if not message:
            return

        self.messages.append(
            message
        )

        self._trim()

    def get_messages(
        self,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return recent messages."""

        if limit is None:
            limit = self.max_messages

        if limit <= 0:
            return []

        return self.messages[-limit:]

    def get_context(
        self,
        limit: int | None = None,
    ) -> str:
        """
        Convert recent messages into LLM context text.
        """

        messages = self.get_messages(
            limit
        )

        lines = []

        for message in messages:
            role = message.get(
                "role",
                "user",
            )

            content = message.get(
                "content",
                "",
            )

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)

    def last_message(
        self,
    ) -> dict[str, Any] | None:
        """Return the most recent message."""

        if not self.messages:
            return None

        return self.messages[-1]

    def clear(self) -> None:
        """Clear short-term memory."""

        self.messages.clear()

    def size(self) -> int:
        """Return number of stored messages."""

        return len(self.messages)

    def _trim(self) -> None:
        """Keep memory within the configured window."""

        if self.max_messages <= 0:
            self.messages.clear()
            return

        if len(self.messages) > self.max_messages:
            self.messages = self.messages[
                -self.max_messages:
            ]