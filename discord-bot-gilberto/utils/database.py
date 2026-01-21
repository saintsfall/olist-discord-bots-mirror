from pathlib import Path
import sqlite3
from typing import Optional, Dict
from datetime import datetime, timedelta
import contextlib

DB_FILE = Path("bot_data.db")
DB_TIMEOUT = 5.0  # Timeout de 5 segundos para evitar locks


@contextlib.contextmanager
def get_connection():
    """
    Context manager que garante fechamento da conexão mesmo em caso de erro.
    Faz commit automático em caso de sucesso e rollback em caso de exceção.
    """
    conn = sqlite3.connect(DB_FILE, timeout=DB_TIMEOUT)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
      Inicializa o banco de dados criando as tabelas se não existirem.
      Deve ser chamado no evento on_ready.
    """
    try:
        with get_connection() as conn:
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

        print(f"[DATABASE] banco de dados inicializado: {DB_FILE}")

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao inicializar banco: {e}")


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
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT user_id, message, status, response FROM migration_requests WHERE request_id = ?",
                (request_id,)
            )
            row = cursor.fetchone()

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
        with get_connection() as conn:
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
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM migration_requests WHERE request_id = ?",
                (request_id,)
            )
            deleted = cursor.rowcount > 0
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
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO migration_requests (request_id, user_id, message, status) VALUES (?, ?, ?, 'pending')",
                (request_id, user_id, message)
            )
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
        with get_connection() as conn:
            cursor = conn.execute(
                """
              DELETE FROM migration_requests
              WHERE status = 'ok'
              AND answered_at < julianday('now', '-' || ? || ' days')
            """,
                (days,)
            )

            deleted = cursor.rowcount

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
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM migration_requests WHERE status = 'pending'"
            )
            count = cursor.fetchone()[0]
            return count

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao contar as solicitações: {e}")
        return 0


def update_response(request_id: str, response: str, status: str = 'ok') -> bool:
    """
      Atualiza uma solicitação com a resposta do moderador.

      Args:
          request_id: ID da solicitação
          response: Resposta do moderador
          status: Status da solicitação ('pending', 'ok', 'review'). Padrão: 'ok'

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        # Valida o status
        if status not in ('pending', 'ok', 'review'):
            print(
                f"[DATABASE ERROR] Status inválido: {status}. Deve ser 'pending', 'ok' ou 'review'")
            return False

        with get_connection() as conn:
            # Se o status for 'ok', atualiza também o answered_at
            if status == 'ok':
                cursor = conn.execute(
                    """
                      UPDATE migration_requests
                      SET response = ?, status = ?, answered_at = julianday('now')
                      WHERE request_id = ?""",
                    (response, status, request_id)
                )
            else:
                cursor = conn.execute(
                    """
                      UPDATE migration_requests
                      SET response = ?, status = ?
                      WHERE request_id = ?""",
                    (response, status, request_id)
                )

            updated = cursor.rowcount > 0
            return updated

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao atualizar resposta: {e}")
        return False


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
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT user_id, message, status, response FROM reindex_requests WHERE request_id = ?",
                (request_id,)
            )
            row = cursor.fetchone()

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
        with get_connection() as conn:
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
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM reindex_requests WHERE request_id = ?",
                (request_id,)
            )
            deleted = cursor.rowcount > 0
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
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO reindex_requests (request_id, user_id, message, status) VALUES (?, ?, ?, 'pending')",
                (request_id, user_id, message)
            )
        return True

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao salvar solicitação de reindex: {e}")
        return False


def update_reindex_response(request_id: str, response: str, status: str = 'ok') -> bool:
    """
      Atualiza uma solicitação de reindex com a resposta do moderador.

      Args:
          request_id: ID da solicitação
          response: Resposta do moderador
          status: Status da solicitação ('pending', 'ok', 'review'). Padrão: 'ok'

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        # Valida o status
        if status not in ('pending', 'ok', 'review'):
            print(
                f"[DATABASE ERROR] Status inválido: {status}. Deve ser 'pending', 'ok' ou 'review'")
            return False

        with get_connection() as conn:
            # Se o status for 'ok', atualiza também o answered_at
            if status == 'ok':
                cursor = conn.execute(
                    """
                      UPDATE reindex_requests
                      SET response = ?, status = ?, answered_at = julianday('now')
                      WHERE request_id = ?""",
                    (response, status, request_id)
                )
            else:
                cursor = conn.execute(
                    """
                      UPDATE reindex_requests
                      SET response = ?, status = ?
                      WHERE request_id = ?""",
                    (response, status, request_id)
                )

            updated = cursor.rowcount > 0
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
        with get_connection() as conn:
            cursor = conn.execute(
                """
                  DELETE FROM reindex_requests
                  WHERE status = 'ok'
                  AND answered_at < julianday('now', '-' || ? || ' days')
                """,
                (days,)
            )

            deleted = cursor.rowcount

            if deleted > 0:
                print(
                    f"[DATABASE] Limpeza: removidas {deleted} solicitações de reindex antigas")

            return deleted

    except Exception as e:
        print(f"[DATABASE ERROR] Erro na limpeza de reindex: {e}")
        return 0
