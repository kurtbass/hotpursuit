from asyncio.log import logger
import logging
import discord
from discord.ext import commands  # Importando a biblioteca de comandos do discord
from commands.music.musicsystem.insert import insert_music  # Importando a função que insere a música na fila
from commands.music.musicsystem.music_system import MusicManager  # Importando a classe MusicManager que gerencia a música
from commands.music.musicsystem.playlists import process_playlist  # Função para processar playlists
from commands.music.musicsystem.voice_utils import join_voice_channel  # Função para conectar ao canal de voz
from commands.music.musicsystem.play_utils import play_next  # Função para tocar a próxima música
from utils.config import get_config  # Importando as configurações centralizadas
from commands.music.musicsystem.ydl_opts import YDL_OPTS  # Opções para o youtube-dl (download de música)
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS  # Opções para o ffmpeg (processamento de áudio)


class PlayCommand(commands.Cog):  # Definindo a classe PlayCommand que contém o comando 'play'
    def __init__(self, bot, music_manager: MusicManager):
        """
        Inicializa o comando de música.
        Passa o bot e o MusicManager que gerencia as músicas do sistema.
        """
        self.bot = bot  # Armazenando a instância do bot
        self.music_manager = music_manager  # Armazenando a instância do MusicManager
        self.ydl_opts = YDL_OPTS  # Definindo as opções para o youtube-dl
        self.ffmpeg_options = FFMPEG_OPTIONS  # Definindo as opções para o ffmpeg

    @commands.command(name="play", aliases=["p", "tocar"])  # Definindo o comando play e seus aliases
    async def play(self, ctx, *, query: str = None):
        """
        Comando play que adiciona uma música à fila e começa a reprodução.
        Se o usuário não fornecer um argumento, exibe uma mensagem com o uso correto.
        """
        if not query:
            # Se o usuário não forneceu um link ou nome de música, envia uma mensagem explicando o uso do comando.
            await ctx.send(embed=self.music_manager.create_embed(
                "Uso do Comando play",  # Título da mensagem
                "⚠️ **Uso do Comando play** ⚠️\n"
                f"Para usar o comando `{get_config('PREFIXO')}play`, forneça o **link** da música, o **nome da música**, ou o **link de uma playlist** do YouTube.\n\n"
                "**Exemplos:**\n"
                f"`{get_config('PREFIXO')}play https://youtube.com/watch?v=xxxxxx`\n"
                f"`{get_config('PREFIXO')}play Bohemian Rhapsody`\n"
                f"`{get_config('PREFIXO')}play https://youtube.com/playlist?list=xxxxxx`"
                , 0xFF8000  # Cor do embed
            ))
            return  # Retorna se não houver nenhum argumento de música ou playlist fornecido

        try:
            # Conectar ao canal de voz do usuário
            voice_client = await join_voice_channel(ctx, self.music_manager)
            if voice_client is None:
                return  # Retorna se não conseguiu conectar ao canal de voz

            # Verifica se o comando refere-se a uma playlist ou música individual
            if 'playlist' in query:
                # Processa a playlist se for o caso
                await process_playlist(ctx, query, self.music_manager, self.ydl_opts)
            else:
                # Insere a música na fila se for uma música individual
                await insert_music(ctx, query, self.music_manager, self.ydl_opts)

            # Se o bot não estiver tocando, começa a reprodução da próxima música
            if not self.music_manager.voice_client.is_playing():
                await play_next(self.music_manager, self.bot)

        except Exception as e:
            # Caso ocorra algum erro ao tentar reproduzir a música
            logger.error(f"Erro ao tentar reproduzir música: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro", f"⚠️ Ocorreu um erro ao tentar tocar a música.\n{str(e)}", 0xFF0000  # Cor do erro
            ))

async def setup(bot, music_manager):
    """
    Adiciona o cog ao bot.

    :param bot: O bot do Discord.
    :param music_manager: O gerenciador de música compartilhado.
    """
    # Adiciona o PlayCommand (cog) ao bot
    await bot.add_cog(PlayCommand(bot, music_manager))
