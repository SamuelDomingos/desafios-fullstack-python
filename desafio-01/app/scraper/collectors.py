from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import Locator, Page

from app.models import Payment, Person
from app.scraper import selectors


@dataclass
class BenefitSummary:
    type: str
    url: str
    nis: str | None = None
    name: str | None = None
    amount_received: str | None = None


def _text_after_label(text: str, label: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    target = label.lower()
    for index, line in enumerate(lines):
        if line.lower() == target and index + 1 < len(lines):
            return lines[index + 1]
    return None


async def extract_person(page: Page) -> Person:
    text = await page.locator("body").inner_text()
    return Person(
        name=_text_after_label(text, "Nome") or "",
        cpf=_text_after_label(text, "CPF"),
        location=_text_after_label(text, "Localidade"),
    )


async def _texts(locator: Locator) -> list[str]:
    total = await locator.count()
    return [(await locator.nth(i).inner_text()).strip() for i in range(total)]


async def _row_cells(row: Locator) -> list[str]:
    return await _texts(row.locator("td"))


async def extract_benefits(page: Page) -> list[BenefitSummary]:
    if await page.locator(selectors.RECEIPTS_SECTION).count() == 0:
        return []

    benefits: list[BenefitSummary] = []
    groups = page.locator(selectors.BENEFIT_BLOCKS)
    for index in range(await groups.count()):
        group = groups.nth(index)
        link = group.locator("a[href*='/beneficios/']").first
        if await link.count() == 0:
            continue

        url = await link.get_attribute("href")
        title = group.locator("strong").first
        benefit_type = (await title.inner_text()).strip() if await title.count() else ""

        row = group.locator("tbody tr").first
        cells = await _row_cells(row) if await row.count() else []

        benefits.append(
            BenefitSummary(
                type=benefit_type,
                url=url or "",
                nis=cells[1] if len(cells) > 1 else None,
                name=cells[2] if len(cells) > 2 else None,
                amount_received=cells[3] if len(cells) > 3 else None,
            )
        )
    return benefits


async def extract_payments(page: Page) -> list[Payment]:
    tables = page.locator("table")
    for index in range(await tables.count()):
        table = tables.nth(index)
        headers = await _texts(table.locator("thead th"))
        if not headers:
            headers = await _texts(table.locator("tr").first.locator("th"))

        rows = table.locator("tbody tr")
        if not headers or await rows.count() == 0:
            continue

        payments: list[Payment] = []
        for i in range(await rows.count()):
            values = await _row_cells(rows.nth(i))
            if len(values) < 2:
                continue
            fields = {
                headers[j]: values[j] for j in range(min(len(headers), len(values)))
            }
            payments.append(Payment(fields=fields))
        if payments:
            return payments
    return []
