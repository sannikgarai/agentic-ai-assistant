"""
Playwright browser management.

Provides a reusable browser lifecycle abstraction for portal
automation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings


class BrowserManager:
    """Manage Playwright browser instances."""

    def __init__(
        self,
        headless: bool | None = None,
        browser_type: str = "chromium",
    ):
        self.headless = (
            settings.playwright_headless
            if headless is None
            else headless
        )

        self.browser_type = browser_type

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self):
        """Start Playwright and create a browser context."""

        try:
            from playwright.async_api import (
                async_playwright,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. "
                "Install it with: pip install playwright"
            ) from exc

        if self._browser is not None:
            return self._page

        self._playwright = (
            await async_playwright().start()
        )

        browser_launcher = getattr(
            self._playwright,
            self.browser_type,
            None,
        )

        if browser_launcher is None:
            await self._playwright.stop()

            raise ValueError(
                f"Unsupported browser type: "
                f"{self.browser_type}"
            )

        self._browser = (
            await browser_launcher.launch(
                headless=self.headless
            )
        )

        self._context = (
            await self._browser.new_context(
                accept_downloads=True
            )
        )

        self._page = (
            await self._context.new_page()
        )

        return self._page

    async def new_page(self):
        """Create a new page."""

        if self._context is None:
            await self.start()

        return await self._context.new_page()

    async def goto(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
    ):
        """Navigate the current page."""

        page = await self._ensure_page()

        if not url:
            raise ValueError(
                "URL cannot be empty."
            )

        return await page.goto(
            url,
            wait_until=wait_until,
        )

    async def current_url(self) -> str:
        """Return current page URL."""

        page = await self._ensure_page()

        return page.url

    async def title(self) -> str:
        """Return current page title."""

        page = await self._ensure_page()

        return await page.title()

    async def screenshot(
        self,
        output_path: str | Path,
        full_page: bool = True,
    ) -> str:
        """Take a screenshot."""

        page = await self._ensure_page()

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await page.screenshot(
            path=str(path),
            full_page=full_page,
        )

        return str(path)

    async def close(self) -> None:
        """Close browser resources."""

        if self._context is not None:
            await self._context.close()
            self._context = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

        self._page = None

    async def _ensure_page(self):
        """Ensure a browser page exists."""

        if self._page is None:
            await self.start()

        if self._page is None:
            raise RuntimeError(
                "Unable to create browser page."
            )

        return self._page

    @property
    def page(self):
        """Return the current page."""

        return self._page

    @property
    def context(self):
        """Return the browser context."""

        return self._context

    @property
    def browser(self):
        """Return the browser."""

        return self._browser