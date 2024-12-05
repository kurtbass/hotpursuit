from utils.database import get_embed_color
import discord
from discord.ext import commands
import logging

from utils.database import get_config

logger = logging.getLogger(__name__)

class RestartCommand(commands.Cog):
    """
    Comando para recarregar comandos específicos.
    """

    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description, color=get_embed_color()):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="restart", aliases=["reload"])
    async def restart(self, ctx, command_name: str):
        """
        Recarrega um comando específico.
        Apenas o dono do bot pode usar.
        """
        # Verificar se o usuário é o dono
        if ctx.author.id != int(get_config("DONO")):
            await ctx.send(embed=self.create_embed(
                "Acesso Negado",
                "⚠️ Apenas o dono do bot pode usar este comando.",
                get_embed_color()
            ))
            return

        try:
            # Recarregar o comando especificado
            self.bot.reload_extension(f"commands.{command_name}")
            logger.info(f"O comando '{command_name}' foi recarregado por {ctx.author}.")
            await ctx.send(embed=self.create_embed(
                "Comando Recarregado",
                f"✅ O comando **{command_name}** foi recarregado com sucesso.",
                get_embed_color()
            ))
        except Exception as e:
            logger.error(f"Erro ao recarregar o comando '{command_name}': {e}")
            await ctx.send(embed=self.create_embed(
                "Erro ao Recarregar",
                f"⚠️ Ocorreu um erro ao tentar recarregar o comando **{command_name}**.\n\n**Detalhes:**\n```{e}```",
                get_embed_color()
            ))


async def setup(bot):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    """
    await bot.add_cog(RestartCommand(bot))
