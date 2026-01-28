import discord
from discord import app_commands
from discord.ext import commands

from utils.database import cleanup_old_threads


def register_admin_commands(bot: commands.Bot) -> None:
    """
    Registra todos os comandos de administração
    """

    @bot.tree.command(name='limpar_threads', description='Remove threads antigas da base de dados (apenas moderadores)')
    @app_commands.describe(
        status="Status dos registros a serem removidos",
        dias="Número de dias para considerar registros como antigos (padrão: 30)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="Pending Support", value="pending_support"),
        app_commands.Choice(name="Closed", value="closed"),
        app_commands.Choice(name="Todos (ALL)", value="ALL")
    ])
    async def limpar_threads(
        interaction: discord.Interaction,
        status: app_commands.Choice[str],
        dias: int = 30
    ) -> None:
        """
        Remove threads antigas da base de dados (apenas moderadores)
        Requer permissão de moderador
        """
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator")
        admin_role = discord.utils.get(
            interaction.guild.roles, name="Admin")

        # Valida se o usuário tem permissão de moderador ou admin
        has_permission = False
        if moderator_role and moderator_role in interaction.user.roles:
            has_permission = True
        if admin_role and admin_role in interaction.user.roles:
            has_permission = True

        if not has_permission:
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo de Moderator ou Admin.",
                ephemeral=True
            )
            return

        # Valida se o número de dias é válido
        if dias < 1:
            await interaction.response.send_message(
                "O número de dias deve ser maior que zero",
                ephemeral=True
            )
            return

        # Extrai o valor do status
        status_value = status.value if isinstance(
            status, app_commands.Choice) else status
        status_list = [status_value]

        # Executa a limpeza
        deleted = cleanup_old_threads(days=dias, status_list=status_list)

        # Cria embed com resultado
        status_display = "Todos" if status_value == "ALL" else status.name
        embed = discord.Embed(
            title="Limpeza de Threads Concluída",
            description=f"Removidos registros com mais de {dias} dia(s)",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Status Filtrado",
            value=status_display,
            inline=True
        )

        embed.add_field(
            name="Threads Removidas",
            value=f"{deleted} thread(s)",
            inline=True
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
