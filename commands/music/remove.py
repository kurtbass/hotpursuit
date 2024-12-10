import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import (
    embed_dj_error,
    embed_error,
    embed_song_removed,
    embed_queue_empty,
    embed_remove_usage,
)
import logging

logger = logging.getLogger(__name__)

class RemoveCommand(commands.Cog):
    """
    Comando para remover músicas específicas da fila.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="remove", aliases=["remover", "rm"])
    async def remove(self, ctx, *, url: str = None):
        """
        Remove uma música específica da fila com base no link.
        """
        if not self.music_manager.music_queue:
            await ctx.send(embed=embed_queue_empty())
            return

        if not url:
            # Envia uma mensagem explicando como usar o comando
            await ctx.send(embed=embed_remove_usage())
            return

        # Localizar a música na fila pelo URL
        song_index = next(
            (i for i, song in enumerate(self.music_manager.music_queue) if song.get("url") == url),
            None,
        )

        if song_index is None:
            await ctx.send(embed=embed_error(f"Música com o link '{url}' não encontrada na fila."))
            return

        song_to_remove = self.music_manager.music_queue[song_index]

        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == int(song_to_remove.get("added_by")) or
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        try:
            # Remove a música da fila
            removed_song = self.music_manager.music_queue.pop(song_index)

            # Log da remoção
            logger.info(f"Usuário {ctx.author.id} removeu a música: {removed_song['title']}")

            # Envia mensagem de confirmação
            await ctx.send(embed=embed_song_removed(removed_song))

        except Exception as e:
            logger.error(f"Erro ao tentar remover a música: {e}")
            await ctx.send(embed=embed_error("Erro ao remover a música.", str(e)))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(RemoveCommand(bot, music_manager))
