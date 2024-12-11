from asyncio.log import logger
import os
import discord
from discord.ext import commands
from commands.music.musicsystem.embeds import embed_error, embed_now_playing
from commands.music.musicsystem.music_system import MusicManager
from utils.database import get_config, get_user_volume

class PlayLocalCommand(commands.Cog):
    """
    Comando para tocar arquivos de áudio locais.
    Apenas o DONO pode usar este comando.
    """

    def __init__(self, bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="playlocal")
    async def playlocal(self, ctx, *, file_path: str = None):
        """
        Toca um arquivo de áudio local.
        Apenas o DONO pode usar este comando.
        """
        # Verifica se o usuário é o dono do bot
        owner_id = int(get_config("DONO"))
        if ctx.author.id != owner_id:
            await ctx.send(embed=embed_error("Apenas o dono pode usar este comando."))
            return

        # Verifica se o arquivo foi especificado
        if not file_path:
            await ctx.send(embed=embed_error("Você deve especificar o caminho do arquivo."))
            return

        # Verifica se o arquivo existe e é um arquivo de áudio
        if not os.path.isfile(file_path):
            await ctx.send(embed=embed_error("Arquivo não encontrado."))
            return
        if not file_path.lower().endswith((".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a")):
            await ctx.send(embed=embed_error("Formato de arquivo não suportado."))
            return

        try:
            # Conecta o bot ao canal de voz do usuário
            voice_client = await self.music_manager.join_voice_channel(ctx)
            if voice_client is None:
                return

            # Define o volume inicial do usuário
            user_volume = get_user_volume(ctx.author.id)
            self.music_manager.volume = user_volume if user_volume is not None else 1.0
            logger.info(f"Volume inicial ajustado para {self.music_manager.volume * 100:.1f}% com base no volume do usuário.")

            # Define o nome da música como o nome do arquivo
            song_name = os.path.basename(file_path)
            self.music_manager.current_song = {
                "title": song_name,
                "url": None,
                "added_by": ctx.author.id,
                "type": "local"
            }

            # Para qualquer áudio que esteja tocando atualmente
            if voice_client.is_playing():
                voice_client.stop()

            # Configura e toca o arquivo de áudio com volume ajustado
            def after_playing(e):
                if e:
                    logger.error(f"Erro durante a reprodução: {e}")
                else:
                    logger.info("Reprodução concluída.")
                # Atualiza o estado do MusicManager
                self.music_manager.current_song = None
                self.music_manager.voice_client.stop()

            audio_source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(file_path),
                volume=self.music_manager.volume
            )
            voice_client.play(audio_source, after=lambda e: after_playing(e))

            # Envia o embed de "Tocando Agora"
            embed = embed_now_playing(
                {
                    "title": song_name,
                    "url": None,
                    "uploader": "Arquivo Local",
                    "added_by": ctx.author.id,
                },
                ctx.author.voice.channel,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(embed=embed_error("Erro ao tentar reproduzir o arquivo."))
            logger.error(f"Erro ao tentar reproduzir o arquivo: {e}")

async def setup(bot, music_manager):
    """
    Adiciona o cog PlayLocalCommand ao bot.
    """
    await bot.add_cog(PlayLocalCommand(bot, music_manager))
