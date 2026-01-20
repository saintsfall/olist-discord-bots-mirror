from typing import Final
import discord
from discord import app_commands
from discord.ext import commands

# IMPORT UTILS TO MANAGE SQLITE3 DATABASE
from utils import (
    delete_request,
    save_request,
    update_response,
    get_request,
    get_user_requests,
    # Reindex functions
    save_reindex_request,
    update_reindex_response,
    get_reindex_request,
    get_user_reindex_requests,
    delete_reindex_request
)

# Logging Launcher Requests
MOD_MIGRATION_CHANNEL_ID: Final[int] = 1461832252043432088
# Loggin Reindex Requests
MOD_REINDEX_CHANNEL_ID: Final[int] = 1462896651562778624
# Store Reindex
REINDEX_CHANNEL_ID: Final[int] = 1462892195219767431
# Pre Launch Migration
MIGRATION_CHANNEL_ID: Final[int] = 1461704921693819005

OLIST_BLUE: Final = discord.Color(0x0057dd)


def set_commands(bot: commands.Bot) -> None:
    """
      Configura todos os slash commands do bot
      Todas as respostas são ephemeral (visiveis apenas para quem executou o commando)
    """

    # ============================================================================
    # COMANDOS PARA MIGRATION REQUESTS
    # ============================================================================

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
    @app_commands.describe(request_id="ID da solicitação", resposta="Sua resposta para o usuário")
    async def response_migration(interaction: discord.Interaction, request_id: str, resposta: str,) -> None:
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
        if update_response(request_id, resposta):
            await interaction.response.send_message(
                f"Resposta registrada para solicitação {request_id}",
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

    # ============================================================================
    # COMANDOS DE REINDEX
    # ============================================================================

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
    @app_commands.describe(request_id="ID da solicitação", resposta="Sua resposta para o usuário")
    async def response_reindex(interaction: discord.Interaction, request_id: str, resposta: str) -> None:
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
        if update_reindex_response(request_id, resposta):
            await interaction.response.send_message(
                f"Resposta registrada para solicitação de reindex {request_id}",
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

    # ============================================================================
    # COMANDOS GERAIS
    # ============================================================================

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
