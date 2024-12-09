import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_dj_error, embed_error, embed_disconnected, embed_permission_denied

class LeaveCommand(commands.Cog):
    """
    Comando para o bot sair do canal de voz.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de saída do canal de voz.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="leave", aliases=["sair", "desconectar", "disconnect", "quit"])
    async def leave(self, ctx):
        """
        Faz o bot sair do canal de voz atual.
        """
        if not self.bot.voice_clients or not any(vc.is_connected() for vc in self.bot.voice_clients):
            await ctx.send(embed=embed_error(
                "Não estou conectado a nenhum canal de voz."
            ))
            return

        # Verifica se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = self.music_manager.dj_role_id
        session_owner_id = self.music_manager.get_session_owner_id()

        if session_owner_id is None and self.music_manager.current_song:
            session_owner_id = self.music_manager.current_song.get('added_by', None)

        try:
            session_owner_id = int(session_owner_id) if session_owner_id else None
        except (TypeError, ValueError):
            session_owner_id = None

        if not (ctx.author.id == session_owner_id or 
                discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=embed_dj_error())
            return

        for vc in self.bot.voice_clients:
            if vc.channel == ctx.author.voice.channel:
                # Parar qualquer música sendo reproduzida antes de sair
                if self.music_manager.is_playing():
                    await self.music_manager.stop_music(ctx)

                await vc.disconnect()
                self.music_manager.voice_client = None  # Resetar o cliente de voz no gerenciador de música
                await ctx.send(embed=embed_disconnected(vc.channel.name))
                return

        await ctx.send(embed=embed_error(
            "Você não está no mesmo canal de voz que eu."
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(LeaveCommand(bot, music_manager))
