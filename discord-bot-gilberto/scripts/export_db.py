"""
Exporta as tabelas do banco SQLite do bot para JSON e CSV.
Usa BOT_DB_PATH (default: bot_data.db). Rode a partir da raiz do projeto:
  python scripts/export_db.py
  python scripts/export_db.py --output ./backups
"""
import argparse
import sys
from pathlib import Path

from utils.db_export import (
    build_export_csv_bytes,
    build_export_json_bytes,
    get_export_data,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta migration_requests e reindex_requests para JSON e CSV."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("export"),
        help="Diretório de saída (default: export)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Gerar apenas JSON",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Gerar apenas CSV",
    )
    args = parser.parse_args()
    out_dir = args.output.resolve()

    data = get_export_data()
    if data is None:
        print("[ERRO] Arquivo do banco não encontrado.", file=sys.stderr)
        sys.exit(1)

    if not args.csv_only:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "export.json"
        json_path.write_bytes(build_export_json_bytes(data))
        print(f"JSON: {json_path}")
    if not args.json_only:
        out_dir.mkdir(parents=True, exist_ok=True)
        for table, content in build_export_csv_bytes(data).items():
            path = out_dir / f"{table}.csv"
            path.write_bytes(content)
            print(f"CSV: {path}")
    print("Exportação concluída.")


if __name__ == "__main__":
    main()
