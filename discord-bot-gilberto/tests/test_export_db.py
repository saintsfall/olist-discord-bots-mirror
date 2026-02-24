"""
Testes do script scripts/export_db.py (exportação JSON e CSV do banco do bot).
Execução: pytest tests/ --alluredir=allure-results
Relatório: allure serve allure-results
"""
import json
import subprocess
import sys
from pathlib import Path

import allure
import pytest


@allure.epic("Scripts")
@allure.feature("export_db")
class TestExportDb:
    """Testes do script de exportação do banco (JSON e CSV)."""

    @allure.title("Exportação gera JSON e CSV quando o banco existe e tem dados")
    @allure.description("Com BOT_DB_PATH apontando para um DB com dados, o script gera export.json e CSVs por tabela.")
    def test_export_creates_json_and_csv(
        self, temp_db_with_data, project_root, tmp_path
    ):
        out_dir = tmp_path / "export_out"
        env = {
            "BOT_DB_PATH": str(temp_db_with_data),
            "PYTHONPATH": str(project_root),
            **__import__("os").environ,
        }
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "export_db.py"),
            "--output",
            str(out_dir),
        ]
        with allure.step("Executar script de export"):
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                env=env,
                capture_output=True,
                text=True,
            )
        assert result.returncode == 0, (result.stdout, result.stderr)

        with allure.step("Verificar export.json"):
            json_path = out_dir / "export.json"
            assert json_path.exists()
            data = json.loads(json_path.read_text(encoding="utf-8"))
            assert "migration_requests" in data
            assert "reindex_requests" in data
            assert len(data["migration_requests"]) == 1
            assert data["migration_requests"][0]["request_id"] == "req-migration-1"
            assert len(data["reindex_requests"]) == 1
            assert data["reindex_requests"][0]["request_id"] == "req-reindex-1"

        with allure.step("Verificar CSVs"):
            assert (out_dir / "migration_requests.csv").exists()
            assert (out_dir / "reindex_requests.csv").exists()
            migration_csv = (out_dir / "migration_requests.csv").read_text(
                encoding="utf-8"
            )
            assert "request_id" in migration_csv
            assert "req-migration-1" in migration_csv

    @allure.title("Exportação com banco vazio gera JSON com listas vazias")
    def test_export_empty_db_creates_valid_json(self, temp_db, project_root, tmp_path):
        out_dir = tmp_path / "export_out"
        env = {
            "BOT_DB_PATH": str(temp_db),
            "PYTHONPATH": str(project_root),
            **__import__("os").environ,
        }
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "export_db.py"),
            "--output",
            str(out_dir),
        ]
        result = subprocess.run(
            cmd, cwd=str(project_root), env=env, capture_output=True, text=True
        )
        assert result.returncode == 0
        data = json.loads((out_dir / "export.json").read_text(encoding="utf-8"))
        assert data["migration_requests"] == []
        assert data["reindex_requests"] == []

    @allure.title("--json-only gera apenas JSON")
    def test_json_only_does_not_create_csv(
        self, temp_db_with_data, project_root, tmp_path
    ):
        out_dir = tmp_path / "export_out"
        env = {
            "BOT_DB_PATH": str(temp_db_with_data),
            "PYTHONPATH": str(project_root),
            **__import__("os").environ,
        }
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "export_db.py"),
            "--output",
            str(out_dir),
            "--json-only",
        ]
        result = subprocess.run(
            cmd, cwd=str(project_root), env=env, capture_output=True, text=True
        )
        assert result.returncode == 0
        assert (out_dir / "export.json").exists()
        assert not (out_dir / "migration_requests.csv").exists()
        assert not (out_dir / "reindex_requests.csv").exists()

    @allure.title("--csv-only gera apenas CSV")
    def test_csv_only_does_not_create_json(
        self, temp_db_with_data, project_root, tmp_path
    ):
        out_dir = tmp_path / "export_out"
        env = {
            "BOT_DB_PATH": str(temp_db_with_data),
            "PYTHONPATH": str(project_root),
            **__import__("os").environ,
        }
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "export_db.py"),
            "--output",
            str(out_dir),
            "--csv-only",
        ]
        result = subprocess.run(
            cmd, cwd=str(project_root), env=env, capture_output=True, text=True
        )
        assert result.returncode == 0
        assert not (out_dir / "export.json").exists()
        assert (out_dir / "migration_requests.csv").exists()
        assert (out_dir / "reindex_requests.csv").exists()

    @allure.title("Script falha com exit 1 quando o arquivo do banco não existe")
    def test_export_fails_when_db_file_missing(self, project_root, tmp_path):
        env = {
            "BOT_DB_PATH": str(tmp_path / "nonexistent.db"),
            "PYTHONPATH": str(project_root),
            **__import__("os").environ,
        }
        cmd = [
            sys.executable,
            str(project_root / "scripts" / "export_db.py"),
            "--output",
            str(tmp_path / "out"),
        ]
        result = subprocess.run(
            cmd, cwd=str(project_root), env=env, capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "não encontrado" in result.stderr or "ERRO" in result.stderr
