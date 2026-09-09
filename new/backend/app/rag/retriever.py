
"""
RAG retrieval.

Retrieves relevant document chunks using vector similarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.core.config import settings
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore


@dataclass
class RetrievalResult:
    """One retrieved document chunk."""

    score: float
    chunk_id: str
    text: str
    source: str
    page_number: int | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert retrieval result to dictionary."""

        return {
            "score": self.score,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "page_number": self.page_number,
            "metadata": self.metadata,
        }


class Retriever:
    """Vector similarity retriever."""

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.vector_store = (
            vector_store
            or VectorStore()
        )

    def load_index(self) -> None:
        """Load the persisted index."""

        self.vector_store.load()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve relevant chunks."""

        if not query.strip():
            return []

        k = top_k or settings.rag_top_k

        query_embedding = (
            self.embedding_model.encode_query(
                query
            )
        )

        raw_results = self.vector_store.search(
            query_embedding,
            top_k=k,
        )

        results: list[
            RetrievalResult
        ] = []

        for score, metadata in raw_results:
            source = str(
                metadata.get(
                    "source",
                    "",
                )
            )

            chunk_value = metadata.get(
                "chunk_id"
            )

            if chunk_value is None or str(
                chunk_value
            ).strip() == "":
                chunk_value = metadata.get(
                    "chunk"
                )

            if chunk_value is None or str(
                chunk_value
            ).strip() == "":
                chunk_id = (
                    f"{source}#vector-{metadata.get('vector_index', '')}"
                )
            else:
                chunk_id = (
                    f"{source}#chunk-{chunk_value}"
                )

            page_value = metadata.get(
                "page_number"
            )

            if page_value is None:
                page_value = metadata.get(
                    "page"
                )

            page_number: int | None = None

            if page_value is not None:
                try:
                    page_number = int(
                        page_value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    page_number = None

            results.append(
                RetrievalResult(
                    score=score,
                    chunk_id=chunk_id,
                    text=str(
                        metadata.get(
                            "text",
                            "",
                        )
                    ),
                    source=source,
                    page_number=page_number,
                    metadata=metadata,
                )
            )

        return results

    async def aretrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Async-compatible retrieval interface."""

        return self.retrieve(
            query=query,
            top_k=top_k,
        )
