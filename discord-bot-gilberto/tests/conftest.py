"""
Fixtures compartilhadas para os testes.
"""
import sqlite3
from pathlib import Path

import pytest


# Schema igual ao utils/database.py
MIGRATION_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS migration_requests (
    request_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    response TEXT,
    created_at REAL DEFAULT (julianday('now')),
    answered_at REAL
)
"""

REINDEX_REQUESTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS reindex_requests (
    request_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    response TEXT,
    created_at REAL DEFAULT (julianday('now')),
    answered_at REAL
)
"""


@pytest.fixture
def temp_db(tmp_path):
    """Banco SQLite temporário com as tabelas migration_requests e reindex_requests."""
    db_path = tmp_path / "bot_data.db"
    conn = sqlite3.connect(db_path)
    conn.execute(MIGRATION_REQUESTS_SCHEMA)
    conn.execute(REINDEX_REQUESTS_SCHEMA)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def temp_db_with_data(temp_db):
    """Banco com uma linha em cada tabela para validar export."""
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO migration_requests (request_id, user_id, message, status) VALUES (?, ?, ?, ?)",
        ("req-migration-1", 123, "Mensagem de teste migração", "pending"),
    )
    conn.execute(
        "INSERT INTO reindex_requests (request_id, user_id, message, status) VALUES (?, ?, ?, ?)",
        ("req-reindex-1", 456, "Mensagem de teste reindex", "ok"),
    )
    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def project_root():
    """Raiz do projeto discord-bot-gilberto."""
    return Path(__file__).resolve().parent.parent
