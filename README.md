# Discord Bots

Repositório contendo três bots Discord desenvolvidos para diferentes funcionalidades.

## Estrutura do Projeto

Este projeto é um monorepo contendo três bots Discord em pastas separadas:

- **discord-bot-sebastiao/** - Bot para gerenciamento de perguntas respondidas automaticamente por IA usando N8N
- **discord-bot-gilberto/** - Bot para funcionalidades específicas (ver README da pasta)
- **discord-bot-jurandir/** - Bot para gerenciamento de roles e parceiros

Cada bot é uma aplicação Python independente com suas próprias dependências e configurações.

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

## Configuração Local

Cada bot possui seu próprio README com instruções específicas. Consulte:

- [README do Bot Sebastião](discord-bot-sebastiao/README.md)
- [README do Bot Gilberto](discord-bot-gilberto/README.md)
- [README do Bot Jurandir](discord-bot-jurandir/README.md)

## Deploy no Shard Cloud

Este projeto está configurado para deploy no Shard Cloud. Como cada bot está em uma pasta separada, você precisa criar **três aplicações separadas** no Shard Cloud, uma para cada bot.

Consulte o arquivo [SHARDCLOUD.md](SHARDCLOUD.md) para instruções detalhadas sobre como configurar cada bot no Shard Cloud.

### Resumo Rápido

1. Crie três aplicações no Shard Cloud:
   - `sebastiao-bot` apontando para `discord-bot-sebastiao/`
   - `gilberto-bot` apontando para `discord-bot-gilberto/`
   - `jurandir-bot` apontando para `discord-bot-jurandir/`

2. Configure as variáveis de ambiente para cada aplicação (cada bot precisa de seu próprio `DISCORD_TOKEN`)

3. Cada pasta já contém um arquivo `.shardcloud` com as configurações necessárias

## Desenvolvimento

Para trabalhar localmente em um bot específico:

```bash
# Navegue até a pasta do bot
cd discord-bot-sebastiao  # ou gilberto, ou jurandir

# Instale as dependências
uv sync --no-install-project

# Execute o bot
uv run python main.py
```

## Estrutura de Cada Bot

Cada bot segue uma estrutura similar:

```
discord-bot-{nome}/
├── bot_commands/      # Comandos do bot
├── bot_events/        # Eventos do bot
├── utils/             # Utilitários
├── main.py            # Arquivo principal
├── pyproject.toml     # Configuração do projeto e dependências
├── requirements.txt   # Dependências (alternativa)
├── .shardcloud        # Configuração do Shard Cloud
└── .env              # Variáveis de ambiente (não versionado)
```

## Contribuindo

Cada bot pode ser desenvolvido e deployado independentemente. Certifique-se de:

1. Manter as dependências atualizadas em cada bot
2. Testar localmente antes de fazer deploy
3. Configurar as variáveis de ambiente corretamente no Shard Cloud
4. Atualizar a documentação quando necessário
