import io

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import cleanup_old_threads
from utils.db_export import (
    build_export_csv_bytes,
    build_export_json_bytes,
    get_export_data,
)


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

    @bot.tree.command(
        name="db_export",
        description="[Moderador/Admin] Exporta o banco de threads (JSON ou CSV) como arquivo.",
    )
    @app_commands.describe(
        formato="Formato do arquivo a ser enviado (JSON ou CSV)",
    )
    @app_commands.choices(formato=[
        app_commands.Choice(name="JSON (recomendado)", value="json"),
        app_commands.Choice(name="CSV (threads)", value="csv"),
    ])
    async def db_export(
        interaction: discord.Interaction,
        formato: app_commands.Choice[str],
    ) -> None:
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator"
        )
        admin_role = discord.utils.get(
            interaction.guild.roles, name="Admin"
        )
        has_permission = (
            (moderator_role and moderator_role in interaction.user.roles)
            or (admin_role and admin_role in interaction.user.roles)
        )
        if not has_permission:
            await interaction.response.send_message(
                "Apenas moderadores ou admins podem usar este comando.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        data = get_export_data()
        if data is None:
            await interaction.followup.send(
                "Banco de dados não encontrado. Verifique se o bot está configurado corretamente.",
                ephemeral=True,
            )
            return

        if formato.value == "json":
            content = build_export_json_bytes(data)
            filename = "export.json"
        else:
            csv_bytes = build_export_csv_bytes(data)
            content = csv_bytes.get("threads", b"")
            filename = "threads.csv"
            if not content:
                await interaction.followup.send(
                    "Nenhum dado para exportar.",
                    ephemeral=True,
                )
                return

        file = discord.File(
            io.BytesIO(content),
            filename=filename,
        )
        await interaction.followup.send(
            f"Export gerado ({formato.name}).",
            file=file,
            ephemeral=True,
        )
