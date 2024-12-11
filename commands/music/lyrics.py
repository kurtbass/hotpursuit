from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_lyrics, embed_error, embed_searching_lyrics
from commands.music.musicsystem.music_system import MusicManager

logger = logging.getLogger(__name__)

class LyricsCommand(commands.Cog):
    """
    Comando para buscar letras da música atual.
    """

    def __init__(self, bot, music_manager: MusicManager):
        """
        Inicializa o comando Lyrics.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="lyrics", aliases=["letra", "lyric", "letras"])
    async def lyrics(self, ctx):
        """
        Comando para buscar letras da música atualmente tocando.
        """
        if not self.music_manager.current_song:
            await ctx.send(embed=embed_error("Nenhuma música está tocando no momento."))
            return

        title = self.music_manager.current_song.get('title', 'Desconhecido')
        logger.info(f"Buscando letras para a música: {title}")

        # Envia a mensagem informando que a letra está sendo pesquisada
        searching_message = await ctx.send(embed=embed_searching_lyrics(title))

        try:
            await self.music_manager.fetch_lyrics(ctx)
            await searching_message.delete()  # Apaga a mensagem de "pesquisando"
        except Exception as e:
            logger.error(f"Erro ao buscar letras: {e}")
            await ctx.send(embed=embed_error("Erro ao buscar letras. Tente novamente."))
            await searching_message.delete()  # Apaga a mensagem de "pesquisando" mesmo em caso de erro

async def setup(bot, music_manager):
    """
    Adiciona o cog LyricsCommand ao bot.
    """
    await bot.add_cog(LyricsCommand(bot, music_manager))
