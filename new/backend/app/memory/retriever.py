"""
Memory retrieval.

Provides lightweight lexical retrieval over short-term,
long-term and multimodal memories.

A vector/embedding-based retriever can be connected later without
changing the public interface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from backend.app.memory.long_term import (
    LongTermMemory,
    MemoryRecord,
)

from backend.app.memory.multimodal import (
    MultimodalMemory,
    MultimodalMemoryItem,
)

from backend.app.memory.short_term import (
    ShortTermMemory,
)


@dataclass
class MemorySearchResult:
    """Represents a retrieved memory."""

    content: str
    score: float
    memory_type: str
    source_id: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "content": self.content,
            "score": self.score,
            "memory_type": self.memory_type,
            "source_id": self.source_id,
            "metadata": self.metadata,
        }


class MemoryRetriever:
    """Retrieve relevant memories."""

    def __init__(
        self,
        long_term: LongTermMemory | None = None,
        multimodal: MultimodalMemory | None = None,
    ):
        self.long_term = (
            long_term
            or LongTermMemory()
        )

        self.multimodal = (
            multimodal
            or MultimodalMemory()
        )

    def search(
        self,
        user_id: str,
        query: str,
        short_term: ShortTermMemory | None = None,
        top_k: int = 5,
    ) -> list[MemorySearchResult]:
        """
        Search available memories.

        Results are ranked using lexical token overlap and
        long-term importance.
        """

        if not query or not query.strip():
            return []

        if top_k <= 0:
            return []

        query_tokens = self._tokenize(
            query
        )

        results: list[
            MemorySearchResult
        ] = []

        # -------------------------------------------------
        # Short-term memory
        # -------------------------------------------------

        if short_term:
            for index, message in enumerate(
                short_term.get_messages()
            ):
                content = str(
                    message.get(
                        "content",
                        "",
                    )
                )

                score = self._score(
                    query_tokens,
                    content,
                )

                if score > 0:
                    results.append(
                        MemorySearchResult(
                            content=content,
                            score=score,
                            memory_type="short_term",
                            source_id=str(index),
                            metadata=message.get(
                                "metadata",
                                {},
                            ),
                        )
                    )

        # -------------------------------------------------
        # Long-term memory
        # -------------------------------------------------

        for record in self.long_term.list(
            user_id
        ):
            score = self._score(
                query_tokens,
                record.content,
            )

            # Importance contributes slightly to ranking.
            score = (
                score * 0.8
                + record.importance * 0.2
            )

            if score > 0:
                results.append(
                    MemorySearchResult(
                        content=record.content,
                        score=score,
                        memory_type=(
                            f"long_term:{record.memory_type}"
                        ),
                        source_id=record.memory_id,
                        metadata=record.metadata,
                    )
                )

        # -------------------------------------------------
        # Multimodal memory
        # -------------------------------------------------

        for item in self.multimodal.list(
            user_id
        ):
            searchable_text = (
                item.content or ""
            )

            if item.file_name:
                searchable_text += (
                    f" {item.file_name}"
                )

            score = self._score(
                query_tokens,
                searchable_text,
            )

            if score > 0:
                results.append(
                    MemorySearchResult(
                        content=searchable_text,
                        score=score,
                        memory_type=(
                            f"multimodal:{item.modality}"
                        ),
                        source_id=item.memory_id,
                        metadata={
                            **item.metadata,
                            "file_path": item.file_path,
                            "mime_type": item.mime_type,
                        },
                    )
                )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:top_k]

    def build_context(
        self,
        user_id: str,
        query: str,
        short_term: ShortTermMemory | None = None,
        top_k: int = 5,
    ) -> str:
        """Build context suitable for an LLM prompt."""

        results = self.search(
            user_id=user_id,
            query=query,
            short_term=short_term,
            top_k=top_k,
        )

        if not results:
            return ""

        lines = [
            "Relevant memory:"
        ]

        for result in results:
            lines.append(
                f"- {result.content}"
            )

        return "\n".join(lines)

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:
        """Tokenize text."""

        return {
            token
            for token in re.findall(
                r"\w+",
                text.lower(),
                flags=re.UNICODE,
            )
            if len(token) > 1
        }

    def _score(
        self,
        query_tokens: set[str],
        content: str,
    ) -> float:
        """Calculate lexical relevance."""

        if not query_tokens or not content:
            return 0.0

        content_tokens = self._tokenize(
            content
        )

        if not content_tokens:
            return 0.0

        overlap = (
            query_tokens
            & content_tokens
        )

        if not overlap:
            return 0.0

        return len(overlap) / len(
            query_tokens
        )