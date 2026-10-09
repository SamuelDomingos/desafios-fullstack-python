import re


class PortalError(Exception):
    default_message = "Erro ao consultar o Portal da Transparência."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(PortalError):
    def __init__(self, term: str) -> None:
        super().__init__(f"Foram encontrados 0 resultados para o termo {term}")


class ResponseTimeoutError(PortalError):
    def __init__(self) -> None:
        super().__init__(
            "Não foi possível retornar os dados no tempo de resposta solicitado"
        )


class AutomationBlockedError(PortalError):
    def __init__(self) -> None:
        super().__init__("Acesso bloqueado pela proteção automatizada do Portal.")


def looks_like_document(term: str) -> bool:
    digits = re.sub(r"\D", "", term)
    return bool(digits) and len(digits) >= 10 and digits == re.sub(r"[\s.\-/]", "", term)
