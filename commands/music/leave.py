import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_disconnected

class LeaveCommand(commands.Cog):
    """
    Comando para o bot sair do canal de voz.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de saída do canal de voz.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="leave", aliases=["sair", "desconectar", "disconnect", "quit"])
    async def leave(self, ctx):
        """
        Faz o bot sair do canal de voz atual.
        """
        if not self.bot.voice_clients or not any(vc.is_connected() for vc in self.bot.voice_clients):
            await ctx.send(embed=embed_error(
                "Não estou conectado a nenhum canal de voz."
            ))
            return

        for vc in self.bot.voice_clients:
            if vc.channel == ctx.author.voice.channel:
                await vc.disconnect()
                await ctx.send(embed=embed_disconnected(vc.channel.name))
                return

        await ctx.send(embed=embed_error(
            "Você não está no mesmo canal de voz que eu."
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(LeaveCommand(bot, music_manager))
