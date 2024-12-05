import discord
from discord.ext import commands

from utils.database import get_config

class LeaveCommand(commands.Cog):
    """
    Comando para pausar a reprodução de música.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de pausa.
        """
        self.bot = bot
        self.music_manager = music_manager

    def create_embed(self, title, description, color=0xFF8000):
        """
        Cria um embed padronizado com título, descrição e cor.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="leave", aliases=["sair", "desconectar, disconnect, quit"])
    async def leave(self, ctx):
        """
        Faz o bot sair do canal de voz atual.
        """
        if not self.bot.voice_clients or not any(vc.is_connected() for vc in self.bot.voice_clients):
            await ctx.send(embed=self.create_embed(
                "Erro",
                "⚠️ Não estou conectado a nenhum canal de voz.",
                0xFF0000
            ))
            return

        for vc in self.bot.voice_clients:
            if vc.channel == ctx.author.voice.channel:
                await vc.disconnect()
                await ctx.send(embed=self.create_embed(
                    "Desconectado",
                    f"✅ Saí do canal **{vc.channel.name}**.",
                    0xFF8000
                ))
                return

        await ctx.send(embed=self.create_embed(
            "Erro",
            "⚠️ Você não está no mesmo canal de voz que eu.",
            0xFF0000
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(LeaveCommand(bot, music_manager))
