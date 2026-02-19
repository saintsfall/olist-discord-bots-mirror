from typing import Final
import asyncio
import io
import logging
from pathlib import Path

import discord
from discord import Message
from discord.ext import commands

# IMPORT UTILS TO MANAGE SQLITE3 DATABASE
from utils import (
    init_database,
    cleanup_old_migration_requests,
    cleanup_old_reindex_requests
)

# IDs dos canais onde apenas slash commands são permitidos
SLASH_COMMANDS_ONLY_CHANNELS: Final[list[int]] = [
    1461704921693819005,  # Pre Launch Migrations (MIGRATION_CHANNEL_ID)
    1462892195219767431   # Store Reindex (REINDEX_CHANNEL_ID)
]


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
                print(f"Erro ao limpar o log: {e}")

    @bot.event
    async def on_ready() -> None:
        """
          Evento quando o bot está pronto e conectado
        """

        # Inicializa banco de dados
        init_database()

        # Limpa solicitações antigas (30 dias atrás)
        cleanup_old_migration_requests(30)
        cleanup_old_reindex_requests(30)

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
            activity=discord.Game(
                name='Use /solicitar para enviar uma nova solicitação'),
            status=discord.Status.online
        )

        # Inicia a tarefa que limpa o arquivo de log a cada 8 horas
        if log_file_path is not None:
            asyncio.create_task(_log_clear_loop())

    @bot.event
    async def on_message(message: Message) -> None:
        """
          Intercepta todas as mensagens do canal e deleta as que não são slash commands
        """

        # Ignora mensagens do si mesmo
        if message.author == bot.user:
            await bot.process_commands(message)
            return

        # Valida se a mensagem vem de um canal que aceita apenas slash commands
        if message.channel.id in SLASH_COMMANDS_ONLY_CHANNELS:
            # Slash commands não entram como evento de on_message, então todas as mensagens nesse canal devem ser deletadas
            try:
                # Deleta mensagem
                await message.delete()

                # Envia aviso - send (comando que envia mensagem) não permite ephemeral
                await message.channel.send(
                    f"{message.author.mention} Este canal funciona somente com slash commands (/). "
                    f"Mensagens de texto não são permitidas neste canal. "
                    f"Caso tenha dúvidas utilize `/ajuda` para obter mais informações",
                    delete_after=5  # Deleta após 5 segundos
                )
            except discord.errors.NotFound:
                # Mensagem já foi deletada por algum outro processo
                print(
                    'Mensagem não encontrada, possivelmente já a mensagem já foi deletada')
            except discord.errors.Forbidden:
                # Caso o bot não tenha permissão para deletar
                print(
                    f'Erro: Bot sem permissão para deletar a mensagem no canal: {message.channel.id}')
            except Exception as e:
                print(f'Erro ao processar mensagens: {e}')

        await bot.process_commands(message)
