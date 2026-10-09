from __future__ import annotations

from app.config import get_settings

CONSULTATION_PATH = "/pessoa-fisica/busca/lista"

TERM_INPUT = "#termo"
SOCIAL_PROGRAM_CHECKBOX = "#beneficiarioProgramaSocial"

RESULT_LINKS = "a[href*='/busca/pessoa-fisica/']"
NO_RESULTS_PREFIX = "Foram encontrados 0 resultados"

RECEIPTS_SECTION = "#accordion-recebimentos-recursos"
BENEFIT_BLOCKS = "#accordion-recebimentos-recursos .form-group"

BLOCK_INDICATORS = (
    "#amzn-captcha-verify-button",
    "#amzn-captcha-feedback-link",
)
BLOCK_TITLE = "Human Verification"


def consultation_url() -> str:
    return get_settings().portal_base_url.rstrip("/") + CONSULTATION_PATH


def absolute_url(path: str) -> str:
    return get_settings().portal_base_url.rstrip("/") + "/" + path.lstrip("/")
