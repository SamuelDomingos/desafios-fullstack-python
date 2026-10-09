from __future__ import annotations

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.exceptions import AutomationBlockedError, NotFoundError, ResponseTimeoutError
from app.models import Evidence, Payment, Person, QueryRequest, QueryStatus
from app.scraper.collectors import BenefitSummary
from app.services import query_service as module
from app.services.query_service import QueryService

HREF = "/busca/pessoa-fisica/1-maria"


def _patch_portal(monkeypatch, *, search=None, collect_payments=None) -> None:
    async def _search(self, term, only_social_program=False):
        return HREF

    async def _open(self, href):
        return None

    async def _collect(self, href):
        return [Payment(fields={"Valor (R$)": "10,00"})]

    monkeypatch.setattr(module.TransparencyPortal, "search", search or _search)
    monkeypatch.setattr(module.TransparencyPortal, "open_record", _open)
    monkeypatch.setattr(
        module.TransparencyPortal, "collect_payments", collect_payments or _collect
    )


def _patch_extraction(monkeypatch) -> None:
    async def _person(page):
        return Person(name="MARIA", cpf="***.000.000-**", location="BR")

    async def _benefits(page):
        return [
            BenefitSummary(
                type="Bolsa Família",
                url="/beneficios/bolsa-familia/1",
                nis="1.2.3",
                name="MARIA",
                amount_received="R$ 10,00",
            )
        ]

    async def _evidence(page):
        return Evidence(image_base64="ZmFrZQ==")

    monkeypatch.setattr(module.collectors, "extract_person", _person)
    monkeypatch.setattr(module.collectors, "extract_benefits", _benefits)
    monkeypatch.setattr(module.screenshot, "capture_evidence", _evidence)


async def test_success_scenario(settings, fake_browser, monkeypatch) -> None:
    _patch_portal(monkeypatch)
    _patch_extraction(monkeypatch)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="Maria")
    )

    assert result.status == QueryStatus.SUCCESS
    assert result.person == Person(name="MARIA", cpf="***.000.000-**", location="BR")
    assert len(result.benefits) == 1
    assert result.benefits[0].type == "Bolsa Família"
    assert result.benefits[0].payments[0].fields["Valor (R$)"] == "10,00"
    assert result.evidence is not None
    assert result.evidence.image_base64 == "ZmFrZQ=="


async def test_not_found_name_scenario(settings, fake_browser, monkeypatch) -> None:
    async def _search(self, term, only_social_program=False):
        raise NotFoundError(term)

    _patch_portal(monkeypatch, search=_search)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="ZzzzInexistente")
    )

    assert result.status == QueryStatus.NOT_FOUND
    assert result.message == (
        "Foram encontrados 0 resultados para o termo ZzzzInexistente"
    )
    assert result.person is None
    assert result.evidence is None


async def test_not_found_document_scenario(settings, fake_browser, monkeypatch) -> None:
    async def _search(self, term, only_social_program=False):
        raise ResponseTimeoutError()

    _patch_portal(monkeypatch, search=_search)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="12345678909")
    )

    assert result.status == QueryStatus.NOT_FOUND
    assert result.message == (
        "Não foi possível retornar os dados no tempo de resposta solicitado"
    )


async def test_browser_timeout_scenario(settings, fake_browser, monkeypatch) -> None:
    async def _search(self, term, only_social_program=False):
        raise PlaywrightTimeoutError("timeout")

    _patch_portal(monkeypatch, search=_search)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="12345678909")
    )

    assert result.status == QueryStatus.NOT_FOUND
    assert "tempo de resposta" in result.message


async def test_waf_block_scenario(settings, fake_browser, monkeypatch) -> None:
    async def _search(self, term, only_social_program=False):
        raise AutomationBlockedError()

    _patch_portal(monkeypatch, search=_search)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="Maria")
    )

    assert result.status == QueryStatus.ERROR
    assert "proteção" in result.message


async def test_failed_benefit_does_not_break_query(
    settings, fake_browser, monkeypatch
) -> None:
    _patch_extraction(monkeypatch)

    async def _collect_fails(self, href):
        raise AutomationBlockedError()

    _patch_portal(monkeypatch, collect_payments=_collect_fails)

    result = await QueryService(fake_browser, settings).query(
        QueryRequest(term="Maria")
    )

    assert result.status == QueryStatus.SUCCESS
    assert result.benefits[0].payments == []
