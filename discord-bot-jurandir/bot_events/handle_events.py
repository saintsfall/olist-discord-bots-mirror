import asyncio
import io
import logging
from pathlib import Path

import discord
from discord import Message
from discord.ext import commands

from utils.utils import send_message


def set_events(bot: commands.Bot, *, log_file_path: Path | None = None) -> None:
    async def _log_clear_loop() -> None:
        """
            A cada 8 horas trunca o discord.log e troca o FileHandler do logger.
        """
        path_str = str(log_file_path)
        logger = logging.getLogger("discord")
        while True:
            await asyncio.sleep(8 * 3600)  # 8 horas
            try:
                for h in list(logger.handlers):
                    if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == path_str:
                        logger.removeHandler(h)
                        h.close()
                        break
                with open(log_file_path, "w", encoding="utf-8"):
                    pass
                new_handler = logging.FileHandler(
                    filename=path_str, encoding="utf-8", mode="a")
                logger.addHandler(new_handler)
            except Exception as e:
                print(f"Erro ao limpar log: {e}")

    @bot.event
    async def on_ready() -> None:
        """
            Evento quando o bot está pronto e conectado.
        """
        print(f'{bot.user.name} está online!')
        print(f'Bot ID: {bot.user.id}')

        # Sincroniza os slash commands com o Discord
        try:
            synced = await bot.tree.sync()
            print(f'Sincronizados {len(synced)} comandos.')

        except Exception as e:
            print(f'Erro ao sincronizar os comandos: {e}')

        # Define status do bot
        await bot.change_presence(
            activity=discord.Game(name="Use /ajuda para ajuda"),
            status=discord.Status.online
        )

        # Inicia tarefa que limpa o arquivo de log a cada 8 horas
        if log_file_path is not None:
            asyncio.create_task(_log_clear_loop())

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
