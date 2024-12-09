import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_dj_error, embed_error, embed_previous_song, embed_permission_denied
import logging

logger = logging.getLogger(__name__)

class PreviousCommand(commands.Cog):
    """
    Comando para voltar e tocar a música anterior na fila.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="previous", aliases=["voltar", "back"])
    async def previous(self, ctx):
        """
        Volta para a música anterior no histórico.
        """
        voice_client = self.music_manager.voice_client

        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=embed_error("bot_not_connected"))
            return

        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == int(self.music_manager.current_song.get('added_by')) or 
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        # Recuperar a música anterior do histórico
        previous_song = self.music_manager.get_previous_song()
        if not previous_song:
            await ctx.send(embed=embed_error("no_previous_song"))
            return

        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=embed_error("user_not_in_same_channel"))
            return

        try:
            # Salva a música atual no início da fila
            if self.music_manager.current_song:
                self.music_manager.add_to_queue(self.music_manager.current_song)

            # Resolver `stream_url` da música anterior se necessário
            if not previous_song.get('stream_url'):
                self.music_manager.resolve_stream_url(previous_song)

            # Atualizar a música atual para a música anterior
            self.music_manager.current_song = previous_song

            # Configurar e tocar a música anterior
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(previous_song['stream_url'], **{
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn'
                }),
                volume=self.music_manager.volume
            )

            voice_client.stop()
            voice_client.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(
                self.music_manager.play_next, voice_client
            ))

            # Enviar mensagem de confirmação
            await ctx.send(embed=embed_previous_song(previous_song))
        except Exception as e:
            logger.error(f"Erro ao reproduzir a música anterior: {e}")
            await ctx.send(embed=embed_error("previous_song_error", str(e)))

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PreviousCommand(bot, music_manager))
