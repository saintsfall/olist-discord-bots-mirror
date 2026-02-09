from discord.ext import commands

from bot_commands.migration_commands import register_migration_commands
from bot_commands.reindex_commands import register_reindex_commands
from bot_commands.general_commands import register_general_commands


def set_commands(bot: commands.Bot) -> None:
    """
    Configura todos os slash commands do bot
    Todas as respostas são ephemeral (visiveis apenas para quem executou o commando)
    """
    # Registra comandos de migração
    register_migration_commands(bot)

    # Registra comandos de reindex
    register_reindex_commands(bot)

    # Registra comandos gerais
    register_general_commands(bot)
