import asyncio
import discord
from yt_dlp import YoutubeDL
import logging
from utils.database import get_config, get_status_by_id
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
        self.default_status_id = 2  # ID do status padrão no banco de dados

    def add_to_queue(self, song):
        """
        Adiciona uma música à fila.
        """
        self.music_queue.append(song)

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
        if not song.get('stream_url'):
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'extract_flat': False
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    song['stream_url'] = info.get('url')
            except Exception as e:
                logger.error(f"Erro ao resolver URL do stream: {e}")
                raise RuntimeError(f"Erro ao resolver URL do stream: {e}")

    def clear_queue(self):
        """
        Limpa a fila de músicas.
        """
        self.music_queue.clear()

    def clear_history(self):
        """
        Limpa o histórico de músicas tocadas.
        """
        self.song_history.clear()

    def get_queue(self):
        """
        Retorna uma cópia da fila de músicas.
        """
        return list(self.music_queue)

    def get_history(self):
        """
        Retorna uma cópia do histórico de músicas.
        """
        return list(self.song_history)

    def create_embed(self, title, description, color=0xFF8000, banner=None, thumbnail=None):
        """
        Cria uma mensagem embed personalizada.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))

        if banner:
            embed.set_image(url=banner)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed

    async def update_bot_status(self):
        """
        Atualiza o status do bot com base no estado atual do MusicManager.
        """
        if self.current_song:
            title = self.current_song.get('title', 'Desconhecida')
            activity = discord.Activity(type=discord.ActivityType.listening, name=title)
            await self.bot.change_presence(activity=activity, status=discord.Status.online)
            logger.info(f"Status atualizado para 'Ouvindo: {title}'.")
        elif not self.music_queue:
            await self.restore_default_status()
        else:
            logger.debug("Música pausada ou aguardando próxima música na fila.")

    async def restore_default_status(self):
        """
        Restaura o status padrão do bot.
        """
        status_data = get_status_by_id(self.default_status_id)
        if status_data:
            status_type, status_message, status_status = status_data
            activity = None
            if status_type == '1':  # Jogando
                activity = discord.Game(name=status_message)
            elif status_type == '2':  # Transmitindo
                activity = discord.Streaming(name=status_message, url="https://www.twitch.tv/seu_canal")
            elif status_type == '3':  # Ouvindo
                activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)
            elif status_type == '4':  # Assistindo
                activity = discord.Activity(type=discord.ActivityType.watching, name=status_message)

            status_map = {
                'online': discord.Status.online,
                'dnd': discord.Status.dnd,
                'idle': discord.Status.idle,
                'invisible': discord.Status.invisible
            }
            await self.bot.change_presence(activity=activity, status=status_map.get(status_status, discord.Status.online))
            logger.info(f"Status restaurado para o padrão: {status_message} ({status_status}).")
        else:
            logger.warning("Status padrão não encontrado no banco de dados.")

    async def play_next(self, ctx):
        """
        Avança para a próxima música da fila e inicia a reprodução.
        """
        try:
            self.save_current_to_history()
            next_song = self.get_next_song()
            if next_song:
                if not next_song.get('stream_url'):
                    self.resolve_stream_url(next_song)

                self.set_current_song(next_song)
                await self.update_bot_status()  # Atualiza o status do bot

                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(next_song['stream_url'], **FFMPEG_OPTIONS),
                    volume=self.volume
                )

                def after_playing(error):
                    if error:
                        logger.error(f"Erro durante a reprodução: {error}")
                    asyncio.run_coroutine_threadsafe(self.play_next(ctx), ctx.bot.loop)

                if self.voice_client and not self.voice_client.is_playing():
                    self.voice_client.play(source, after=after_playing)
                    await ctx.send(embed=self.create_embed(
                        "🎵 Tocando Agora",
                        f"**Título:** {next_song['title']}\n"
                        f"**Duração:** {self.format_duration(next_song['duration'])}\n"
                        f"**Adicionado por:** {next_song['added_by']}",
                        0xFF8000,
                        thumbnail=next_song.get('thumbnail')
                    ))
            else:
                self.current_song = None
                await self.update_bot_status()  # Atualiza o status para padrão após a fila terminar
                await ctx.send(embed=self.create_embed(
                    "🎶 Fila Vazia",
                    "Adicione mais músicas para continuar a reprodução.",
                    0xFF8000
                ))
                await asyncio.sleep(5)
                if self.voice_client:
                    await self.voice_client.disconnect()
                    self.voice_client = None
                    logger.info("Bot desconectado por inatividade.")
        except Exception as e:
            logger.error(f"Erro ao reproduzir a próxima música: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro",
                f"⚠️ Ocorreu um erro ao tentar reproduzir a próxima música: {str(e)}",
                0xFF0000
            ))

    def save_current_to_history(self):
        """
        Move a música atualmente tocando para o histórico.
        """
        if self.current_song:
            self.song_history.append(self.current_song)
            logger.info(f"Música movida para o histórico: {self.current_song['title']}")
            self.current_song = None

    def get_total_duration(self):
        """
        Calcula a duração total das músicas na fila.
        """
        return sum(song.get('duration', 0) for song in self.music_queue)

    @staticmethod
    def format_duration(seconds):
        """
        Formata a duração em segundos para o formato HH:MM:SS.
        """
        return f"{seconds // 3600}:{(seconds % 3600) // 60:02}:{seconds % 60:02}"
