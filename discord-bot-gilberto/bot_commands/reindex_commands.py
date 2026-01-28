import discord
from discord import app_commands
from discord.ext import commands

from utils import (
    save_reindex_request,
    update_reindex_response,
    get_reindex_request,
    get_user_reindex_requests,
    cleanup_old_reindex_requests
)
from bot_commands.constants import (
    REINDEX_CHANNEL_ID,
    MOD_REINDEX_CHANNEL_ID,
    OLIST_BLUE
)


def register_reindex_commands(bot: commands.Bot) -> None:
    """
    Registra todos os comandos relacionados a reindex
    """

    @bot.tree.command(name="reindexar", description="Envia solicitação para reindexar uma loja.")
    @app_commands.describe(mensagem="Informe qual o dominio final da loja a ser reindexada")
    async def reindexar(interaction: discord.Interaction, mensagem: str) -> None:
        """
          Comando para solicitar reindexação de uma loja
        """
        # Valida se o comando está sendo usado no canal correto
        if interaction.channel.id != REINDEX_CHANNEL_ID:
            await interaction.response.send_message(
                f"❌ Este comando só pode ser usado no canal de reindex. "
                f"Use `/reindexar` no canal apropriado.",
                ephemeral=True
            )
            return

        # Resposta ephemeral - somente o usuário que executou o comando consegue ver
        await interaction.response.send_message(
            "Sua solicitação de reindex foi recebida! Um moderador irá atendê-la em breve",
            ephemeral=True
        )

        request_id = str(interaction.id)
        user_id = interaction.user.id

        if save_reindex_request(request_id, user_id, mensagem):
            print(f"[INFO] Solicitação de reindex {request_id} salva no banco")
        else:
            print(
                f"[WARNING] Falha ao salvar solicitação de reindex {request_id} (pode já existir)")

        if MOD_REINDEX_CHANNEL_ID:
            mod_reindex_channel = bot.get_channel(MOD_REINDEX_CHANNEL_ID)
            if mod_reindex_channel:
                try:
                    embed = discord.Embed(
                        title="Nova solicitação de reindex",
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
                        name="Reindex Request",
                        value=f"`{request_id}`",
                        inline=False
                    )

                    await mod_reindex_channel.send(embed=embed)
                except discord.errors.Forbidden:
                    print(
                        f"[ERROR] Bot sem acesso ao canal de moderação de reindex {MOD_REINDEX_CHANNEL_ID}")
                except Exception as e:
                    print(
                        f"[ERROR] Erro ao enviar para canal de moderação de reindex: {e}")

    @bot.tree.command(name='ver_reindexacoes', description='Lista todas as suas solicitações de reindex')
    async def ver_reindexacoes(interaction: discord.Interaction) -> None:
        """
          Comando para usuários verem todas as suas solicitações de reindex e status
        """
        user_id = interaction.user.id
        requests = get_user_reindex_requests(user_id)

        if not requests:
            await interaction.response.send_message(
                "Você ainda não possui solicitações de reindex.",
                ephemeral=True
            )
            return

        # Cria embed com lista de solicitações
        embed = discord.Embed(
            title="Suas Solicitações de Reindex",
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
                name=f"ID: `{req['request_id'][:8]}...`",
                value=field_value,
                inline=False
            )

        if len(requests) > 10:
            embed.set_footer(
                text=f"Mostrando 10 de {len(requests)} solicitações. Use /ver_reindexacao <id> para ver detalhes completos.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="ver_reindexacao", description="Ver detalhes completos de uma solicitação de reindex específica")
    @app_commands.describe(request_id="ID da solicitação (use /ver_reindexacoes para ver os IDs)")
    async def ver_reindexacao(interaction: discord.Interaction, request_id: str) -> None:
        """
        Comando para usuários verem detalhes completos de uma solicitação de reindex específica
        """
        request_data = get_reindex_request(request_id)

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
            title=f"Solicitação de Reindex {request_id[:8]}...",
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

    @bot.tree.command(name='response_reindex', description='Responde a uma solicitação de reindex (apenas moderadores)')
    @app_commands.describe(
        request_id="ID da solicitação",
        resposta="Sua resposta para o usuário",
        status="Status da solicitação"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="OK", value="ok"),
        app_commands.Choice(name="Review", value="review")
    ])
    async def response_reindex(
        interaction: discord.Interaction,
        request_id: str,
        resposta: str,
        status: app_commands.Choice[str]
    ) -> None:
        """
          Comando para moderadores responderem solicitações de reindex
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

        # Moderadores respondem as requests de reindex
        status_value = status.value if isinstance(
            status, app_commands.Choice) else status
        if update_reindex_response(request_id, resposta, status_value):
            await interaction.response.send_message(
                f"Resposta registrada para solicitação de reindex {request_id} com status '{status_value}'",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Solicitação de reindex {request_id} não encontrada",
                ephemeral=True
            )

    @bot.tree.command(name="check_reindex", description="Verifica uma solicitação de reindex específica (apenas moderadores)")
    @app_commands.describe(request_id="ID da solicitação")
    async def check_reindex(interaction: discord.Interaction, request_id: str):
        """
        Comando para moderadores verificarem uma solicitação de reindex específica
        """
        moderator_role = discord.utils.get(
            interaction.guild.roles, name="Moderator")

        if moderator_role is None or moderator_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando",
                ephemeral=True
            )
            return

        request_data = get_reindex_request(request_id)

        if request_data:
            embed = discord.Embed(
                title=f"Solicitação de Reindex {request_id}",
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
                f"Solicitação de reindex {request_id} não encontrada",
                ephemeral=True
            )

    @bot.tree.command(name='clear_reindex', description='Remove registros antigos de reindex da base de dados (apenas moderadores)')
    @app_commands.describe(
        status="Status dos registros a serem removidos",
        dias="Número de dias para considerar registros como antigos (padrão: 30)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Pending", value="pending"),
        app_commands.Choice(name="OK", value="ok"),
        app_commands.Choice(name="Review", value="review"),
        app_commands.Choice(name="Todos (ALL)", value="ALL")
    ])
    async def clear_reindex(
        interaction: discord.Interaction,
        status: app_commands.Choice[str],
        dias: int = 30
    ) -> None:
        """
          Comando para moderadores limparem registros antigos de reindex da base de dados
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
        deleted = cleanup_old_reindex_requests(
            days=dias, status_list=status_list)

        # Cria embed com resultado
        status_display = "Todos" if status_value == "ALL" else status.name
        embed = discord.Embed(
            title="Limpeza de Reindex Concluída",
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
