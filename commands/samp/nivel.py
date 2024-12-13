from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
from utils.database import get_embed_color
import discord
from discord.ext import commands
from utils.database import execute_query, get_config
import logging

logger = logging.getLogger(__name__)

class NivelCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tag_membro = int(get_config("TAG_MEMBRO") or 0)
        self.lema = get_config("LEMA") or "LEMA NÃO CARREGADO, PROCURE O PROGRAMADOR DO BOT"

    def create_embed(self, title, description, color=get_embed_color()):
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
                get_embed_color()
            ))
            return False
        return True

    @commands.command(name="nivel")
    async def nivel(self, ctx):
        """Comando para registrar o nível do usuário no jogo."""
        if not await self.check_permissions(ctx):
            return

        await ctx.send(embed=self.create_embed(
            "Registro de Nível",
            "Qual o seu nível no jogo?",
        ))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300, check=check)
            nivel_jogo = int(response.content.strip())

            # Atualiza ou insere o nível, sem afetar o número de prisões
            execute_query(
                """
                INSERT INTO niveleprisoes (userid, nivel)
                VALUES (?, ?)
                ON CONFLICT(userid) DO UPDATE SET nivel = excluded.nivel
                """,
                (ctx.author.id, nivel_jogo)
            )
            await ctx.send(embed=self.create_embed(
                "Sucesso",
                f"✅ Registro salvo: Seu nível no jogo é **{nivel_jogo}**.",
                get_embed_color()
            ))
        except ValueError:
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Por favor, insira um número válido.",
                get_embed_color()
            ))
        except Exception as e:
            logger.error(f"Erro ao registrar nível: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Ocorreu um erro ao salvar suas informações. Tente novamente mais tarde.",
                get_embed_color()
            ))


async def setup(bot):
    """Adiciona o comando ao bot."""
    await bot.add_cog(NivelCommand(bot))
