import discord
from discord.ext import commands

from bot_commands.constants import OLIST_BLUE


def register_general_commands(bot: commands.Bot) -> None:
    """
    Registra todos os comandos gerais
    """

    @bot.tree.command(name='ajuda', description='Passa informações sobre como usar o bot')
    async def ajuda(interaction: discord.Interaction) -> None:
        """
          Comando de ajuda com informações sobre o bot
          A resposta é ephemeral e adaptada ao contexto
        """

        embed = discord.Embed(
            title="Como usar o bot",
            description="Este bot utiliza slash commands (/)",
            color=OLIST_BLUE
        )

        # Comandos de Administração
        admin_commands = []
        admin_commands.append(
            "`/limpar_threads <status> [dias]` - Remove threads antigas da base de dados (apenas moderadores)")

        admin_text = ""
        for cmd in admin_commands:
            admin_text = admin_text + cmd + "\n"

        embed.add_field(
            name="⚙️ Comandos de Administração",
            value=admin_text,
            inline=False
        )

        embed.add_field(
            name="Privacidade",
            value="Todas as respostas são privadas e visíveis apenas para você.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
