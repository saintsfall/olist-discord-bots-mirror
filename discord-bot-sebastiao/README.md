# Discord Bot Sebastião

Bot Discord para gerenciamento de perguntas a serem respondidas automáticamente por IA usando o N8N como intermediario entre o discord e uma base de conhecimento em RAG.

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
# Modo MCP (recomendado): define para usar o orquestrador em vez do N8N
ORCHESTRATOR_URL=http://localhost:4000

# Modo N8N (legado): usado quando ORCHESTRATOR_URL não está definida
N8N_WEBHOOK_URL=seu-webhook-n8n-aqui
DISCORD_WEBHOOK=seu-webhook-discord-aqui

DISCORD_TOKEN=seu-token-discord-aqui # Sebastião Bot
```

O bot usa o orquestrador (MCP) se `ORCHESTRATOR_URL` estiver definida; caso contrário, usa o N8N.

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

## Testes

Instale as dependências de desenvolvimento e rode os testes:

```bash
uv sync --extra dev
uv run pytest
```

Para rodar com saída detalhada:

```bash
uv run pytest -v
```

### Relatório Allure

Para gerar relatórios visuais dos testes, use o Allure:

1. Instale o Allure CLI (uma vez no sistema):

   - **macOS:** `brew install allure`
   - **npm:** `npm install -g allure-commandline`

2. Rode os testes gerando dados para o Allure:

```bash
uv run pytest --alluredir=allure-results
```

3. Abra o relatório no navegador:

```bash
allure serve allure-results
```

O Allure exibirá um relatório interativo com detalhes de cada teste, duração e resultados.

## Estrutura do Projeto

```
discord-bot-sebastiao/
├── bot_commands/      # Comandos do bot
├── bot_events/        # Eventos do bot
├── utils/             # Utilitários
├── main.py            # Arquivo principal
├── pyproject.toml     # Configuração do projeto e dependências
└── .env              # Variáveis de ambiente (não versionado)
```

## Comandos do Bot

Use `!sebastiao` no Discord para ver todos os comandos disponíveis.

