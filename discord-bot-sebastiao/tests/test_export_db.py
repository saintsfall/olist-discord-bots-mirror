"""
Testes do script scripts/export_db.py (exportação JSON e CSV do banco de threads).
Execução: pytest tests/ --alluredir=allure-results
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
        result = subprocess.run(
            cmd, cwd=str(project_root), env=env, capture_output=True, text=True
        )
        assert result.returncode == 0, (result.stdout, result.stderr)

        json_path = out_dir / "export.json"
        assert json_path.exists()
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "threads" in data
        assert len(data["threads"]) == 1
        assert data["threads"][0]["thread_id"] == "111"

        assert (out_dir / "threads.csv").exists()
        csv_content = (out_dir / "threads.csv").read_text(encoding="utf-8")
        assert "thread_id" in csv_content
        assert "111" in csv_content

    @allure.title("Exportação com banco vazio gera JSON com lista vazia")
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
        assert data["threads"] == []

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
        assert not (out_dir / "threads.csv").exists()

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
        assert (out_dir / "threads.csv").exists()

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
