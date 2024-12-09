import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_current_volume, embed_volume_set
from utils.database import set_user_volume, get_user_volume

class VolumeCommand(commands.Cog):
    """
    Comando para ajustar o volume da música tocando.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="volume", aliases=["v", "vol"])
    async def volume(self, ctx, volume: int = None):
        """
        Altera o volume da música atual ou exibe o volume atual.

        :param ctx: Contexto do comando.
        :param volume: Volume desejado (0 a 100). Se não for informado, exibe o volume atual.
        """
        voice_client = self.music_manager.voice_client

        # Verificar se há conexão de voz
        if not voice_client or not voice_client.is_connected():
            await ctx.send(embed=embed_error("bot_not_connected"))
            return

        # Exibir o volume atual caso nenhum valor seja informado
        if volume is None:
            current_volume = self.music_manager.volume * 100
            await ctx.send(embed=embed_current_volume(current_volume))
            return

        # Validar intervalo do volume
        if not 0 <= volume <= 100:
            await ctx.send(embed=embed_error("invalid_volume_range"))
            return

        # Ajustar o volume no player e no gerenciador de música
        decimal_volume = volume / 100  # Converter de 0-100 para 0.0-1.0
        self.music_manager.volume = decimal_volume

        if voice_client.source and hasattr(voice_client.source, "volume"):
            voice_client.source.volume = decimal_volume

        # Salvar o volume no banco de dados como decimal
        set_user_volume(ctx.author.id, decimal_volume)

        # Confirmar ajuste para o usuário
        await ctx.send(embed=embed_volume_set(volume))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(VolumeCommand(bot, music_manager))
