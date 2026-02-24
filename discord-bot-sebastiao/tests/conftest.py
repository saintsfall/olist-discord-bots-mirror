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


# --- Fixtures para testes do script export_db ---
import sqlite3
from pathlib import Path

THREADS_SCHEMA = """
CREATE TABLE IF NOT EXISTS threads (
    thread_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    iteration_count INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    closed_at REAL
)
"""


@pytest.fixture
def temp_db(tmp_path):
    """Banco SQLite temporário com a tabela threads."""
    db_path = tmp_path / "threads.db"
    conn = sqlite3.connect(db_path)
    conn.execute(THREADS_SCHEMA)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def temp_db_with_data(temp_db):
    """Banco com uma linha na tabela threads."""
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO threads (thread_id, user_id, message_id, iteration_count, status) VALUES (?, ?, ?, ?, ?)",
        ("111", 12345, 999, 1, "pending"),
    )
    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def project_root():
    """Raiz do projeto discord-bot-sebastiao."""
    return Path(__file__).resolve().parent.parent
