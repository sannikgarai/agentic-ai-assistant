"""
Multimodal memory.

Stores references and metadata for non-text information associated
with conversations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MultimodalMemoryItem:
    """Represents a multimodal memory."""

    memory_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    user_id: str = ""

    conversation_id: str | None = None

    modality: str = "unknown"

    content: str | None = None

    file_path: str | None = None

    file_name: str | None = None

    mime_type: str | None = None

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert item to dictionary."""

        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "modality": self.modality,
            "content": self.content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class MultimodalMemory:
    """
    Multimodal memory manager.

    Supported modalities:
    - image
    - audio
    - video
    - document
    """

    SUPPORTED_MODALITIES = {
        "image",
        "audio",
        "video",
        "document",
    }

    def __init__(self):
        self._items: dict[
            str,
            list[MultimodalMemoryItem],
        ] = {}

    def add(
        self,
        user_id: str,
        modality: str,
        content: str | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MultimodalMemoryItem:
        """Add multimodal memory."""

        modality = modality.strip().lower()

        if modality not in self.SUPPORTED_MODALITIES:
            raise ValueError(
                f"Unsupported modality: {modality}"
            )

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if not content and not file_path:
            raise ValueError(
                "Either content or file_path is required."
            )

        item = MultimodalMemoryItem(
            user_id=user_id,
            conversation_id=conversation_id,
            modality=modality,
            content=content,
            file_path=file_path,
            file_name=file_name,
            mime_type=mime_type,
            metadata=metadata or {},
        )

        self._items.setdefault(
            user_id,
            [],
        ).append(item)

        return item

    def list(
        self,
        user_id: str,
        modality: str | None = None,
        conversation_id: str | None = None,
    ) -> list[MultimodalMemoryItem]:
        """List multimodal memories."""

        items = self._items.get(
            user_id,
            [],
        )

        if modality:
            modality = modality.lower()

            items = [
                item
                for item in items
                if item.modality == modality
            ]

        if conversation_id:
            items = [
                item
                for item in items
                if item.conversation_id
                == conversation_id
            ]

        return sorted(
            items,
            key=lambda item: item.timestamp,
            reverse=True,
        )

    def get(
        self,
        user_id: str,
        memory_id: str,
    ) -> MultimodalMemoryItem | None:
        """Get a multimodal memory item."""

        for item in self._items.get(
            user_id,
            [],
        ):
            if item.memory_id == memory_id:
                return item

        return None

    def delete(
        self,
        user_id: str,
        memory_id: str,
    ) -> bool:
        """Delete a multimodal memory."""

        items = self._items.get(
            user_id,
            [],
        )

        for index, item in enumerate(
            items
        ):
            if item.memory_id == memory_id:
                items.pop(index)
                return True

        return False