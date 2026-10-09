# Relatório técnico

Documento complementar ao `README.md`, com as decisões técnicas, os desafios
enfrentados e as justificativas solicitadas no desafio.

## 1. Visão geral da solução

Automação em Python que consulta o Portal da Transparência, extrai os dados da
pessoa física e dos benefícios sociais e devolve um JSON com evidência (screenshot
em Base64). O robô é exposto como API (FastAPI + Scalar) e integrado a um workflow
de hiperautomação (Activepieces → Google Drive/Sheets).

Camadas:
- `scraper/` — automação web (Playwright) e extração de dados.
- `services/` — orquestração e tratamento de erros.
- `api/` — exposição HTTP e documentação.

Todo o código usa **identificadores em inglês**; as **mensagens ao usuário final**
(e os textos de documentação da API) permanecem em português.

## 2. Decisões técnicas

### Playwright (vs. Selenium / requests)
- **Auto-wait** e seletores resilientes reduzem flakiness.
- API **async** nativa → execuções simultâneas com um único navegador e
  **contextos isolados** por consulta (cookies/sessão separados).
- Screenshot nativo (`full_page`) para a evidência.
- Roda em **headless** e em container.

### FastAPI + Scalar
- O FastAPI gera o **OpenAPI automaticamente** a partir dos modelos Pydantic, que
  são os mesmos usados pelo CLI — **contrato único**, sem duplicação.
- O **Scalar** foi escolhido como UI de documentação (moderna e solicitada),
  substituindo o Swagger/Redoc padrão (`docs_url=None`, `redoc_url=None`).

### Modelo `Payment` genérico (mapa cabeçalho → valor)
- Cada benefício expõe colunas diferentes: *Auxílio Brasil* usa "Mês Folha";
  *Auxílio Emergencial* usa "Mês de disponibilização"; *BPC* inclui campos do
  representante legal. Um modelo fixo quebraria.
- Solução: `Payment.fields: dict[str, str]` lido dinamicamente do `<thead>`.

### Seletores centralizados
- `scraper/selectors.py` isola todo seletor/CSS e as URLs. Quando o Portal muda o
  layout, o ajuste é local — sem tocar na lógica de navegação.

### Segurança
- Nenhuma credencial no código: `.env` (ignorado pelo git) + `.env.example`.
- Parte 2 via **OAuth 2.0** com escopos mínimos (`drive.file`, `spreadsheets`).

## 3. Desafios enfrentados (e como foram resolvidos)

### 3.1 AWS WAF no Portal
O Portal é protegido por **AWS WAF**. O Chromium do Playwright, por padrão,
recebe a tela *"Human Verification"* (CAPTCHA) tanto em headless quanto visível.
**Causa:** o flag `--enable-automation` e a propriedade `navigator.webdriver`.
**Solução:** remover o flag (`ignore_default_args=["--enable-automation"]`),
usar `--disable-blink-features=AutomationControlled` e ocultar `navigator.webdriver`.
Com isso a navegação ocorre normalmente.

### 3.2 Formulário oculto e listagem transitória (AJAX)
- O botão "Consultar" e os filtros só aparecem após expandir **"REFINE A BUSCA"**.
- Após submeter, a página exibe uma **listagem padrão transitória** (~1,5 s) e só
  depois os resultados reais, carregados via **AJAX**.
**Solução:** buscar digitando o termo e pressionando **Enter** (o mesmo GET do
formulário) e aguardar por **estabilidade** — o estado só é aceito quando se
repete idêntico em duas verificações consecutivas.

### 3.3 Busca por dígitos (CPF/NIS)
A busca por dígitos também passa pela listagem transitória.
**Solução:** mesma espera por estabilidade, validada com um NIS real.

### 3.4 Mapeamento das mensagens de erro
- Nome inexistente → `"Foram encontrados 0 resultados para o termo …"`.
- CPF/NIS sem retorno → `"Não foi possível retornar os dados no tempo de resposta solicitado"`.
**Solução:** `looks_like_document(term)` decide qual mensagem usar quando a busca
retorna vazio; timeouts do navegador caem na mesma mensagem de tempo de resposta.

> Observação: o CPF `00000000000` é interpretado pelo próprio Portal como
> **curinga** (retorna ~10.000 resultados) — não é um "não encontrado".

### 3.5 Dados mascarados
O Portal exibe CPF mascarado (`***.380.953-**`). O robô preserva exatamente o que
é exibido, em conformidade com a fonte.

## 4. Parte 2 — Plataforma escolhida

**Activepieces**, pelos motivos:
- **Open-source** e com bom *free tier* (inclusive self-host).
- Peças nativas de **Google Drive** e **Google Sheets** com **OAuth 2.0**.
- Editor visual simples que evidencia bem o conceito de hiperautomação na demo.

Fluxo: **HTTP → Code (nome do arquivo) → Google Drive (create file) → Google
Sheets (insert row)**, conforme `docs/activepieces/README.md`.

## 5. Validação

- **5 cenários** do desafio executados contra o Portal real (sucesso por NIS/nome,
  erro por CPF/nome, e busca filtrada).
- **Concorrência**: 3 consultas simultâneas concluídas em ~9,5 s (contextos isolados).
- **API** validada localmente e **dentro do container Docker** (`/health`,
  `/query`, `/scalar`).
- **18 testes** automatizados (`pytest`) verdes e `ruff` sem apontamentos.

## 6. Melhorias futuras

- Cache/rate-limit por termo e métricas de execução.
- Testes de integração reais agendados (não só unitários).
- Extração de todas as páginas de parcelas (paginação).
- Mensagens de erro tipadas na API (mapear `status` para códigos HTTP) por
  configuração.
