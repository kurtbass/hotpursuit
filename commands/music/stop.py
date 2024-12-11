import discord
import logging
from commands.music.musicsystem.embeds import (
    embed_dj_error,
    embed_error,
    embed_stop_music,
    embed_permission_denied,
    embed_user_not_in_same_channel
)
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
        """
        Comando para parar a reprodução de música e limpar a fila.
        """
        # Verificar se o bot está tocando alguma música
        if not self.music_manager.voice_client or not self.music_manager.voice_client.is_playing():
            await ctx.send(embed=embed_error("Nenhuma música está tocando no momento."))
            return

        # Verificar se o usuário está no mesmo canal de voz que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=embed_user_not_in_same_channel())
            return

        # Verificar permissões do usuário
        if not self._user_has_permissions(ctx):
            await ctx.send(embed=embed_dj_error())
            return

        try:
            # Parar a música, limpar a fila e redefinir o loop
            self.music_manager.voice_client.stop()
            self.music_manager.clear_queue()
            self.music_manager.current_song = None
            self.music_manager.set_loop_mode("none")  # Desativa o loop

            logger.info(f"Usuário {ctx.author.id} parou a música e limpou a fila.")
            await ctx.send(embed=embed_stop_music())

        except Exception as e:
            logger.error(f"Erro ao parar a música: {e}")
            await ctx.send(embed=embed_error("Erro ao tentar parar a música.", str(e)))

    def _user_has_permissions(self, ctx):
        """
        Verifica se o usuário tem permissão para parar a música.
        Retorna True se o usuário for o dono da sessão ou possuir a tag de DJ.
        """
        tag_dj_id = self.music_manager.dj_role_id
        if not self.music_manager.current_song:
            logger.warning("Nenhuma música atual definida para verificar permissões.")
            return False

        # Verifica se o usuário é o dono da sessão ou possui a tag de DJ
        is_session_owner = ctx.author.id == int(self.music_manager.current_song.get('added_by', 0))
        has_dj_role = any(role.id == int(tag_dj_id) for role in ctx.author.roles)
        return is_session_owner or has_dj_role

async def setup(bot, music_manager):
    await bot.add_cog(StopMusicCommand(bot, music_manager))