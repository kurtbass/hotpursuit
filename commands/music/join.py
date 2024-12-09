import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import (
    embed_already_being_used_only_owner_can_move,
    embed_error,
    embed_connected,
    embed_need_to_be_connected_in_voice_channel
)

class JoinCommand(commands.Cog):
    """
    Comando para o bot entrar ou se mover para outro canal de voz.
    """

    def __init__(self, bot, music_manager):
        """
        Inicializa o comando de entrada no canal de voz.
        """
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="join", aliases=["entrar", "enter", "connect", "conectar"])
    async def join(self, ctx):
        """
        Faz o bot entrar ou se mover para o canal de voz do usuário.
        """
        if ctx.author.voice is None:
            await ctx.send(embed=embed_need_to_be_connected_in_voice_channel())
            return

        user_channel = ctx.author.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if bot_voice_client:
            # O bot já está conectado a um canal
            current_channel = bot_voice_client.channel

            if self.music_manager.is_playing():
                # O bot está tocando música
                session_owner_id = self.music_manager.get_session_owner_id()

                if session_owner_id is None:
                    if self.music_manager.current_song:
                        session_owner_id = self.music_manager.current_song.get('added_by', None)

                try:
                    session_owner_id = int(session_owner_id)  # Garantir que o ID seja um número inteiro
                except (TypeError, ValueError):
                    session_owner_id = None

                if session_owner_id is None:
                    await ctx.send(embed=embed_error(
                        "Erro: Não foi possível determinar o dono da sessão."
                    ))
                    return

                if session_owner_id == ctx.author.id:
                    # O dono da sessão solicitou o movimento
                    await bot_voice_client.move_to(user_channel)
                    self.music_manager.voice_channel = user_channel  # Atualiza o canal de voz no gerenciador
                    self.music_manager.voice_client = bot_voice_client  # Atualiza o cliente de voz no gerenciador
                    await ctx.send(embed=embed_connected(user_channel.name))
                else:
                    # Outro usuário tentou mover o bot enquanto ele está tocando
                    await ctx.send(embed=embed_already_being_used_only_owner_can_move(current_channel))
            else:
                # O bot não está tocando música, mover para o canal solicitado
                await bot_voice_client.move_to(user_channel)
                self.music_manager.voice_channel = user_channel  # Atualiza o canal de voz no gerenciador
                self.music_manager.voice_client = bot_voice_client  # Atualiza o cliente de voz no gerenciador
                await ctx.send(embed=embed_connected(user_channel.name))
        else:
            # O bot não está conectado a nenhum canal, conectar ao canal do usuário
            self.music_manager.voice_channel = user_channel  # Atualiza o canal de voz no gerenciador
            voice_client = await user_channel.connect()
            self.music_manager.voice_client = voice_client  # Atualiza o cliente de voz no gerenciador
            await ctx.send(embed=embed_connected(user_channel.name))

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    await bot.add_cog(JoinCommand(bot, music_manager))
