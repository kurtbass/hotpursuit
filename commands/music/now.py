import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class NowCommand(commands.Cog):
    """
    Comando para exibir informações sobre a música atualmente tocando.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="now", aliases=["agora", "tocandoagora"])
    async def now(self, ctx):
        """
        Exibe informações da música atualmente tocando.

        :param ctx: Contexto do comando.
        """
        # Verifica se há uma música sendo tocada
        if not self.music_manager.current_song:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Não há nenhuma música tocando no momento.", 0xFF0000
            ))
            return

        # Verifica se o usuário está no mesmo canal de voz que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000
            ))
            return

        try:
            # Informações da música atual
            song = self.music_manager.current_song
            duration_formatted = f"{song['duration'] // 60}:{song['duration'] % 60:02d}"
            voice_channel = self.music_manager.voice_client.channel.name if self.music_manager.voice_client else "Desconhecido"

            # Cria e envia o embed com as informações
            embed = self.music_manager.create_embed(
                title="🎶 Tocando Agora",
                description=(f"**Música:** [{song['title']}]({song['url']})\n"
                             f"**Canal do YouTube:** {song['uploader']}\n"
                             f"**Duração:** {duration_formatted}\n"
                             f"**Adicionado por:** {song['added_by']}\n"
                             f"**Canal de Voz:** {voice_channel}"),
                banner=song['thumbnail']
            )
            await ctx.send(embed=embed)
            logger.info("Informações da música atual enviadas com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao exibir informações da música atual: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Ocorreu um erro ao tentar exibir as informações da música atual.", 0xFF0000
            ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(NowCommand(bot, music_manager))
