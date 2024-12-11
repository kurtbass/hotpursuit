import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_play_usage
from commands.music.musicsystem.music_system import MusicManager
from commands.music.musicsystem.playlists import process_playlist
from commands.music.musicsystem.ydl_opts import YDL_OPTS
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
        self.ydl_opts = YDL_OPTS  # Certifique-se de definir corretamente aqui

    @commands.command(name="play", aliases=["p", "tocar"])
    async def play(self, ctx, *, query: str = None):
        if not query:
            await ctx.send(embed=embed_play_usage())
            return

        try:
            voice_client = await self.music_manager.join_voice_channel(ctx)
            if voice_client is None:
                return

            # Configura volume inicial
            user_volume = get_user_volume(ctx.author.id)
            self.music_manager.volume = user_volume if user_volume is not None else 1.0
            if voice_client.source and hasattr(voice_client.source, "volume"):
                voice_client.source.volume = self.music_manager.volume

            logger.info(f"Volume ajustado para {self.music_manager.volume * 100:.1f}%.")

            # Determina se é playlist ou música individual
            if "playlist" in query.lower() or "list=" in query:
                logger.info(f"Processando playlist: {query}")
                await process_playlist(ctx, query, self.music_manager, added_by_id=ctx.author.id)
            else:
                logger.info(f"Adicionando música: {query}")
                await self.music_manager.insert_music(ctx, query, self.ydl_opts, added_by_id=ctx.author.id)

            # Toca próxima música se não estiver tocando
            if not self.music_manager.voice_client.is_playing():
                await self.music_manager.play_next(ctx)

        except Exception as e:
            logger.error(f"Erro ao tentar reproduzir música ou playlist: {e}")
            await ctx.send(embed=embed_error("Erro ao tentar reproduzir música ou playlist."))


async def setup(bot, music_manager):
    """
    Adiciona o cog PlayCommand ao bot.
    """
    await bot.add_cog(PlayCommand(bot, music_manager))
