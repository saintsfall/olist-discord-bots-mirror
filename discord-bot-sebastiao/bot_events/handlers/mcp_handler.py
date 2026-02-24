"""
    Handler do fluxo MCP: chamada síncrona ao orquestrador.
"""
import io
import logging

import discord
import requests
from discord import Message
from discord.ext import commands

from utils.database import save_thread, update_thread

# Frases que o bot envia e que não fazem parte do histórico de respostas
_BOT_SYSTEM_PHRASES = (
    "Solicitação recebida",
    "Processando sua solicitação!",
    "Isso resolveu",
    "Ok 👍",
    "**Atendimento encerrado**",
)


async def _build_history_from_thread(
    thread: discord.Thread, current_message_id: int, max_exchanges: int = 2
) -> list[dict[str, str]]:
    """
        Monta o histórico (últimas N trocas user/assistant) a partir das mensagens da thread.
    """
    collected: list[dict[str, str]] = []

    async for msg in thread.history(limit=50, oldest_first=True):
        if msg.id == current_message_id:
            continue

        if msg.author.bot:
            if msg.content and len(msg.content) > 20:
                if not any(p in msg.content[:60] for p in _BOT_SYSTEM_PHRASES):
                    collected.append(
                        {"role": "assistant", "content": msg.content})
        else:
            if msg.content:
                collected.append({"role": "user", "content": msg.content})

    return collected[-(max_exchanges * 2):]


async def handle_with_orchestrator(
    bot: commands.Bot,
    thread: discord.Thread,
    message: Message,
    orchestrator_url: str,
    thread_db: dict | None,
) -> None:
    """
        Chama o orquestrador (MCP), recebe resposta síncrona e envia na thread.
    """
    url = orchestrator_url.rstrip("/") + "/answer"
    user_message = str(message.content)
    history = await _build_history_from_thread(thread, message.id)

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
        "history": history,
    }

    try:
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()

        content = result.get("content", "")
        attachment_content = result.get("attachment_content")
        guardrail_triggered = result.get("guardrail_triggered", False)

        if guardrail_triggered:
            await thread.send(content)
            await thread.edit(archived=True, locked=True)
            return

        files_to_send = []
        if attachment_content:
            files_to_send = [
                discord.File(
                    fp=io.BytesIO(attachment_content.encode("utf-8")),
                    filename=f"resposta_{thread.id}.md",
                )
            ]

        if files_to_send:
            await thread.send(content=content, files=files_to_send)
        else:
            await thread.send(content)

        bot_message = "Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n"
        if thread_db and thread_db.get("iteration_count", 0) >= 2:
            bot_message = "Isso resolveu seu problema?\n ✅ Sim  ❌ Não  💬 Preciso de ajuda\n\n"

        reaction_msg = await thread.send(bot_message)
        await reaction_msg.add_reaction("✅")
        await reaction_msg.add_reaction("❌")
        if thread_db and thread_db.get("iteration_count", 0) >= 2:
            await reaction_msg.add_reaction("💬")

        if thread_db:
            update_thread(str(thread.id), reaction_msg.id)
        else:
            save_thread(
                str(thread.id),
                int(thread.owner_id or message.author.id),
                reaction_msg.id,
            )

    except requests.exceptions.Timeout:
        await thread.send(
            f"Sua solicitação levou tempo demais para ser processada. Tente novamente. {message.author.mention}"
        )
        await thread.edit(locked=False)
    except requests.exceptions.RequestException as e:
        logging.getLogger(__name__).exception(
            "Erro ao chamar orquestrador: %s", e)
        await thread.send(
            f"Não foi possível analisar sua pergunta. Tente novamente. {message.author.mention}"
        )
        await thread.edit(locked=False)
    except Exception as e:
        logging.getLogger(__name__).exception(
            "Erro inesperado no orquestrador: %s", e
        )
        await thread.send(
            f"Erro ao processar sua solicitação. Tente novamente. {message.author.mention}"
        )
        await thread.edit(locked=False)
