
"""
RAG indexing.

Converts text chunks into embeddings and stores them in FAISS.
"""

from __future__ import annotations

from typing import Any

from backend.app.rag.chunker import TextChunk
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore


class FAISSIndexer:
    """Build and persist a FAISS index."""

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

    def build(
        self,
        chunks: list[TextChunk],
        save: bool = True,
    ) -> VectorStore:
        """Build a new vector index."""

        self.vector_store.clear()

        if not chunks:
            self.vector_store.create(
                self.embedding_model.dimension
            )

            if save:
                self.vector_store.save()

            return self.vector_store

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = (
            self.embedding_model.encode(
                texts
            )
        )

        metadata: list[
            dict[str, Any]
        ] = []

        for chunk in chunks:
            metadata.append(
                chunk.to_dict()
            )

        self.vector_store.add(
            embeddings,
            metadata,
        )

        if save:
            self.vector_store.save()

        return self.vector_store

    def append(
        self,
        chunks: list[TextChunk],
        save: bool = True,
    ) -> VectorStore:
        """Append new chunks to an existing index."""

        if not chunks:
            return self.vector_store

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = (
            self.embedding_model.encode(
                texts
            )
        )

        metadata = [
            chunk.to_dict()
            for chunk in chunks
        ]

        self.vector_store.add(
            embeddings,
            metadata,
        )

        if save:
            self.vector_store.save()

        return self.vector_store
