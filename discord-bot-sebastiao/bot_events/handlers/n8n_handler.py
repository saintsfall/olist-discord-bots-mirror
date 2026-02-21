"""
    Handler do fluxo N8N: trigger via webhook e processamento de resposta no canal.
"""
import asyncio
import io

import discord
import requests
from discord import Message
from discord.ext import commands

from utils.database import get_thread, save_thread, update_thread


async def handle_with_n8n(
    thread: discord.Thread,
    message: Message,
    webhook_url: str,
) -> None:
    """
        Envia a mensagem para o webhook N8N. A resposta virá via canal WEBHOOK_CHANNEL_ID.
    """
    user_message: str = str(message.content)
    data = {
        "message": user_message,
        "discord": {
            "thread_id": str(thread.id),
            "channel_id": str(thread.parent_id),
            "message_id": str(message.id),
        },
        "author": {
            "id": str(message.author.id),
            "username": message.author.name,
            "display_name": message.author.display_name,
        },
    }

    try:
        response = requests.post(webhook_url, json=data, timeout=10)

        if response.status_code == 200:
            await thread.send("Processando sua solicitação!")
        else:
            await thread.send(
                f"Não foi possível analisar sua pergunta, por favor tente novamente! {message.author.mention}"
            )
            await thread.edit(locked=False)
    except requests.exceptions.Timeout:
        await thread.send(
            f"Sua solicitação levou tempo de mais para ser processada, por favor tente novamente! {message.author.mention}"
        )
        await thread.edit(locked=False)
    except Exception:
        await thread.send(
            f"Erro ao enviar sua solicitação, por favor tente novamente! {message.author.mention}"
        )
        await thread.edit(locked=False)


async def handle_n8n_webhook_response(bot: commands.Bot, message: Message) -> None:
    """
        Processa mensagem do N8N no canal de webhook e encaminha a resposta para a thread.
    """
    if not message.embeds:
        return

    data = {}
    for embed in message.embeds:
        for field in embed.fields:
            data[field.name] = field.value

    if data.get("source") != "n8n":
        return

    thread_id = data.get("thread_id")
    if not thread_id:
        return

    thread_id = int(thread_id)
    thread = bot.get_channel(thread_id)

    if thread is None:
        try:
            thread = await bot.fetch_channel(thread_id)
        except Exception as e:
            print(f"Erro ao buscar thread {thread_id}: {e}")
            return

    if not isinstance(thread, discord.Thread):
        return

    thread_db = get_thread(thread.id)

    if thread_db and (
        thread_db["status"] == "closed" or thread_db["status"] == "pending_support"
    ):
        return

    event_type = data.get("event_type")
    if event_type == "guardrail_triggered":
        await thread.send(message.content)
        await thread.edit(archived=True, locked=True)
        return

    bot_message_text = "Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n"
    if thread_db and thread_db.get("iteration_count", 0) >= 2:
        bot_message_text = "Isso resolveu seu problema?\n ✅ Sim  ❌ Não  💬 Preciso de ajuda\n\n"

    files_to_send = []
    if message.attachments:
        attachment = message.attachments[0]
        try:
            response = await asyncio.to_thread(
                requests.get, attachment.url, timeout=30
            )
            response.raise_for_status()
            filename = attachment.filename
            if filename.endswith(".txt"):
                filename = filename[:-4] + ".md"
            files_to_send = [
                discord.File(fp=io.BytesIO(
                    response.content), filename=filename)
            ]
        except Exception as e:
            print(f"Erro ao baixar anexo para thread {thread.id}: {e}")

    if files_to_send:
        await thread.send(content=message.content, files=files_to_send)
    else:
        await thread.send(message.content)

    bot_message = await thread.send(bot_message_text)
    await bot_message.add_reaction("✅")
    await bot_message.add_reaction("❌")

    if thread_db:
        update_thread(thread.id, bot_message.id)
        if thread_db.get("iteration_count", 0) >= 2:
            await bot_message.add_reaction("💬")

    if not thread_db:
        starter = await thread.fetch_message(thread.id)
        save_thread(thread_id, starter.author.id, bot_message.id)
