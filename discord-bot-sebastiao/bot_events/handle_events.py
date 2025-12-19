from typing import Final
import discord
from discord import Message
from discord.ext import commands

from utils.utils import send_message

# Lista dos canais permitidos (ID)
ALLOWED_CHANNEL_IDS: Final[list[int]] = [
    1451223826862968902
]


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
            activity=discord.Game(name="!sebastiao para ajuda"),
            status=discord.Status.online
        )

    @bot.event
    async def on_message(message: Message) -> None:
        if message.author == bot.user:
            return

        # Verifica se o canal está dentro da lista de canais permitidos
        if ALLOWED_CHANNEL_IDS and message.channel.id not in ALLOWED_CHANNEL_IDS:
            return  # ignora todas as mensagens de canais não permitidos

        username: str = str(message.author)
        user_message: str = str(message.content)
        channel: str = str(message.channel)

        print(f'[{channel}] {username}: "{user_message}"')

        await message.reply(f'Hello there {message.author.mention}')

        await bot.process_commands(message)
