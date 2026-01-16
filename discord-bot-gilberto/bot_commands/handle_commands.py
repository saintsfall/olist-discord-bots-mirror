from typing import Final
import discord
from discord import app_commands
from discord.ext import commands

OLIST_BLUE: Final = discord.Color(0x0057dd)


def set_commands(bot: commands.Bot) -> None:
    """
      Configura todos os slash commands do bot
      Todas as respostas são ephemeral (visiveis apenas para quem executou o commando)
    """

    @bot.tree.command(name="solicitar", description="Envia solicitação de loja a ter os dados migrados no Launcher.")
    @app_commands.describe(mensagem="Informe qual o dominio final da loja a ter os dados migrados")
    async def solicitar(interaction: discord.Interaction, mensagem: str) -> None:
        """
          Comando para informar loja a ter os dados migrados de STG para CDN via Launcher
        """
        # Resposta ephemeral - somente o usuário que executou o comando consegue ver
        await interaction.response.send_message(
            "Sua solicitação foi recebida! Um moderador irá atendê-la em breve",
            ephemeral=True
        )

        # TODO Envia para solicitação para canal privado dos moderadores

    @bot.tree.command(name='ajuda', description='Passa informações sobre como usar o bot')
    async def ajuda(interaction: discord.Interaction) -> None:
        """
          Comando de ajuda com informações sobre o bot
          A resposta é ephemeral
        """

        embed = discord.Embed(
            title="Como usar o bot",
            description="Este canal aceita apenas slash commands (/)",
            color=OLIST_BLUE
        )

        embed.add_field(
            name="Comandos disponíveis",
            value="`/solicitar <mensagem>` - Envie uma solicitação privada\n"
            "`/ajuda` - Mostra esta mensagem de ajuda",
            inline=False
        )

        embed.add_field(
            name="Privacidade",
            value="Todas as respostas são privadas e visíveis apenas para você.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
