from utils.database import execute_query
from commands.music.musicsystem.embeds import create_embed, embed_now_playing, embed_queue_empty, embed_error, embed_stop_music
import asyncio
import discord
from yt_dlp import YoutubeDL
import logging
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS

logger = logging.getLogger(__name__)

class MusicManager:
    """
    Gerenciador centralizado para músicas e lógica de fila.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.music_queue = []  # Fila de músicas
        self.song_history = []  # Histórico de músicas tocadas na sessão
        self.current_song = None  # Música atualmente tocando
        self.volume = 1.0  # Volume padrão (100%)

    def add_to_queue(self, song, added_by_id):
        """
        Adiciona uma música à fila e registra quem a adicionou.
        """
        song['added_by'] = added_by_id
        self.music_queue.append(song)

    def get_session_owner_id(self):
        """
        Retorna o ID de quem iniciou a sessão (primeira música da fila).
        """
        return self.music_queue[0].get('added_by', None) if self.music_queue else None

    def get_next_song(self):
        """
        Retorna e remove a próxima música da fila.
        """
        return self.music_queue.pop(0) if self.music_queue else None

    def get_previous_song(self):
        """
        Retorna e remove a última música do histórico.
        """
        return self.song_history.pop() if self.song_history else None

    def set_current_song(self, song):
        """
        Define a música atual e move a anterior para o histórico.
        """
        if self.current_song:
            self.song_history.append(self.current_song)
        self.current_song = song

    def resolve_stream_url(self, song):
        """
        Resolve a `stream_url` da música se ainda não foi resolvida.
        """
        if 'stream_url' not in song:
            try:
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': False}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    song['stream_url'] = info.get('url')
            except Exception as e:
                logger.error(f"Erro ao resolver URL do stream: {e}")
                raise RuntimeError(f"Erro ao resolver URL do stream: {e}")

    def clear_queue(self):
        """Limpa a fila de músicas."""
        self.music_queue.clear()

    def clear_history(self):
        """Limpa o histórico de músicas tocadas."""
        self.song_history.clear()

    def get_queue(self):
        """Retorna uma cópia da fila de músicas."""
        return list(self.music_queue)

    def get_history(self):
        """Retorna uma cópia do histórico de músicas."""
        return list(self.song_history)

    async def play_next(self, ctx):
        """
        Avança para a próxima música da fila e inicia a reprodução.
        """
        try:
            # Salvar a música atual no histórico
            self.save_current_to_history()

            # Obter a próxima música
            next_song = self.get_next_song()
            if not next_song:
                self.current_song = None
                await ctx.send(embed=embed_queue_empty())
                return

            # Verificar conexão ao canal de voz
            if not self.voice_client or not self.voice_client.is_connected():
                try:
                    logger.info("Reconectando ao canal de voz...")
                    self.voice_client = await ctx.author.voice.channel.connect()
                except Exception as e:
                    logger.error(f"Erro ao tentar reconectar ao canal de voz: {e}")
                    return

            # Verificar se já há áudio sendo reproduzido
            if self.voice_client.is_playing():
                logger.warning("Áudio já está sendo reproduzido. Pulando reprodução duplicada.")
                return

            # Resolver URL e iniciar a reprodução
            self.resolve_stream_url(next_song)
            self.set_current_song(next_song)

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(next_song['stream_url'], **FFMPEG_OPTIONS),
                volume=self.volume
            )

            def after_playing(error):
                if error:
                    logger.error(f"Erro durante a reprodução: {error}")
                if self.voice_client and self.voice_client.is_playing():
                    self.voice_client.stop()
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), ctx.bot.loop)

            self.voice_client.play(source, after=after_playing)

            # Informar sobre a música atual
            await ctx.send(embed=embed_now_playing(next_song))

        except Exception as e:
            logger.error(f"Erro ao reproduzir a próxima música: {e}")
            await ctx.send(embed=embed_error(str(e)))

    def save_current_to_history(self):
        """Move a música atualmente tocando para o histórico."""
        if self.current_song:
            self.song_history.append(self.current_song)
            self.current_song = None

    def get_total_duration(self):
        """Calcula a duração total das músicas na fila."""
        return sum(song.get('duration', 0) for song in self.music_queue)

    async def stop_music(self, ctx):
        """Para a música atual e limpa a fila."""
        try:
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
                self.clear_queue()
                await ctx.send(embed=embed_stop_music())
        except Exception as e:
            logger.error(f"Erro ao parar a música: {e}")
            await ctx.send(embed=embed_error(str(e)))

    def adjust_volume(self, volume):
        """Ajusta o volume da reprodução atual."""
        if 0.0 <= volume <= 2.0:
            self.volume = volume
            if self.voice_client and self.voice_client.source:
                self.voice_client.source.volume = self.volume
            logger.info(f"Volume ajustado para: {volume * 100}%")
        else:
            logger.warning("Volume fora do intervalo permitido.")

    def is_queue_empty(self):
        """Verifica se a fila de músicas está vazia."""
        return len(self.music_queue) == 0

    def is_playing(self):
        """Verifica se uma música está sendo reproduzida atualmente."""
        return self.voice_client and self.voice_client.is_playing()
