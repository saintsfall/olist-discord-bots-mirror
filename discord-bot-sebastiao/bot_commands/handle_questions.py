from discord.ext import commands

from bot_commands.general_commands import register_general_commands
from bot_commands.admin_commands import register_admin_commands


def set_commands(bot: commands.Bot) -> None:
    """
    Configura todos os comandos do bot
    """
    # Registra comandos gerais
    register_general_commands(bot)
    
    # Registra comandos de administração
    register_admin_commands(bot)
