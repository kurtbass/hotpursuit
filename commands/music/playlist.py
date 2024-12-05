import discord
from discord.ext import commands
from utils.database import get_config, execute_query, fetchall, fetchone, get_user_volume
from yt_dlp import YoutubeDL
import asyncio
import logging

logger = logging.getLogger(__name__)

class PlaylistCommand(commands.Cog):
    """
    Comando para gerenciar playlists de usuários.
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    @commands.command(name="playlist", aliases=["pl"])
    async def playlist(self, ctx):
        """
        Gerencia playlists do usuário.
        """
        embed = discord.Embed(
            title="🎶 Gerenciamento de Playlists",
            description=(
                "1️⃣ **Salvar playlist atual**\n"
                "2️⃣ **Carregar uma playlist**\n"
                "3️⃣ **Apagar uma playlist**\n"
                "4️⃣ **Apagar todas as suas playlists**\n\n"
                "Digite o número referente à opção desejada."
            ),
            color=0xFF8000
        )
        embed.set_footer(text=get_config("LEMA"))
        await ctx.send(embed=embed)

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            option = int(msg.content.strip())

            if option == 1:
                await self.save_playlist(ctx)
            elif option == 2:
                await self.load_playlist(ctx)
            elif option == 3:
                await self.delete_playlist(ctx)
            elif option == 4:
                await self.delete_all_playlists(ctx)
            else:
                await ctx.send(embed=discord.Embed(
                    title="Erro",
                    description="⚠️ Opção inválida. Por favor, tente novamente.",
                    color=0xFF0000
                ).set_footer(text=get_config("LEMA")))
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⏳ Tempo limite excedido. Por favor, tente novamente.",
                color=0xFF0000
            ).set_footer(text=get_config("LEMA")))

    async def load_playlist(self, ctx):
        """
        Lista e carrega uma playlist do usuário.
        """
        playlists = fetchall("SELECT id, name, duration FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⚠️ Você não tem playlists salvas.",
                color=0xFF0000
            ).set_footer(text=get_config("LEMA")))
            return

        description = "\n".join(f"**{i+1}.** {pl[1]} | ⏱️ {pl[2]}" for i, pl in enumerate(playlists))
        embed = discord.Embed(
            title="🎶 Suas Playlists",
            description=f"{description}\n\nDigite o número da playlist que deseja carregar.",
            color=0xFF8000
        )
        embed.set_footer(text=get_config("LEMA"))
        await ctx.send(embed=embed)

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            playlist_number = int(msg.content.strip())

            if not 1 <= playlist_number <= len(playlists):
                await ctx.send(embed=discord.Embed(
                    title="Erro",
                    description="⚠️ Número inválido. Por favor, tente novamente.",
                    color=0xFF0000
                ).set_footer(text=get_config("LEMA")))
                return

            playlist_id = playlists[playlist_number - 1][0]
            playlist_data = fetchone("SELECT links FROM playlists WHERE id = ?", (playlist_id,))
            if playlist_data:
                links = playlist_data[0].split(",")
                self.music_manager.clear_queue()

                if ctx.author.voice:
                    if not self.music_manager.voice_client or not self.music_manager.voice_client.is_connected():
                        self.music_manager.voice_client = await ctx.author.voice.channel.connect()

                    user_volume = get_user_volume(ctx.author.id)
                    self.music_manager.volume = user_volume if user_volume is not None else 1.0

                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'ignoreerrors': True  # Ignorar automaticamente vídeos problemáticos
                    }

                    with YoutubeDL(ydl_opts) as ydl:
                        for link in links:
                            try:
                                info = ydl.extract_info(link, download=False)
                                if info:
                                    song = {
                                        'title': info.get('title', 'Desconhecido'),
                                        'url': link,
                                        'duration': info.get('duration', 0),
                                        'stream_url': info.get('url', None),
                                        'thumbnail': info.get('thumbnail', None),
                                        'added_by': ctx.author.display_name
                                    }
                                    self.music_manager.add_to_queue(song)
                            except Exception as e:
                                logger.error(f"Erro ao carregar vídeo: {link} - {e}")
                                await ctx.send(embed=discord.Embed(
                                    title="Erro",
                                    description=f"⚠️ Não foi possível carregar o vídeo: {link}. Ignorando...",
                                    color=0xFF0000
                                ))
                            await asyncio.sleep(0.1)

                    await ctx.send(embed=discord.Embed(
                        title="🎶 Playlist Carregada",
                        description=f"Playlist **{playlists[playlist_number - 1][1]}** carregada com sucesso!",
                        color=0x00FF00
                    ).set_footer(text=get_config("LEMA")))
                else:
                    await ctx.send(embed=discord.Embed(
                        title="Erro",
                        description="⚠️ Você precisa estar em um canal de voz para carregar a playlist.",
                        color=0xFF0000
                    ).set_footer(text=get_config("LEMA")))
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⏳ Tempo limite excedido. Por favor, tente novamente.",
                color=0xFF0000
            ).set_footer(text=get_config("LEMA")))

    async def delete_all_playlists(self, ctx):
        """
        Apaga todas as playlists do usuário.
        """
        playlists = fetchall("SELECT id FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=discord.Embed(
                title="Erro",
                description="⚠️ Você não tem playlists salvas.",
                color=0xFF0000
            ).set_footer(text=get_config("LEMA")))
            return

        execute_query("DELETE FROM playlists WHERE userid = ?", (str(ctx.author.id),))

        await ctx.send(embed=discord.Embed(
            title="🎉 Todas as Playlists Apagadas",
            description="Todas as suas playlists foram apagadas com sucesso.",
            color=0x00FF00
        ).set_footer(text=get_config("LEMA")))


async def setup(bot, music_manager):
    await bot.add_cog(PlaylistCommand(bot, music_manager))
