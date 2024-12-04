import discord
from utils.database import get_config
from yt_dlp import YoutubeDL

class MusicManager:
    """
    Gerenciador centralizado para músicas e lógica de fila.
    """
    def __init__(self):
        self.voice_client = None
        self.music_queue = []  # Fila de músicas
        self.song_history = []  # Histórico de músicas tocadas na sessão
        self.current_song = None  # Música atualmente tocando
        self.volume = 1.0  # Volume padrão (100%)

    def add_to_queue(self, song):
        """
        Adiciona uma música à fila.
        """
        self.music_queue.append(song)

    def get_next_song(self):
        """
        Retorna e remove a próxima música da fila, resolvendo `stream_url` se necessário.
        """
        if self.music_queue:
            next_song = self.music_queue.pop(0)
            self.resolve_stream_url(next_song)
            return next_song
        return None

    def get_previous_song(self):
        """
        Retorna e remove a última música do histórico, resolvendo `stream_url` se necessário.
        """
        if self.song_history:
            previous_song = self.song_history.pop()
            self.resolve_stream_url(previous_song)
            return previous_song
        return None

    def set_current_song(self, song):
        """
        Define a música atual e move a anterior para o histórico.
        """
        if self.current_song:
            self.song_history.append(self.current_song)  # Salva a música atual no histórico
        self.current_song = song  # Define a nova música como atual

    def resolve_stream_url(self, song):
        """
        Resolve a `stream_url` da música se ainda não foi resolvida.
        """
        if not song.get('stream_url'):
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'extract_flat': False
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song['url'], download=False)
                song['stream_url'] = info.get('url')

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

    def create_embed(self, title, description, color=0xFF8000, banner=None):
        """
        Cria uma mensagem embed personalizada.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))  # Adicionando o lema no rodapé
        if banner:
            embed.set_image(url=banner)
        return embed

    def play_next(self, voice_client):
        """
        Avança para a próxima música da fila e inicia a reprodução.
        """
        next_song = self.get_next_song()
        if next_song:
            self.set_current_song(next_song)  # Define a próxima música como atual
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(next_song['stream_url'], options='-vn'),
                volume=self.volume
            )
            voice_client.play(source, after=lambda e: self.play_next(voice_client))
        else:
            self.current_song = None  # Não há próxima música


    def save_current_to_history(self):
        """
        Salva a música atual no histórico de músicas tocadas.
        """
        if self.current_song:  # Certifica que há uma música atual
         self.song_history.append(self.current_song)
         self.current_song = None

    def play_previous(self, voice_client):
        """
        Retorna para a música anterior e inicia a reprodução.
        """
        previous_song = self.get_previous_song()
        if previous_song:
            self.set_current_song(previous_song)  # Define a música anterior como atual
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(previous_song['stream_url'], options='-vn'),
                volume=self.volume
            )
            voice_client.play(source, after=lambda e: self.play_next(voice_client))
        else:
            self.current_song = None  # Não há música anterior
