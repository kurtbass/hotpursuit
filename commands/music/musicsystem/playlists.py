from yt_dlp import YoutubeDL
from asyncio.log import logger
import asyncio
from utils.database import get_config
import discord


async def process_playlist(ctx, playlist_url, music_manager, ydl_opts, from_db=False, db_links=None, send_embed=True):
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

        for entry in entries:
            if not entry or 'url' not in entry:
                logger.warning(f"Música inválida encontrada e ignorada: {entry}")
                continue
            song = {
                'title': entry.get('title', 'Título desconhecido'),
                'url': entry.get('url'),
                'duration': entry.get('duration', 0),
                'uploader': entry.get('uploader', 'Uploader desconhecido'),
                'added_by': ctx.author.display_name,
                'thumbnail': entry.get('thumbnail', None),
                'channel': ctx.author.voice.channel.name,
            }
            music_manager.add_to_queue(song)
            valid_songs += 1

        if send_embed:
            embed = music_manager.create_embed(
                "🎶 Playlist Adicionada à Fila",
                f"**Título:** {playlist_title}\n"
                f"**Uploader:** {playlist_uploader}\n"
                f"**Quantidade de Músicas:** {valid_songs}\n"
                f"**Duração Total:** {total_duration // 3600}:{(total_duration % 3600) // 60:02}:{total_duration % 60:02}\n"
                f"**Adicionada por:** {ctx.author.mention}",
                0xFF8000
            )
            if playlist_thumbnail:
                embed.set_image(url=playlist_thumbnail)
            await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Erro ao processar playlist: {e}")
        if send_embed:
            await ctx.send(embed=music_manager.create_embed(
                "Erro",
                f"⚠️ Ocorreu um erro ao processar a playlist: {str(e)}",
                0xFF0000
            ))


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
            await ctx.send(embed=music_manager.create_embed(
                "🎶 Fila Vazia",
                "Adicione mais músicas para continuar a reprodução.",
                0xFF8000
            ))
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
        await ctx.send(embed=music_manager.create_embed(
            "🎵 Tocando Agora",
            f"**Título:** {current_song.get('title', 'Título desconhecido')}\n"
            f"**Duração:** {current_song.get('duration', 0)} segundos\n"
            f"**Adicionado por:** {current_song.get('added_by', 'Desconhecido')}",
            0xFF8000
        ))

    except Exception as e:
        logger.error(f"Erro ao reproduzir música: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            f"⚠️ Ocorreu um erro ao reproduzir a música: {str(e)}",
            0xFF0000
        ))
