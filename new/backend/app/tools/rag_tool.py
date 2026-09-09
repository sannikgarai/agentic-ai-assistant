
"""
RAG tool.

Provides the agent with access to the Retrieval-Augmented
Generation pipeline for government documents.
"""

from __future__ import annotations

from typing import Any

from backend.app.rag.pipeline import RAGPipeline


class RAGTool:
    """
    Tool for retrieving information from the RAG system.

    Connects the agent to the project's RAG pipeline.
    """

    name = "rag"

    description = (
        "Search government documents and retrieve "
        "relevant authoritative information."
    )

    def __init__(
        self,
        pipeline: Any | None = None,
    ):
        """
        Initialize the RAG tool.

        If a pipeline is supplied, use it.
        Otherwise, create the project's default RAG pipeline.
        """

        self.pipeline = pipeline or RAGPipeline()

    async def execute(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search the RAG knowledge base.
        """

        if not query or not query.strip():
            return {
                "success": False,
                "query": query,
                "results": [],
                "message": "Search query cannot be empty.",
            }

        try:
            if hasattr(self.pipeline, "asearch"):
                results = await self.pipeline.asearch(
                    query=query.strip(),
                    top_k=top_k,
                    filters=filters,
                )

            elif hasattr(self.pipeline, "search"):
                results = self.pipeline.search(
                    query=query.strip(),
                    top_k=top_k,
                    filters=filters,
                )

            elif hasattr(self.pipeline, "aretrieve"):
                results = await self.pipeline.aretrieve(
                    query=query.strip(),
                    top_k=top_k,
                )

            elif hasattr(self.pipeline, "retrieve"):
                results = self.pipeline.retrieve(
                    query=query.strip(),
                    top_k=top_k,
                )

            else:
                raise RuntimeError(
                    "RAG pipeline does not provide "
                    "a search or retrieve method."
                )

            if results is None:
                results = []

            return {
                "success": True,
                "query": query.strip(),
                "results": results,
                "message": (
                    "RAG search completed successfully."
                ),
            }

        except Exception as exc:
            print("=" * 60)
            print("RAG TOOL ERROR")
            print("=" * 60)
            print(f"Error type: {type(exc).__name__}")
            print(f"Error: {exc}")
            print("=" * 60)

            return {
                "success": False,
                "query": query.strip(),
                "results": [],
                "error": str(exc),
                "message": "RAG search failed.",
            }
