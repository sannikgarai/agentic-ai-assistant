
"""
FAISS vector store.

Stores embeddings and associated chunk metadata on disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from backend.app.core.config import VECTOR_DB_DIR


class VectorStore:
    """Persistent FAISS vector store."""

    def __init__(
        self,
        directory: str | Path | None = None,
    ):
        self.directory = Path(
            directory or VECTOR_DB_DIR
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_path = (
            self.directory / "index.faiss"
        )

        self.metadata_path = (
            self.directory / "metadata.json"
        )

        self.index: faiss.Index | None = None

        self.metadata: list[dict[str, Any]] = []

    def create(
        self,
        dimension: int,
    ) -> None:
        """Create an empty FAISS index."""

        if dimension <= 0:
            raise ValueError(
                "Embedding dimension must be positive."
            )

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.metadata = []

    def add(
        self,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> None:
        """Add embeddings and metadata."""

        if embeddings.ndim != 2:
            raise ValueError(
                "Embeddings must be a 2D array."
            )

        if len(embeddings) != len(metadata):
            raise ValueError(
                "Number of embeddings and metadata "
                "records must match."
            )

        if len(embeddings) == 0:
            return

        if self.index is None:
            self.create(
                embeddings.shape[1]
            )

        if embeddings.shape[1] != (
            self.index.d
        ):
            raise ValueError(
                "Embedding dimension does not match "
                "the FAISS index."
            )

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        self.index.add(vectors)

        self.metadata.extend(
            metadata
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[tuple[float, dict[str, Any]]]:
        """Search the vector store."""

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        if top_k <= 0:
            return []

        query = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        if query.ndim == 1:
            query = query.reshape(
                1,
                -1,
            )

        if query.shape[1] != self.index.d:
            raise ValueError(
                "Query embedding dimension does not match "
                "the FAISS index."
            )

        k = min(
            top_k,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            query,
            k,
        )

        results: list[
            tuple[float, dict[str, Any]]
        ] = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            if index >= len(self.metadata):
                continue

            metadata = dict(
                self.metadata[index]
            )

            metadata["vector_index"] = int(
                index
            )

            results.append(
                (
                    float(score),
                    metadata,
                )
            )

        return results

    def save(self) -> None:
        """Save FAISS index and metadata."""

        if self.index is None:
            raise RuntimeError(
                "Cannot save an empty vector store."
            )

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        self.metadata_path.write_text(
            json.dumps(
                self.metadata,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> None:
        """Load FAISS index and metadata."""

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: "
                f"{self.index_path}"
            )

        self.index = faiss.read_index(
            str(self.index_path)
        )

        if self.metadata_path.exists():
            content = (
                self.metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            data = json.loads(content)

            if not isinstance(data, list):
                raise ValueError(
                    "Vector metadata must be a list."
                )

            self.metadata = data

        else:
            self.metadata = []

        if self.index.ntotal != len(
            self.metadata
        ):
            raise ValueError(
                "FAISS index and metadata size mismatch."
            )

    def clear(self) -> None:
        """Clear the in-memory vector store."""

        self.index = None
        self.metadata = []

    @property
    def size(self) -> int:
        """Number of stored vectors."""

        if self.index is None:
            return 0

        return int(
            self.index.ntotal
        )
