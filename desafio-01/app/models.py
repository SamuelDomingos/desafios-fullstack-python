from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class QueryStatus(StrEnum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"


class Payment(BaseModel):
    fields: dict[str, str] = Field(default_factory=dict)


class Benefit(BaseModel):
    type: str
    nis: str | None = None
    name: str | None = None
    amount_received: str | None = None
    payments: list[Payment] = Field(default_factory=list)


class Person(BaseModel):
    name: str
    cpf: str | None = None
    location: str | None = None


class Evidence(BaseModel):
    image_base64: str
    content_type: str = "image/png"


class QueryRequest(BaseModel):
    term: str = Field(
        ...,
        min_length=3,
        description="Nome, CPF ou NIS da pessoa física a ser consultada.",
        examples=["Maria da Silva", "12345678900"],
    )
    only_social_program: bool = Field(
        default=False,
        description="Aplica o filtro 'Beneficiário de Programa Social'.",
    )


class QueryResult(BaseModel):
    query_id: str = Field(description="Identificador único da consulta.")
    timestamp: datetime = Field(description="Data/hora da execução da consulta.")
    term: str = Field(description="Termo utilizado na busca.")
    only_social_program: bool = Field(
        description="Indica se o filtro social foi aplicado."
    )
    status: QueryStatus
    message: str | None = Field(
        default=None, description="Mensagem descritiva do resultado."
    )
    person: Person | None = None
    benefits: list[Benefit] = Field(default_factory=list)
    evidence: Evidence | None = None
