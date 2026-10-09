from __future__ import annotations

import uuid
from datetime import UTC, datetime

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.config import Settings
from app.exceptions import NotFoundError, PortalError, ResponseTimeoutError
from app.models import Benefit, QueryRequest, QueryResult, QueryStatus
from app.scraper import collectors, screenshot
from app.scraper.browser import BrowserManager
from app.scraper.portal import TransparencyPortal


class QueryService:
    def __init__(self, browser: BrowserManager, settings: Settings) -> None:
        self._browser = browser
        self._settings = settings

    async def query(self, request: QueryRequest) -> QueryResult:
        query_id = uuid.uuid4().hex
        try:
            return await self._execute(request, query_id)
        except (NotFoundError, ResponseTimeoutError) as error:
            return self._error_result(request, query_id, error, QueryStatus.NOT_FOUND)
        except PlaywrightTimeoutError:
            error = ResponseTimeoutError()
            return self._error_result(request, query_id, error, QueryStatus.NOT_FOUND)
        except PortalError as error:
            return self._error_result(request, query_id, error, QueryStatus.ERROR)

    async def _execute(self, request: QueryRequest, query_id: str) -> QueryResult:
        async with self._browser.new_page() as page:
            portal = TransparencyPortal(page)
            href = await portal.search(request.term, request.only_social_program)

            await portal.open_record(href)
            person = await collectors.extract_person(page)
            evidence = await screenshot.capture_evidence(page)
            summaries = await collectors.extract_benefits(page)

            benefits: list[Benefit] = []
            for summary in summaries:
                try:
                    payments = await portal.collect_payments(summary.url)
                except PortalError:
                    payments = []
                benefits.append(
                    Benefit(
                        type=summary.type,
                        nis=summary.nis,
                        name=summary.name,
                        amount_received=summary.amount_received,
                        payments=payments,
                    )
                )

            return QueryResult(
                query_id=query_id,
                timestamp=datetime.now(UTC),
                term=request.term,
                only_social_program=request.only_social_program,
                status=QueryStatus.SUCCESS,
                message="Consulta realizada com sucesso.",
                person=person,
                benefits=benefits,
                evidence=evidence,
            )

    @staticmethod
    def _error_result(
        request: QueryRequest,
        query_id: str,
        error: PortalError,
        status: QueryStatus,
    ) -> QueryResult:
        return QueryResult(
            query_id=query_id,
            timestamp=datetime.now(UTC),
            term=request.term,
            only_social_program=request.only_social_program,
            status=status,
            message=error.message,
        )
