
"""
Tool registry.

Provides a centralized mechanism for registering, discovering,
and executing agent tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


ToolFunction = Callable[..., Awaitable[Any]]


@dataclass
class ToolDefinition:
    """Definition of an agent tool."""

    name: str
    description: str
    function: ToolFunction
    requires_confirmation: bool = False
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ToolResult:
    """Standardized result returned by a tool."""

    success: bool
    tool_name: str
    data: Any = None
    message: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a dictionary."""

        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "metadata": self.metadata,
        }


class ToolRegistry:
    """
    Registry for all agent tools.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        function: ToolFunction,
        requires_confirmation: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool."""

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        if not callable(function):
            raise TypeError(
                "Tool function must be callable."
            )

        self._tools[normalized_name] = ToolDefinition(
            name=normalized_name,
            description=description,
            function=function,
            requires_confirmation=requires_confirmation,
            metadata=metadata or {},
        )

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Remove a registered tool."""

        normalized_name = name.strip().lower()

        if normalized_name not in self._tools:
            return False

        del self._tools[normalized_name]
        return True

    def get(
        self,
        name: str,
    ) -> ToolDefinition | None:
        """Get a tool definition."""

        return self._tools.get(
            name.strip().lower()
        )

    def has(
        self,
        name: str,
    ) -> bool:
        """Check whether a tool exists."""

        return (
            name.strip().lower()
            in self._tools
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return information about all registered tools."""

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_confirmation": (
                    tool.requires_confirmation
                ),
                "metadata": tool.metadata,
            }
            for tool in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a registered tool."""

        normalized_name = name.strip().lower()

        tool = self._tools.get(
            normalized_name
        )

        if tool is None:
            return ToolResult(
                success=False,
                tool_name=normalized_name,
                error=(
                    f"Tool '{normalized_name}' "
                    f"is not registered."
                ),
                message="Tool not found.",
            )

        try:
            result = await tool.function(
                **kwargs
            )

            if isinstance(
                result,
                ToolResult,
            ):
                return result

            return ToolResult(
                success=True,
                tool_name=normalized_name,
                data=result,
                message=(
                    "Tool executed successfully."
                ),
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                tool_name=normalized_name,
                error=str(exc),
                message="Tool execution failed.",
            )

    def clear(self) -> None:
        """Remove all registered tools."""

        self._tools.clear()


# ------------------------------------------------------------------
# Default tool registry
# ------------------------------------------------------------------

default_registry = ToolRegistry()


# ------------------------------------------------------------------
# RAG tool registration
# ------------------------------------------------------------------

def _register_default_tools() -> None:
    """
    Register the tools used by the agent.

    Tool initialization is kept here so that the registry
    remains the central place for agent tool discovery.
    """

    from backend.app.tools.rag_tool import RAGTool

    rag_tool = RAGTool()

    default_registry.register(
        name=rag_tool.name,
        description=rag_tool.description,
        function=rag_tool.execute,
        requires_confirmation=False,
        metadata={
            "category": "retrieval",
            "source": "government_documents",
        },
    )


_register_default_tools()
