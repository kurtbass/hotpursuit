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
        Passa o bot e o MusicManager que gerencia as músicas do sistema.
        """
        self.bot = bot
        self.music_manager = music_manager  # Armazenando a instância do MusicManager

    @commands.command(name="pause", aliases=["pausar"])  # Definindo o comando 'pause' com alias 'pausar'
    async def pause(self, ctx):
        """
        Pausa a música atual.

        :param ctx: Contexto do comando.
        """
        voice_client = self.music_manager.voice_client  # Obtém o voice client da música manager

        if voice_client is None or not voice_client.is_connected():
            # Verifica se o bot não está no canal de voz
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", 0xFF0000  # Cor do erro
            ))
            return  # Retorna se o bot não estiver conectado a um canal de voz

        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            # Verifica se o usuário está no mesmo canal de voz do bot
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000  # Cor do erro
            ))
            return  # Retorna se o usuário não estiver no mesmo canal

        if not voice_client.is_playing():
            # Verifica se o bot está tocando uma música
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Nenhuma música está tocando para pausar.", 0xFF0000  # Cor do erro
            ))
            return  # Retorna se não estiver tocando música

        try:
            voice_client.pause()  # Pausa a música
            await ctx.send(embed=self.music_manager.create_embed(
                "Música Pausada", f"⏸️ A música atual foi pausada. {get_config('LEMA')}", 0xFF8000  # Cor do sucesso
            ))
            logger.info("Música pausada com sucesso.")
        except Exception as e:
            # Log de erro e envio de mensagem caso algo dê errado
            logger.error(f"Erro ao tentar pausar a música: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", f"⚠️ Ocorreu um erro ao tentar pausar a música. {str(e)}", 0xFF0000  # Cor do erro
            ))


async def setup(bot, music_manager):
    """
    Adiciona o comando de pausa ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PauseCommand(bot, music_manager))  # Adiciona o cog ao bot
