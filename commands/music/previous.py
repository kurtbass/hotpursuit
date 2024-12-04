import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class PreviousCommand(commands.Cog):
    """
    Comando para voltar e tocar a música anterior na fila.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="previous", aliases=["voltar", "back"])
    async def previous(self, ctx):
        """
        Volta para a música anterior no histórico.
        """
        voice_client = self.music_manager.voice_client

        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ O bot não está conectado a nenhum canal de voz.", 0xFF0000
            ))
            return

        # Recuperar a música anterior do histórico
        previous_song = self.music_manager.get_previous_song()
        if not previous_song:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Não há nenhuma música anterior no histórico.", 0xFF0000
            ))
            return

        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Você precisa estar no mesmo canal de voz do bot para usar este comando.", 0xFF0000
            ))
            return

        try:
            # Salva a música atual no início da fila
            if self.music_manager.current_song:
                self.music_manager.add_to_queue(self.music_manager.current_song)

            # Reproduz a música anterior
            self.music_manager.current_song = previous_song

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(previous_song['stream_url'], **{
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn'
                }),
                volume=self.music_manager.volume
            )

            voice_client.stop()
            voice_client.play(source, after=lambda e: logger.info(f"Música anterior finalizada: {previous_song['title']}"))

            # Formata a duração da música anterior
            duration_formatted = f"{previous_song['duration'] // 60}:{previous_song['duration'] % 60:02d}"

            # Envia a mensagem formatada
            await ctx.send(embed=self.music_manager.create_embed(
                "⏮️ Voltando para a Música Anterior",
                description=(f"**Música:** [{previous_song['title']}]({previous_song['url']})\n"
                             f"**Canal do YouTube:** {previous_song['uploader']}\n"
                             f"**Duração:** {duration_formatted}\n"
                             f"**Adicionado por:** {previous_song['added_by']}"),
                banner=previous_song.get('thumbnail')
            ))
        except Exception as e:
            logger.error(f"Erro ao reproduzir a música anterior: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", "⚠️ Ocorreu um erro ao tentar reproduzir a música anterior.", 0xFF0000
            ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(PreviousCommand(bot, music_manager))
