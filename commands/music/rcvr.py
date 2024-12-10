import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_now_playing
from commands.music.musicsystem.voice_utils import join_voice_channel
from utils.database import get_user_volume
import discord

logger = logging.getLogger(__name__)

class RcvrCommand(commands.Cog):
    """
    Comando para reproduzir um stream de rádio predefinido.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando Rcvr.
        """
        self.bot = bot
        self.music_manager = music_manager
        self.stream_url = "http://stream1.svrdedicado.org:8172/stream"  # URL do stream predefinido
        self.banner_url = "https://loskatchorros.com.br/radio/images/logo.png?crc=4021875005"  # URL do banner

    @commands.command(name="rcvr")
    async def rcvr(self, ctx):
        """
        Reproduz um stream de rádio predefinido.
        :param ctx: Contexto do comando.
        """
        try:
            # Conecta o bot ao canal de voz do usuário
            voice_client = await join_voice_channel(ctx, self.music_manager)
            if voice_client is None:
                return

            # Ajusta o volume da sessão com base no volume salvo na database
            user_volume = get_user_volume(ctx.author.id)
            self.music_manager.volume = user_volume if user_volume is not None else 1.0

            if voice_client.source and hasattr(voice_client.source, "volume"):
                voice_client.source.volume = self.music_manager.volume

            logger.info(f"Volume inicial ajustado para {self.music_manager.volume * 100:.1f}% com base no volume do usuário.")

            # Configurar e tocar o stream
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(self.stream_url, options="-vn"),
                volume=self.music_manager.volume
            )

            if voice_client.is_playing():
                voice_client.stop()

            voice_client.play(source, after=lambda e: logger.info(f"Stream encerrado: {e}" if e else "Stream concluído."))

            # Criar embed para exibir o stream
            embed = embed_now_playing(
                {"title": ":: RÁDIO CIDADE VIDA REAL ::", "url": self.stream_url, "uploader": "Transmissão ao Vivo", "added_by": ctx.author.id},
                ctx.author.voice.channel
            )
            embed.set_image(url=self.banner_url)  # Adiciona o banner ao embed
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao tentar reproduzir o stream: {e}")
            await ctx.send(embed=embed_error("Ocorreu um erro ao tentar reproduzir o stream."))

async def setup(bot, music_manager):
    """
    Adiciona o cog RcvrCommand ao bot.
    """
    await bot.add_cog(RcvrCommand(bot, music_manager))
