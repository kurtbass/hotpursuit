import logging
from discord.ext import commands
from commands.music.musicsystem.insert import insert_music
from commands.music.musicsystem.music_system import MusicManager
from commands.music.musicsystem.playlists import process_playlist
from commands.music.musicsystem.voice_utils import join_voice_channel
from commands.music.musicsystem.play_utils import play_next
from utils.config import get_config
from commands.music.musicsystem.ydl_opts import YDL_OPTS
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS

logger = logging.getLogger(__name__)

class PlayCommand(commands.Cog):
    """
    Comando para reproduzir músicas e playlists.
    """

    def __init__(self, bot, music_manager: MusicManager):
        """
        Inicializa o comando Play.
        """
        self.bot = bot
        self.music_manager = music_manager
        self.ydl_opts = YDL_OPTS
        self.ffmpeg_options = FFMPEG_OPTIONS

    @commands.command(name="play", aliases=["p", "tocar"])
    async def play(self, ctx, *, query: str = None):
        """
        Comando para adicionar uma música ou playlist à fila e iniciar a reprodução.
        Se não for fornecido um argumento, envia uma explicação ao usuário no chat.
        """
        if not query:
            # Envia uma mensagem explicando como usar o comando
            await ctx.send(embed=self.music_manager.create_embed(
                "Como Usar o Comando play",
                f"⚠️ **Uso do Comando play** ⚠️\n\n"
                f"**Opções de uso:**\n"
                f"- Link do YouTube: `https://youtube.com/watch?v=<ID>`\n"
                f"- Nome da Música: Exemplo: `Bohemian Rhapsody`\n"
                f"- Playlist do YouTube: `https://youtube.com/playlist?list=<ID>`\n\n"
                f"**Exemplos de Comando:**\n"
                f"- `{get_config('PREFIXO')}play https://youtube.com/watch?v=xxxxxx`\n"
                f"- `{get_config('PREFIXO')}play Nome da Música`\n"
                f"- `{get_config('PREFIXO')}play https://youtube.com/playlist?list=xxxxxx`\n",
                0xFF8000  # Cor do embed
            ))
            return

        try:
            # Conecta o bot ao canal de voz do usuário
            voice_client = await join_voice_channel(ctx, self.music_manager)
            if voice_client is None:
                return

            # Determina se o argumento é uma playlist ou música individual
            if "playlist" in query.lower() or "list=" in query:
                logger.info(f"Processando playlist: {query}")
                await process_playlist(ctx, query, self.music_manager, self.ydl_opts)
            else:
                logger.info(f"Adicionando música individual: {query}")
                await insert_music(ctx, query, self.music_manager, self.ydl_opts)

            # Se o bot não estiver tocando, inicie a reprodução
            if not self.music_manager.voice_client.is_playing():
                logger.info("Iniciando reprodução da próxima música na fila.")
                await play_next(self.music_manager, self.bot)

        except Exception as e:
            # Caso ocorra algum erro ao tentar reproduzir a música
            logger.error(f"Erro ao tentar reproduzir música ou playlist: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", f"⚠️ Ocorreu um erro ao tentar tocar a música.\n{str(e)}", 0xFF0000  # Cor do erro
            ))

async def setup(bot, music_manager):
    """
    Adiciona o cog PlayCommand ao bot.
    """
    await bot.add_cog(PlayCommand(bot, music_manager))
