"""
Lógica de exportação do banco (JSON/CSV) para uso pelo script CLI e pelo comando Discord.
Usa o mesmo banco que utils.database (BOT_DB_PATH).
"""
import csv
import io
import json
import sqlite3
from pathlib import Path

from utils.database import DB_FILE, get_connection

TABLES = ("threads",)
DATE_COLUMNS = ("closed_at",)


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def _fetch_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    date_cols = [c for c in DATE_COLUMNS if c in _get_columns(conn, table)]
    if date_cols:
        cols = _get_columns(conn, table)
        selects = [
            f"datetime({c}, 'localtime') as {c}" if c in date_cols else c
            for c in cols
        ]
        cols_str = ", ".join(selects)
    else:
        cols_str = "*"
    cursor = conn.execute(f"SELECT {cols_str} FROM {table}")
    rows = cursor.fetchall()
    col_names = [d[0] for d in cursor.description]
    return [dict(zip(col_names, row)) for row in rows]


def get_export_data() -> dict[str, list] | None:
    """
    Lê as tabelas do banco e retorna um dict com listas de registros.
    Retorna None se o arquivo do banco não existir.
    """
    if not DB_FILE.exists():
        return None
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        data = {}
        for table in TABLES:
            try:
                rows = _fetch_table(conn, table)
                data[table] = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                data[table] = []
        return data


def build_export_json_bytes(data: dict[str, list]) -> bytes:
    """Retorna o export em JSON como bytes (UTF-8)."""
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def build_export_csv_bytes(data: dict[str, list]) -> dict[str, bytes]:
    """Retorna um dict table_name -> bytes do CSV (UTF-8)."""
    result = {}
    for table, rows in data.items():
        if not rows:
            continue
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        result[table] = buf.getvalue().encode("utf-8")
    return result
