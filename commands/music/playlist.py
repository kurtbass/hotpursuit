import asyncio
import logging
from discord.ext import commands
from commands.music.musicsystem.embeds import (
    embed_playlist_menu,
    embed_error,
    embed_save_playlist,
    embed_playlist_saved,
    embed_playlist_loaded,
    embed_all_playlists_deleted
)
from utils.database import fetchall, fetchone, execute_query

logger = logging.getLogger(__name__)

class PlaylistCommand(commands.Cog):
    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager
        self.voice_channel = None

    @commands.command(name="playlist", aliases=["pl"])
    async def playlist(self, ctx):
        """
        Menu principal para gerenciamento de playlists.
        """
        await ctx.send(embed=embed_playlist_menu())

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
                await ctx.send(embed=embed_error("invalid_option"))
        except asyncio.TimeoutError:
            await ctx.send(embed=embed_error("timeout"))

    async def save_playlist(self, ctx):
        """
        Salva a playlist atual na base de dados.
        """
        if not self.music_manager.music_queue:
            await ctx.send(embed=embed_error("no_songs_in_queue"))
            return

        await ctx.send(embed=embed_save_playlist())

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            playlist_name = msg.content.strip()

            # Verifica se uma playlist com o mesmo nome já existe
            existing = fetchone("SELECT id FROM playlists WHERE userid = ? AND name = ?", (str(ctx.author.id), playlist_name))
            if existing:
                await ctx.send(embed=embed_error("Você já tem uma playlist com esse nome."))
                return

            # Insere a playlist na tabela playlists
            total_duration = self.music_manager.get_total_duration()
            execute_query(
                "INSERT INTO playlists (userid, name, duration) VALUES (?, ?, ?)",
                (str(ctx.author.id), playlist_name, total_duration)
            )
            playlist_id = fetchone("SELECT id FROM playlists WHERE userid = ? AND name = ?", (str(ctx.author.id), playlist_name))[0]

            # Insere as músicas da fila na tabela playlist_songs
            for song in self.music_manager.music_queue:
                execute_query(
                    "INSERT INTO playlist_songs (playlist_id, title, url, duration, uploader, thumbnail) VALUES (?, ?, ?, ?, ?, ?)",
                    (playlist_id, song['title'], song['url'], song['duration'], song['uploader'], song['thumbnail'])
                )

            await ctx.send(embed=embed_playlist_saved(playlist_name, total_duration, ctx.author))
        except asyncio.TimeoutError:
            await ctx.send(embed=embed_error("timeout"))
        except Exception as e:
            logger.error(f"Erro ao salvar a playlist: {e}")
            await ctx.send(embed=embed_error("save_playlist_error"))

    async def load_playlist(self, ctx):
        """
        Carrega uma playlist do banco de dados.
        """
        playlists = fetchall("SELECT id, name, duration FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=embed_error("no_playlists"))
            return

        description = "\n".join(f"**{i+1}.** {pl[1]}" for i, pl in enumerate(playlists))
        await ctx.send(embed=embed_playlist_menu(description=description))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            playlist_number = int(msg.content.strip())

            if not 1 <= playlist_number <= len(playlists):
                await ctx.send(embed=embed_error("invalid_option"))
                return

            playlist_data = playlists[playlist_number - 1]
            playlist_id, playlist_name, playlist_duration = playlist_data

            songs = fetchall("SELECT title, url, duration, uploader, thumbnail FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
            if not songs:
                await ctx.send(embed=embed_error("empty_playlist", playlist_name))
                return

            for song in songs:
                self.music_manager.add_to_queue({
                    'title': song[0],
                    'url': song[1],
                    'duration': song[2],
                    'uploader': song[3],
                    'thumbnail': song[4],
                    'added_by': ctx.author.mention
                }, ctx.author.id)

            await ctx.send(embed=embed_playlist_loaded(playlist_name, len(songs), playlist_duration, ctx.author))

            # Garantir que o bot esteja conectado ao canal de voz
            if not self.music_manager.voice_client or not self.music_manager.voice_client.is_connected():
                if ctx.author.voice:
                    self.music_manager.voice_client = await ctx.author.voice.channel.connect()
                else:
                    await ctx.send(embed=embed_error("not_in_voice_channel"))
                    return

            # Toca a próxima música se o bot não estiver reproduzindo nada
            if not self.music_manager.voice_client.is_playing():
                await self.music_manager.play_next(ctx)

        except asyncio.TimeoutError:
            await ctx.send(embed=embed_error("timeout"))
        except Exception as e:
            logger.error(f"Erro ao carregar playlist: {e}")
            await ctx.send(embed=embed_error("load_playlist_error", str(e)))

    async def delete_all_playlists(self, ctx):
        """
        Remove todas as playlists do usuário.
        """
        playlists = fetchall("SELECT id FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=embed_error("no_playlists"))
            return

        execute_query("DELETE FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        execute_query("DELETE FROM playlist_songs WHERE playlist_id IN (SELECT id FROM playlists WHERE userid = ?)", (str(ctx.author.id),))

        await ctx.send(embed=embed_all_playlists_deleted())


async def setup(bot, music_manager):
    """
    Adiciona o cog de playlists ao bot.
    """
    await bot.add_cog(PlaylistCommand(bot, music_manager))
