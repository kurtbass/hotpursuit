from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import asyncio
from yt_dlp import YoutubeDL
from asyncio.log import logger
from commands.music.musicsystem.embeds import embed_playlist_added, embed_error, embed_now_playing
from utils.database import get_user_volume, set_user_volume
import discord

async def process_playlist(ctx, playlist_url, music_manager, ydl_opts, from_db=False, db_links=None, send_embed=True, added_by_id=None):
    """
    Processa uma playlist e adiciona suas músicas à fila como links individuais.
    """
    try:
        entries = []
        playlist_title = "Playlist Salva"
        playlist_uploader = "Usuário"
        playlist_thumbnail = None
        total_duration = 0

        if from_db:
            # Processar playlist diretamente da base de dados
            entries = [{'url': link} for link in db_links]
        else:
            # Processar playlist externa
            with YoutubeDL({**ydl_opts, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info or 'entries' not in info:
                    raise ValueError(f"Nenhuma música válida encontrada na playlist: {playlist_url}")
                entries = info.get('entries', [])
                playlist_title = info.get('title', 'Playlist sem título')
                playlist_uploader = info.get('uploader', 'Uploader desconhecido')
                playlist_thumbnail = info.get('thumbnail', None)

        if not entries:
            raise ValueError("Nenhuma entrada válida encontrada na playlist.")

        total_duration = sum(entry.get('duration', 0) or 0 for entry in entries if entry and 'duration' in entry)
        valid_songs = 0

        # Garantir que o bot esteja conectado ao canal de voz
        if not music_manager.voice_client or not music_manager.voice_client.is_connected():
            if ctx.author.voice:
                music_manager.voice_client = await ctx.author.voice.channel.connect()
                logger.info(f"Conectado ao canal de voz: {ctx.author.voice.channel.name}")
            else:
                await ctx.send(embed=embed_error("user_not_in_voice_channel"))
                return

        # Ajustar o volume do usuário após conectar ao canal
        user_volume = get_user_volume(ctx.author.id)
        if user_volume is None:
            user_volume = 1.0  # Volume padrão
            set_user_volume(ctx.author.id, user_volume)
        music_manager.volume = user_volume
        logger.info(f"Volume inicial ajustado para {music_manager.volume * 100:.1f}%")

        for entry in entries:
            if not entry or 'url' not in entry:
                logger.warning(f"Música inválida encontrada e ignorada: {entry}")
                continue
            song = {
                'title': entry.get('title', 'Título desconhecido'),
                'url': entry.get('url'),
                'duration': entry.get('duration', 0),
                'uploader': entry.get('uploader', 'Uploader desconhecido'),
                'added_by': ctx.author.display_name if added_by_id is None else added_by_id,
                'thumbnail': entry.get('thumbnail', playlist_thumbnail),
                'channel': ctx.author.voice.channel.name,
            }
            music_manager.add_to_queue(song, added_by_id or ctx.author.id)
            valid_songs += 1

        if send_embed:
            await ctx.send(embed=embed_playlist_added(
                title=playlist_title,
                uploader=playlist_uploader,
                valid_songs=valid_songs,
                total_duration=total_duration,
                thumbnail=playlist_thumbnail,
                user=ctx.author
            ))

    except Exception as e:
        logger.error(f"Erro ao processar playlist: {e}")
        if send_embed:
            await ctx.send(embed=embed_error("playlist_processing_error", str(e)))


async def play_song(ctx, music_manager, ydl_opts):
    """
    Faz o download e reproduz a música atual da fila.
    """
    try:
        # Salva a música atual no histórico
        music_manager.save_current_to_history()

        # Obtém a próxima música na fila
        current_song = music_manager.get_next_song()
        if not current_song:
            # Caso a fila esteja vazia, notifica e desconecta
            await ctx.send(embed=embed_error("queue_empty"))
            await asyncio.sleep(5)
            if music_manager.voice_client:
                await music_manager.voice_client.disconnect()
                music_manager.voice_client = None
                logger.info("Bot desconectado por inatividade.")
            return

        # Resolve a URL da música, se necessário
        if not current_song.get('stream_url'):
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(current_song['url'], download=False)
                current_song['stream_url'] = info.get('url')

        # Garantir que o volume está atualizado antes de tocar a música
        user_volume = get_user_volume(ctx.author.id)
        if user_volume is not None:
            music_manager.volume = user_volume

        # Configura o áudio e inicia a reprodução
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(current_song['stream_url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn'),
            volume=music_manager.volume
        )

        def after_playing(error):
            if error:
                logger.error(f"Erro durante a reprodução: {error}")
            ctx.bot.loop.create_task(play_song(ctx, music_manager, ydl_opts))

        music_manager.voice_client.play(source, after=after_playing)

        # Envia feedback sobre a música atual
        await ctx.send(embed=embed_now_playing(current_song, ctx.author.voice.channel))

    except Exception as e:
        logger.error(f"Erro ao reproduzir música: {e}")
        await ctx.send(embed=embed_error("play_song_error", str(e)))
