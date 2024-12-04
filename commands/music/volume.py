import discord
from discord.ext import commands
from utils.database import set_user_volume, get_user_volume  # Funções de banco de dados

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

        # Ajustar o volume no player se possível
        if voice_client.source and hasattr(voice_client.source, "volume"):
            voice_client.source.volume = volume / 100

        # Atualizar o volume no gerenciador de música
        self.music_manager.volume = volume / 100

        # Salvar o volume no banco de dados
        set_user_volume(ctx.author.id, volume)

        # Confirmar ajuste para o usuário
        await ctx.send(embed=discord.Embed(
            title="🔊 Volume Ajustado",
            description=f"O volume foi ajustado para **{volume}%**.",
            color=0xFF8000
        ))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Recupera o volume padrão do usuário ao entrar no canal.
        """
        if member.bot or not after.channel:
            return

        # Recuperar volume salvo para o usuário
        saved_volume = get_user_volume(member.id)
        if saved_volume is not None and self.music_manager.voice_client:
            self.music_manager.volume = saved_volume / 100
            if self.music_manager.voice_client.source and hasattr(self.music_manager.voice_client.source, "volume"):
                self.music_manager.voice_client.source.volume = saved_volume / 100


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(VolumeCommand(bot, music_manager))
