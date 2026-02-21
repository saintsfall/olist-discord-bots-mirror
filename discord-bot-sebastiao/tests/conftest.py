"""
    Fixtures compartilhadas para os testes.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class AsyncIteratorMock:
    """Simula um async iterator vazio (ex.: thread.history())."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


@pytest.fixture
def mock_author():
    """Autor mock da mensagem (usuário do Discord)."""
    author = MagicMock()
    author.id = 12345
    author.name = "UsuarioTeste"
    author.display_name = "Usuario Teste"
    author.mention = "<@12345>"
    return author


@pytest.fixture
def mock_message(mock_author):
    """Mensagem mock do usuário na thread."""
    message = MagicMock()
    message.id = 999
    message.content = "Como configuro o frete?"
    message.author = mock_author
    return message


@pytest.fixture
def mock_reaction_msg():
    """Mensagem mock que o bot envia (esperando reações)."""
    msg = AsyncMock()
    msg.add_reaction = AsyncMock()
    return msg


@pytest.fixture
def mock_thread(mock_reaction_msg):
    """Thread mock do Discord."""
    thread = MagicMock()
    thread.id = 111
    thread.parent_id = 222
    thread.owner_id = 12345

    thread.send = AsyncMock(return_value=mock_reaction_msg)
    thread.edit = AsyncMock()
    thread.history = MagicMock(return_value=AsyncIteratorMock())

    return thread


@pytest.fixture
def mock_bot(mock_thread):
    """Bot mock do Discord."""
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=mock_thread)
    bot.fetch_channel = AsyncMock(return_value=mock_thread)
    return bot
