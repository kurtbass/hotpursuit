import asyncio
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_skip, embed_queue_empty
import logging

logger = logging.getLogger(__name__)

class SkipCommand(commands.Cog):
    """
    Comando para pular a música atual.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager  # Gerenciador centralizado de músicas

    @commands.command(name="skip", aliases=["pular", "s"])
    async def skip(self, ctx):
        """
        Pula a música atualmente sendo tocada e avança para a próxima na fila.
        """
        voice_client = self.music_manager.voice_client

        if voice_client is None or not voice_client.is_connected():
            await ctx.send(embed=embed_error("bot_not_connected"))
            return

        if not voice_client.is_playing():
            await ctx.send(embed=embed_error("no_music_playing"))
            return

        try:
            # Para a música atual antes de avançar
            voice_client.stop()

            # Pular para a próxima música
            next_song = self.music_manager.get_next_song()
            if next_song:
                self.music_manager.save_current_to_history()  # Salvar a música atual no histórico
                self.music_manager.set_current_song(next_song)  # Atualizar a música atual

                # Resolver `stream_url` caso ainda não esteja resolvido
                self.music_manager.resolve_stream_url(next_song)

                # Configurar e tocar a próxima música
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(next_song['stream_url'], **{
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn'
                    }),
                    volume=self.music_manager.volume  # Ajustar volume atual
                )

                voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.music_manager.play_next(ctx), ctx.bot.loop
                ))

                # Informar sobre a próxima música
                await ctx.send(embed=embed_skip(next_song))
            else:
                # Fila vazia
                if self.music_manager.current_song:
                    self.music_manager.save_current_to_history()  # Salvar música atual no histórico
                    self.music_manager.current_song = None
                await ctx.send(embed=embed_queue_empty())

        except Exception as e:
            logger.error(f"Erro ao tentar pular para a próxima música: {e}")
            await ctx.send(embed=embed_error("skip_error", str(e)))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(SkipCommand(bot, music_manager))
