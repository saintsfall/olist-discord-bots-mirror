from pathlib import Path
import sqlite3
from typing import Optional, Dict
from datetime import datetime, timedelta

DB_FILE = Path("bot_data.db")


def init_database() -> None:
    """
      Inicializa o banco de dados criando as tabelas se não existirem.
      Deve ser chamado no evento on_ready.
    """
    conn = sqlite3.connect(DB_FILE)

    # Tabela para solicitações de migração (Launcher)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS migration_requests (
        request_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        response TEXT,
        created_at REAL DEFAULT (julianday('now')),
        answered_at REAL
      )
    """)

    # Tabela para solicitações de reindex
    conn.execute("""
      CREATE TABLE IF NOT EXISTS reindex_requests (
        request_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        response TEXT,
        created_at REAL DEFAULT (julianday('now')),
        answered_at REAL
      )
    """)

    conn.commit()
    conn.close()

    print(f"[DATABASE] banco de dados inicializado: {DB_FILE}")


# ============================================================================
# FUNÇÕES PARA MIGRATION REQUESTS
# ============================================================================

def get_request(request_id: str) -> Optional[Dict]:
    """
      Busca uma solicitação pelo ID.

      Args:
          request_id: ID da solicitação

      Returns:
          Dicionário com dados da solicitação ou None se não encontrada
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT user_id, message, status, response FROM migration_requests WHERE request_id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row["user_id"],
                "message": row["message"],
                "status": row["status"],
                "response": row["response"]
            }
        return None

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao buscar solicitação: {e}")
        return None


def get_user_requests(user_id: int) -> list[Dict]:
    """
      Busca todas as solicitações de um usuário específico.

      Args:
          user_id: ID do usuário

      Returns:
          Lista de dicionários com dados das solicitações, ordenadas por data (mais recente primeiro)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome
        cursor = conn.execute(
            """
          SELECT
            request_id,
            message,
            status,
            response,
            datetime(created_at, 'localtime') as created_at,
            datetime(answered_at, 'localtime') as answered_at
          FROM migration_requests
          WHERE user_id = ?
          ORDER BY created_at DESC
        """,
            (user_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "request_id": row["request_id"],
                "message": row["message"],
                "status": row["status"],
                "response": row["response"],
                "created_at": row["created_at"],
                "answered_at": row["answered_at"]
            }
            for row in rows
        ]

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao buscar solicitações do usuário: {e}")
        return []


def delete_request(request_id: str) -> bool:
    """
      Remove uma solicitação do banco de dados.
      Útil quando o usuário já verificou a resposta.

      Args:
          request_id: ID da solicitação

      Returns:
          True se removeu com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            "DELETE FROM migration_requests WHERE request_id = ?",
            (request_id,)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao deletar a solicitação: {e}")
        return False


def save_request(request_id: str, user_id: int, message: str) -> bool:
    """
      Salva uma nova solicitação no banco de dados.

      Args:
        request_id: ID único da solicitação (geralmente interaction.id)
        user_id: ID do usuário que criou a solicitação
        message: Mensagem da solicitação enviada pelo usuário

      Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO migration_requests (request_id, user_id, message, status) VALUES (?, ?, ?, 'pending')",
            (request_id, user_id, message)
        )
        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao salvar solicitação: {e}")
        return False


def cleanup_old_migration_requests(days: int = 30) -> int:
    """
      Remove solicitações antigas do banco de dados.

      Args:
          days: Número de dias para considerar uma solicitação como "antiga"

      Returns:
          Número de solicitações removidas
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            """
          DELETE FROM migration_requests
          WHERE status = 'ok'
          AND answered_at < julianday('now', '-' || ? || ' days')
        """,
            (days,)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            print(
                f"[DATABASE] Limpeza: removidas {deleted} solicitações antigas")

        return deleted

    except Exception as e:
        print(f"[DATABASE ERROR] Erro na limpeza: {e}")
        return 0


def get_pending_requests_count() -> int:
    """
      Retorna o número de solicitações pendentes.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM migration_requests WHERE status = 'pending'"
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao contar as solicitações: {e}")
        return 0


def update_response(request_id: str, response: str) -> bool:
    """
      Atualiza uma solicitação com a resposta do moderador.

      Args:
          request_id: ID da solicitação
          resposta: Resposta do moderador

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            """
              UPDATE migration_requests
              SET response = ?, status = 'ok', answered_at = julianday('now')
              WHERE request_id = ?""",
            (response, request_id)
        )

        updated = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return updated

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao atualizar resposta: {e}")


# ============================================================================
# FUNÇÕES PARA REINDEX REQUESTS
# ============================================================================

def get_reindex_request(request_id: str) -> Optional[Dict]:
    """
      Busca uma solicitação de reindex pelo ID.

      Args:
          request_id: ID da solicitação

      Returns:
          Dicionário com dados da solicitação ou None se não encontrada
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT user_id, message, status, response FROM reindex_requests WHERE request_id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row["user_id"],
                "message": row["message"],
                "status": row["status"],
                "response": row["response"]
            }
        return None

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao buscar solicitação de reindex: {e}")
        return None


def get_user_reindex_requests(user_id: int) -> list[Dict]:
    """
      Busca todas as solicitações de reindex de um usuário específico.

      Args:
          user_id: ID do usuário

      Returns:
          Lista de dicionários com dados das solicitações, ordenadas por data (mais recente primeiro)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
          SELECT
            request_id,
            message,
            status,
            response,
            datetime(created_at, 'localtime') as created_at,
            datetime(answered_at, 'localtime') as answered_at
          FROM reindex_requests
          WHERE user_id = ?
          ORDER BY created_at DESC
        """,
            (user_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "request_id": row["request_id"],
                "message": row["message"],
                "status": row["status"],
                "response": row["response"],
                "created_at": row["created_at"],
                "answered_at": row["answered_at"]
            }
            for row in rows
        ]

    except Exception as e:
        print(
            f"[DATABASE ERROR] Erro ao buscar solicitações de reindex do usuário: {e}")
        return []


def delete_reindex_request(request_id: str) -> bool:
    """
      Remove uma solicitação de reindex do banco de dados.

      Args:
          request_id: ID da solicitação

      Returns:
          True se removeu com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            "DELETE FROM reindex_requests WHERE request_id = ?",
            (request_id,)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao deletar solicitação de reindex: {e}")
        return False


def save_reindex_request(request_id: str, user_id: int, message: str) -> bool:
    """
      Salva uma nova solicitação de reindex no banco de dados.

      Args:
        request_id: ID único da solicitação (geralmente interaction.id)
        user_id: ID do usuário que criou a solicitação
        message: Mensagem da solicitação enviada pelo usuário

      Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO reindex_requests (request_id, user_id, message, status) VALUES (?, ?, ?, 'pending')",
            (request_id, user_id, message)
        )
        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao salvar solicitação de reindex: {e}")
        return False


def update_reindex_response(request_id: str, response: str) -> bool:
    """
      Atualiza uma solicitação de reindex com a resposta do moderador.

      Args:
          request_id: ID da solicitação
          response: Resposta do moderador

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            """
              UPDATE reindex_requests
              SET response = ?, status = 'ok', answered_at = julianday('now')
              WHERE request_id = ?""",
            (response, request_id)
        )

        updated = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return updated

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao atualizar resposta de reindex: {e}")
        return False


def cleanup_old_reindex_requests(days: int = 30) -> int:
    """
      Remove solicitações de reindex antigas do banco de dados.

      Args:
          days: Número de dias para considerar uma solicitação como "antiga"

      Returns:
          Número de solicitações removidas
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.execute(
            """
              DELETE FROM reindex_requests
              WHERE status = 'ok'
              AND answered_at < julianday('now', '-' || ? || ' days')
            """,
            (days,)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            print(
                f"[DATABASE] Limpeza: removidas {deleted} solicitações de reindex antigas")

        return deleted

    except Exception as e:
        print(f"[DATABASE ERROR] Erro na limpeza de reindex: {e}")
        return 0
