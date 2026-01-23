from typing import Final
import discord
import os
import requests
from discord import Message
from discord.ext import commands

from utils.utils import send_message
from utils.database import (
    save_thread,
    update_thread,
    get_thread,
    close_thread,
    delete_thread,
    cleanup_old_threads,
    init_database
)

# Lista dos canais permitidos (ID)
ALLOWED_CHANNEL_IDS: Final[list[int]] = [
    1451223826862968902,
    1448786609603608677,
    1448679548454441044,
    1463970153753608347
]

WEBHOOK_CHANNEL_ID = 1461435767636103262
SUPPORT_CHANNEL_ID = 1463970153753608347

def set_events(bot: commands.Bot) -> None:
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

        # Define status do bot
        await bot.change_presence(
            activity=discord.Game(name="!sebastiao para ajuda"),
            status=discord.Status.online
        )

    @bot.event
    async def on_message(message: Message) -> None:
        if isinstance(message.channel, discord.Thread) and message.author != bot.user:
            thread = message.channel

            thread_db = get_thread(thread.id)

            if thread_db and (thread_db["status"] == 'closed' or thread_db["status"] == 'pending_support'):
                return #ignora threads fechadas ou aguardando contato

            # Thread fica bloqueada até o bot responder. Evita solicitações fora de ordem
            await thread.send('Solicitação recebida')
            await thread.edit(locked=True)

            webhook_url = os.getenv("N8N_WEBHOOK_URL")

            if not webhook_url:
                return

            # Pega o id do autor da primeira mensagem da thread. É o mesmo id do thread.owner_id
            starter_message = await thread.fetch_message(thread.id)

            username: str = str(message.author)
            user_message: str = str(message.content)
            channel: str = str(message.channel)

            # Estrutura de dados enviada para o n8n
            data = {
                "message": user_message,
                "discord": {
                    "thread_id": str(thread.id),
                    "channel_id": str(thread.parent_id),
                    "message_id": str(message.id)
                },
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                    "display_name": message.author.display_name
                },
            }

            try:
                response = requests.post(webhook_url, json=data, timeout=10)

                if response.status_code == 200:
                    await thread.send(f'Processando sua solicitação!')
                else:
                    await thread.send(f'Não foi possível analisar sua pergunta, por favor tente novamente! {message.author.mention}')
                    await thread.edit(locked=False)
            except requests.exceptions.Timeout:
                await thread.send(f'Sua solicitação levou tempo de mais para ser processada, por favor tente novamente! {message.author.mention}')
                await thread.edit(locked=False)
            except Exception as e:
                await thread.send(f'Erro ao inviar sua solicitão, por favor tente novamente! {message.author.mention}')
                await thread.edit(locked=False)

        # Verifica se a mensagem foi enviado no canal dos logs e se quem enviou foi o próprio bot
        elif message.channel.id == WEBHOOK_CHANNEL_ID and message.author == bot.user:
            if not message.embeds:
                return

            # Armazena os dados recebidos nos embeds da mensagem
            data = {}

            for embed in message.embeds:
                for field in embed.fields:
                    data[field.name] = field.value

            if data.get("source") != "n8n":
                return #Ignora mensagens de fontes que não sejam o n8n

            thread_id = data.get("thread_id")

            if not thread_id:
                return #Ignora mensagens sem thread_id nos embeds

            thread_id = int(thread_id)

            # Tenta buscar a thread no cache do bot
            thread = bot.get_channel(thread_id)

            # Caso a thread não esteja no cache, faz uma requisição para a API
            if thread is None:
                try:
                    thread = await bot.fetch_channel(thread_id)
                except Exception as e:
                    print(f"Erro ao buscar thread {thread_id}: {e}")
                    return

            if not isinstance(thread, discord.Thread):
                return

            thread_db = get_thread(thread.id)

            if thread_db and (thread_db["status"] == "closed" or thread_db["status"] == "pending_support"):
                return #ignora threads fechadas ou aguardando contato

            # Verifica se a mensagem foi bloqueada pelo guardrails
            event_type = data.get("event_type")

            if event_type == "guardrail_triggered":
                await thread.send(message.content)
                await thread.edit(archived=True, locked=True)
                return

            bot_message = 'Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n'

            if thread_db and thread_db["iteration_count"] >= 2:
                bot_message = 'Isso resolveu seu problema?\n ✅ Sim  ❌ Não  💬 Preciso de ajuda\n\n'

            await thread.send(message.content)
            bot_message = await thread.send(bot_message)
            await bot_message.add_reaction("✅")
            await bot_message.add_reaction("❌")

            if thread_db:
                # A cada mensagem do bot, aumenta o contado de interações e atualiza mensagem esperando reação
                update_thread(thread.id, bot_message.id)

                if thread_db["iteration_count"] >= 2:
                    await bot_message.add_reaction("💬")

            # Cria a thread no banco, caso ela ainda não exista
            if not thread_db:
                starter = await thread.fetch_message(thread.id)
                save_thread(thread_id, starter.author.id, bot_message.id)

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
            return #ignora threads fechadas ou reação em mensagens diferentes

        # Só aceita emojis válidos
        if str(reaction.emoji) not in ("✅", "❌", "💬"):
            return

        # Decisão do usuário
        if str(reaction.emoji) == "✅":
            resolved_message = await thread.send("**Atendimento encerrado**")
            await resolved_message.pin()
            close_thread(thread.id)

        #Reabre a thread, para que o usuário possa responder
        elif str(reaction.emoji) == "❌":
            await thread.send("Ok 👍 Pode mandar mais detalhes que continuo te ajudando.")
            await thread.edit(locked=False)

        elif str(reaction.emoji) == "💬":
            await thread.send("Ok 👍 Vou sinalizar a equipe sobre o seu caso.")
            update_thread(thread.id, thread_db["message_id"], "pending_support")
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
        #Evento para remover do banco as threads que forem deletadas manualmente
        thread_db = get_thread(thread.id)

        if not thread_db:
            return

        deleted = delete_thread(thread.id)

        if deleted:
            print(f'Thread: {thread.id} excluída com sucesso')
        else:
            print(f'Erro ao deletar a Thread: {thread.id}')