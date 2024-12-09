import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_music_paused
import logging
from commands.music.musicsystem.music_system import MusicManager

logger = logging.getLogger(__name__)

class PauseCommand(commands.Cog):
    """
    Comando para pausar a reprodução de música.
    """

    def __init__(self, bot, music_manager: MusicManager):
        """
        Inicializa o comando de pausa.

        :param bot: O bot do Discord.
        :param music_manager: Instância de MusicManager.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="pause", aliases=["pausar"])
    async def pause(self, ctx):
        """
        Pausa a música atual.

        :param ctx: Contexto do comando.
        """
        voice_client = self.music_manager.voice_client

        # Verifica se o bot está conectado a um canal de voz
        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=embed_error("bot_not_connected"))
            return

        # Verifica se o usuário está no mesmo canal do bot
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=embed_error("user_not_in_same_channel"))
            return

        # Verifica se há uma música tocando
        if not voice_client.is_playing():
            await ctx.send(embed=embed_error("no_music_playing"))
            return

        try:
            # Pausa a música
            voice_client.pause()

            # Verifica se o estado do player mudou para pausado
            if not voice_client.is_playing():
                current_song = self.music_manager.current_song
                await ctx.send(embed=embed_music_paused(current_song))
                logger.info(f"Música pausada com sucesso: {current_song.get('title', 'Desconhecida')}")

        except Exception as e:
            logger.error(f"Erro ao tentar pausar a música: {e}")
            await ctx.send(embed=embed_error("pause_error", str(e)))


async def setup(bot, music_manager: MusicManager):
    """
    Adiciona o comando de pausa ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PauseCommand(bot, music_manager))
