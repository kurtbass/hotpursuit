from utils.database import get_embed_color
import asyncio
from discord.ext import commands
from commands.music.musicsystem.playlists import process_playlist
from commands.music.musicsystem.ydl_opts import YDL_OPTS
from utils.database import get_config, fetchall, fetchone, execute_query, get_user_volume
import discord
import logging

logger = logging.getLogger(__name__)


class PlaylistCommand(commands.Cog):
    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music_manager = music_manager

    def create_embed(self, title, description, color=get_embed_color()):
        """
        Cria uma mensagem embed personalizada.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=get_config("LEMA"))
        return embed

    @commands.command(name="playlist", aliases=["pl"])
    async def playlist(self, ctx):
        """
        Menu principal para gerenciamento de playlists.
        """
        embed = self.create_embed(
            "🎶 Gerenciamento de Playlists",
            "1️⃣ **Salvar playlist atual**\n"
            "2️⃣ **Carregar uma playlist**\n"
            "3️⃣ **Apagar uma playlist**\n"
            "4️⃣ **Apagar todas as suas playlists**\n\n"
            "Digite o número referente à opção desejada."
        )
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
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Opção inválida. Por favor, tente novamente.", get_embed_color()
                ))
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed(
                "Erro", "⏳ Tempo limite excedido. Por favor, tente novamente.", get_embed_color()
            ))

    async def save_playlist(self, ctx):
        """
        Salva a playlist atual na base de dados.
        """
        if not self.music_manager.music_queue:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Não há músicas na fila para salvar.", get_embed_color()
            ))
            return

        await ctx.send(embed=self.create_embed(
            "🎶 Salvar Playlist",
            "Digite o nome da sua playlist:"
        ))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            playlist_name = msg.content.strip()

            # Verifica se uma playlist com o mesmo nome já existe
            existing = fetchone("SELECT id FROM playlists WHERE userid = ? AND name = ?", (str(ctx.author.id), playlist_name))
            if existing:
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Você já tem uma playlist com esse nome. Escolha outro nome.", get_embed_color()
                ))
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

            await ctx.send(embed=self.create_embed(
                "🎉 Playlist Salva",
                f"Playlist salva como **{playlist_name}**.\n"
                f"**Duração Total:** {total_duration // 3600}:"
                f"{(total_duration % 3600) // 60:02}:"
                f"{total_duration % 60:02}\n"
                f"Criada por: {ctx.author.mention}",
                get_embed_color()
            ))
        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed(
                "Erro", "⏳ Tempo limite excedido. Por favor, tente novamente.", get_embed_color()
            ))
        except Exception as e:
            logger.error(f"Erro ao salvar a playlist: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Ocorreu um erro ao salvar a playlist. Verifique os logs para mais detalhes.", get_embed_color()
            ))

    async def load_playlist(self, ctx):
        """
        Carrega uma playlist do banco de dados.
        """
        playlists = fetchall("SELECT id, name, duration FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Você não tem playlists salvas.", get_embed_color()
            ))
            return

        description = "\n".join(f"**{i+1}.** {pl[1]}" for i, pl in enumerate(playlists))
        embed = self.create_embed(
            "🎶 Suas Playlists",
            f"{description}\n\nDigite o número da playlist que deseja carregar."
        )
        await ctx.send(embed=embed)

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            playlist_number = int(msg.content.strip())

            if not 1 <= playlist_number <= len(playlists):
                await ctx.send(embed=self.create_embed(
                    "Erro", "⚠️ Número inválido. Por favor, tente novamente.", get_embed_color()
                ))
                return

            playlist_data = playlists[playlist_number - 1]
            playlist_id, playlist_name, playlist_duration = playlist_data

            songs = fetchall("SELECT title, url, duration, uploader, thumbnail FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
            if not songs:
                await ctx.send(embed=self.create_embed(
                    "Erro", f"⚠️ A playlist **{playlist_name}** está vazia.", get_embed_color()
                ))
                return

            for song in songs:
                self.music_manager.add_to_queue({
                    'title': song[0],
                    'url': song[1],
                    'duration': song[2],
                    'uploader': song[3],
                    'thumbnail': song[4],
                    'added_by': ctx.author.display_name
                })

            await ctx.send(embed=self.create_embed(
                "🎶 Playlist Adicionada à Fila",
                f"**Título:** {playlist_name}\n"
                f"**Quantidade de Músicas:** {len(songs)}\n"
                f"**Duração Total:** {playlist_duration // 3600}:"
                f"{(playlist_duration % 3600) // 60:02}:"
                f"{playlist_duration % 60:02}\n"
                f"**Adicionada por:** {ctx.author.mention}",
                get_embed_color()
            ))

            # Garantir que o bot esteja conectado ao canal de voz
            if not self.music_manager.voice_client or not self.music_manager.voice_client.is_connected():
                if ctx.author.voice:
                    self.music_manager.voice_client = await ctx.author.voice.channel.connect()
                else:
                    await ctx.send(embed=self.create_embed(
                        "Erro", "⚠️ Você precisa estar em um canal de voz para carregar a playlist.", get_embed_color()
                    ))
                    return

            # Toca a próxima música se o bot não estiver reproduzindo nada
            if not self.music_manager.voice_client.is_playing():
                await self.music_manager.play_next(ctx)

        except asyncio.TimeoutError:
            await ctx.send(embed=self.create_embed(
                "Erro", "⏳ Tempo limite excedido. Por favor, tente novamente.", get_embed_color()
            ))
        except Exception as e:
            logger.error(f"Erro ao carregar playlist: {e}")
            await ctx.send(embed=self.create_embed(
                "Erro", f"⚠️ Ocorreu um erro ao carregar a playlist: {str(e)}", get_embed_color()
            ))

    async def delete_all_playlists(self, ctx):
        """
        Remove todas as playlists do usuário.
        """
        playlists = fetchall("SELECT id FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        if not playlists:
            await ctx.send(embed=self.create_embed(
                "Erro", "⚠️ Você não tem playlists salvas.", get_embed_color()
            ))
            return

        execute_query("DELETE FROM playlists WHERE userid = ?", (str(ctx.author.id),))
        execute_query("DELETE FROM playlist_songs WHERE playlist_id IN (SELECT id FROM playlists WHERE userid = ?)", (str(ctx.author.id),))

        await ctx.send(embed=self.create_embed(
            "🎉 Todas as Playlists Apagadas",
            "Todas as suas playlists foram apagadas com sucesso.", get_embed_color()
        ))


async def setup(bot, music_manager):
    """
    Adiciona o cog de playlists ao bot.
    """
    await bot.add_cog(PlaylistCommand(bot, music_manager))
