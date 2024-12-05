from utils.database import get_embed_color
import discord
from discord.ext import commands
import logging
from utils.database import get_config
from commands.music.musicsystem.music_system import MusicManager

logger = logging.getLogger(__name__)

class PauseCommand(commands.Cog):
    """
    Comando para pausar a reprodução de música.
    """

    def __init__(self, bot, music_manager: MusicManager):
        """
        Inicializa o comando de pausa.

        :param bot: O bot do Discord.
        :param music_manager: Instância de MusicManager.
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
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", get_embed_color()
            ))
            return

        # Verifica se o usuário está no mesmo canal do bot
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", get_embed_color()
            ))
            return

        # Verifica se há uma música tocando
        if not voice_client.is_playing():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Nenhuma música está tocando para pausar.", get_embed_color()
            ))
            return

        try:
            # Pausa a música
            voice_client.pause()

            # Verifica se o estado do player mudou para pausado
            if not voice_client.is_playing():
                current_song = self.music_manager.current_song
                song_title = current_song.get('title', 'Desconhecida') if current_song else 'Desconhecida'

                # Envia mensagem de confirmação com thumbnail (se disponível)
                await ctx.send(embed=self.music_manager.create_embed(
                    "Música Pausada",
                    f"⏸️ A música **{song_title}** foi pausada.",
                    get_embed_color(),
                    thumbnail=current_song.get('thumbnail') if current_song else None
                ))
                logger.info(f"Música pausada com sucesso: {song_title}")

        except Exception as e:
            # Ignora o erro e verifica se o estado mudou para pausado
            if not voice_client.is_playing():
                current_song = self.music_manager.current_song
                song_title = current_song.get('title', 'Desconhecida') if current_song else 'Desconhecida'

                # Envia mensagem de confirmação
                await ctx.send(embed=self.music_manager.create_embed(
                    "Música Pausada",
                    f"⏸️ A música **{song_title}** foi pausada (após ignorar o erro).\n{get_config('LEMA')}",
                    get_embed_color(),
                    thumbnail=current_song.get('thumbnail') if current_song else None
                ))
                logger.warning(f"Erro ignorado ao pausar a música, mas o estado foi alterado: {e}")
            else:
                logger.error(f"Erro ao tentar pausar a música: {e}")
                await ctx.send(embed=self.music_manager.create_embed(
                    "Erro", f"⚠️ Ocorreu um erro ao tentar pausar a música: {str(e)}", get_embed_color()
                ))


async def setup(bot, music_manager: MusicManager):
    """
    Adiciona o comando de pausa ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PauseCommand(bot, music_manager))
