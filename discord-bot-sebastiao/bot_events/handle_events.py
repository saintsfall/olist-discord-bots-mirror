from typing import Final
import discord
import os
import requests
from discord import Message
from discord.ext import commands

from utils.utils import send_message

# Lista dos canais permitidos (ID)
ALLOWED_CHANNEL_IDS: Final[list[int]] = [
    1451223826862968902,
    1448786609603608677,
    1448679548454441044
]

# Memória local, perdida ao reiniciar o bot
pending_feedback: dict[int, int] = {}

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

        if isinstance(message.channel, discord.Thread):
            thread = message.channel

            pins = await thread.pins()

            if any(pin.author == bot.user and "Atendimento encerrado" in pin.content for pin in pins):
                return  # ignora thread resolvida

            await thread.send('Solicitação recebida')
            await thread.edit(locked=True)

            webhook_url = os.getenv("N8N_WEBHOOK_URL")

            if not webhook_url:
                return

            starter_message = await thread.fetch_message(thread.id)

            username: str = str(message.author)
            user_message: str = str(message.content)
            channel: str = str(message.channel)

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

            # Envia para o webhook usando requests
            try:
                response = requests.post(webhook_url, json=data, timeout=10)

                if response.status_code == 200:
                    await thread.send(f'Processando sua solicitação! {message.author.mention}')
                else:
                    await thread.send(f'Não foi possível analisar sua pergunta, por favor tente novamente! {message.author.mention}')
                    await thread.edit(locked=False)
            except requests.exceptions.Timeout:
                await thread.send(f'Sua solicitação levou tempo de mais para ser processada, por favor tente novamente! {message.author.mention}')
                await thread.edit(locked=False)
            except Exception as e:
                await thread.send(f'Erro ao inviar sua solicitão, por favor tente novamente! {message.author.mention}')
                await thread.edit(locked=False)

            # await thread.edit(locked=True)
            # await thread.send(f'👀 Mensagem recebida, vamos analisar! {message.author.mention}')

            # bot_message = await thread.send(f'Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n {message.author.mention}')
            # await bot_message.add_reaction("✅")
            # await bot_message.add_reaction("❌")

            # pending_feedback[thread.id] = bot_message.id
        elif message.channel.id == 1461435767636103262:
            if message.author != 'n8n#0000'
                return
            print('entrou else evento on_message')
            print('Autor', message.author)

    # @bot.event
    # async def on_message(message: Message) -> None:
    #     print(f'autor da mensagem', message.author)
    #     print(f'bot', bot.user)
    #     print(message.author == bot.user)

    #     if message.author == bot.user:
    #         return

    #     if isinstance(message.channel, discord.Thread):
    #         thread = message.channel

    #         pins = await thread.pins()

    #         if any(pin.author == bot.user and "Atendimento encerrado" in pin.content for pin in pins):
    #             return  # ignora thread resolvida

    #         starter_message = await thread.fetch_message(thread.id)

    #         username: str = str(message.author)
    #         user_message: str = str(message.content)
    #         channel: str = str(message.channel)

    #         await thread.edit(locked=True)
    #         await thread.send(f'👀 Mensagem recebida, vamos analisar! {message.author.mention}')
    #         print('MANDOU MENSAGEM DO ON_MESSAGE')
            
    #         bot_message = await thread.send(f'Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n {message.author.mention}')
    #         await bot_message.add_reaction("✅")
    #         await bot_message.add_reaction("❌")

    #         pending_feedback[thread.id] = bot_message.id

    @bot.event
    async def on_thread_update(before, after) -> None:
        print('TRHEAD UPDATE')
        if before.archived == False and after.archived == True:
            pins = await after.pins()

            if any(pin.author == bot.user and "Atendimento encerrado" in pin.content for pin in pins):
                print('JÁ TEM A MENSAGEM FIXADA')
                return  # ignora thread resolvida
            
            resolved_message = await after.send("**Atendimento encerrado**")
            await resolved_message.pin()
            await after.edit(archived=True, locked=True)
            print('post rearquivado')

            if after.id in pending_feedback:
                pending_feedback.pop(after.id, None)
                print('feedback removido da lista')

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

        if user.id != starter.author.id:
            return

        # A thread precisa estar aguardando feedback
        expected_message_id = pending_feedback.get(thread.id)
        if expected_message_id != message.id:
            return

        # Só aceita emojis válidos
        if str(reaction.emoji) not in ("✅", "❌"):
            return

        # Decisão do usuário
        if str(reaction.emoji) == "✅":
            resolved_message = await thread.send("**Atendimento encerrado**")
            await resolved_message.pin()

        elif str(reaction.emoji) == "❌":
            await thread.send("Ok 👍 Pode mandar mais detalhes que continuo te ajudando.")
            await thread.edit(locked=False)
            
        pending_feedback.pop(thread.id, None)