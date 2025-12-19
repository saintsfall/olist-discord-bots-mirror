from typing import Final
import discord
from discord.ext import commands

from bot_commands.partners_roles_list import partners_diamond, partners_gold, partners_silver, partners_bronze

OLIST_BLUE: Final = discord.Color(0x0057dd)


def set_commands(bot: commands.Bot) -> None:
    ####################################################################
    # COMANDOS HELP
    ####################################################################
    # Comando !jurandir com output em embed
    @bot.command()
    async def jurandir(ctx: commands.Context, command_name: str = None) -> None:
        """
            Lista todos os comandos que o bot possui
            Use: !jurandir ou !jurandir <nome_do_comando>
        """

        # Se o usuário pediu ajuda sobre um comando específico
        if command_name:
            command = bot.get_command(command_name)

            if command is None:
                embed = discord.Embed(
                    title="❌ Comando não encontrado",
                    description=f"O comando `{command_name}` não existe.\nUse `!jurandir` para ver todos os comandos disponíveis.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Embed para comando específico
            embed = discord.Embed(
                title=f"📖 Comando: `!{command.name}`",
                color=OLIST_BLUE
            )

            if command.jurandir:
                embed.description = command.jurandir

            if command.signature:
                embed.add_field(
                    name="Uso",
                    value=f"`!{command.name} {command.signature}`",
                    inline=False
                )

            # Verifica se precisa de permissões especiais
            requires_admin = False
            for check in command.checks:
                if hasattr(check, '__name__') and 'has_role' in str(check):
                    requires_admin = True
                    break

            if requires_admin:
                embed.add_field(
                    name="Permissões",
                    value="Requer cargo: **Admin**",
                    inline=False
                )

            await ctx.send(embed=embed)
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
            "`!list_roles [membro]` - Lista cargos de um membro")
        consulta_commands.append(
            "`!members_with_role <cargo>` - Lista membros com um cargo")
        consulta_commands.append(
            "`!all_roles` - Lista todos os cargos do servidor")
        consulta_commands.append(
            "`!role_stats <cargo>` - Estatísticas de um cargo")
        consulta_commands.append(
            "`!role_info <cargo>` - Informações detalhadas de um cargo")

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
            "`!assign_role <cargo>` - Adiciona cargo a você mesmo")
        atribuicao_commands.append(
            "`!remove_role <cargo>` - Remove cargo de você mesmo")
        atribuicao_commands.append(
            "`!assign_role_to <@membro> <cargo>` - Adiciona cargo a um membro")
        atribuicao_commands.append(
            "`!remove_role_from <@membro> <cargo>` - Remove cargo de um membro")

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
            "`!copy_roles <@origem> <@destino>` - Copia cargos entre membros")
        gerenciamento_commands.append(
            "`!clear_roles <@membro>` - Remove todos os cargos de um membro")
        gerenciamento_commands.append(
            "`!partner_roles_sanitizer` - Sanitiza cargos de parceiros")

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
            text="Use !jurandir <comando> para mais detalhes • Requer cargo Admin para todos os comandos"
        )

        await ctx.send(embed=embed)

    ####################################################################
    # COMANDOS DE CONSULTA
    ####################################################################
    # LISTA ROLES DE UM USUARIO
    @bot.command()
    @commands.has_role('Admin')
    async def list_roles(ctx: commands.Context, member: discord.Member = None) -> None:
        """
            Lista todos os roles de um membro (ou do author caso não seja especificado)
        """
        if member is None:
            target = ctx.author
        else:
            target = member

        roles_list = []
        for role in target.roles:
            if role.name != '@everyone':
                roles_list.append(role.mention)

        if len(roles_list) > 0:
            roles_text = ", ".join(roles_list)
            await ctx.send(f'**Roles do {target.mention}:**\n{roles_text}')
        else:
            await ctx.send(f'{target.mention} não possui roles')

    # LISTA USUARIOS COM UM ROLE
    @bot.command()
    @commands.has_role('Admin')
    async def members_with_role(ctx: commands.Context, role_name: str) -> None:
        """
            Lista todos os membros que possuem um cargo específico
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            await ctx.send(f"Cargo '{role_name}' não encontrado.")
            return

        members_list = []
        for member in ctx.guild.members:
            if role in member.roles:
                members_list.append(member.display_name)

        if len(members_list) > 0:
            members_text = "\n".join([f"- {name}" for name in members_list])
            await ctx.send(f"**Membros com o cargo {role.mention} ({len(members_list)}):**\n{members_text}")
        else:
            await ctx.send(f"Nenhum membro possui o cargo {role.mention}.")

    # LISTA ROLES DO SERVER
    @bot.command()
    @commands.has_role('Admin')
    async def all_roles(ctx: commands.Context) -> None:
        """
            Lista todos os cargos disponíveis no servidor
        """
        roles_list = []
        for role in ctx.guild.roles:
            if role.name != '@everyone':
                roles_list.append(role)

        # Ordena por posição (maior primeiro)
        roles_list.sort(key=lambda r: r.position, reverse=True)

        role_lines = []
        for role in roles_list:
            # Conta quantos membros têm esse cargo
            member_count = 0
            for member in ctx.guild.members:
                if role in member.roles:
                    member_count += 1

            role_lines.append(f"{role.mention} ({member_count} membros)")

        roles_text = "\n".join(role_lines)
        await ctx.send(f"**Cargos do servidor ({len(roles_list)}):**\n{roles_text}")

    ####################################################################
    # COMANDOS DE ATRIBUIÇAO
    ####################################################################
    # ATRIBUIR CARGO SI MESMO
    @bot.command()
    @commands.has_role('Admin')
    async def assign_role(ctx: commands.Context, role_name: str) -> None:
        """
        Adiciona um cargo ao usuário que executou o comando
        :param ctx:
        :param role_name:
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f'{ctx.author.mention} is now assigned to {role}')
        else:
            await ctx.send(f'The role {role} was not found')

    @assign_role.error
    async def assign_role_error(ctx: commands.Context, error) -> None:
        await ctx.send(f'assign_role failed with "{error}" error')

    # REMOVER CARGO DE SI MESMO
    @bot.command()
    @commands.has_role('Admin')
    async def remove_role(ctx: commands.Context, role_name: str) -> None:
        """
        Remove um cargo do usuário que executou o comando
        :param ctx:
        :param role_name:
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role:
            await ctx.author.remove_roles(role)
            await ctx.send(f'{ctx.author.mention} has had the role {role} removed')
        else:
            await ctx.send(f'The role {role} was not found')

    @remove_role.error
    async def remove_role_error(ctx: commands.Context, error) -> None:
        await ctx.send(f'remove_role failed with "{error}" error')

    # ADICIONA ROLE A USUARIO
    @bot.command()
    @commands.has_role('Admin')
    async def assign_role_to(ctx: commands.Context, member: discord.Member, role_name: str) -> None:
        """
            Adicionar um role a um usuário específico
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            await ctx.send(f'A role "{role_name}" não foi encontrada')
            return

        if role in member.roles:
            await ctx.send(f'O usuário {member.mention} já possui a role {role.mention}')
            return

        await member.add_roles(role)
        await ctx.send(f'A role {role.mention} foi adicionada ao {member.mention}')

    # REMOVE ROLE DE USUARIO
    @bot.command()
    @commands.has_role('Admin')
    async def remove_role_from(ctx: commands.Context, member: discord.Member, role_name: str) -> None:
        """
            Remove um role a um usuário específico
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            await ctx.send(f'A role "{role_name}" não foi encontrada')
            return

        if role in member.roles:
            await ctx.send(f'O usuário {member.mention} não possui a role {role.mention}')
            return

        await member.remove_roles(role)
        await ctx.send(f'A role {role.mention} foi removida ao {member.mention}')

    # COPIA ROLES DE UM USUARIO PARA OUTRO
    @bot.command()
    @commands.has_role('Admin')
    async def copy_roles(ctx: commands.Context, source: discord.Member, target: discord.Member) -> None:
        """
            Copia todos os cargos de um membro para outro
        """
        # Lista a ser populada com os roles
        roles_to_add = []

        for role in source.roles:
            if role.name != '@everyone':
                if role not in target.roles:
                    roles_to_add.append(role)

        if len(roles_to_add) == 0:
            await ctx.send(f'{target.mention} já possui todos os roles de {source.mention}')

        # Usado *roles_to_add para não enviar a lista e sim os seus itens
        # O *roles_to_add funciona como um [...] em JS
        await target.add_roles(*roles_to_add)

        # Reune as roles para report
        role_mentions = []

        # Sobre o role.metion:
        # Se você tem um cargo chamado "Admin"
        # role.name = "Admin"

        # role.mention retorna uma string especial:
        # role.mention = "<@&123456789>"  # Formato especial do Discord

        # Quando você envia essa string no Discord, aparece como:
        # @Admin (clicável e destacado)

        for role in roles_to_add:
            role_mentions.append(role.mention)

        roles_text = ", ".join(role_mentions)
        await ctx.send(f"Cargos copiados: {roles_text}")

    # REMOVE TODAS AS ROLES DE UM USUARIO
    @bot.command()
    @commands.has_role('Admin')
    async def clear_roles(ctx: commands.Context, member: discord.Member) -> None:
        """
            Remove todos os cargos de um membro (exceto @everyone)
        """
        # Lista a ser populada com os roles
        roles_to_remove = []

        for role in member.roles:
            if role.name != '@everyone':
                roles_to_remove.append(role)

        if len(roles_to_remove) == 0:
            await ctx.send(f'{member.mention} não possui roles para serem removidos')

        await member.remove_roles(roles_to_remove)
        await ctx.send(f'Todos os roles foram removidos de {member.mention}')

    ####################################################################
    # COMANDOS DE ESTATISTICAS
    ####################################################################
    @bot.command()
    @commands.has_role('Admin')
    async def role_stats(ctx: commands.Context, role_name: str) -> None:
        """
            Mostra usuários com uma role especifica
        """
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            await ctx.send(f'Role "{role_name}" não encontrada.')

        members_with_role = []
        bots = []
        humans = []

        for member in ctx.guild.members:
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

        await ctx.send(stats)

    ####################################################################
    # COMANDOS DE FUNCIONALIDADES
    ####################################################################
    # SANITIZADOR DE CARGOS DE PARCEIROS
    @bot.command()
    @commands.has_role('Admin')
    async def partner_roles_sanitizer(ctx: commands.Context) -> None:
        """
            Sanitiza os cargos de parceiros para todos os membros do servidor.
            Garante que os membros tenham os cargos de tier corretos baseados em seus cargos de parceiros.
        """
        try:
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

            members = ctx.guild.members
            total_members = len(members)

            # Estatísticas
            stats = {
                "roles_added": 0,
                "roles_removed": 0,
                "members_processed": 0,
                "errors": 0
            }

            await ctx.send(f"Starting partner roles sanitization for {total_members} members...")

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
                            ctx.guild.roles, name=tier_role_name)

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
                        await ctx.send(f"Progress: {index}/{total_members} members processed...")

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

            await ctx.send(summary)

        except Exception as e:
            error_msg = f"**Error in partner_roles_sanitizer:** {str(e)}\n```{type(e).__name__}```"
            await ctx.send(error_msg)
            print(f"Critical error in partner_roles_sanitizer: {str(e)}")
            import traceback
            traceback.print_exc()

    @partner_roles_sanitizer.error
    async def partner_roles_sanitizer_error(ctx: commands.Context, error) -> None:
        """Tratador de erros para o comando partner_roles_sanitizer"""
        if isinstance(error, commands.MissingRole):
            await ctx.send(f"You need the 'Admin' role to use this command.")
        else:
            await ctx.send(f"partner_roles_sanitizer failed with error: {str(error)}")
            print(f"partner_roles_sanitizer error: {str(error)}")
            import traceback
            traceback.print_exc()
