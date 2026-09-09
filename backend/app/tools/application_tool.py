"""
Application tool.

Handles government/service application workflows.

Actual browser automation will be connected through the
automation package later.
"""

from __future__ import annotations

from typing import Any


class ApplicationTool:
    """
    Agent tool for application workflows.

    Consequential actions such as final submission should
    require explicit user confirmation.
    """

    name = "application"

    description = (
        "Prepare and manage applications for government "
        "or online services."
    )

    def __init__(
        self,
        automation: Any | None = None,
    ):
        self.automation = automation

    async def execute(
        self,
        operation: str,
        scheme_name: str,
        application_data: dict[str, Any] | None = None,
        document_ids: list[str] | None = None,
        confirmed: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute an application operation."""

        if not isinstance(operation, str) or not operation.strip():
            return {
                "success": False,
                "operation": operation,
                "message": "Application operation is required.",
            }

        if not isinstance(scheme_name, str) or not scheme_name.strip():
            return {
                "success": False,
                "operation": operation.strip().lower(),
                "message": "Scheme name is required.",
            }

        operation = operation.strip().lower()
        scheme_name = scheme_name.strip()

        if application_data is None:
            application_data = {}

        if document_ids is None:
            document_ids = []

        if not isinstance(application_data, dict):
            return {
                "success": False,
                "operation": operation,
                "scheme_name": scheme_name,
                "message": "Application data must be an object.",
            }

        if not isinstance(document_ids, list):
            return {
                "success": False,
                "operation": operation,
                "scheme_name": scheme_name,
                "message": "Document IDs must be a list.",
            }

        consequential_operations = {
            "submit",
            "final_submit",
            "pay",
            "confirm",
        }

        if (
            operation in consequential_operations
            and not confirmed
        ):
            return {
                "success": False,
                "status": "confirmation_required",
                "operation": operation,
                "scheme_name": scheme_name,
                "message": (
                    "User confirmation is required before "
                    "performing this consequential action."
                ),
            }

        if self.automation is None:
            return {
                "success": True,
                "status": "not_connected",
                "operation": operation,
                "scheme_name": scheme_name,
                "application_data": application_data,
                "document_ids": document_ids,
                "message": (
                    "Application automation is not connected yet."
                ),
            }

        try:
            if hasattr(self.automation, "execute"):
                result = self.automation.execute(
                    operation=operation,
                    scheme_name=scheme_name,
                    application_data=application_data,
                    document_ids=document_ids,
                    confirmed=confirmed,
                    **kwargs,
                )

                if hasattr(result, "__await__"):
                    result = await result

            elif hasattr(self.automation, operation):
                method = getattr(
                    self.automation,
                    operation,
                )

                result = method(
                    scheme_name=scheme_name,
                    application_data=application_data,
                    document_ids=document_ids,
                    confirmed=confirmed,
                    **kwargs,
                )

                if hasattr(result, "__await__"):
                    result = await result

            else:
                raise RuntimeError(
                    f"Automation does not support "
                    f"operation '{operation}'."
                )

            return {
                "success": True,
                "status": "completed",
                "operation": operation,
                "scheme_name": scheme_name,
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "operation": operation,
                "scheme_name": scheme_name,
                "error": str(exc),
                "message": (
                    "Application operation failed."
                ),
            }