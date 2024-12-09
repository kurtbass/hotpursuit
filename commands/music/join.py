import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_connected

class JoinCommand(commands.Cog):
    """
    Comando para o bot entrar no canal de voz do usuário.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de entrada no canal de voz.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="join", aliases=["entrar", "enter", "connect", "conectar"])
    async def join(self, ctx):
        """
        Faz o bot entrar no canal de voz do usuário.
        """
        if ctx.author.voice is None:
            await ctx.send(embed=embed_error(
                "Você precisa estar em um canal de voz para usar este comando."
            ))
            return

        user_channel = ctx.author.voice.channel

        if self.bot.voice_clients and any(vc.channel != user_channel for vc in self.bot.voice_clients):
            current_channel = [vc.channel.name for vc in self.bot.voice_clients if vc.is_connected()][0]
            await ctx.send(embed=embed_error(
                f"Já estou conectado no canal **{current_channel}**."
            ))
            return

        # Conecta ao canal do usuário
        await user_channel.connect()
        await ctx.send(embed=embed_connected(user_channel.name))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(JoinCommand(bot, music_manager))
