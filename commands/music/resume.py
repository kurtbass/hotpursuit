import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class ResumeCommand(commands.Cog):
    """
    Comando para retomar a reprodução de música pausada.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="resume", aliases=["resumir", "retomar"])
    async def resume(self, ctx):
        """
        Retoma a reprodução da música pausada.

        :param ctx: Contexto do comando.
        """
        voice_client = self.music_manager.voice_client

        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", 0xFF0000
            ))
            return

        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000
            ))
            return

        if not voice_client.is_paused():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Nenhuma música está pausada para retomar.", 0xFF0000
            ))
            return

        try:
            voice_client.resume()
            await ctx.send(embed=self.music_manager.create_embed(
                "Música Retomada", "▶️ A música pausada foi retomada.", 0x00FF00
            ))
            logger.info("Música retomada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao tentar retomar a música: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Ocorreu um erro ao tentar retomar a música.", 0xFF0000
            ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(ResumeCommand(bot, music_manager))
