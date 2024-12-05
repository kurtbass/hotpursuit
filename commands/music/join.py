from utils.database import get_embed_color
import discord
from discord.ext import commands

from utils.database import get_config

class JoinCommand(commands.Cog):
    """
    Comando para pausar a reprodução de música.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de pausa.
        """
        self.bot = bot
        self.music_manager = music_manager

    def create_embed(self, title, description, color=get_embed_color()):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="join", aliases=["entrar, enter, connect, conectar"])
    async def join(self, ctx):
        """
        Faz o bot entrar no canal de voz do usuário.
        """
        if ctx.author.voice is None:
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Você precisa estar em um canal de voz para usar este comando.",
                get_embed_color()
            ))
            return

        user_channel = ctx.author.voice.channel

        if self.bot.voice_clients and any(vc.channel != user_channel for vc in self.bot.voice_clients):
            current_channel = [vc.channel.name for vc in self.bot.voice_clients if vc.is_connected()][0]
            await ctx.send(embed=self.create_embed(
                "Erro",
                f"⚠️ Já estou conectado no canal **{current_channel}**.",
                get_embed_color()
            ))
            return

        # Conecta ao canal do usuário
        await user_channel.connect()
        await ctx.send(embed=self.create_embed(
            "Conectado",
            f"✅ Entrei no canal **{user_channel.name}**.",
            get_embed_color()
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(JoinCommand(bot, music_manager))
