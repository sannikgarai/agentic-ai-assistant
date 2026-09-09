"""
Verification tool.

Provides the agent with document and data verification
capabilities.
"""

from __future__ import annotations

from typing import Any


class VerificationTool:
    """Agent tool for verification."""

    name = "verification"

    description = (
        "Compare documents and extracted information, "
        "detect mismatches, and check eligibility."
    )

    def __init__(
        self,
        engine: Any | None = None,
    ):
        self.engine = engine

    async def execute(
        self,
        operation: str,
        data: dict[str, Any],
        reference_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a verification operation."""

        if not isinstance(operation, str) or not operation.strip():
            return {
                "success": False,
                "operation": operation,
                "message": "Verification operation is required.",
            }

        if not isinstance(data, dict):
            return {
                "success": False,
                "operation": operation.strip().lower(),
                "message": "Verification data must be an object.",
            }

        operation = operation.strip().lower()

        if self.engine is None:
            return {
                "success": True,
                "operation": operation,
                "status": "not_connected",
                "result": {
                    "matched_fields": [],
                    "mismatched_fields": [],
                    "missing_fields": [],
                },
                "message": (
                    "Verification engine is not connected yet."
                ),
            }

        try:
            if hasattr(self.engine, "verify"):
                result = self.engine.verify(
                    data=data,
                    reference_data=reference_data,
                    operation=operation,
                    **kwargs,
                )

                if hasattr(result, "__await__"):
                    result = await result

            elif hasattr(self.engine, "check"):
                result = self.engine.check(
                    data=data,
                    reference_data=reference_data,
                    operation=operation,
                    **kwargs,
                )

                if hasattr(result, "__await__"):
                    result = await result

            else:
                raise RuntimeError(
                    "Verification engine does not provide "
                    "verify() or check()."
                )

            return {
                "success": True,
                "operation": operation,
                "result": result,
                "message": (
                    "Verification completed successfully."
                ),
            }

        except Exception as exc:
            return {
                "success": False,
                "operation": operation,
                "error": str(exc),
                "message": "Verification failed.",
            }