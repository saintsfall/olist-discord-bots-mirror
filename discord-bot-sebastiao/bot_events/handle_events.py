from typing import Final
import discord
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

            starter_message = await thread.fetch_message(thread.id)

            username: str = str(message.author)
            user_message: str = str(message.content)
            channel: str = str(message.channel)

            print('📌 Thread:', thread.name)
            print('Descrição:', starter_message.content)
            print('Nova resposta:', user_message)
            print('Usuário:', username)

            await thread.edit(locked=True)
            await thread.send(f'👀 Mensagem recebida, vamos analisar! {message.author.mention}')
            
            bot_message = await thread.send(f'Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n {message.author.mention}')
            await bot_message.add_reaction("✅")
            await bot_message.add_reaction("❌")

            pending_feedback[thread.id] = bot_message.id

    @bot.event
    async def on_thread_create(thread: discord.Thread) -> None:
        if not isinstance(thread.parent, discord.ForumChannel):
            return

        # Mensagem inicial (descrição do post)
        starter_message = await thread.fetch_message(thread.id)

        author = starter_message.author
        content = starter_message.content

        print('📄 Post criado')
        print('Autor:', author)
        print('Descrição:', content)

        await thread.edit(locked=True)
        await thread.send(f'👀 Mensagem recebida, vamos analisar! {starter_message.author.mention}')
        
        bot_message = await thread.send(f'Isso resolveu seu problema?\n ✅ Sim  ❌ Não\n\n {message.author.mention}')
        await bot_message.add_reaction("✅")
        await bot_message.add_reaction("❌")

        pending_feedback[thread.id] = bot_message.id

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
