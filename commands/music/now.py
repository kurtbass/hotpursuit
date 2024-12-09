import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_now_playing, embed_error
import logging

logger = logging.getLogger(__name__)

class NowCommand(commands.Cog):
    """
    Comando para exibir informações sobre a música atualmente tocando.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="now", aliases=["agora", "tocandoagora"])
    async def now(self, ctx):
        """
        Exibe informações da música atualmente tocando.

        :param ctx: Contexto do comando.
        """
        # Verifica se há uma música sendo tocada
        if not self.music_manager.current_song:
            await ctx.send(embed=embed_error(
                "Não há nenhuma música tocando no momento."
            ))
            return

        # Verifica se o usuário está no mesmo canal de voz que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=embed_error(
                "Você precisa estar no mesmo canal de voz do bot para usar este comando."
            ))
            return

        try:
            # Informações da música atual
            song = self.music_manager.current_song

            # Enviar embed com as informações da música atual
            embed = embed_now_playing(song, self.music_manager.voice_client.channel)
            await ctx.send(embed=embed)
            logger.info(f"Informações da música atual enviadas: {song.get('title', 'Título Desconhecido')}")

        except Exception as e:
            logger.error(f"Erro ao exibir informações da música atual: {e}")
            await ctx.send(embed=embed_error(
                "Ocorreu um erro ao tentar exibir as informações da música atual."
            ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(NowCommand(bot, music_manager))