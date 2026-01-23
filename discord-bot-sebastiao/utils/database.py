from pathlib import Path
import sqlite3
from typing import Optional, Dict
from datetime import datetime, timedelta
import contextlib

DB_FILE = Path("threads.db")
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
            # Tabela para threads de ajuda
            conn.execute("""
              CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                iteration_count INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                closed_at REAL
              )
            """)

        print(f"[DATABASE] banco de dados inicializado: {DB_FILE}")

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao inicializar banco: {e}")

def get_thread(thread_id: str) -> Optional[Dict]:
    """
      Busca uma thread pelo ID.

      Args:
          thread_id: ID da thread

      Returns:
          Dados salvos da thread, ou None
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT thread_id, user_id, message_id, iteration_count, status FROM threads WHERE thread_id = ?",
                (thread_id,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    "thread_id": row["thread_id"],
                    "user_id": row["user_id"],
                    "message_id": row["message_id"],
                    "iteration_count": row["iteration_count"],
                    "status": row["status"]
                }
            return None

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao buscar threads: {e}")
        return None

def delete_thread(thread_id: str) -> bool:
    """
      Remove uma thread do banco de dados.
      Útil quando a thread já foi resolvida.

      Args:
          thread_id: ID da thread

      Returns:
          True se removeu com sucesso, False caso contrário
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM threads WHERE thread_id = ?",
                (thread_id,)
            )
            deleted = cursor.rowcount > 0
            return deleted
    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao deletar a thread: {e}")
        return False

def save_thread(thread_id: str, user_id: int, message_id: int) -> bool:
    """
      Salva uma nova thread no banco de dados.

      Args:
        thread_id: ID único da thread
        user_id: ID do usuário que criou a thread
        message_id: ID da mensagem aguardando reação

      Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO threads (thread_id, user_id, message_id, iteration_count, status, closed_at) VALUES (?, ?, ?, 0, 'pending', NULL)",
                (thread_id, user_id, message_id)
            )
        return True

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao salvar threads: {e}")
        return False

def update_thread(thread_id: str, message_id: int, status: str = "pending") -> bool:
    """
      Atualiza uma thread.

      Args:
          thread_id: ID da thread
          status: Status da solicitação ('pending', 'pending_support')
          message_id: id da mensagem aguardando reação

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        # Valida o status
        if status not in ('pending', 'pending_support'):
            print(
                f"[DATABASE ERROR] Status inválido: {status}. Deve ser 'pending' ou 'pending_support'")
            return False

        with get_connection() as conn:
            cursor = conn.execute(
                """
                    UPDATE threads
                    SET status = ?, message_id = ?, iteration_count = iteration_count + 1
                    WHERE thread_id = ?""",
                (status, message_id, thread_id)
            )

            return cursor.rowcount > 0

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao atualizar a thread: {e}")
        return False

def close_thread(thread_id: str) -> bool:
    """
      Atualiza uma thread.

      Args:
          thread_id: ID da thread
          status: Status da solicitação ('pending', 'closed', 'pending_support').

      Returns:
          True se atualizou com sucesso, False caso contrário
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                    UPDATE threads
                    SET status = 'closed', closed_at = julianday('now')
                    WHERE thread_id = ?""",
                (thread_id,)
            )
            return cursor.rowcount > 0

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao fechar a thread: {e}")
        return False

def cleanup_old_threads(days: int = 30) -> int:
    """
      Remove threads antigas do banco de dados.

      Args:
          days: Número de dias para considerar uma thread como "antiga"

      Returns:
          Número de threads removidas
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
              DELETE FROM threads
              WHERE status = 'closed'
              AND closed_at < julianday('now', '-' || ? || ' days')
            """,
                (days,)
            )

            deleted = cursor.rowcount

            if deleted > 0:
                print(
                    f"[DATABASE] Limpeza: removidas {deleted} threads antigas")

            return deleted

    except Exception as e:
        print(f"[DATABASE ERROR] Erro na limpeza: {e}")
        return 0

def get_pending_threads_count() -> int:
    """
      Retorna o número de threads pendentes.
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM threads WHERE status = 'pending' OR status = 'pending_support'"
            )
            count = cursor.fetchone()[0]
            return count

    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao contar as threads: {e}")
        return 0