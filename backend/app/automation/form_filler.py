"""
Form filling utilities.

The Agent should provide explicit selectors or portal-specific
instructions instead of blindly guessing form fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldFillResult:
    """Result of filling one form field."""

    field_name: str
    selector: str
    value: Any
    success: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "selector": self.selector,
            "value": self.value,
            "success": self.success,
            "message": self.message,
        }


class FormFiller:
    """Fill web forms using Playwright."""

    async def fill_field(
        self,
        page,
        field_name: str,
        selector: str,
        value: Any,
        timeout: int = 10000,
    ) -> FieldFillResult:
        """Fill a single field."""

        if not selector:
            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=value,
                success=False,
                message="Selector is empty.",
            )

        if value is None:
            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=None,
                success=False,
                message="Field value is missing.",
            )

        try:
            locator = page.locator(
                selector
            )

            await locator.wait_for(
                state="visible",
                timeout=timeout,
            )

            await locator.fill(
                str(value)
            )

            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=value,
                success=True,
                message="Field filled successfully.",
            )

        except Exception as exc:
            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=value,
                success=False,
                message=str(exc),
            )

    async def fill_form(
        self,
        page,
        fields: dict[str, dict[str, Any]],
        timeout: int = 10000,
    ) -> list[FieldFillResult]:
        """
        Fill multiple form fields.

        Expected format:

        {
            "name": {
                "selector": "#name",
                "value": "John"
            },
            "email": {
                "selector": "#email",
                "value": "john@example.com"
            }
        }
        """

        results = []

        for field_name, field_data in fields.items():
            selector = field_data.get(
                "selector"
            )

            value = field_data.get(
                "value"
            )

            result = await self.fill_field(
                page=page,
                field_name=field_name,
                selector=selector,
                value=value,
                timeout=timeout,
            )

            results.append(result)

        return results

    async def select_option(
        self,
        page,
        field_name: str,
        selector: str,
        value: str,
        timeout: int = 10000,
    ) -> FieldFillResult:
        """Select an option from a dropdown."""

        try:
            locator = page.locator(
                selector
            )

            await locator.wait_for(
                state="visible",
                timeout=timeout,
            )

            await locator.select_option(
                value=value
            )

            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=value,
                success=True,
                message="Option selected successfully.",
            )

        except Exception as exc:
            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=value,
                success=False,
                message=str(exc),
            )

    async def check(
        self,
        page,
        field_name: str,
        selector: str,
        timeout: int = 10000,
    ) -> FieldFillResult:
        """Check a checkbox."""

        try:
            locator = page.locator(
                selector
            )

            await locator.wait_for(
                state="visible",
                timeout=timeout,
            )

            await locator.check()

            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=True,
                success=True,
                message="Checkbox checked successfully.",
            )

        except Exception as exc:
            return FieldFillResult(
                field_name=field_name,
                selector=selector,
                value=True,
                success=False,
                message=str(exc),
            )

    @staticmethod
    def successful(
        results: list[FieldFillResult],
    ) -> bool:
        """Return whether all fields were filled successfully."""

        return bool(results) and all(
            result.success
            for result in results
        )