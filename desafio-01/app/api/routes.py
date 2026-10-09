from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_service
from app.models import QueryRequest, QueryResult
from app.services.query_service import QueryService

router = APIRouter(tags=["Sistema"])


@router.get("/health", summary="Verifica a saúde da API")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/query",
    response_model=QueryResult,
    summary="Executa uma consulta no Portal da Transparência",
    description=(
        "Recebe Nome, CPF ou NIS (e o filtro opcional de beneficiário de programa "
        "social), executa o robô em modo headless e devolve os dados coletados com "
        "a evidência em Base64. O campo `status` indica o resultado: `success`, "
        "`not_found` ou `error`."
    ),
)
async def query(
    payload: QueryRequest,
    service: Annotated[QueryService, Depends(get_service)],
) -> QueryResult:
    return await service.query(payload)
