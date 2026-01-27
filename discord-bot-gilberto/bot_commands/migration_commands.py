import discord
from discord import app_commands
from discord.ext import commands

from utils import (
    save_request,
    update_response,
    get_request,
    get_user_requests,
    cleanup_old_migration_requests
)
from bot_commands.constants import (
    MIGRATION_CHANNEL_ID,
    MOD_MIGRATION_CHANNEL_ID,
    OLIST_BLUE
)


def register_migration_commands(bot: commands.Bot) -> None:
    """
    Registra todos os comandos relacionados a migração
    """

    @bot.tree.command(name="migrar", description="Envia solicitação de loja a ter os dados migrados no Launcher.")
    @app_commands.describe(mensagem="Informe qual o dominio final da loja a ter os dados migrados")
    async def migrar(interaction: discord.Interaction, mensagem: str) -> None:
        """
          Comando para informar loja a ter os dados migrados de STG para CDN via Launcher
        """
        # Valida se o comando está sendo usado no canal correto
        if interaction.channel.id != MIGRATION_CHANNEL_ID:
            await interaction.response.send_message(
                f"❌ Este comando só pode ser usado no canal de migração. "
                f"Use `/migrar` no canal apropriado.",
                ephemeral=True
            )
            return

        # Resposta ephemeral - somente o usuário que executou o comando consegue ver
        await interaction.response.send_message(
            "Sua solicitação foi recebida! Um moderador irá atendê-la em breve",
            ephemeral=True
        )

        request_id = str(interaction.id)
        user_id = interaction.user.id

        if save_request(request_id, user_id, mensagem):
            print(
                f"[INFO] Solicitação de migração {request_id} salva no banco")

        else:
            print(
                f"[WARNING] Falha ao salvar solicitação {request_id} (pode já existir)")

        if MOD_MIGRATION_CHANNEL_ID:
            mod_channel = bot.get_channel(MOD_MIGRATION_CHANNEL_ID)
            if mod_channel:
                embed = discord.Embed(
                    title="Nova solicitação",
                    description=mensagem,
                    color=OLIST_BLUE,
                    timestamp=interaction.created_at
                )

                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url
                )

                embed.add_field(
                    name="Usuário",
                    value=interaction.user.mention,
                    inline=True
                )

                embed.add_field(
                    name="Migration Request",
                    value=f"`{request_id}`",
                    inline=False
                )

                await mod_channel.send(embed=embed)

    @bot.tree.command(name='ver_solicitacoes', description='Lista todas as suas solicitações de migração')
    async def ver_solicitacoes(interaction: discord.Interaction) -> None:
        """
          Comando para usuários verem todas as suas solicitações e status
        """

        user_id = interaction.user.id
        requests = get_user_requests(user_id)

        if not requests:
            await interaction.response.send_message(
                "Você ainda não possui solicitações de migração.",
                ephemeral=True
            )
            return

        # Cria embed com lista de solicitações
        embed = discord.Embed(
            title="Suas Solicitações de Migração",
            description=f"Total: {len(requests)} solicitação(ões)",
            color=OLIST_BLUE
        )

        # Limita a 10 mais recentes para não exceder limite do Discord
        for req in requests[:10]:
            status_emoji = "✅" if req["status"] == "ok" else "⏳"
            status_text = "Respondida" if req["status"] == "ok" else "Pendente"

            # Preview da mensagem (limita a 50 caracteres)
            message_preview = req.get("message", "N/A")
            if len(message_preview) > 50:
                message_preview = message_preview[:50] + "..."

            field_value = f"**Mensagem:** {message_preview}\n"
            field_value += f"**Status:** {status_emoji} {status_text}\n"
            field_value += f"**Criada em:** {req['created_at']}\n"

            if req["answered_at"]:
                field_value += f"**Respondida em:** {req['answered_at']}\n"

            if req["response"]:
                # Limita resposta a 100 caracteres no campo
                response_preview = req["response"][:100] + \
                    "..." if len(req["response"]) > 100 else req["response"]
                field_value += f"**Resposta:** {response_preview}"

            embed.add_field(
                name=f"ID: `{req['request_id']}`",
                value=field_value,
                inline=False
            )

        if len(requests) > 10:
            embed.set_footer(
                text=f"Mostrando 10 de {len(requests)} solicitações. Use /ver_solicitacao <id> para ver detalhes completos.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="ver_solicitacao", description="Ver detalhes completos de uma solicitação específica")
    @app_commands.describe(request_id="ID da solicitação (use /ver_solicitacoes para ver os IDs)")
    async def ver_solicitacao(interaction: discord.Interaction, request_id: str) -> None:
        """
        Comando para usuários verem detalhes completos de uma solicitação específica
        """
        request_data = get_request(request_id)

        if not request_data:
            await interaction.response.send_message(
                "Solicitação não encontrada.",
                ephemeral=True
            )
            return

        # Verifica se a solicitação pertence ao usuário
        if request_data["user_id"] != interaction.user.id:
            await interaction.response.send_message(
                "Esta solicitação não pertence a você.",
                ephemeral=True
            )
            return

        # Cria embed com detalhes completos
        status_emoji = "✅" if request_data["status"] == "ok" else "⏳"
        status_text = "Respondida" if request_data["status"] == "ok" else "Pendente"

        embed = discord.Embed(
            title=f"Solicitação {request_id[:8]}...",
            color=discord.Color.green(
            ) if request_data["status"] == "ok" else discord.Color.orange()
        )

        # Mensagem original da solicitação
        embed.add_field(
            name="Sua Solicitação",
            value=request_data.get("message", "N/A"),
            inline=False
        )

        embed.add_field(
            name="Status", value=f"{status_emoji} {status_text}", inline=True)
        embed.add_field(name="ID Completo",
                        value=f"`{request_id}`", inline=False)

        if request_data["response"]:
            embed.add_field(
                name="Resposta do Moderador",
                value=request_data["response"],
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="Aguardando resposta de um moderador...",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name='response_migration', description='Responde a uma solicitação de migração (apenas moderadores)')
    @app_commands.describe(
        request_id="ID da solicitação",
        resposta="Sua resposta para o usuário",
        status="Status da solicitação"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pendente", value="pending"),
        app_commands.Choice(name="OK", value="ok"),
        app_commands.Choice(name="Revisar", value="review")
    ])
    async def response_migration(
        interaction: discord.Interaction,
        request_id: str,
        resposta: str,
        status: app_commands.Choice[str]
    ) -> None:
        """
          Comando para moderadores responderem a solicitação
          Requer permissão de moderador
        """

        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator")

        # Valida se o usuário tem permissão de moderador
        if moderator_role is None:
            await interaction.response.send_message(
                "Erro: Role de 'Moderator' não encontrado no server",
                ephemeral=True
            )
            return

        if moderator_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando",
                ephemeral=True
            )
            return

        # Moderadores respondem as requests já concluidas
        status_value = status.value if isinstance(
            status, app_commands.Choice) else status
        if update_response(request_id, resposta, status_value):
            await interaction.response.send_message(
                f"Resposta registrada para solicitação {request_id} com status '{status_value}'",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Solicitação {request_id} não encontrada",
                ephemeral=True
            )

    @bot.tree.command(name="check_request", description="Verifica uma solicitação específica (apenas moderadores)")
    @app_commands.describe(request_id="ID da solicitação")
    async def check_request(interaction: discord.Interaction, request_id: str):
        """
          Comando para moderadores verificarem uma solicitação específica
        """
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator")

        if moderator_role is None or moderator_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando",
                ephemeral=True
            )
            return

        request_data = get_request(request_id)

        if request_data:
            embed = discord.Embed(
                title=f"Solicitação {request_id}",
                color=OLIST_BLUE
            )

            embed.add_field(
                name="User ID",
                value=str(request_data["user_id"]),
                inline=True
            )
            embed.add_field(
                name="Status",
                value=request_data["status"],
                inline=True
            )

            # Mensagem original da solicitação
            embed.add_field(
                name="Mensagem Original",
                value=request_data.get("message", "N/A"),
                inline=False
            )

            if request_data["response"]:
                embed.add_field(
                    name="Resposta",
                    value=request_data["response"],
                    inline=False
                )
            else:
                embed.add_field(
                    name="Status",
                    value="Pendente",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"Solicitação {request_id} não encontrada",
                ephemeral=True
            )

    @bot.tree.command(name='limpar_migracoes', description='Remove registros antigos de migração da base de dados (apenas moderadores)')
    @app_commands.describe(
        status="Status dos registros a serem removidos",
        dias="Número de dias para considerar registros como antigos (padrão: 30)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pendente", value="pending"),
        app_commands.Choice(name="OK", value="ok"),
        app_commands.Choice(name="Revisar", value="review"),
        app_commands.Choice(name="Todos (ALL)", value="ALL")
    ])
    async def limpar_migracoes(
        interaction: discord.Interaction,
        status: app_commands.Choice[str],
        dias: int = 30
    ) -> None:
        """
          Comando para moderadores limparem registros antigos de migração da base de dados
          Remove registros que foram criados/respondidos há mais de X dias
          Requer permissão de moderador
        """
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator")

        # Valida se o usuário tem permissão de moderador
        if moderator_role is None:
            await interaction.response.send_message(
                "Erro: Role de 'Moderator' não encontrado no server",
                ephemeral=True
            )
            return

        if moderator_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando",
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
        deleted = cleanup_old_migration_requests(days=dias, status_list=status_list)

        # Cria embed com resultado
        status_display = "Todos" if status_value == "ALL" else status.name
        embed = discord.Embed(
            title="Limpeza de Migrações Concluída",
            description=f"Removidos registros com mais de {dias} dia(s)",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Status Filtrado",
            value=status_display,
            inline=True
        )

        embed.add_field(
            name="Registros Removidos",
            value=f"{deleted} registro(s)",
            inline=True
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
