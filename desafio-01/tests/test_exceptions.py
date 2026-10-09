import pytest

from app.exceptions import (
    AutomationBlockedError,
    NotFoundError,
    ResponseTimeoutError,
    looks_like_document,
)


def test_not_found_message() -> None:
    error = NotFoundError("Joao")
    assert str(error) == "Foram encontrados 0 resultados para o termo Joao"


def test_response_timeout_message() -> None:
    assert (
        str(ResponseTimeoutError())
        == "Não foi possível retornar os dados no tempo de resposta solicitado"
    )


def test_blocked_message() -> None:
    assert "proteção" in str(AutomationBlockedError())


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        ("12345678900", True),
        ("123.456.789-00", True),
        ("20666631640", True),
        ("2.066.663.164-0", True),
        ("Maria da Silva", False),
        ("123", False),
    ],
)
def test_looks_like_document(term: str, expected: bool) -> None:
    assert looks_like_document(term) is expected
