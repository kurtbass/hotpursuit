import discord
from discord.ext import commands
from utils.database import execute_query, get_config
import logging

logger = logging.getLogger(__name__)

class PrisoesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tag_membro = int(get_config("TAG_MEMBRO") or 0)
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"

    def create_embed(self, title, description, color=0xFF8000):
        """Cria um embed padronizado."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def check_permissions(self, ctx):
        """Verifica se o usuário tem a TAG_MEMBRO."""
        membro_cargo = discord.utils.get(ctx.guild.roles, id=self.tag_membro)
        if not membro_cargo or membro_cargo not in ctx.author.roles:
            await ctx.send(embed=self.create_embed(
                "Sem Permissão",
                "⚠️ Você não tem permissão para usar este comando.",
                0xFF0000
            ))
            return False
        return True

    @commands.command(name="prisoes")
    async def prisoes(self, ctx):
        """Comando para registrar a quantidade de prisões do usuário."""
        if not await self.check_permissions(ctx):
            return

        await ctx.send(embed=self.create_embed(
            "Registro de Prisões",
            "Quantas prisões você tem?",
        ))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300, check=check)
            prisao_count = int(response.content.strip())

            # Atualiza ou insere o número de prisões, sem afetar o nível
            execute_query(
                """
                INSERT INTO niveleprisoes (userid, prisoes)
                VALUES (?, ?)
                ON CONFLICT(userid) DO UPDATE SET prisoes = excluded.prisoes
                """,
                (ctx.author.id, prisao_count)
            )
            await ctx.send(embed=self.create_embed(
                "Sucesso",
                f"✅ Registro salvo: Você tem **{prisao_count} prisões**.",
                0x00FF00
            ))
        except ValueError:
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Por favor, insira um número válido.",
                0xFF0000
            ))
        except Exception as e:
            logger.error(f"Erro ao registrar prisões: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Ocorreu um erro ao salvar suas informações. Tente novamente mais tarde.",
                0xFF0000
            ))


async def setup(bot):
    """Adiciona o comando ao bot."""
    await bot.add_cog(PrisoesCommand(bot))
