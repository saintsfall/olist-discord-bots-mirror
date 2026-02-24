from discord.ext import commands

from bot_commands.admin_commands import register_admin_commands
from bot_commands.general_commands import register_general_commands
from bot_commands.migration_commands import register_migration_commands
from bot_commands.reindex_commands import register_reindex_commands


def set_commands(bot: commands.Bot) -> None:
    """
    Configura todos os slash commands do bot
    Todas as respostas são ephemeral (visiveis apenas para quem executou o commando)
    """
    register_migration_commands(bot)
    register_reindex_commands(bot)
    register_general_commands(bot)
    register_admin_commands(bot)
