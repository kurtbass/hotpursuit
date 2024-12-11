from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
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

        # Exibir o volume atual caso nenhum valor seja informado
        if volume is None:
            if voice_client and voice_client.is_connected():
                # Exibir o volume atual do bot
                current_volume = int(self.music_manager.volume * 100)
                await ctx.send(embed=embed_current_volume(current_volume))
            else:
                # Exibir o volume salvo no banco de dados
                user_volume = get_user_volume(ctx.author.id)
                current_volume = user_volume if user_volume is not None else 100
                await ctx.send(embed=embed_current_volume(current_volume))
            return

        # Validar intervalo do volume
        if not 0 <= volume <= 100:
            await ctx.send(embed=embed_error("invalid_volume_range"))
            return

        # Ajustar o volume no banco de dados
        set_user_volume(ctx.author.id, volume)  # Salvar como inteiro

        # Ajustar o volume no player e no gerenciador de música, se conectado
        if voice_client and voice_client.is_connected():
            self.music_manager.volume = volume / 100  # Converter para decimal para uso interno
            if voice_client.source and hasattr(voice_client.source, "volume"):
                voice_client.source.volume = self.music_manager.volume

        # Confirmar ajuste para o usuário
        await ctx.send(embed=embed_volume_set(volume))

        
async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(VolumeCommand(bot, music_manager))
