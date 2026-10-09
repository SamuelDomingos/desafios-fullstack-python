from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page, Playwright, async_playwright

from app.config import Settings

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]
DEFAULT_ARGS_TO_REMOVE = ["--enable-automation"]
STEALTH_SCRIPT = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class BrowserManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def start(self) -> None:
        if self._browser is not None:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._settings.headless,
            args=LAUNCH_ARGS,
            ignore_default_args=DEFAULT_ARGS_TO_REMOVE,
        )

    async def stop(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def new_page(self) -> AsyncIterator[Page]:
        if self._browser is None:
            await self.start()

        async with self._semaphore:
            assert self._browser is not None
            context = await self._browser.new_context(
                locale="pt-BR",
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 900},
            )
            await context.add_init_script(STEALTH_SCRIPT)
            page = await context.new_page()
            timeout_ms = self._settings.navigation_timeout * 1000
            page.set_default_timeout(timeout_ms)
            page.set_default_navigation_timeout(timeout_ms)
            try:
                yield page
            finally:
                await context.close()
