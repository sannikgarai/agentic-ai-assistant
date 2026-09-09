"""
Government portal automation.

Provides controlled navigation and portal state handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass
class PortalResult:
    """Result of a portal operation."""

    success: bool
    action: str
    url: str | None = None
    message: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "url": self.url,
            "message": self.message,
            "metadata": self.metadata,
        }


class PortalManager:
    """Manage navigation to approved portals."""

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
    ):
        self.allowed_domains = {
            self._normalize_domain(domain)
            for domain in (
                allowed_domains or []
            )
        }

    async def navigate(
        self,
        page,
        url: str,
        wait_until: str = "domcontentloaded",
    ) -> PortalResult:
        """Navigate to a portal URL."""

        if not self.is_allowed(url):
            return PortalResult(
                success=False,
                action="navigate",
                url=url,
                message=(
                    "The portal domain is not in "
                    "the approved domain list."
                ),
            )

        try:
            response = await page.goto(
                url,
                wait_until=wait_until,
            )

            status = (
                response.status
                if response is not None
                else None
            )

            return PortalResult(
                success=True,
                action="navigate",
                url=page.url,
                message="Portal opened successfully.",
                metadata={
                    "status": status,
                },
            )

        except Exception as exc:
            return PortalResult(
                success=False,
                action="navigate",
                url=url,
                message=str(exc),
            )

    async def wait_for_selector(
        self,
        page,
        selector: str,
        timeout: int = 10000,
    ) -> PortalResult:
        """Wait for an important portal element."""

        try:
            await page.locator(
                selector
            ).wait_for(
                state="visible",
                timeout=timeout,
            )

            return PortalResult(
                success=True,
                action="wait_for_selector",
                url=page.url,
                message="Element is available.",
                metadata={
                    "selector": selector,
                },
            )

        except Exception as exc:
            return PortalResult(
                success=False,
                action="wait_for_selector",
                url=page.url,
                message=str(exc),
                metadata={
                    "selector": selector,
                },
            )

    async def get_page_text(
        self,
        page,
    ) -> str:
        """Return visible page text."""

        return await page.locator(
            "body"
        ).inner_text()

    def is_allowed(
        self,
        url: str,
    ) -> bool:
        """
        Check whether a URL belongs to an approved domain.

        An empty allowed-domain list rejects all external URLs.
        """

        if not self.allowed_domains:
            return False

        try:
            parsed = urlparse(
                url
            )

            hostname = (
                parsed.hostname
                or ""
            ).lower()

            if not hostname:
                return False

            return any(
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
                for domain in self.allowed_domains
            )

        except Exception:
            return False

    @staticmethod
    def _normalize_domain(
        domain: str,
    ) -> str:
        domain = domain.strip().lower()

        domain = domain.replace(
            "https://",
            "",
        )

        domain = domain.replace(
            "http://",
            "",
        )

        domain = domain.split(
            "/"
        )[0]

        return domain