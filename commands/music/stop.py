import discord
import logging
from commands.music.musicsystem.embeds import embed_error, embed_stop_music, embed_permission_denied
from commands.music.musicsystem.music_system import MusicManager
from discord.ext import commands

logger = logging.getLogger(__name__)

class StopMusicCommand(commands.Cog):
    """
    Comando para parar a música e limpar a fila.
    """
    def __init__(self, bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name='stop', aliases=['parar'])
    async def stop(self, ctx):
        # Verificar se o bot está tocando alguma música
        if not self.music_manager.voice_client or not self.music_manager.voice_client.is_playing():
            await ctx.send(embed=embed_error("no_music_playing"))
            return

        # Verificar se o usuário está no mesmo canal de voz que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=embed_error("user_not_in_same_channel"))
            return

        # Verificar se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == int(self.music_manager.current_song.get('added_by')) or discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_permission_denied("stop_music_permission"))
            return

        try:
            # Parar a música e limpar a fila
            self.music_manager.voice_client.stop()
            self.music_manager.clear_queue()
            self.music_manager.current_song = None

            logger.info(f"Usuário {ctx.author.id} parou a música.")

            # Enviar mensagem de confirmação
            await ctx.send(embed=embed_stop_music())

        except Exception as e:
            logger.error(f"Erro ao parar a música: {e}")
            await ctx.send(embed=embed_error("stop_music_error", str(e)))

async def setup(bot, music_manager):
    await bot.add_cog(StopMusicCommand(bot, music_manager))
