from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_shuffle_success, embed_shuffle_error_no_songs, embed_dj_error

class ShuffleCommand(commands.Cog):
    """
    Comando para embaralhar a fila de músicas.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="shuffle", aliases=["embaralhar"])
    async def shuffle(self, ctx):
        """
        Embaralha a fila de músicas.
        """
        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == int(self.music_manager.get_session_owner_id()) or
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        # Verifica se há músicas suficientes para embaralhar
        if len(self.music_manager.music_queue) < 2:
            await ctx.send(embed=embed_shuffle_error_no_songs())
            return

        # Embaralha a fila
        self.music_manager.shuffle_queue()

        # Feedback ao usuário
        await ctx.send(embed=embed_shuffle_success())

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(ShuffleCommand(bot, music_manager))
