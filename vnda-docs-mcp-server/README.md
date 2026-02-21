# Vnda Docs MCP Server

MCP Server no estilo Context7: expõe tools que acessam a documentação de [developers.vnda.com.br](https://developers.vnda.com.br/) via fetch direto ao site.

## Estrutura

- `vnda_docs_mcp_server/server.py` – Cria o FastMCP e registra as tools.
- `vnda_docs_mcp_server/tools/` – Pasta das tools:
  - `vnda_docs.py` – Tools (list_docs_sections, get_vnda_docs_context), registro e extração de slugs da query (ex.: load_banners, getparam).
  - `doc_fetcher.py` – BASE_URL, crawler da navegação (get_doc_sections com cache 1h e fallback estático), fetch_page_text e relevant_sections.

## Tools

- **list_docs_sections** – Lista seções/páginas disponíveis da documentação. Usa crawler da sidebar (cache 1h); fallback para lista estática se falhar (Search Library).
- **get_vnda_docs_context(query, max_pages=5)** – Busca contexto na doc para responder à pergunta. Extrai slugs da query (ex.: load_banners, avise-me) e prioriza essas páginas; depois busca por relevância nas seções. Retorna snippets com URL de fonte (Get Context).

## Uso local

Requer Python 3.10+ e uv (ou pip).

```bash
# Com uv
uv sync

# Transporte HTTP (para orquestrador e testes)
uv run python -m vnda_docs_mcp_server
```

Por padrão o server sobe em `http://localhost:8000` com transporte streamable-http. O endpoint MCP fica em `http://localhost:8000/mcp`.

## Teste com MCP Inspector

1. Suba o server: `uv run python -m vnda_docs_mcp_server`
2. Em outro terminal: `npx -y @modelcontextprotocol/inspector`
3. Conecte a `http://localhost:8000/mcp`
