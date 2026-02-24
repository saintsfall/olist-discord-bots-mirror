"""
    Testes unitários dos handlers MCP e N8N.
"""
import builtins
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot_events.handlers.mcp_handler import handle_with_orchestrator
from bot_events.handlers.n8n_handler import handle_n8n_webhook_response, handle_with_n8n


_original_isinstance = builtins.isinstance


def _patched_isinstance(obj, cls):
    """Faz mocks de thread passarem em isinstance(..., discord.Thread)."""
    if cls is discord.Thread and hasattr(obj, "id"):
        return True
    return _original_isinstance(obj, cls)


class TestMcpHandler:
    """Testes do handler MCP (orquestrador)."""

    @pytest.mark.asyncio
    async def test_handle_with_orchestrator_sucesso(
        self, mock_bot, mock_thread, mock_message, mock_reaction_msg
    ):
        """Resposta normal: envia conteúdo na thread e registra no banco."""
        with (
            patch(
                "bot_events.handlers.mcp_handler.requests.post",
                return_value=MagicMock(
                    raise_for_status=MagicMock(),
                    json=lambda: {
                        "content": "Para configurar o frete, acesse...",
                        "attachment_content": None,
                        "guardrail_triggered": False,
                    },
                ),
            ),
            patch("bot_events.handlers.mcp_handler.update_thread") as mock_update,
            patch("bot_events.handlers.mcp_handler.save_thread") as mock_save,
        ):
            thread_db = {"thread_id": "111", "iteration_count": 1}
            await handle_with_orchestrator(
                mock_bot, mock_thread, mock_message, "http://orchestrator.local", thread_db
            )

            mock_thread.send.assert_called()
            mock_update.assert_called_once_with("111", mock_reaction_msg.id)
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_orchestrator_primeira_interacao_salva_thread(
        self, mock_bot, mock_thread, mock_message, mock_reaction_msg
    ):
        """Primeira mensagem: salva thread no banco (não atualiza)."""
        with (
            patch(
                "bot_events.handlers.mcp_handler.requests.post",
                return_value=MagicMock(
                    raise_for_status=MagicMock(),
                    json=lambda: {
                        "content": "Resposta curta",
                        "attachment_content": None,
                        "guardrail_triggered": False,
                    },
                ),
            ),
            patch("bot_events.handlers.mcp_handler.update_thread") as mock_update,
            patch("bot_events.handlers.mcp_handler.save_thread") as mock_save,
        ):
            await handle_with_orchestrator(
                mock_bot, mock_thread, mock_message, "http://orchestrator.local", None
            )

            mock_save.assert_called_once()
            assert mock_save.call_args[0][0] == "111"
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_orchestrator_guardrail(
        self, mock_bot, mock_thread, mock_message
    ):
        """Guardrail disparado: envia mensagem e arquiva a thread."""
        with patch(
            "bot_events.handlers.mcp_handler.requests.post",
            return_value=MagicMock(
                raise_for_status=MagicMock(),
                json=lambda: {
                    "content": "Sua mensagem foi bloqueada.",
                    "attachment_content": None,
                    "guardrail_triggered": True,
                },
            ),
        ):
            await handle_with_orchestrator(
                mock_bot, mock_thread, mock_message, "http://orchestrator.local", None
            )

            mock_thread.send.assert_called_with("Sua mensagem foi bloqueada.")
            mock_thread.edit.assert_called_once_with(archived=True, locked=True)

    @pytest.mark.asyncio
    async def test_handle_with_orchestrator_timeout(
        self, mock_bot, mock_thread, mock_message
    ):
        """Timeout: envia mensagem de erro e desbloqueia a thread."""
        import requests

        with patch(
            "bot_events.handlers.mcp_handler.requests.post",
            side_effect=requests.exceptions.Timeout(),
        ):
            await handle_with_orchestrator(
                mock_bot, mock_thread, mock_message, "http://orchestrator.local", None
            )

            mock_thread.send.assert_called()
            assert "tempo demais" in mock_thread.send.call_args[0][0].lower()
            mock_thread.edit.assert_called_once_with(locked=False)

    @pytest.mark.asyncio
    async def test_handle_with_orchestrator_payload_correto(
        self, mock_bot, mock_thread, mock_message
    ):
        """Verifica se o payload enviado ao orquestrador está correto."""
        with (
            patch("bot_events.handlers.mcp_handler.requests.post") as mock_post,
            patch("bot_events.handlers.mcp_handler.update_thread"),
        ):
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json.return_value = {
                "content": "OK",
                "attachment_content": None,
                "guardrail_triggered": False,
            }
            thread_db = {"thread_id": "111"}
            await handle_with_orchestrator(
                mock_bot,
                mock_thread,
                mock_message,
                "https://api.example.com/",
                thread_db,
            )

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "json" in call_kwargs
            data = call_kwargs["json"]
            assert data["message"] == "Como configuro o frete?"
            assert data["discord"]["thread_id"] == "111"
            assert data["discord"]["channel_id"] == "222"
            assert data["author"]["username"] == "UsuarioTeste"
            assert data["history"] == []
            assert mock_post.call_args[0][0] == "https://api.example.com/answer"


class TestN8nHandler:
    """Testes do handler N8N."""

    @pytest.mark.asyncio
    async def test_handle_with_n8n_sucesso(self, mock_thread, mock_message):
        """Webhook retorna 200: envia 'Processando sua solicitação!'."""
        with patch(
            "bot_events.handlers.n8n_handler.requests.post",
            return_value=MagicMock(status_code=200),
        ):
            await handle_with_n8n(
                mock_thread, mock_message, "https://n8n.example.com/webhook"
            )

            mock_thread.send.assert_called_once_with("Processando sua solicitação!")

    @pytest.mark.asyncio
    async def test_handle_with_n8n_erro_http(self, mock_thread, mock_message):
        """Webhook retorna erro: envia mensagem de falha e desbloqueia."""
        with patch(
            "bot_events.handlers.n8n_handler.requests.post",
            return_value=MagicMock(status_code=500),
        ):
            await handle_with_n8n(
                mock_thread, mock_message, "https://n8n.example.com/webhook"
            )

            mock_thread.send.assert_called()
            assert "Não foi possível" in mock_thread.send.call_args[0][0]
            mock_thread.edit.assert_called_once_with(locked=False)

    @pytest.mark.asyncio
    async def test_handle_with_n8n_timeout(self, mock_thread, mock_message):
        """Timeout no webhook: desbloqueia a thread."""
        import requests

        with patch(
            "bot_events.handlers.n8n_handler.requests.post",
            side_effect=requests.exceptions.Timeout(),
        ):
            await handle_with_n8n(
                mock_thread, mock_message, "https://n8n.example.com/webhook"
            )

            mock_thread.edit.assert_called_once_with(locked=False)

    @pytest.mark.asyncio
    async def test_handle_with_n8n_payload(self, mock_thread, mock_message):
        """Verifica payload enviado ao webhook N8N."""
        with patch(
            "bot_events.handlers.n8n_handler.requests.post",
        ) as mock_post:
            mock_post.return_value.status_code = 200
            await handle_with_n8n(
                mock_thread, mock_message, "https://n8n.example.com/webhook"
            )

            data = mock_post.call_args[1]["json"]
            assert data["message"] == "Como configuro o frete?"
            assert data["discord"]["thread_id"] == "111"
            assert data["author"]["display_name"] == "Usuario Teste"

    @pytest.mark.asyncio
    async def test_handle_n8n_webhook_response_sem_embeds(self, mock_bot):
        """Mensagem sem embeds: retorna silenciosamente."""
        message = MagicMock()
        message.embeds = []

        await handle_n8n_webhook_response(mock_bot, message)

        mock_bot.get_channel.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_n8n_webhook_response_source_diferente_n8n(self, mock_bot):
        """Embed com source diferente de 'n8n': ignora."""
        embed = MagicMock()
        embed.fields = [MagicMock(name="source", value="outro")]
        message = MagicMock()
        message.embeds = [embed]

        await handle_n8n_webhook_response(mock_bot, message)

        mock_bot.get_channel.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_n8n_webhook_response_sucesso(
        self, mock_bot, mock_thread, mock_reaction_msg
    ):
        """Resposta N8N válida: encaminha para thread e atualiza banco."""
        embed = MagicMock()
        embed.fields = [
            SimpleNamespace(name="source", value="n8n"),
            SimpleNamespace(name="thread_id", value="111"),
        ]
        message = MagicMock()
        message.embeds = [embed]
        message.attachments = []
        message.content = "Resposta do assistente"

        mock_thread.send = AsyncMock(return_value=mock_reaction_msg)
        mock_bot.get_channel.return_value = mock_thread

        with (
            patch(
                "bot_events.handlers.n8n_handler.get_thread",
                return_value={"thread_id": "111", "status": "pending"},
            ),
            patch("bot_events.handlers.n8n_handler.update_thread") as mock_update,
            patch("bot_events.handlers.n8n_handler.save_thread") as mock_save,
            patch.object(builtins, "isinstance", _patched_isinstance),
        ):
            await handle_n8n_webhook_response(mock_bot, message)

            mock_thread.send.assert_called()
            mock_update.assert_called_once()
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_n8n_webhook_response_guardrail(
        self, mock_bot, mock_thread
    ):
        """Evento guardrail: envia conteúdo e arquiva thread."""
        embed = MagicMock()
        embed.fields = [
            SimpleNamespace(name="source", value="n8n"),
            SimpleNamespace(name="thread_id", value="111"),
            SimpleNamespace(name="event_type", value="guardrail_triggered"),
        ]
        message = MagicMock()
        message.embeds = [embed]
        message.content = "Mensagem bloqueada"

        mock_thread.send = AsyncMock()
        mock_thread.edit = AsyncMock()
        mock_bot.get_channel.return_value = mock_thread

        with (
            patch("bot_events.handlers.n8n_handler.get_thread", return_value=None),
            patch.object(builtins, "isinstance", _patched_isinstance),
        ):
            await handle_n8n_webhook_response(mock_bot, message)

            mock_thread.send.assert_called_with("Mensagem bloqueada")
            mock_thread.edit.assert_called_once_with(archived=True, locked=True)
