"""
Comandos restritos a moderadores (ex.: export do banco).
"""
import io

import discord
from discord import app_commands
from discord.ext import commands

from utils.db_export import (
    build_export_csv_bytes,
    build_export_json_bytes,
    get_export_data,
)


def register_admin_commands(bot: commands.Bot) -> None:
    """Registra comandos de administração (role Moderator)."""

    @bot.tree.command(
        name="db_export",
        description="[Moderador] Exporta o banco de solicitações (JSON ou CSV) como arquivo.",
    )
    @app_commands.describe(
        formato="Formato do arquivo a ser enviado (JSON ou CSV)",
    )
    @app_commands.choices(formato=[
        app_commands.Choice(name="JSON (recomendado)", value="json"),
        app_commands.Choice(name="CSV (migration_requests)", value="csv_migration"),
        app_commands.Choice(name="CSV (reindex_requests)", value="csv_reindex"),
    ])
    async def db_export(
        interaction: discord.Interaction,
        formato: app_commands.Choice[str],
    ) -> None:
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator"
        )
        if moderator_role is None:
            await interaction.response.send_message(
                "Configuração do servidor: role 'Moderator' não encontrada.",
                ephemeral=True,
            )
            return
        if moderator_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Apenas moderadores podem usar este comando.",
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
            if formato.value == "csv_migration":
                content = csv_bytes.get("migration_requests", b"")
                filename = "migration_requests.csv"
            else:
                content = csv_bytes.get("reindex_requests", b"")
                filename = "reindex_requests.csv"
            if not content:
                await interaction.followup.send(
                    "Nenhum dado para exportar nesta tabela.",
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
