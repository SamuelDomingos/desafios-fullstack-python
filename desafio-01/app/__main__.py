from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import uvicorn

from app.config import get_settings
from app.models import QueryRequest, QueryStatus
from app.scraper.browser import BrowserManager
from app.services.query_service import QueryService


def _serve_api() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )


async def _run_query(term: str, only_social_program: bool, output: str | None) -> int:
    settings = get_settings()
    browser = BrowserManager(settings)
    service = QueryService(browser, settings)
    await browser.start()
    try:
        result = await service.query(
            QueryRequest(term=term, only_social_program=only_social_program)
        )
    finally:
        await browser.stop()

    text = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"JSON salvo em: {output}")
    else:
        print(text)
    return 0 if result.status == QueryStatus.SUCCESS else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app",
        description="Robô de consulta ao Portal da Transparência (RPA + hiperautomação).",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Sobe a API HTTP (FastAPI + Scalar).")

    query = sub.add_parser("query", help="Executa uma consulta e gera o JSON.")
    query.add_argument("--term", required=True, help="Nome, CPF ou NIS.")
    query.add_argument(
        "--only-social-program",
        action="store_true",
        help="Aplica o filtro 'Beneficiário de Programa Social'.",
    )
    query.add_argument("--output", default=None, help="Arquivo JSON de destino.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "query":
        code = asyncio.run(_run_query(args.term, args.only_social_program, args.output))
        raise SystemExit(code)

    _serve_api()


if __name__ == "__main__":
    main()
