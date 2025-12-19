# Discord Bot Jurandir

Bot Discord para gerenciamento de cargos e parceiros.

## Pré-requisitos

- Python 3.10 ou superior
- [uv](https://github.com/astral-sh/uv) instalado

### Instalando o uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Configuração

1. Clone o repositório (se aplicável)

2. Instale as dependências e crie o ambiente virtual:

```bash
uv sync --no-install-project
```

Isso irá:
- Criar um ambiente virtual automaticamente
- Instalar todas as dependências do projeto
- Configurar o ambiente de forma otimizada

**Nota:** Usamos `--no-install-project` porque este é um projeto executável simples que não precisa ser instalado como pacote Python.

3. Configure as variáveis de ambiente:

Crie um arquivo `.env` na raiz do projeto:

```env
DISCORD_TOKEN=seu-token-discord-aqui # Jurandir Bot
```

## Executando o Bot

### Opção 1: Usando uv run (recomendado)

```bash
uv run python main.py
```

### Opção 2: Ativando o ambiente virtual manualmente

```bash
# Ativar o ambiente virtual
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

# Executar o bot
python main.py
```

### Opção 3: Usando os scripts helper (opcional)

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

## Gerenciamento de Dependências

### Adicionar uma nova dependência

```bash
uv add nome-do-pacote
```

### Adicionar uma dependência de desenvolvimento

```bash
uv add --dev nome-do-pacote
```

### Remover uma dependência

```bash
uv remove nome-do-pacote
```

### Atualizar dependências

```bash
uv sync --upgrade
```

### Verificar dependências

```bash
uv pip list
```

## Estrutura do Projeto

```
discord-bot-jurandir/
├── bot_commands/      # Comandos do bot
├── bot_events/        # Eventos do bot
├── utils/             # Utilitários
├── main.py            # Arquivo principal
├── pyproject.toml     # Configuração do projeto e dependências
└── .env              # Variáveis de ambiente (não versionado)
```

## Comandos do Bot

Use `!jurandir` no Discord para ver todos os comandos disponíveis.

