from typing import Final
import discord
from discord import Message
from discord.ext import commands

# ID do canal onde as solicitação devem ser feitas apenas usando slash commands
PRE_LAUNCH_MIGRATIONS_CHANNEL_ID: Final[int] = 1461704921693819005


def set_events(bot: commands.Bot) -> None:
    @bot.event
    async def on_ready() -> None:
        """
          Evento quando o bot está pronto e conectado
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
            activity=discord.Game(
                name='Use /solicitar para enviar uma nova solicitação'),
            status=discord.Status.online
        )

    @bot.event
    async def on_message(message: Message) -> None:
        """
          Intercepta todas as mensagens do canal e deleta as que não são slash commands
        """

        # Ignora mensagens do si mesmo
        if message.author == bot.user:
            await bot.process_commands(message)
            return

        # Valida se a mensagem vem do canal correto
        if message.channel.id == PRE_LAUNCH_MIGRATIONS_CHANNEL_ID:
            # Slash commands não entram como evento de on_message, então todas as mensagens nesse canal devem ser deletadas
            try:
                # Deleta mensagem
                await message.delete()

                # Envia aviso - send (comando que envia mensagem) não permite ephemeral
                await message.channel.send(
                    f"{message.author.mention} Ainda não tenho a mensagem correta aqui..."
                    f"Mensagens de texto não são permitidas neste canal.",
                    delete_after=5  # Deleta após 5 segundos
                )
            except discord.erros.NotFound:
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
