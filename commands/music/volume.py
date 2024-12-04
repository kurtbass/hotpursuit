import discord
from discord.ext import commands
from utils.database import set_user_volume  # Função para salvar volume no banco de dados

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
        # Verificar se há conexão de voz
        if not self.music_manager.voice_client or not self.music_manager.voice_client.is_connected():
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⚠️ O bot não está conectado a nenhum canal de voz.",
                color=0xFF0000
            ))
            return

        # Exibir o volume atual caso nenhum valor seja informado
        if volume is None:
            current_volume = int(self.music_manager.volume * 100)
            await ctx.send(embed=discord.Embed(
                title="🔊 Volume Atual",
                description=f"O volume atual é **{current_volume}%**.",
                color=0xFF8000
            ))
            return

        # Validar intervalo do volume
        if volume < 0 or volume > 100:
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⚠️ O volume deve ser entre 0 e 100.",
                color=0xFF0000
            ))
            return

        # Verificar se o ajuste de volume é suportado
        if not self.music_manager.voice_client.source or not hasattr(self.music_manager.voice_client.source, "volume"):
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⚠️ O ajuste de volume não é suportado para a fonte atual.",
                color=0xFF0000
            ))
            return

        # Ajustar o volume no player
        self.music_manager.voice_client.source.volume = volume / 100
        self.music_manager.volume = volume / 100

        # Salvar o volume no banco de dados para o usuário
        set_user_volume(ctx.author.id, volume)

        # Confirmar ajuste para o usuário
        await ctx.send(embed=discord.Embed(
            title="🔊 Volume Ajustado",
            description=f"O volume foi ajustado para **{volume}%**.",
            color=0xFF8000
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(VolumeCommand(bot, music_manager))
