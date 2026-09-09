"""
Text chunking.

Splits extracted document text into overlapping chunks suitable
for embedding and retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextChunk:
    """Represents one RAG text chunk."""

    chunk_id: str
    text: str
    source: str
    page_number: int | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to a dictionary."""

        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }


class TextChunker:
    """Create overlapping chunks from document text."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        text: str,
        source: str,
        page_number: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """Chunk a single text string."""

        if not text.strip():
            return []

        normalized = self._normalize_text(
            text
        )

        chunks: list[TextChunk] = []

        start = 0
        chunk_index = 0

        while start < len(normalized):
            end = min(
                start + self.chunk_size,
                len(normalized),
            )

            if end < len(normalized):
                boundary = self._find_boundary(
                    normalized,
                    start,
                    end,
                )

                if boundary > start:
                    end = boundary

            chunk_text = normalized[
                start:end
            ].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_id=(
                            f"{source}:"
                            f"{page_number or 0}:"
                            f"{chunk_index}"
                        ),
                        text=chunk_text,
                        source=source,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        metadata=metadata or {},
                    )
                )

                chunk_index += 1

            if end >= len(normalized):
                break

            next_start = end - self.chunk_overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def chunk_pages(
        self,
        pages: list[Any],
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """Chunk multiple extracted pages."""

        all_chunks: list[TextChunk] = []

        for page in pages:
            page_number = getattr(
                page,
                "page_number",
                None,
            )

            text = getattr(
                page,
                "text",
                "",
            )

            page_metadata = dict(
                metadata or {}
            )

            page_metadata["page_number"] = (
                page_number
            )

            all_chunks.extend(
                self.chunk_text(
                    text=text,
                    source=source,
                    page_number=page_number,
                    metadata=page_metadata,
                )
            )

        return all_chunks

    def _find_boundary(
        self,
        text: str,
        start: int,
        end: int,
    ) -> int:
        """Find a natural sentence/word boundary."""

        window = text[
            start:end
        ]

        sentence_matches = list(
            re.finditer(
                r"[.!?]\s",
                window,
            )
        )

        if sentence_matches:
            return (
                start
                + sentence_matches[-1].end()
            )

        whitespace_matches = list(
            re.finditer(
                r"\s",
                window,
            )
        )

        if whitespace_matches:
            return (
                start
                + whitespace_matches[-1].end()
            )

        return end

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        """Normalize whitespace without destroying paragraphs."""

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()