from datetime import UTC, datetime

from app.models import (
    Benefit,
    Evidence,
    Payment,
    Person,
    QueryRequest,
    QueryResult,
    QueryStatus,
)


def test_status_is_str_enum() -> None:
    assert QueryStatus.SUCCESS == "success"
    assert QueryStatus.NOT_FOUND == "not_found"


def test_query_request_validates_min_length() -> None:
    request = QueryRequest(term="Maria")
    assert request.only_social_program is False


def test_query_result_serializes_to_json() -> None:
    result = QueryResult(
        query_id="abc123",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        term="Maria",
        only_social_program=True,
        status=QueryStatus.SUCCESS,
        message="ok",
        person=Person(name="MARIA", cpf="***.000.000-**", location="BR"),
        benefits=[
            Benefit(
                type="Bolsa Família",
                nis="1.2.3",
                name="MARIA",
                amount_received="R$ 100,00",
                payments=[Payment(fields={"Mês Folha": "01/2024", "Valor (R$)": "100,00"})],
            )
        ],
        evidence=Evidence(image_base64="ZmFrZQ=="),
    )

    payload = result.model_dump(mode="json")
    assert payload["status"] == "success"
    assert payload["person"]["name"] == "MARIA"
    assert payload["benefits"][0]["payments"][0]["fields"]["Valor (R$)"] == "100,00"
    assert payload["evidence"]["content_type"] == "image/png"
