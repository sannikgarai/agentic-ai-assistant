"""
Search tool.

Provides a generic interface for searching external information.

A real search provider can be connected later without changing
the agent interface.
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable


SearchProvider = Callable[
    [str, int],
    Awaitable[list[dict[str, Any]]],
]


class SearchTool:
    """External search tool."""

    name = "search"

    description = (
        "Search external sources for current "
        "information when required."
    )

    def __init__(
        self,
        provider: SearchProvider | None = None,
    ):
        self.provider = provider

    async def execute(
        self,
        query: str,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """Execute a search."""

        if not query.strip():
            return {
                "success": False,
                "query": query,
                "results": [],
                "message": "Search query cannot be empty.",
            }

        if max_results < 1:
            max_results = 1

        max_results = min(
            max_results,
            20,
        )

        if self.provider is None:
            return {
                "success": True,
                "query": query,
                "results": [],
                "message": (
                    "Search provider is not connected yet."
                ),
            }

        try:
            results = await self.provider(
                query,
                max_results,
            )

            return {
                "success": True,
                "query": query,
                "results": results,
                "message": "Search completed successfully.",
            }

        except Exception as exc:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": str(exc),
                "message": "Search failed.",
            }