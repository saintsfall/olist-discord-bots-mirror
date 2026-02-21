"""
    Handlers para fluxos de resposta do bot (MCP/orquestrador, N8N).
"""
from bot_events.handlers.mcp_handler import handle_with_orchestrator
from bot_events.handlers.n8n_handler import (
    handle_with_n8n,
    handle_n8n_webhook_response,
)

__all__ = [
    "handle_with_orchestrator",
    "handle_with_n8n",
    "handle_n8n_webhook_response",
]
