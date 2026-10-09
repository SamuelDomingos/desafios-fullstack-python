from __future__ import annotations

import base64

from playwright.async_api import Page

from app.models import Evidence


async def capture_evidence(page: Page, full_page: bool = True) -> Evidence:
    png = await page.screenshot(full_page=full_page, type="png")
    return Evidence(
        image_base64=base64.b64encode(png).decode("ascii"),
        content_type="image/png",
    )
