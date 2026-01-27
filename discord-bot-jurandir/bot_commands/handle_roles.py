from typing import Final, Optional
import discord
from discord import app_commands
from discord.ext import commands

from bot_commands.partners_roles_list import partners_diamond, partners_gold, partners_silver, partners_bronze

OLIST_BLUE: Final = discord.Color(0x0057dd)


def check_admin_role(interaction: discord.Interaction) -> bool:
    """
    Verifica se o usuário tem o cargo Admin
    """
    admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
    if admin_role is None:
        return False
    return admin_role in interaction.user.roles


def set_commands(bot: commands.Bot) -> None:
    """
      Configura todos os slash commands do bot
      Todas as respostas são ephemeral (visiveis apenas para quem executou o comando)
    """

    ####################################################################
    # COMANDOS HELP
    ####################################################################
    # Comando de ajuda com output em embed
    @bot.tree.command(name="ajuda", description="Lista todos os comandos que o bot possui")
    @app_commands.describe(comando="Nome do comando para ver detalhes (opcional)")
    async def ajuda(interaction: discord.Interaction, comando: Optional[str] = None) -> None:
        """
            Lista todos os comandos que o bot possui
            Use: /ajuda ou /ajuda <nome_do_comando>
        """

        # Se o usuário pediu ajuda sobre um comando específico
        if comando:
            # Para slash commands, vamos apenas mostrar uma mensagem informativa
            embed = discord.Embed(
                title="ℹ️ Informação",
                description=f"Use `/ajuda` para ver todos os comandos disponíveis.\n"
                          f"Todos os comandos são slash commands (/) e requerem cargo **Admin**.",
                color=OLIST_BLUE
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Embed principal com todos os comandos organizados por categoria
        embed = discord.Embed(
            title="📚 Comandos Disponíveis",
            description="Lista de todos os comandos do bot organizados por categoria",
            color=OLIST_BLUE
        )

        # Comandos de Consulta
        consulta_commands = []
        consulta_commands.append(
            "`/list_roles [membro]` - Lista cargos de um membro")
        consulta_commands.append(
            "`/members_with_role <cargo>` - Lista membros com um cargo")
        consulta_commands.append(
            "`/all_roles` - Lista todos os cargos do servidor")
        consulta_commands.append(
            "`/role_stats <cargo>` - Estatísticas de um cargo")

        consulta_text = ""
        for cmd in consulta_commands:
            consulta_text = consulta_text + cmd + "\n"

        embed.add_field(
            name="🔍 Comandos de Consulta",
            value=consulta_text,
            inline=False
        )

        # Comandos de Atribuição
        atribuicao_commands = []
        atribuicao_commands.append(
            "`/assign_role <cargo>` - Adiciona cargo a você mesmo")
        atribuicao_commands.append(
            "`/remove_role <cargo>` - Remove cargo de você mesmo")
        atribuicao_commands.append(
            "`/assign_role_to <@membro> <cargo>` - Adiciona cargo a um membro")
        atribuicao_commands.append(
            "`/remove_role_from <@membro> <cargo>` - Remove cargo de um membro")

        atribuicao_text = ""
        for cmd in atribuicao_commands:
            atribuicao_text = atribuicao_text + cmd + "\n"

        embed.add_field(
            name="⚙️ Comandos de Atribuição",
            value=atribuicao_text,
            inline=False
        )

        # Comandos de Gerenciamento
        gerenciamento_commands = []
        gerenciamento_commands.append(
            "`/copy_roles <@origem> <@destino>` - Copia cargos entre membros")
        gerenciamento_commands.append(
            "`/clear_roles <@membro>` - Remove todos os cargos de um membro")
        gerenciamento_commands.append(
            "`/partner_roles_sanitizer` - Sanitiza cargos de parceiros")

        gerenciamento_text = ""
        for cmd in gerenciamento_commands:
            gerenciamento_text = gerenciamento_text + cmd + "\n"

        embed.add_field(
            name="🛠️ Comandos de Gerenciamento",
            value=gerenciamento_text,
            inline=False
        )

        # Footer com informações adicionais
        embed.set_footer(
            text="Use /ajuda para mais detalhes • Requer cargo Admin para todos os comandos"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    ####################################################################
    # COMANDOS DE CONSULTA
    ####################################################################
    # LISTA ROLES DE UM USUARIO
    @bot.tree.command(name="list_roles", description="Lista todos os roles de um membro")
    @app_commands.describe(membro="Membro para listar os cargos (opcional, padrão: você mesmo)")
    async def list_roles(interaction: discord.Interaction, membro: Optional[discord.Member] = None) -> None:
        """
            Lista todos os roles de um membro (ou do author caso não seja especificado)
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        if membro is None:
            target = interaction.user
        else:
            target = membro

        roles_list = []
        for role in target.roles:
            if role.name != '@everyone':
                roles_list.append(role.mention)

        if len(roles_list) > 0:
            roles_text = ", ".join(roles_list)
            await interaction.response.send_message(
                f'**Roles do {target.mention}:**\n{roles_text}',
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'{target.mention} não possui roles',
                ephemeral=True
            )

    # LISTA USUARIOS COM UM ROLE
    @bot.tree.command(name="members_with_role", description="Lista todos os membros que possuem um cargo específico")
    @app_commands.describe(cargo="Nome do cargo para listar os membros")
    async def members_with_role(interaction: discord.Interaction, cargo: str) -> None:
        """
            Lista todos os membros que possuem um cargo específico
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role is None:
            await interaction.response.send_message(
                f"Cargo '{cargo}' não encontrado.",
                ephemeral=True
            )
            return

        members_list = []
        for member in interaction.guild.members:
            if role in member.roles:
                members_list.append(member.display_name)

        if len(members_list) > 0:
            members_text = "\n".join([f"- {name}" for name in members_list])
            await interaction.response.send_message(
                f"**Membros com o cargo {role.mention} ({len(members_list)}):**\n{members_text}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Nenhum membro possui o cargo {role.mention}.",
                ephemeral=True
            )

    # LISTA ROLES DO SERVER
    @bot.tree.command(name="all_roles", description="Lista todos os cargos disponíveis no servidor")
    async def all_roles(interaction: discord.Interaction) -> None:
        """
            Lista todos os cargos disponíveis no servidor
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        roles_list = []
        for role in interaction.guild.roles:
            if role.name != '@everyone':
                roles_list.append(role)

        # Ordena por posição (maior primeiro)
        roles_list.sort(key=lambda r: r.position, reverse=True)

        role_lines = []
        for role in roles_list:
            # Conta quantos membros têm esse cargo
            member_count = 0
            for member in interaction.guild.members:
                if role in member.roles:
                    member_count += 1

            role_lines.append(f"{role.mention} ({member_count} membros)")

        roles_text = "\n".join(role_lines)
        await interaction.response.send_message(
            f"**Cargos do servidor ({len(roles_list)}):**\n{roles_text}",
            ephemeral=True
        )

    ####################################################################
    # COMANDOS DE ATRIBUIÇAO
    ####################################################################
    # ATRIBUIR CARGO SI MESMO
    @bot.tree.command(name="assign_role", description="Adiciona um cargo a você mesmo")
    @app_commands.describe(cargo="Nome do cargo a ser adicionado")
    async def assign_role(interaction: discord.Interaction, cargo: str) -> None:
        """
        Adiciona um cargo ao usuário que executou o comando
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f'{interaction.user.mention} agora possui o cargo {role.mention}',
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'O cargo "{cargo}" não foi encontrado',
                ephemeral=True
            )

    # REMOVER CARGO DE SI MESMO
    @bot.tree.command(name="remove_role", description="Remove um cargo de você mesmo")
    @app_commands.describe(cargo="Nome do cargo a ser removido")
    async def remove_role(interaction: discord.Interaction, cargo: str) -> None:
        """
        Remove um cargo do usuário que executou o comando
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                f'O cargo {role.mention} foi removido de {interaction.user.mention}',
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'O cargo "{cargo}" não foi encontrado',
                ephemeral=True
            )

    # ADICIONA ROLE A USUARIO
    @bot.tree.command(name="assign_role_to", description="Adiciona um cargo a um membro específico")
    @app_commands.describe(membro="Membro para adicionar o cargo", cargo="Nome do cargo a ser adicionado")
    async def assign_role_to(interaction: discord.Interaction, membro: discord.Member, cargo: str) -> None:
        """
            Adicionar um role a um usuário específico
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role is None:
            await interaction.response.send_message(
                f'O cargo "{cargo}" não foi encontrado',
                ephemeral=True
            )
            return

        if role in membro.roles:
            await interaction.response.send_message(
                f'O usuário {membro.mention} já possui o cargo {role.mention}',
                ephemeral=True
            )
            return

        await membro.add_roles(role)
        await interaction.response.send_message(
            f'O cargo {role.mention} foi adicionado ao {membro.mention}',
            ephemeral=True
        )

    # REMOVE ROLE DE USUARIO
    @bot.tree.command(name="remove_role_from", description="Remove um cargo de um membro específico")
    @app_commands.describe(membro="Membro para remover o cargo", cargo="Nome do cargo a ser removido")
    async def remove_role_from(interaction: discord.Interaction, membro: discord.Member, cargo: str) -> None:
        """
            Remove um role de um usuário específico
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role is None:
            await interaction.response.send_message(
                f'O cargo "{cargo}" não foi encontrado',
                ephemeral=True
            )
            return

        if role not in membro.roles:
            await interaction.response.send_message(
                f'O usuário {membro.mention} não possui o cargo {role.mention}',
                ephemeral=True
            )
            return

        await membro.remove_roles(role)
        await interaction.response.send_message(
            f'O cargo {role.mention} foi removido do {membro.mention}',
            ephemeral=True
        )

    # COPIA ROLES DE UM USUARIO PARA OUTRO
    @bot.tree.command(name="copy_roles", description="Copia todos os cargos de um membro para outro")
    @app_commands.describe(origem="Membro de origem (de onde copiar os cargos)", destino="Membro de destino (para onde copiar os cargos)")
    async def copy_roles(interaction: discord.Interaction, origem: discord.Member, destino: discord.Member) -> None:
        """
            Copia todos os cargos de um membro para outro
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        # Lista a ser populada com os roles
        roles_to_add = []

        for role in origem.roles:
            if role.name != '@everyone':
                if role not in destino.roles:
                    roles_to_add.append(role)

        if len(roles_to_add) == 0:
            await interaction.response.send_message(
                f'{destino.mention} já possui todos os cargos de {origem.mention}',
                ephemeral=True
            )
            return

        # Usado *roles_to_add para não enviar a lista e sim os seus itens
        # O *roles_to_add funciona como um [...] em JS
        await destino.add_roles(*roles_to_add)

        # Reune as roles para report
        role_mentions = []

        # Sobre o role.mention:
        # Se você tem um cargo chamado "Admin"
        # role.name = "Admin"

        # role.mention retorna uma string especial:
        # role.mention = "<@&123456789>"  # Formato especial do Discord

        # Quando você envia essa string no Discord, aparece como:
        # @Admin (clicável e destacado)

        for role in roles_to_add:
            role_mentions.append(role.mention)

        roles_text = ", ".join(role_mentions)
        await interaction.response.send_message(
            f"Cargos copiados: {roles_text}",
            ephemeral=True
        )

    # REMOVE TODAS AS ROLES DE UM USUARIO
    @bot.tree.command(name="clear_roles", description="Remove todos os cargos de um membro (exceto @everyone)")
    @app_commands.describe(membro="Membro para remover todos os cargos")
    async def clear_roles(interaction: discord.Interaction, membro: discord.Member) -> None:
        """
            Remove todos os cargos de um membro (exceto @everyone)
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        # Lista a ser populada com os roles
        roles_to_remove = []

        for role in membro.roles:
            if role.name != '@everyone':
                roles_to_remove.append(role)

        if len(roles_to_remove) == 0:
            await interaction.response.send_message(
                f'{membro.mention} não possui cargos para serem removidos',
                ephemeral=True
            )
            return

        await membro.remove_roles(*roles_to_remove)
        await interaction.response.send_message(
            f'Todos os cargos foram removidos de {membro.mention}',
            ephemeral=True
        )

    ####################################################################
    # COMANDOS DE ESTATISTICAS
    ####################################################################
    @bot.tree.command(name="role_stats", description="Mostra estatísticas de um cargo específico")
    @app_commands.describe(cargo="Nome do cargo para ver estatísticas")
    async def role_stats(interaction: discord.Interaction, cargo: str) -> None:
        """
            Mostra usuários com uma role especifica
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=cargo)

        if role is None:
            await interaction.response.send_message(
                f'Cargo "{cargo}" não encontrado.',
                ephemeral=True
            )
            return

        members_with_role = []
        bots = []
        humans = []

        for member in interaction.guild.members:
            if role in member.roles:
                members_with_role.append(member)
                if member.bot:
                    bots.append(member)
                else:
                    humans.append(member)

        stats = (
            f"**Estatísticas do cargo {role.mention}:**\n"
            f"• Total de membros: {len(members_with_role)}\n"
            f"• Humanos: {len(humans)}\n"
            f"• Bots: {len(bots)}\n"
            f"• Posição: {role.position}\n"
            f"• Cor: {role.color}"
        )

        await interaction.response.send_message(stats, ephemeral=True)

    ####################################################################
    # COMANDOS DE FUNCIONALIDADES
    ####################################################################
    # SANITIZADOR DE CARGOS DE PARCEIROS
    @bot.tree.command(name="partner_roles_sanitizer", description="Sanitiza os cargos de parceiros para todos os membros do servidor")
    async def partner_roles_sanitizer(interaction: discord.Interaction) -> None:
        """
            Sanitiza os cargos de parceiros para todos os membros do servidor.
            Garante que os membros tenham os cargos de tier corretos baseados em seus cargos de parceiros.
        """
        if not check_admin_role(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar esse comando. Requer cargo: **Admin**",
                ephemeral=True
            )
            return

        try:
            # Resposta inicial
            await interaction.response.send_message(
                f"Iniciando sanitização de cargos de parceiros...",
                ephemeral=True
            )

            # Converte as listas de parceiros em sets para comparação eficiente
            partners_diamond_set = set(partners_diamond)
            partners_gold_set = set(partners_gold)
            partners_silver_set = set(partners_silver)
            partners_bronze_set = set(partners_bronze)

            # Mapeamento: set de nomes de empresas <-> nome do cargo de tier
            # Cada tupla: (set de nomes de cargos de empresas, nome do cargo de tier correspondente)
            tier_configs = [
                (partners_diamond_set, "Parceiro Diamante"),
                (partners_gold_set, "Parceiro Ouro"),
                (partners_silver_set, "Parceiro Prata"),
                (partners_bronze_set, "Parceiro Bronze")
            ]

            members = interaction.guild.members
            total_members = len(members)

            # Estatísticas
            stats = {
                "roles_added": 0,
                "roles_removed": 0,
                "members_processed": 0,
                "errors": 0
            }

            # Envia mensagem de progresso inicial
            progress_channel = interaction.channel
            progress_msg = await progress_channel.send(f"Starting partner roles sanitization for {total_members} members...")

            # Processando cada membro
            # O enumerate gera um loop com o índice, esse número é usado para atualizar o progresso no feedback para o usuário
            for index, member in enumerate(members, 1):
                try:
                    # Obtém os nomes dos cargos atuais do membro como um set
                    member_role_names = {role.name for role in member.roles}

                    # Verifica cada tier (Diamante, Ouro, Prata, Bronze)
                    for company_names_set, tier_role_name in tier_configs:
                        # Verifica se o membro tem algum cargo de empresa (como "Californio", "Uncode", etc.)
                        # Interseção de sets: encontra cargos que existem em ambos os sets
                        matching_company_roles = member_role_names & company_names_set
                        has_company_role = len(matching_company_roles) > 0

                        # Verifica se o tier_role_name ("Parceiro Diamante", "Parceiro Ouro"... etc) existe como role no server
                        tier_role = discord.utils.get(
                            interaction.guild.roles, name=tier_role_name)

                        if not tier_role:
                            print(
                                f"Warning: Role '{tier_role_name}' not found in guild")
                            continue

                        # Verifica se o membro atualmente tem o cargo de tier
                        has_tier_role = tier_role in member.roles

                        # Adiciona ou remove o cargo de tier conforme necessário
                        if has_company_role and not has_tier_role:
                            # Membro tem um cargo de empresa mas está faltando o cargo de tier - adiciona
                            await member.add_roles(tier_role)
                            stats["roles_added"] += 1
                            print(
                                f"Added '{tier_role_name}' to {member.display_name}")
                        elif not has_company_role and has_tier_role:
                            # Membro não tem um cargo de empresa mas tem o cargo de tier - remove
                            await member.remove_roles(tier_role)
                            stats["roles_removed"] += 1
                            print(
                                f"Removed '{tier_role_name}' from {member.display_name}")

                    stats["members_processed"] += 1

                    # Atualização de progresso a cada 10 membros
                    if index % 10 == 0:
                        await progress_msg.edit(content=f"Progress: {index}/{total_members} members processed...")

                except Exception as e:
                    stats["errors"] += 1
                    print(
                        f"Error processing {member.display_name}: {str(e)}")
                    continue

            # Envia resumo de conclusão
            summary = (
                f"**Sanitization Complete!**\n"
                f"**Statistics:**\n"
                f"  • Members processed: {stats['members_processed']}/{total_members}\n"
                f"  • Roles added: {stats['roles_added']}\n"
                f"  • Roles removed: {stats['roles_removed']}\n"
                f"  • Errors: {stats['errors']}"
            )

            await progress_channel.send(summary)

        except Exception as e:
            error_msg = f"**Error in partner_roles_sanitizer:** {str(e)}\n```{type(e).__name__}```"
            await interaction.followup.send(error_msg, ephemeral=True)
            print(f"Critical error in partner_roles_sanitizer: {str(e)}")
            import traceback
            traceback.print_exc()
