import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_play_usage
from commands.music.musicsystem.insert import insert_music
from commands.music.musicsystem.music_system import MusicManager
from commands.music.musicsystem.playlists import process_playlist
from commands.music.musicsystem.voice_utils import join_voice_channel
from commands.music.musicsystem.ydl_opts import YDL_OPTS
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
from utils.database import get_user_volume

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
            await ctx.send(embed=embed_play_usage())
            return

        try:
            # Conecta o bot ao canal de voz do usuário
            voice_client = await join_voice_channel(ctx, self.music_manager)
            if voice_client is None:
                return

            # Ajusta o volume da sessão com base no volume salvo na database
            user_volume = get_user_volume(ctx.author.id)
            self.music_manager.volume = user_volume if user_volume is not None else 1.0

            if voice_client.source and hasattr(voice_client.source, "volume"):
                voice_client.source.volume = self.music_manager.volume

            logger.info(f"Volume inicial ajustado para {self.music_manager.volume * 100:.1f}% com base no volume do usuário.")

            # Determina se o argumento é uma playlist ou música individual
            if "playlist" in query.lower() or "list=" in query:
                logger.info(f"Processando playlist: {query}")
                await process_playlist(ctx, query, self.music_manager, self.ydl_opts, added_by_id=ctx.author.id)
            else:
                logger.info(f"Adicionando música individual: {query}")
                await insert_music(ctx, query, self.music_manager, self.ydl_opts, added_by_id=ctx.author.id)

            # Verifica se há um voice_client antes de acessar is_playing
            if self.music_manager.voice_client and not self.music_manager.voice_client.is_playing():
                logger.info("Iniciando reprodução da próxima música na fila.")
                await self.music_manager.play_next(ctx)

        except Exception as e:
            # Caso ocorra algum erro ao tentar reproduzir a música
            logger.error(f"Erro ao tentar reproduzir música ou playlist: {e}")
            await ctx.send(embed=embed_error("Ocorreu um erro durante a reprodução."))

async def setup(bot, music_manager):
    """
    Adiciona o cog PlayCommand ao bot.
    """
    await bot.add_cog(PlayCommand(bot, music_manager))
