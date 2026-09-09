"""
Long-term memory.

Provides persistent-style storage abstraction for information that
should survive beyond the current short-term conversation context.

The current implementation uses an in-memory repository. It is
structured so a Supabase repository can be connected later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MemoryRecord:
    """A long-term memory record."""

    memory_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    user_id: str = ""
    content: str = ""
    memory_type: str = "general"
    importance: float = 0.5
    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""

        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class LongTermMemory:
    """
    Long-term memory manager.

    Memory types may include:
    - preference
    - profile
    - task
    - document
    - application
    - general
    """

    def __init__(self):
        self._records: dict[
            str,
            list[MemoryRecord],
        ] = {}

    def add(
        self,
        user_id: str,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Store a memory record."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if not content or not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        importance = max(
            0.0,
            min(
                1.0,
                float(importance),
            ),
        )

        record = MemoryRecord(
            user_id=user_id,
            content=content.strip(),
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
        )

        self._records.setdefault(
            user_id,
            [],
        ).append(record)

        return record

    def get(
        self,
        user_id: str,
        memory_id: str,
    ) -> MemoryRecord | None:
        """Get one memory record."""

        records = self._records.get(
            user_id,
            [],
        )

        for record in records:
            if record.memory_id == memory_id:
                return record

        return None

    def list(
        self,
        user_id: str,
        memory_type: str | None = None,
    ) -> list[MemoryRecord]:
        """List user memories."""

        records = self._records.get(
            user_id,
            [],
        )

        if memory_type is not None:
            records = [
                record
                for record in records
                if record.memory_type
                == memory_type
            ]

        return sorted(
            records,
            key=lambda record: (
                record.importance,
                record.created_at,
            ),
            reverse=True,
        )

    def delete(
        self,
        user_id: str,
        memory_id: str,
    ) -> bool:
        """Delete a memory."""

        records = self._records.get(
            user_id,
            [],
        )

        for index, record in enumerate(
            records
        ):
            if record.memory_id == memory_id:
                records.pop(index)
                return True

        return False

    def clear_user(
        self,
        user_id: str,
    ) -> None:
        """Delete all long-term memories for a user."""

        self._records.pop(
            user_id,
            None,
        )

    def count(
        self,
        user_id: str,
    ) -> int:
        """Return number of memories."""

        return len(
            self._records.get(
                user_id,
                [],
            )
        )