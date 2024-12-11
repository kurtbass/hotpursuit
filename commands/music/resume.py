from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_dj_error, embed_error, embed_music_resumed, embed_no_music_paused, embed_permission_denied, embed_user_not_in_same_channel
import logging

logger = logging.getLogger(__name__)

class ResumeCommand(commands.Cog):
    """
    Comando para retomar a reprodução de música pausada.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="resume", aliases=["resumir", "retomar"])
    async def resume(self, ctx):
        """
        Retoma a reprodução da música pausada.

        :param ctx: Contexto do comando.
        """
        voice_client = self.music_manager.voice_client

        # Verificar conexão com canal de voz
        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=embed_error("bot_not_connected"))
            return

        # Verificar se o usuário está no mesmo canal
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=embed_user_not_in_same_channel())
            return

        # Verificar se há música pausada
        if not voice_client.is_paused():
            await ctx.send(embed=embed_no_music_paused())
            return

        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        if not (ctx.author.id == int(self.music_manager.current_song.get('added_by')) or 
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        try:
            # Retomar a música
            voice_client.resume()
            self.music_manager.current_song['status'] = 'playing'  # Atualizar o estado da música no MusicManager
            await ctx.send(embed=embed_music_resumed())
            logger.info("Música retomada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao tentar retomar a música: {e}")
            await ctx.send(embed=embed_error("resume_error", str(e)))

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(ResumeCommand(bot, music_manager))
