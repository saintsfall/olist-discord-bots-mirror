"""
    Ponto de entrada para rodar o MCP Server com transporte HTTP (streamable-http).
    Uso: uv run python -m olist_docs_mcp_server
"""
from olist_docs_mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
