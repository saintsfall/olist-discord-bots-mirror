# Guia item a item – substituição N8N por MCP (Estilo Context7)

Este guia descreve o que foi feito e o que fazer em cada item do plano de substituição N8N por MCP.

---

## Item 1: MCP Server com tools (concluído)

**O que foi feito:**

- Projeto `olist-docs-mcp-server` na raiz do repo (ao lado de `discord-bot-sebastiao`).
- Duas tools no estilo Context7:
  - **list_docs_sections** – lista seções/URLs da doc via crawler da sidebar (cache 1h); fallback para lista estática se falhar (Search Library).
  - **get_olist_docs_context(query, max_pages=5)** – extrai slugs da query (ex.: load_banners, avise-me), prioriza essas páginas e busca por relevância. Fetch direto ao site developers.vnda.com.br, extração de texto com BeautifulSoup, retorno de snippets com URL (Get Context).
- Transporte: streamable-http na porta 8000.

**O que você faz agora:**

1. No terminal, entre na pasta do MCP Server e instale as dependências (use uv ou pip):

   ```bash
   cd olist-docs-mcp-server
   uv sync
   # ou: pip install "mcp[cli]" requests beautifulsoup4
   ```

2. Suba o server:

   ```bash
   uv run python -m olist_docs_mcp_server
   # ou: python -m olist_docs_mcp_server
   ```

   Deve aparecer algo como "Listening on..." na porta 8000. O endpoint MCP fica em `http://localhost:8000/mcp` (ou conforme a mensagem no terminal).

3. (Opcional) Teste com o MCP Inspector:

   ```bash
   npx -y @modelcontextprotocol/inspector
   ```

   Na interface, conecte a `http://localhost:8000/mcp` e chame as tools `list_docs_sections` e `get_olist_docs_context` com uma query (ex.: "como customizar loja").

Quando o Item 1 estiver rodando e testado, avance para o **Item 2** (orquestrador).

---

## Item 2: Orquestrador (LLM + MCP client) – concluído

**O que foi feito:** Projeto `olist-docs-mcp-client/` na raiz do repo (pasta isolada; pacote `orchestrator` genérico para uso por vários bots, hoje pelo Sebastião).

- **Stack:** Python, FastAPI, OpenAI (ChatGPT), MCP client (streamable HTTP) para falar com o MCP Server.
- **Rotas:**
  - `POST /answer` – recebe o mesmo payload que o bot envia ao N8N (`message`, `discord`, `author`, opcional `history` para follow-ups); devolve `{ content, attachment_content, guardrail_triggered }`.
  - `GET /health` – health check para o Shard Cloud.
- **Fluxo:** Guardrails (OpenAI Moderation na mensagem do usuário) -> MCP + LLM -> se resposta > 2000 chars, `content` vira preview e `attachment_content` recebe o texto completo.
- **Variáveis:** `OPENAI_API_KEY`, `MCP_SERVER_URL` (ex.: `http://localhost:8000/mcp`), opcional `OPENAI_MODEL` (default: gpt-4o-mini).
- **Habilitar/desabilitar:** Cada bot usa o orquestrador **somente** se `ORCHESTRATOR_URL` estiver definida. Se não estiver, o bot segue o fluxo atual (ex.: N8N no Sebastião). Assim o fluxo MCP pode ser ligado ou desligado só por configuração.

**Como rodar localmente:**

1. Subir o MCP Server: `cd olist-docs-mcp-server && uv run python -m olist_docs_mcp_server`
2. Criar `.env` em `olist-docs-mcp-client/` com `OPENAI_API_KEY` e `MCP_SERVER_URL=http://localhost:8000/mcp`
3. Subir o orquestrador: `cd olist-docs-mcp-client && uv sync && uv run uvicorn orchestrator.app:app --reload --port 4000`
4. Testar: `curl -X POST http://localhost:4000/answer -H "Content-Type: application/json" -d '{"message":"como customizar loja?","discord":{},"author":{}}'`

---

## Item 3: Testes locais (em andamento)

Rodar em conjunto: MCP Server (porta 8000) + Orquestrador (porta 4000) + bot ou `curl` chamando o orquestrador. Validar: a pergunta chega, guardrails rodam, o LLM chama as tools do MCP, recebe o contexto e devolve a resposta (com preview + anexo se for longa).

---

## Item 4: Integração no bot

Alterar `discord-bot-sebastiao/bot_events/handle_events.py` para chamar a URL do orquestrador em vez do webhook N8N e tratar a resposta síncrona (enviar conteúdo na thread). Remover/desativar o fluxo que depende do canal de webhook do N8N.

---

## Item 5: Deploy no Shard Cloud

Deploy do MCP Server e do Orquestrador como aplicações no Shard Cloud; configurar a variável de ambiente do bot (ex.: `ORCHESTRATOR_URL` ou `BACKEND_ANSWER_URL`) com a URL pública do orquestrador.
