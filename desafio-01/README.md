# Desafio Full Stack Developer — Python (RPA e Hiperautomação)

Robô de automação web que consulta **Pessoas Físicas** no
[Portal da Transparência](https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista)
e devolve um JSON com os dados coletados e a **evidência da tela em Base64**.
Inclui uma **API REST** documentada (FastAPI + Scalar) e um roteiro de
**hiperautomação** (bônus) com Activepieces, Google Drive e Google Sheets.

## Stack

| Camada | Tecnologia |
|---|---|
| Automação web | **Playwright** (Chromium, async, headless) |
| API | **FastAPI** + **Uvicorn** |
| Documentação | **Scalar** (sobre o OpenAPI do FastAPI) |
| Modelos/validação | **Pydantic v2** + **pydantic-settings** |
| Testes / lint | **pytest**, **pytest-asyncio**, **ruff** |
| Empacotamento | **Docker** + **Docker Compose** |
| Hiperautomação (bônus) | **Activepieces** + Google Drive/Sheets (OAuth 2.0) |

## Arquitetura

```
Cliente (CLI) / Activepieces
        │  POST /query  { term, only_social_program }
        ▼
┌───────────────────────────┐
│  FastAPI  (api/)          │  docs em /scalar (Scalar)
│  QueryService (services/) │
└───────────┬───────────────┘
            ▼
┌───────────────────────────┐
│  Scraper (scraper/)        │  BrowserManager → TransparencyPortal
│  Playwright headless       │  → collectors → screenshot
└───────────┬───────────────┘
            ▼
   models.py (Pydantic)  →  JSON final
```

## Estrutura de pastas

```
desafio-01/
├── app/
│   ├── __main__.py            # CLI: `serve` e `query`
│   ├── config.py              # Settings (pydantic-settings)
│   ├── models.py              # Contrato Pydantic (request/result/benefit)
│   ├── exceptions.py          # Erros de domínio + mensagens exigidas
│   ├── api/                   # FastAPI + Scalar
│   │   ├── app.py             # app factory + lifespan do navegador
│   │   ├── routes.py          # POST /query, GET /health
│   │   └── dependencies.py
│   ├── scraper/               # Automação web
│   │   ├── browser.py         # BrowserManager (headless, isolado, concorrente)
│   │   ├── portal.py          # Navegação de alto nível
│   │   ├── collectors.py      # Extração de dados das páginas
│   │   ├── selectors.py       # Seletores centralizados (manutenção)
│   │   └── screenshot.py      # Screenshot → Base64
│   └── services/
│       └── query_service.py   # Orquestra o fluxo e trata erros
├── tests/                     # pytest (models, exceptions, service)
├── docs/activepieces/         # Guia da Parte 2 (Drive/Sheets + OAuth)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt / requirements-dev.txt
```

## Como executar

### Local

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

### CLI (gera o JSON de uma consulta)

```bash
python -m app query --term "Maria das Gracas de Maria" --output resultado.json
python -m app query --term "20666631640" --only-social-program --output resultado.json
```

### API + documentação

```bash
python -m app serve
# Documentação Scalar:  http://localhost:8000/scalar
# OpenAPI:              http://localhost:8000/openapi.json
```

Exemplo de requisição:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"term": "20666631640", "only_social_program": true}'
```

### Docker

```bash
docker compose up --build
# API em http://localhost:8000/scalar
```

### Expor a API online (para testes)

O desafio pede o bot disponível como API online para testes. Duas opções:

**Túnel (mais rápido, ideal para a demo):**

```bash
python -m app serve
# em outro terminal:
cloudflared tunnel --url http://localhost:8000   # ou: ngrok http 8000
```

Use a URL pública gerada no passo HTTP do Activepieces (Parte 2).

**Container (Docker) em qualquer host — Render, Fly.io, Railway, VPS:**

```bash
docker compose up --build
```

### Testes

```bash
pip install -r requirements-dev.txt
pytest
ruff check app tests
```

## Contrato do JSON

```json
{
  "query_id": "fb1d8222c2aa414b92301f72682cae93",
  "timestamp": "2026-10-08T20:08:30.078903Z",
  "term": "20666631640",
  "only_social_program": true,
  "status": "success",
  "message": "Consulta realizada com sucesso.",
  "person": { "name": "DAIANY ...", "cpf": "***.531.732-**", "location": "BARCARENA - PA" },
  "benefits": [
    {
      "type": "Auxílio Brasil",
      "nis": "1.2.3",
      "name": "DAIANY ...",
      "amount_received": "R$ 1.098,00",
      "payments": [ { "fields": { "Mês Folha": "02/2022", "Valor Parcela": "195,00" } } ]
    }
  ],
  "evidence": { "image_base64": "iVBORw0KGgo...", "content_type": "image/png" }
}
```

- `status`: `success` | `not_found` | `error`.
- `benefits[].payments[].fields`: mapa **cabeçalho → valor**, pois as colunas
  variam por tipo de benefício (Auxílio Brasil, Auxílio Emergencial, BPC, etc.).

## Cenários de teste cobertos

| Cenário | Entrada | Resultado |
|---|---|---|
| Sucesso (CPF/NIS) | NIS válido | `success` + dados + evidência |
| Erro (CPF/NIS) | documento inexistente | `not_found` + *"Não foi possível retornar os dados no tempo de resposta solicitado"* |
| Sucesso (Nome) | nome completo | `success` + 1º registro equivalente + evidência |
| Erro (Nome) | nome inexistente | `not_found` + *"Foram encontrados 0 resultados para o termo …"* |
| Filtrado | nome + filtro social | `success` + 1º registro (beneficiário) + evidência |

## Parte 2 — Hiperautomação (bônus)

Workflow no **Activepieces** que chama a API, grava o JSON no Google Drive
(`[ID]_[DATA_HORA].json`) e registra a consulta no Google Sheets via **OAuth 2.0**.

Passo a passo em [`docs/activepieces/README.md`](docs/activepieces/README.md).
Os IDs da pasta e da planilha vão no `.env`
(`GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_SHEETS_SPREADSHEET_ID`).

## Decisões técnicas (resumo)

- **Playwright** por robustez, auto-wait e suporte nativo a execução headless e
  contextos isolados (concorrência).
- **FastAPI** pela geração automática do OpenAPI; **Scalar** como UI de docs.
- **Separação em camadas** (scraper / service / api) e **seletores centralizados**
  para facilitar manutenção quando o Portal muda.
- **WAF**: o Portal usa AWS WAF; a automação remove os sinais de automação do
  Chromium (`--enable-automation`, `navigator.webdriver`) para navegar normalmente.

Detalhes completos, dificuldades e justificativas em [`RELATORIO.md`](RELATORIO.md).
