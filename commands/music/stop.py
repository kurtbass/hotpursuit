import discord
import logging
from commands.music.musicsystem.music_system import MusicManager
from utils.database import get_embed_color, get_config
from discord.ext import commands

logger = logging.getLogger(__name__)

class StopMusicCommand(commands.Cog):
    """
    Comando para parar a música e limpar a fila.
    """
    def __init__(self, bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name='stop', aliases=['parar'])
    async def stop(self, ctx):
        # Verificar se o bot está tocando alguma música
        if not self.music_manager.voice_client or not self.music_manager.voice_client.is_playing():
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro",
                "⚠️ Não há nenhuma música tocando no momento.",
                get_embed_color()
            ))
            return

        # Verificar se o usuário está no mesmo canal de voz que o bot
        if not ctx.author.voice or ctx.author.voice.channel != self.music_manager.voice_client.channel:
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro",
                "⚠️ Você precisa estar no mesmo canal de voz que o bot para usar este comando.",
                get_embed_color()
            ))
            return

        # Verificar se o usuário iniciou a sessão ou tem a tag de DJ
        tag_dj_id = get_config("TAG_DJ")
        if not (ctx.author.id == self.music_manager.current_song.get('added_by') or discord.utils.get(ctx.author.roles, id=int(tag_dj_id))):
            await ctx.send(embed=self.music_manager.create_embed(
                "Permissão Negada",
                "⚠️ Apenas quem adicionou a música ou quem tem a tag de DJ pode parar a reprodução.",
                get_embed_color()
            ))
            return

        try:
            if self.music_manager.voice_client and self.music_manager.voice_client.is_playing():
                self.music_manager.voice_client.stop()
                self.music_manager.clear_queue()
                self.music_manager.current_song = None
                await ctx.send(embed=self.music_manager.create_embed(
                    "⏹ Música Parada",
                    "A reprodução foi interrompida e a fila foi limpa.",
                    get_embed_color()
                ))
                await self.music_manager.restore_default_status()
        except Exception as e:
            logger.error(f"Erro ao parar a música: {e}")
            await ctx.send(embed=self.music_manager.create_embed(
                "Erro",
                f"⚠️ Ocorreu um erro ao tentar parar a música: {str(e)}",
                get_embed_color()
            ))

async def setup(bot, music_manager):
    await bot.add_cog(StopMusicCommand(bot, music_manager))
