import discord
from discord import Message
from discord.ext import commands

from utils.utils import send_message


def set_events(bot: commands.Bot) -> None:
    @bot.event
    async def on_ready() -> None:
        """
            Evento quando o bot está pronto e conectado.
        """
        print(f'{bot.user.name} está online!')
        print(f'Bot ID: {bot.user.id}')

        # Define status do bot
        await bot.change_presence(
            activity=discord.Game(name="!jurandir para ajuda"),
            status=discord.Status.online
        )

    @bot.event
    async def on_message(message: Message) -> None:
        if message.author == bot.user:
            return

        username: str = str(message.author)
        user_message: str = str(message.content)
        channel: str = str(message.channel)

        print(f'[{channel}] {username}: "{user_message}"')

        # Skips messages that are bot bot_commands
        # if not user_message.startswith(bot.command_prefix):
        #     await send_message(message, user_message)

        await bot.process_commands(message)
