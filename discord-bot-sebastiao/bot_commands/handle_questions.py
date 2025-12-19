from typing import Final
import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

OLIST_BLUE: Final = discord.Color(0x0057dd)


def set_commands(bot: commands.Bot) -> None:
    ####################################################################
    # COMANDOS HELP
    ####################################################################
    # Comando !sebastiao com output em embed
    @bot.command()
    async def sebastiao(ctx: commands.Context, command_name: str = None) -> None:
        """
            Lista todos os comandos que o bot possui
            Use: !sebastiao ou !sebastiao <nome_do_comando>
        """

        # Se o usuário pediu ajuda sobre um comando específico
        if command_name:
            command = bot.get_command(command_name)

            if command is None:
                embed = discord.Embed(
                    title="❌ Comando não encontrado",
                    description=f"O comando `{command_name}` não existe.\nUse `!sebastiao` para ver todos os comandos disponíveis.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Embed para comando específico
            embed = discord.Embed(
                title=f"📖 Comando: `!{command.name}`",
                color=OLIST_BLUE
            )

            if command.sebastiao:
                embed.description = command.sebastiao

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

        # Comandos
        consulta_commands = []
        consulta_commands.append(
            "`!ask <pergunta>` - Envia uma pergunta para o webhook do n8n")

        consulta_text = ""
        for cmd in consulta_commands:
            consulta_text = consulta_text + cmd + "\n"

        embed.add_field(
            name="🔍 Comandos",
            value=consulta_text,
            inline=False
        )

        # Footer com informações adicionais
        embed.set_footer(
            text="Use !sebastiao <comando> para mais detalhes • Requer cargo Admin para todos os comandos"
        )

        await ctx.send(embed=embed)

    ####################################################################
    # COMANDOS N8N
    ####################################################################

    @bot.command()
    async def ask(ctx: commands.Context, *, message: str) -> None:
        """
        Envia uma mensagem para o webhook do n8n
        Uso: !ask sua pergunta aqui
        """
        webhook_url = os.getenv("N8N_WEBHOOK_URL")

        if not webhook_url:
            embed = discord.Embed(
                title="❌ Erro de Configuração",
                description="Webhook URL não configurada. Contate um administrador.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Prepara os dados para enviar ao webhook
        data = {
            "message": message,
            "author": {
                "id": str(ctx.author.id),
                "username": ctx.author.name,
                "display_name": ctx.author.display_name,
                "mention": ctx.author.mention
            },
            "channel": {
                "id": str(ctx.channel.id),
                "name": ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
            },
            "guild": {
                "id": str(ctx.guild.id) if ctx.guild else None,
                "name": ctx.guild.name if ctx.guild else None
            },
            "timestamp": ctx.message.created_at.isoformat()
        }

        # Envia para o webhook usando requests
        try:
            response = requests.post(webhook_url, json=data, timeout=10)

            if response.status_code == 200:
                embed = discord.Embed(
                    title="✅ Pergunta enviada",
                    description=f"Sua pergunta foi enviada com sucesso para o n8n!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Pergunta",
                                value=message[:1024], inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description=f"Não foi possível enviar a pergunta. Status: {response.status_code}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        except requests.exceptions.Timeout:
            embed = discord.Embed(
                title="❌ Timeout",
                description="O webhook demorou muito para responder. Tente novamente.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro ao enviar webhook: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    # Adiciona descrição para o comando help
    ask.sebastiao = "Envia uma pergunta para o webhook do n8n"
