# Olist Docs MCP Client (Orchestrator)

Serviço HTTP que recebe perguntas de bots (hoje usado pelo bot Sebastião), conecta ao MCP Server (doc Olist), usa OpenAI ChatGPT com as tools do MCP e devolve a resposta no contrato esperado. A pasta e o pacote `orchestrator` são genéricos para permitir que outros bots usem o mesmo recurso no futuro.

Pasta isolada: no Shard Cloud pode ser uma aplicação individual. Cada bot habilita ou desabilita o fluxo MCP via variável de ambiente (`ORCHESTRATOR_URL`); quando desabilitada, o bot segue o fluxo atual (ex.: N8N no caso do Sebastião).

## Variáveis de ambiente

- `OPENAI_API_KEY` – Chave da API OpenAI.
- `MCP_SERVER_URL` – URL do MCP Server (ex.: `http://localhost:8000/mcp` em local).
- `OPENAI_MODEL` – (opcional) Modelo a usar (default: `gpt-4o-mini`).

## Uso local

```bash
uv sync
uv run uvicorn orchestrator.app:app --reload --port 4000
```

## Endpoints

- `POST /answer` – Recebe o mesmo payload que o bot envia ao N8N; retorna `{ "content", "attachment_content", "guardrail_triggered" }`.
  - **Payload:** `message`, `discord`, `author`, e opcionalmente `history` (lista de `{ role, content }` para follow-ups).
  - **Resposta:** Se a resposta tiver mais de 2000 caracteres, `content` traz preview (500 chars) e `attachment_content` o texto completo (Discord envia como anexo). Se `guardrail_triggered` for `true`, a mensagem do usuário foi sinalizada pela moderação (OpenAI Moderation).
- `GET /health` – Health check para o Shard Cloud.

## Fluxo

1. Guardrails: moderação da mensagem via OpenAI Moderation; se sinalizada, retorna mensagem de bloqueio.
2. Conecta ao MCP via streamable-http e chama `answer_with_mcp` (loop de tool calls com OpenAI).
3. Se a resposta for longa (> 2000 chars), divide em preview + attachment_content.

## Estrutura

- `orchestrator/app.py` – FastAPI app, rota `/answer`, guardrails e preparação de content/attachment.
- `orchestrator/llm.py` – Integração OpenAI + MCP (loop de tool calls).
- `orchestrator/prompts.py` – System prompt e diretrizes.
