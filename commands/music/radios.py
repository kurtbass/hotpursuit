import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import (
    embed_error,
    embed_radio_menu,
    embed_radio_now_playing,
    embed_radio_stopped
)
from commands.music.musicsystem.music_system import MusicManager
from utils.database import get_user_volume
from colorama import Fore, Style
import discord

logger = logging.getLogger(__name__)

RADIOS = [
    {"name": "Rádio Cidade Vida Real", "stream": "http://stream1.svrdedicado.org:8172/stream", "banner": "https://loskatchorros.com.br/radio/images/logo.png?crc=4021875005"},
    {"name": "Rádio Hunter Master", "stream": "https://live.hunter.fm/master_high", "banner": "https://cdn.hunter.fm/image/thumb/station/master-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Hits Brasil", "stream": "https://live.hunter.fm/hitsbrasil_high", "banner": "https://cdn.hunter.fm/image/thumb/station/hitsbrasil-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Pop", "stream": "https://live.hunter.fm/pop_high", "banner": "https://cdn.hunter.fm/image/thumb/station/pop-third/400x400ht.jpg"},
    {"name": "Rádio Hunter K-pop", "stream": "https://live.hunter.fm/kpop_high", "banner": "https://cdn.hunter.fm/image/thumb/station/kpop-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Sertanejo", "stream": "https://live.hunter.fm/sertanejo_high", "banner": "https://cdn.hunter.fm/image/thumb/station/sertanejo-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Moda Sertaneja", "stream": "https://live.hunter.fm/modasertaneja_high", "banner": "https://cdn.hunter.fm/image/thumb/station/modasertaneja-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Pagode", "stream": "https://live.hunter.fm/pagode_high", "banner": "https://cdn.hunter.fm/image/thumb/station/pagode-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Gospel", "stream": "https://live.hunter.fm/gospel_high", "banner": "https://cdn.hunter.fm/image/thumb/station/gospel-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Pisadinha", "stream": "https://live.hunter.fm/pisadinha_high", "banner": "https://cdn.hunter.fm/image/thumb/station/pisadinha-third/400x400ht.jpg"},
    {"name": "Rádio Hunter MPB", "stream": "https://live.hunter.fm/mpb_high", "banner": "https://cdn.hunter.fm/image/thumb/station/mpb-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Rock", "stream": "https://live.hunter.fm/rock_high", "banner": "https://cdn.hunter.fm/image/thumb/station/rock-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Tropical", "stream": "https://live.hunter.fm/tropical_high", "banner": "https://cdn.hunter.fm/image/thumb/station/tropical-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Lofi", "stream": "https://live.hunter.fm/lofi_high", "banner": "https://cdn.hunter.fm/image/thumb/station/lofi-third/400x400ht.jpg"},
    {"name": "Rádio Hunter Pop2K", "stream": "https://live.hunter.fm/pop2k_high", "banner": "https://cdn.hunter.fm/image/thumb/station/pop2k-third/400x400ht.jpg"},
    {"name": "Rádio Hunter 80s", "stream": "https://live.hunter.fm/80s_high", "banner": "https://cdn.hunter.fm/image/thumb/station/80s-third/400x400ht.jpg"},
    {"name": "Rádio Hunter SMASH!", "stream": "https://live.hunter.fm/smash_high", "banner": "https://cdn.hunter.fm/image/thumb/station/smash-third/400x400ht.jpg"},
]

class RadiosCommand(commands.Cog):
    """
    Comando para exibir um menu de rádios e permitir a reprodução.
    """

    def __init__(self, bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="radios")
    async def radios(self, ctx):
        """
        Exibe o menu de rádios e permite a seleção.
        """
        try:
            # Obtém o menu de rádios do embeds.py
            embed_menu = embed_radio_menu(RADIOS)
            await ctx.send(embed=embed_menu)

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            choice = int(msg.content.strip())

            if 1 <= choice <= len(RADIOS):
                radio = RADIOS[choice - 1]
                await self.play_radio(ctx, radio)
            elif choice == 12:
                await self.stop_radio(ctx)
            else:
                await ctx.send(embed=embed_error("Opção inválida. Por favor, escolha um número válido."))

        except Exception as e:
            logger.error(f"Erro no menu de rádios: {e}")
            await ctx.send(embed=embed_error("Ocorreu um erro ao processar sua escolha."))

    async def play_radio(self, ctx, radio):
        """
        Reproduz a rádio selecionada.
        """
        try:
            # Conecta ao canal de voz
            await self.music_manager.join_voice_channel(ctx)

            # Ajusta o volume
            user_volume = get_user_volume(ctx.author.id)
            self.music_manager.volume = user_volume if user_volume is not None else 1.0
            logger.info(Fore.BLUE + f"Volume ajustado para {self.music_manager.volume * 100:.1f}%" + Style.RESET_ALL)

            # Reproduz a rádio usando o MusicManager
            await self.music_manager.play_radio(radio["name"], radio["stream"], ctx.author.id)

            # Obtém a embed da rádio do embeds.py
            embed = embed_radio_now_playing(radio["name"], radio["stream"], radio["banner"], ctx.author)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(Fore.RED + f"Erro ao reproduzir a rádio {radio['name']}: {e}" + Style.RESET_ALL)
            await ctx.send(embed=embed_error("Ocorreu um erro ao tentar reproduzir a rádio."))

    async def stop_radio(self, ctx):
        """
        Para a reprodução da rádio.
        """
        try:
            if self.music_manager.current_song and self.music_manager.current_song.get("type") == "radio":
                self.music_manager.stop_radio()
                embed = embed_radio_stopped()
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=embed_error("Nenhuma rádio está tocando no momento."))
        except Exception as e:
            logger.error(Fore.RED + f"Erro ao tentar parar a rádio: {e}" + Style.RESET_ALL)
            await ctx.send(embed=embed_error("Ocorreu um erro ao tentar parar a rádio."))


async def setup(bot, music_manager):
    """
    Adiciona o cog RadiosCommand ao bot.
    """
    await bot.add_cog(RadiosCommand(bot, music_manager))
