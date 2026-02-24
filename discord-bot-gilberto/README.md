# discord-bot-gilberto

Bot do Discord para solicitações de migração (Launcher) e reindexação de lojas. Usa SQLite como banco de dados local.

## Configuração

- **DISCORD_TOKEN**: token do bot (obrigatório).
- **BOT_DB_PATH** (opcional): caminho do arquivo do banco SQLite. Padrão: `bot_data.db` no diretório atual. Útil em ambientes com volume persistente para não perder dados entre deploys.

## Banco de dados

O bot usa apenas **SQLite** (sem suporte a outros backends), para manter a curva de aprendizado baixa. As solicitações ficam em um arquivo SQLite com as tabelas `migration_requests` e `reindex_requests`. O arquivo do banco não deve ser commitado (está no `.gitignore`).

### Visualização local

Com o banco no seu ambiente (arquivo `bot_data.db` ou o caminho definido em `BOT_DB_PATH`):

- Abra o arquivo com [DB Browser for SQLite](https://sqlitebrowser.org/) (ou similar) para inspecionar e consultar as tabelas.

### Export para JSON/CSV

Em qualquer ambiente (local ou hospedado), você pode gerar um export legível:

**Script na linha de comando** (a partir da raiz do projeto):

```bash
# Gera pasta export/ com export.json e os dois CSVs
python scripts/export_db.py

# Diretório de saída customizado
python scripts/export_db.py --output ./backups

# Apenas JSON
python scripts/export_db.py --json-only -o ./out

# Apenas CSV
python scripts/export_db.py --csv-only -o ./out
```

O script usa `BOT_DB_PATH` quando definido; caso contrário usa `bot_data.db` no diretório atual.

**Comando no Discord** (apenas role "Moderator"):

- `/db_export`: escolha o formato (JSON ou CSV de uma das tabelas) e o bot envia o arquivo como anexo na conversa (resposta ephemeral). Útil quando não há acesso ao filesystem do host.

## Testes

Dependências de desenvolvimento (pytest + Allure):

```bash
uv sync --extra dev
uv run pytest tests/ -v --alluredir=allure-results
allure serve allure-results
```

## Execução

```bash
uv run python main.py
# ou
python main.py
```
