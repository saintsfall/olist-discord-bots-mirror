import discord
from discord.ext import commands

from bot_commands.constants import (
    MIGRATION_CHANNEL_ID,
    REINDEX_CHANNEL_ID,
    OLIST_BLUE
)


def register_general_commands(bot: commands.Bot) -> None:
    """
    Registra todos os comandos gerais
    """

    @bot.tree.command(name='ajuda', description='Passa informações sobre como usar o bot')
    async def ajuda(interaction: discord.Interaction) -> None:
        """
          Comando de ajuda com informações sobre o bot
          A resposta é ephemeral e adaptada ao canal onde é executado
        """

        embed = discord.Embed(
            title="Como usar o bot",
            description="Este canal aceita apenas slash commands (/)",
            color=OLIST_BLUE
        )

        # Adapta a ajuda baseado no canal onde o comando foi executado
        if interaction.channel.id == MIGRATION_CHANNEL_ID:
            embed.add_field(
                name="Comandos de Migração",
                value="`/migrar <mensagem>` - Solicite a migração dos cadastros de uma loja\n"
                      "`/ver_solicitacoes` - Lista todas as suas solicitações de migração\n"
                      "`/ver_solicitacao <id>` - Ver detalhes completos de uma solicitação de migração\n"
                      "`/ajuda` - Mostra esta mensagem de ajuda",
                inline=False
            )
        elif interaction.channel.id == REINDEX_CHANNEL_ID:
            embed.add_field(
                name="Comandos de Reindex",
                value="`/reindexar <mensagem>` - Solicite a reindexação de uma loja\n"
                      "`/ver_reindexacoes` - Lista todas as suas solicitações de reindex\n"
                      "`/ver_reindexacao <id>` - Ver detalhes completos de uma solicitação de reindex\n"
                      "`/ajuda` - Mostra esta mensagem de ajuda",
                inline=False
            )
        else:
            # Se executado em outro canal, mostra todos os comandos
            embed.add_field(
                name="Comandos de Migração",
                value="`/migrar <mensagem>` - Use no canal de migração\n"
                      "`/ver_solicitacoes` - Lista suas solicitações de migração\n"
                      "`/ver_solicitacao <id>` - Ver detalhes de uma solicitação de migração",
                inline=False
            )
            embed.add_field(
                name="Comandos de Reindex",
                value="`/reindexar <mensagem>` - Use no canal de reindex\n"
                      "`/ver_reindexacoes` - Lista suas solicitações de reindex\n"
                      "`/ver_reindexacao <id>` - Ver detalhes de uma solicitação de reindex",
                inline=False
            )

        embed.add_field(
            name="Privacidade",
            value="Todas as respostas são privadas e visíveis apenas para você.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
