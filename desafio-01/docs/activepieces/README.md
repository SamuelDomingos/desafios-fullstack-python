# Parte 2 — Hiperautomação com Activepieces

Fluxo low-code que consome a API do robô (Parte 1), armazena o JSON no
**Google Drive** e registra a consulta em uma planilha do **Google Sheets**.

> Os nomes exatos das peças/steps do Activepieces podem variar levemente entre
> versões; a lógica e os mapeamentos de campos abaixo são o que importa.

## Arquitetura do fluxo

```
[Trigger: Webhook / Formulário]  (term, only_social_program)
              │
              ▼
[HTTP] POST {API_PUBLIC_URL}/query  ─────────►  Robô (API Parte 1)
              │  { query_id, timestamp, person, benefits, evidence, status }
              ▼
[Código] monta nome do arquivo: "{query_id}_{AAAAMMDD_HHMMSS}.json"
              │
              ▼
[Google Drive] Create File  → pasta GOOGLE_DRIVE_FOLDER_ID
              │  { id, webViewLink }
              ▼
[Google Sheets] Insert Row  → planilha GOOGLE_SHEETS_SPREADSHEET_ID
```

## 1. Pré-requisitos no Google Cloud

1. Crie/abra um projeto no [Google Cloud Console](https://console.cloud.google.com/).
2. Em **APIs e serviços → Biblioteca**, habilite:
   - **Google Drive API**
   - **Google Sheets API**
3. Em **APIs e serviços → Tela de consentimento OAuth**, configure o tipo
   *Externo* (ou *Interno*, se tiver Workspace) e adicione os escopos mínimos:
   - `https://www.googleapis.com/auth/drive.file` (apenas arquivos criados pela app)
   - `https://www.googleapis.com/auth/spreadsheets`
4. Em **APIs e serviços → Credenciais**, crie um **ID do cliente OAuth 2.0**
   (tipo *Aplicativo da Web*) e registre a **URI de redirecionamento** fornecida
   pela conexão do Activepieces (algo como `https://<sua-instancia>/redirect`).
5. Guarde `Client ID` e `Client Secret`.

## 2. Recursos no Google

- Crie uma **pasta no Drive** para os JSONs e copie o ID (parte final da URL
  `https://drive.google.com/drive/folders/<FOLDER_ID>`).
- Crie uma **planilha no Sheets** com o cabeçalho:

  | query_id | name | cpf | timestamp | link_json |
  |---|---|---|---|---|

  Copie o ID (trecho entre `/d/` e `/edit` na URL).

## 3. Conexões no Activepieces

Em **Connections**, crie as conexões via **OAuth 2.0**:

- `Google Drive` → preencha Client ID/Secret e conclua o consentimento.
- `Google Sheets` → idem.

As credenciais são guardadas pela própria plataforma — **nunca** as coloque no
repositório.

## 4. Construção do fluxo

1. **Trigger** — escolha conforme o acionamento desejado:
   - *Webhook*, *Form* ou *Manual (Run test)*. Recebe `term` e, opcionalmente,
     `only_social_program`.
2. **HTTP Request** (peça *Webhook/HTTP* → *Send HTTP Request*):
   - Método: `POST`
   - URL: `{API_PUBLIC_URL}/query` (ex.: `https://sua-api/query`)
   - Headers: `Content-Type: application/json`
   - Body (JSON):
     ```json
     {
       "term": "{{trigger.term}}",
       "only_social_program": "{{trigger.only_social_program}}"
     }
     ```
   - Timeout: **180s** (a automação leva alguns segundos por consulta).
3. *(Opcional)* **Branch** — trate `status`:
   - `success` → segue para o Drive/Sheets.
   - `not_found` / `error` → apenas log/notificação (não gera arquivo).
4. **Code** — compose o nome do arquivo (padrão `[ID]_[DATA_HORA].json`):
   ```js
   export const code = async (inputs) => {
     const id = inputs.consulta.query_id;
     const dt = new Date(inputs.consulta.timestamp);
     const p = (n) => String(n).padStart(2, "0");
     const stamp =
       `${dt.getUTCFullYear()}${p(dt.getUTCMonth() + 1)}${p(dt.getUTCDate())}` +
       `_${p(dt.getUTCHours())}${p(dt.getUTCMinutes())}${p(dt.getUTCSeconds())}`;
     return { filename: `${id}_${stamp}.json` };
   };
   ```
5. **Google Drive → Create File**:
   - Parent Folder: `GOOGLE_DRIVE_FOLDER_ID`
   - File Name: `{{code.filename}}`
   - File Content / Body: o **JSON completo** retornado pelo passo HTTP
     (serialize com um passo *Code*: `JSON.stringify(inputs.consulta, null, 2)`)
   - MIME type: `application/json`
   - A saída fornece `id` e `webViewLink`.
6. **Google Sheets → Insert Row**:
   - Spreadsheet: `GOOGLE_SHEETS_SPREADSHEET_ID`
   - Sheet: `Sheet1`
   - Values:
     ```
     {{http.body.query_id}}
     {{http.body.person.name}}
     {{http.body.person.cpf}}
     {{http.body.timestamp}}
     {{drive.webViewLink}}
     ```

## 5. Mapeamento de campos

| Origem (resposta da API) | Destino |
|---|---|
| `query_id` | nome do arquivo + coluna `query_id` |
| `timestamp` | carimbo do nome do arquivo + coluna `timestamp` |
| `person.name` | coluna `name` |
| `person.cpf` | coluna `cpf` |
| `drive.webViewLink` | coluna `link_json` |
| JSON completo | conteúdo do arquivo no Drive |

## 6. Segurança

- OAuth 2.0 com escopos mínimos (Drive `drive.file`, Sheets) — sem chaves embutidas.
- IDs de pasta/planilha apenas como variáveis de ambiente
  (`GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_SHEETS_SPREADSHEET_ID` no `.env`).
- A automação só acessa os arquivos que ela mesma cria (`drive.file`).

## 7. Teste ponta a ponta

1. Suba a API: `python -m app serve` (e exponha publicamente, ex.: túnel/ngrok
   em desenvolvimento, ou use `API_PUBLIC_URL` acessível pela nuvem).
2. Rode o fluxo no Activepieces com um termo de teste (ex.: NIS válido).
3. Verifique:
   - O arquivo `[id]_[carimbo].json` na pasta do Drive.
   - A nova linha na planilha do Sheets com o `webViewLink`.

## 8. Troubleshooting

- **Timeout no HTTP**: aumente para 180s; a primeira execução inclui o start do navegador.
- **Erro de escopo no Drive/Sheets**: reconecte a conexão OAuth após ajustar escopos.
- **Arquivo grande**: a evidência Base64 aumenta o JSON (~200 KB) — normal.
- **`status: not_found`**: o fluxo não deve gravar arquivo; trate no Branch.
