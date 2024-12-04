import discord
from discord.ext import commands
import logging

from utils.config import get_config

logger = logging.getLogger(__name__)

class PauseCommand(commands.Cog):
    """
    Comando para pausar a reprodução de música.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de pausa.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="pause", aliases=["pausar"])
    async def pause(self, ctx):
        """
        Pausa a música atual.

        :param ctx: Contexto do comando.
        """
        voice_client = self.music_manager.voice_client

        # Verifica se o bot está conectado a um canal de voz
        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", 0xFF0000
            ))
            return

        # Verifica se o usuário está no mesmo canal do bot
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000
            ))
            return

        # Verifica se há uma música tocando
        if not voice_client.is_playing():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Nenhuma música está tocando para pausar.", 0xFF0000
            ))
            return

        try:
            # Pausa a música e atualiza o estado no MusicManager
            voice_client.pause()
            current_song = self.music_manager.current_song
            song_title = current_song.get('title', 'Desconhecida') if current_song else 'Desconhecida'

            # Envia mensagem de confirmação
            await ctx.send(embed=self.music_manager.create_embed(
                "Música Pausada",
                f"⏸️ A música **{song_title}** foi pausada.\n{get_config('LEMA')}",
                0xFF8000
            ))
            logger.info(f"Música pausada com sucesso: {song_title}")

        except Exception as e:
            logger.error(f"Erro ao tentar pausar a música: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", f"⚠️ Ocorreu um erro ao tentar pausar a música: {str(e)}", 0xFF0000
            ))


async def setup(bot, music_manager):
    """
    Adiciona o comando de pausa ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PauseCommand(bot, music_manager))
