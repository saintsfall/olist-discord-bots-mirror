"""
    MCP Server: ponto de criação do FastMCP e registro das tools.
"""
from mcp.server.fastmcp import FastMCP

from vnda_docs_mcp_server.tools import register_tools

mcp = FastMCP(
    "Olist Docs",
    json_response=True,
)

register_tools(mcp)
