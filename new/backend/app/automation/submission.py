"""
Application submission management.

Submission is separated from form filling so the approval layer can
require explicit user confirmation before a final irreversible action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubmissionResult:
    """Result of application submission."""

    success: bool
    submitted: bool
    status: str
    message: str
    confirmation_number: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "submitted": self.submitted,
            "status": self.status,
            "message": self.message,
            "confirmation_number": (
                self.confirmation_number
            ),
            "metadata": self.metadata,
        }


class SubmissionManager:
    """Manage application submission."""

    async def prepare(
        self,
        page,
        submit_selector: str,
    ) -> SubmissionResult:
        """
        Prepare a page for submission.

        Does not click the final submit button.
        """

        if not submit_selector:
            return SubmissionResult(
                success=False,
                submitted=False,
                status="invalid",
                message="Submit selector is empty.",
            )

        try:
            button = page.locator(
                submit_selector
            )

            visible = await button.is_visible()

            if not visible:
                return SubmissionResult(
                    success=False,
                    submitted=False,
                    status="not_ready",
                    message=(
                        "Submit button is not visible."
                    ),
                )

            enabled = await button.is_enabled()

            if not enabled:
                return SubmissionResult(
                    success=False,
                    submitted=False,
                    status="not_ready",
                    message=(
                        "Submit button is disabled."
                    ),
                )

            return SubmissionResult(
                success=True,
                submitted=False,
                status="ready_for_approval",
                message=(
                    "Application is ready for final submission."
                ),
                metadata={
                    "submit_selector": submit_selector,
                    "url": page.url,
                },
            )

        except Exception as exc:
            return SubmissionResult(
                success=False,
                submitted=False,
                status="error",
                message=str(exc),
            )

    async def submit(
        self,
        page,
        submit_selector: str,
        approved: bool = False,
    ) -> SubmissionResult:
        """
        Submit the application.

        Final submission requires explicit approval.
        """

        if not approved:
            return SubmissionResult(
                success=False,
                submitted=False,
                status="approval_required",
                message=(
                    "Explicit user approval is required "
                    "before final submission."
                ),
            )

        if not submit_selector:
            return SubmissionResult(
                success=False,
                submitted=False,
                status="invalid",
                message="Submit selector is empty.",
            )

        try:
            button = page.locator(
                submit_selector
            )

            await button.wait_for(
                state="visible",
                timeout=10000,
            )

            if not await button.is_enabled():
                return SubmissionResult(
                    success=False,
                    submitted=False,
                    status="not_ready",
                    message=(
                        "Submit button is disabled."
                    ),
                )

            await button.click()

            return SubmissionResult(
                success=True,
                submitted=True,
                status="submitted",
                message=(
                    "Application submission action completed."
                ),
                metadata={
                    "url": page.url,
                },
            )

        except Exception as exc:
            return SubmissionResult(
                success=False,
                submitted=False,
                status="error",
                message=str(exc),
            )