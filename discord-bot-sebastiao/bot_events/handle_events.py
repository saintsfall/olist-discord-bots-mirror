import asyncio
import logging
import os
from pathlib import Path

import discord
from discord import Message
from discord.ext import commands

from bot_events.constants import WEBHOOK_CHANNEL_ID, SUPPORT_CHANNEL_ID
from bot_events.handlers import (
    handle_n8n_webhook_response,
    handle_with_n8n,
    handle_with_orchestrator,
)
from utils.database import (
    cleanup_old_threads,
    close_thread,
    delete_thread,
    get_thread,
    init_database,
    update_thread,
)


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

        # Inicializa banco de dados
        init_database()

        # Limpa solicitações antigas (30 dias atrás)
        cleanup_old_threads(30)

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
            activity=discord.Game(name='Use /ajuda para ver os comandos'),
            status=discord.Status.online
        )

        # Inicia tarefa que limpa o arquivo de log a cada 8 horas
        if log_file_path is not None:
            asyncio.create_task(_log_clear_loop())

    @bot.event
    async def on_message(message: Message) -> None:
        if isinstance(message.channel, discord.Thread) and message.author != bot.user:
            thread = message.channel
            thread_db = get_thread(thread.id)

            if thread_db and (
                thread_db["status"] == "closed" or thread_db["status"] == "pending_support"
            ):
                return

            await thread.send("Solicitação recebida")
            await thread.edit(locked=True)

            # Verifica no .env qual o fluxo está "ativo"
            orchestrator_url = os.getenv("ORCHESTRATOR_URL")
            webhook_url = os.getenv("N8N_WEBHOOK_URL")

            # MCP
            if orchestrator_url:
                await handle_with_orchestrator(
                    bot, thread, message, orchestrator_url, thread_db
                )
                return

            # N8N
            if webhook_url:
                await handle_with_n8n(thread, message, webhook_url)
                return

            await thread.edit(locked=False)
            return

        # No fluxo N8N a resposta é enviada a um canal de respostas
        if message.channel.id == WEBHOOK_CHANNEL_ID and message.author == bot.user:
            await handle_n8n_webhook_response(bot, message)

    @bot.event
    async def on_thread_update(before, after) -> None:
        # Quando uma thread é arquivada, fixa uma mensagem do bot e altera o status no banco para "closed"
        if before.archived == False and after.archived == True:
            pins = await after.pins()

            if not any(pin.author == bot.user and "Atendimento encerrado" in pin.content for pin in pins):
                resolved_message = await after.send("**Atendimento encerrado**")
                await resolved_message.pin()

            await after.edit(archived=True, locked=True)

            thread_db = get_thread(after.id)

            if thread_db:
                close_thread(after.id)

    @bot.event
    async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        message = reaction.message

        # Só interessa se estiver dentro de uma thread
        if not isinstance(message.channel, discord.Thread):
            return

        thread = message.channel

        starter = await thread.fetch_message(thread.id)

        # Só considera a reação do autor da thread
        if user.id != starter.author.id:
            return

        thread_db = get_thread(thread.id)

        if not thread_db:
            print(f'A thread: {thread.id} não existe no banco.')
            return

        if thread_db["status"] == 'closed' or message.id != thread_db["message_id"]:
            return  # ignora threads fechadas ou reação em mensagens diferentes

        # Só aceita emojis válidos
        if str(reaction.emoji) not in ("✅", "❌", "💬"):
            return

        # Decisão do usuário
        if str(reaction.emoji) == "✅":
            resolved_message = await thread.send("**Atendimento encerrado**")
            await resolved_message.pin()
            close_thread(thread.id)

        # Reabre a thread, para que o usuário possa responder
        elif str(reaction.emoji) == "❌":
            await thread.send("Ok 👍 Pode mandar mais detalhes que continuo te ajudando.")
            await thread.edit(locked=False)

        elif str(reaction.emoji) == "💬":
            await thread.send("Ok 👍 Vou sinalizar a equipe sobre o seu caso.")
            update_thread(
                thread.id, thread_db["message_id"], "pending_support")
            channel = bot.get_channel(SUPPORT_CHANNEL_ID)

            if channel is None:
                try:
                    channel = await bot.fetch_channel(SUPPORT_CHANNEL_ID)
                except Exception as e:
                    print(f"Erro ao buscar canal {SUPPORT_CHANNEL_ID}: {e}")
                    return

            # Envia mensagem em outro canal, indicando a thread que precisa de atendimento
            embed = discord.Embed(
                title="Solicitação de atendimento",
                description=(
                    f"Thread: <#{thread_db['thread_id']}>\n"
                    f"Usuário: <@{user.id}>\n"
                )
            )

            await channel.send(embed=embed)

    @bot.event
    async def on_thread_delete(thread: discord.Thread):
        # Evento para remover do banco as threads que forem deletadas manualmente
        thread_db = get_thread(thread.id)

        if not thread_db:
            return

        deleted = delete_thread(thread.id)

        if deleted:
            print(f'Thread: {thread.id} excluída com sucesso')
        else:
            print(f'Erro ao deletar a Thread: {thread.id}')
