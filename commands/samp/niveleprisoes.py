from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
from utils.database import get_embed_color
import discord
from discord.ext import commands
from utils.database import fetchall, get_config
import logging

logger = logging.getLogger(__name__)

class NivelEPrisoesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [
            int(get_config("DONO") or 0),
            int(get_config("SUBDONO") or 0)
        ]
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"

    def create_embed(self, title, description, color=get_embed_color()):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=self.lema)
        return embed

    async def check_permissions(self, ctx):
        """
        Verifica se o usuário tem permissão para usar o comando (DONO ou SUBDONO).
        """
        if ctx.author.id not in self.allowed_ids:
            await ctx.send(embed=self.create_embed(
                "Sem Permissão",
                "⚠️ Você não tem permissão para usar este comando.",
                get_embed_color()
            ))
            return False
        return True

    @commands.command(name="niveleprisoes")
    async def niveleprisoes(self, ctx):
        """
        Comando para listar os dados salvos na tabela niveleprisoes.
        """
        if not await self.check_permissions(ctx):
            return

        # Buscar dados na tabela niveleprisoes
        try:
            data = fetchall("SELECT userid, nivel, prisoes FROM niveleprisoes")
            if not data:
                await ctx.send(embed=self.create_embed(
                    "Nenhum Dado Encontrado",
                    "⚠️ Não há registros salvos na tabela de níveis e prisões.",
                    get_embed_color()
                ))
                return

            description = "Lista de Níveis e Prisões\n\n"
            for row in data:
                userid, nivel, prisoes = row
                description += f"**Usuário:** <@{userid}>\n"
                description += f"**Nível:** {nivel if nivel is not None else 'Não registrado'}\n"
                description += f"**Prisões:** {prisoes if prisoes is not None else 'Não registrado'}\n\n"

            await ctx.send(embed=self.create_embed(
                "Níveis e Prisões Registrados",
                description
            ))
        except Exception as e:
            logger.error(f"Erro ao listar dados de niveleprisoes: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Ocorreu um erro ao buscar os dados. Tente novamente mais tarde.",
                get_embed_color()
            ))

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(NivelEPrisoesCommand(bot))
