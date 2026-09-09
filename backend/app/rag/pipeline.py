
"""
End-to-end RAG pipeline.

Provides:
- PDF ingestion
- Text extraction
- Cleaning
- Chunking
- Embedding
- FAISS indexing
- Retrieval
- Reranking
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.rag.chunker import TextChunker
from backend.app.rag.cleaner import TextCleaner
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.extractor import PDFExtractor
from backend.app.rag.indexing import FAISSIndexer
from backend.app.rag.loader import PDFLoader
from backend.app.rag.reranker import Reranker
from backend.app.rag.retriever import RetrievalResult, Retriever
from backend.app.rag.vector_store import VectorStore


class RAGPipeline:
    """
    Complete Retrieval-Augmented Generation pipeline.

    This class currently performs retrieval. The LLM generation
    layer remains separate and is handled by the Gemini client.
    """

    def __init__(
        self,
        loader: PDFLoader | None = None,
        extractor: PDFExtractor | None = None,
        cleaner: TextCleaner | None = None,
        chunker: TextChunker | None = None,
        embedding_model: EmbeddingModel | None = None,
        vector_store: VectorStore | None = None,
        indexer: FAISSIndexer | None = None,
        retriever: Retriever | None = None,
        reranker: Reranker | None = None,
    ):
        self.loader = (
            loader
            or PDFLoader()
        )

        self.extractor = (
            extractor
            or PDFExtractor()
        )

        self.cleaner = (
            cleaner
            or TextCleaner()
        )

        self.chunker = (
            chunker
            or TextChunker()
        )

        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.vector_store = (
            vector_store
            or VectorStore()
        )

        self.indexer = (
            indexer
            or FAISSIndexer(
                embedding_model=self.embedding_model,
                vector_store=self.vector_store,
            )
        )

        self.retriever = (
            retriever
            or Retriever(
                embedding_model=self.embedding_model,
                vector_store=self.vector_store,
            )
        )

        self.reranker = (
            reranker
            or Reranker()
        )

    def ingest_pdf(
        self,
        file_path: str | Path,
    ) -> list[dict[str, Any]]:
        """
        Process one PDF into chunks.

        This does not automatically rebuild the global index.
        """

        document = self.loader.load(
            file_path
        )

        extracted = self.extractor.extract(
            document.file_path
        )

        chunks = []

        for page in extracted.pages:
            cleaned_text = (
                self.cleaner.clean(
                    page.text
                )
            )

            if not cleaned_text:
                continue

            page_chunks = (
                self.chunker.chunk_text(
                    text=cleaned_text,
                    source=document.file_path,
                    page_number=page.page_number,
                    metadata={
                        "filename": document.filename,
                        "category": document.category,
                        "page_number": page.page_number,
                    },
                )
            )

            chunks.extend(
                page_chunks
            )

        return [
            chunk.to_dict()
            for chunk in chunks
        ]

    def build_index(
        self,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Build a complete FAISS index from government PDFs."""

        pdf_files = self.loader.discover(
            category=category
        )

        all_chunks = []

        processed_files = 0
        failed_files = 0

        for pdf_path in pdf_files:
            try:
                document = self.loader.load(
                    pdf_path
                )

                extracted = (
                    self.extractor.extract(
                        document.file_path
                    )
                )

                for page in extracted.pages:
                    cleaned_text = (
                        self.cleaner.clean(
                            page.text
                        )
                    )

                    if not cleaned_text:
                        continue

                    page_chunks = (
                        self.chunker.chunk_text(
                            text=cleaned_text,
                            source=document.file_path,
                            page_number=page.page_number,
                            metadata={
                                "filename": (
                                    document.filename
                                ),
                                "category": (
                                    document.category
                                ),
                                "page_number": (
                                    page.page_number
                                ),
                            },
                        )
                    )

                    all_chunks.extend(
                        page_chunks
                    )

                processed_files += 1

            except Exception:
                failed_files += 1

        self.indexer.build(
            chunks=all_chunks,
            save=True,
        )

        return {
            "success": True,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "chunks": len(all_chunks),
            "vectors": self.vector_store.size,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the indexed government documents.

        Returns serializable dictionaries so this method can
        be consumed directly by RAGTool.
        """

        results = self.retrieve(
            query=query,
            top_k=max(
                top_k * 3,
                top_k,
            ),
        )

        if filters:
            results = self._apply_filters(
                results,
                filters,
            )

        reranked = self.reranker.rerank(
            query=query,
            results=results,
            top_k=top_k,
        )

        return [
            result.to_dict()
            for result in reranked
        ]

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Retrieve chunks from the vector database."""

        if self.vector_store.size == 0:
            try:
                self.retriever.load_index()
            except FileNotFoundError:
                return []

        return self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

    async def aretrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Async-compatible retrieval method."""

        return self.search(
            query=query,
            top_k=top_k,
        )

    async def asearch(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Async-compatible search method."""

        return self.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

    @staticmethod
    def _apply_filters(
        results: list[RetrievalResult],
        filters: dict[str, Any],
    ) -> list[RetrievalResult]:
        """Apply metadata filters."""

        filtered = []

        for result in results:
            matches = True

            for key, expected in filters.items():
                actual = result.metadata.get(
                    key
                )

                if isinstance(
                    expected,
                    list,
                ):
                    if actual not in expected:
                        matches = False
                        break

                elif actual != expected:
                    matches = False
                    break

            if matches:
                filtered.append(
                    result
                )

        return filtered
