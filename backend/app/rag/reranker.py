
"""
RAG reranker.

Reorders retrieved chunks using a lightweight lexical relevance
score combined with the original vector similarity.
"""

from __future__ import annotations

import re
from typing import Iterable

from backend.app.rag.retriever import RetrievalResult


class Reranker:
    """Lightweight retrieval reranker."""

    def __init__(
        self,
        vector_weight: float = 0.7,
        lexical_weight: float = 0.3,
    ):
        if vector_weight < 0 or lexical_weight < 0:
            raise ValueError(
                "Reranker weights cannot be negative."
            )

        total = (
            vector_weight
            + lexical_weight
        )

        if total == 0:
            raise ValueError(
                "At least one reranker weight must be positive."
            )

        self.vector_weight = (
            vector_weight / total
        )

        self.lexical_weight = (
            lexical_weight / total
        )

    def rerank(
        self,
        query: str,
        results: Iterable[RetrievalResult],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Rerank retrieval results."""

        query_terms = self._tokenize(
            query
        )

        scored: list[
            tuple[float, RetrievalResult]
        ] = []

        for result in results:
            lexical_score = (
                self._lexical_score(
                    query_terms,
                    result.text,
                )
            )

            combined_score = (
                self.vector_weight
                * self._normalize_vector_score(
                    result.score
                )
                + self.lexical_weight
                * lexical_score
            )

            updated = RetrievalResult(
                score=combined_score,
                chunk_id=result.chunk_id,
                text=result.text,
                source=result.source,
                page_number=result.page_number,
                metadata={
                    **result.metadata,
                    "original_vector_score": (
                        result.score
                    ),
                    "lexical_score": lexical_score,
                    "reranked_score": combined_score,
                },
            )

            scored.append(
                (
                    combined_score,
                    updated,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        reranked = [
            result
            for _, result in scored
        ]

        if top_k is not None:
            reranked = reranked[
                :max(0, top_k)
            ]

        return reranked

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:
        """Tokenize text."""

        return set(
            re.findall(
                r"\b\w+\b",
                text.lower(),
                flags=re.UNICODE,
            )
        )

    def _lexical_score(
        self,
        query_terms: set[str],
        text: str,
    ) -> float:
        """Calculate simple term overlap."""

        if not query_terms:
            return 0.0

        text_terms = self._tokenize(
            text
        )

        if not text_terms:
            return 0.0

        overlap = (
            query_terms
            & text_terms
        )

        return len(overlap) / len(
            query_terms
        )

    @staticmethod
    def _normalize_vector_score(
        score: float,
    ) -> float:
        """
        Normalize cosine/IP similarity into approximately
        [0, 1].
        """

        normalized = (
            float(score) + 1.0
        ) / 2.0

        return max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )
