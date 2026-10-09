from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app import __version__
from app.api.routes import router
from app.config import get_settings
from app.scraper.browser import BrowserManager
from app.services.query_service import QueryService

DESCRIPTION = """
API de RPA para consulta de **Pessoas Físicas** no Portal da Transparência.

Recebe *Nome*, *CPF* ou *NIS* (e um filtro opcional de programa social),
executa a automação web em modo headless e devolve um JSON com os dados
coletados e a evidência (screenshot em Base64).
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    browser = BrowserManager(settings)
    await browser.start()
    app.state.service = QueryService(browser, settings)
    try:
        yield
    finally:
        await browser.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title="API RPA - Portal da Transparência",
        description=DESCRIPTION,
        version=__version__,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    application.include_router(router)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "nome": "API RPA - Portal da Transparência",
            "documentacao": "/scalar",
            "openapi": application.openapi_url or "/openapi.json",
        }

    @application.get("/scalar", include_in_schema=False)
    async def scalar_reference():
        return get_scalar_api_reference(
            openapi_url=application.openapi_url,
            title="Documentação da API",
            scalar_proxy_url="https://proxy.scalar.com",
        )

    return application


app = create_app()
