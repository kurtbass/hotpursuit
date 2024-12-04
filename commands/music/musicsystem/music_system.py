import discord
from utils.database import get_config

class MusicManager:
    """
    Gerenciador centralizado para lidar com músicas e conexão de voz.
    """
    def __init__(self):
        self.voice_client = None
        self.music_queue = []
        self.song_history = []  # Histórico de músicas tocadas
        self.current_song = None
        self.volume = 1.0  # Volume padrão (100%)

    def add_to_queue(self, song):
        self.music_queue.append(song)

    def get_next_song(self):
        return self.music_queue.pop(0) if self.music_queue else None

    def clear_queue(self):
        self.music_queue.clear()

    def save_current_to_history(self):
        """
        Salva a música atual no histórico.
        """
        if self.current_song:
            self.song_history.append(self.current_song)

    def get_previous_song(self):
        """
        Retorna a última música do histórico.
        """
        if self.song_history:
            return self.song_history.pop()
        return None

    def create_embed(self, title, description, color=0xFF8000, banner=None):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))  # Adicionando o lema no rodapé
        if banner:
            embed.set_image(url=banner)
        return embed
