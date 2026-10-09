from __future__ import annotations

from playwright.async_api import Page

from app.exceptions import (
    AutomationBlockedError,
    NotFoundError,
    ResponseTimeoutError,
    looks_like_document,
)
from app.models import Payment
from app.scraper import collectors, selectors

RESULTS_WAIT_MS = 25000
POLL_INTERVAL_MS = 500
_JS_RESULTS_SNAPSHOT = (
    "() => {"
    " const links = Array.from(document.querySelectorAll(\"a[href*='/busca/pessoa-fisica/']\"))"
    "   .map(e => e.getAttribute('href'));"
    " const t = document.body ? document.body.innerText : '';"
    " return { links, zero: t.includes('Foram encontrados 0 resultados') };"
    "}"
)


class TransparencyPortal:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def search(self, term: str, only_social_program: bool = False) -> str:
        page = self._page
        await page.goto(selectors.consultation_url(), wait_until="domcontentloaded")
        await self._validate_access()

        await page.fill(selectors.TERM_INPUT, term)
        if only_social_program:
            await self._check_social_filter()
        await page.press(selectors.TERM_INPUT, "Enter")

        state = await self._wait_for_results()
        await self._validate_access()
        if state == "empty":
            raise self._not_found_error(term)

        link = page.locator(selectors.RESULT_LINKS).first
        if await link.count() == 0:
            raise self._not_found_error(term)
        return await link.get_attribute("href") or ""

    async def open_record(self, href: str) -> None:
        await self._page.goto(selectors.absolute_url(href), wait_until="domcontentloaded")
        await self._page.wait_for_timeout(800)
        await self._validate_access()

    async def collect_payments(self, href: str) -> list[Payment]:
        await self._page.goto(selectors.absolute_url(href), wait_until="domcontentloaded")
        await self._page.wait_for_timeout(800)
        await self._validate_access()
        return await collectors.extract_payments(self._page)

    @staticmethod
    def _not_found_error(term: str) -> Exception:
        if looks_like_document(term):
            return ResponseTimeoutError()
        return NotFoundError(term)

    async def _check_social_filter(self) -> None:
        checkbox = self._page.locator(selectors.SOCIAL_PROGRAM_CHECKBOX)
        if await checkbox.is_visible():
            await checkbox.check()
        else:
            await checkbox.evaluate("el => { if (!el.checked) el.click(); }")

    async def _wait_for_results(self) -> str:
        previous: dict | None = None
        attempts = max(1, RESULTS_WAIT_MS // POLL_INTERVAL_MS)
        for _ in range(attempts):
            await self._page.wait_for_timeout(POLL_INTERVAL_MS)
            current = await self._page.evaluate(_JS_RESULTS_SNAPSHOT)
            ready = bool(current["links"]) or current["zero"]
            if ready and current == previous:
                return "empty" if current["zero"] else "results"
            previous = current
        return "empty"

    async def _validate_access(self) -> None:
        if (await self._page.title()).strip() == selectors.BLOCK_TITLE:
            raise AutomationBlockedError()
        for selector in selectors.BLOCK_INDICATORS:
            if await self._page.locator(selector).count():
                raise AutomationBlockedError()
