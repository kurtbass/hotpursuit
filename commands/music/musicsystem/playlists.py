from yt_dlp import YoutubeDL
from asyncio.log import logger
import asyncio
from utils.database import get_config
import discord


async def process_playlist(ctx, playlist_url, music_manager, ydl_opts):
    """
    Processa uma playlist e adiciona suas músicas à fila como links individuais.
    Apenas a música atual, anterior e próxima serão baixadas no momento da reprodução.
    """
    try:
        with YoutubeDL({**ydl_opts, 'extract_flat': True}) as ydl:  # 'extract_flat' extrai apenas os metadados
            info = ydl.extract_info(playlist_url, download=False)

            # Verificar se a playlist foi encontrada
            if not info or 'entries' not in info:
                raise ValueError(f"Nenhuma música válida encontrada na playlist: {playlist_url}")

            entries = info.get('entries', [])
            if not entries:
                raise ValueError("Nenhuma entrada válida encontrada na playlist.")

            # Detalhes da playlist
            playlist_title = info.get('title', 'Playlist sem título')
            playlist_uploader = info.get('uploader', 'Uploader desconhecido')
            playlist_thumbnail = info.get('thumbnail', None)

            # Corrigir cálculo de duração total
            total_duration = sum(entry.get('duration', 0) or 0 for entry in entries if entry and 'duration' in entry)

            # Adicionar músicas à fila como links individuais
            valid_songs = 0
            for entry in entries:
                # Pular entradas inválidas ou sem URL
                if not entry or 'url' not in entry:
                    logger.warning(f"Música inválida encontrada e ignorada: {entry}")
                    continue

                # Criar o objeto da música
                song = {
                    'title': entry.get('title', 'Título desconhecido'),
                    'url': entry.get('url', 'URL não disponível'),
                    'duration': entry.get('duration', 0) or 0,  # Evitar valores None
                    'uploader': entry.get('uploader', 'Uploader desconhecido'),
                    'added_by': ctx.author.display_name,
                    'thumbnail': entry.get('thumbnail', None),
                    'channel': ctx.author.voice.channel.name,
                }
                music_manager.add_to_queue(song)
                valid_songs += 1

            # Mensagem com detalhes da playlist
            embed = music_manager.create_embed(
                "🎶 Playlist Adicionada à Fila",
                f"**Título:** [{playlist_title}]({playlist_url})\n"
                f"**Uploader:** {playlist_uploader}\n"
                f"**Quantidade de Músicas:** {valid_songs}\n"
                f"**Duração Total:** {str(total_duration // 3600)}:"
                f"{str((total_duration % 3600) // 60).zfill(2)}:"
                f"{str(total_duration % 60).zfill(2)}\n"
                f"**Adicionada por:** {ctx.author.mention}\n"
                f"**Canal:** <#{ctx.author.voice.channel.id}>",
                0xFF8000
            )
            if playlist_thumbnail:
                embed.set_image(url=playlist_thumbnail)  # Define a thumbnail da playlist como banner
                embed.set_footer(text=f"`{get_config('LEMA')}`", icon_url=playlist_thumbnail)

            await ctx.send(embed=embed)

    except ValueError as e:
        logger.error(f"Erro ao processar playlist: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            f"⚠️ {e}",
            0xFF0000
        ))

    except Exception as e:
        logger.error(f"Erro inesperado ao processar a playlist: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            f"⚠️ Ocorreu um erro ao processar a playlist: {str(e)}",
            0xFF0000
        ))


async def play_song(ctx, music_manager, ydl_opts):
    """
    Faz o download e reproduz a música atual, garantindo que apenas a atual, anterior e próxima sejam baixadas.
    """
    try:
        current_song = music_manager.get_current_song()
        previous_song = music_manager.get_previous_song()
        next_song = music_manager.get_next_song()

        # Baixar apenas as músicas necessárias
        for song in [previous_song, current_song, next_song]:
            if song and not song.get('stream_url'):  # Se ainda não foi baixada
                with YoutubeDL(ydl_opts) as ydl:
                    song_info = ydl.extract_info(song['url'], download=False)
                    song['stream_url'] = song_info['url']

        # Reproduzir a música atual
        if current_song:
            music_manager.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(current_song['stream_url'], **{
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn'
                    }),
                    volume=music_manager.volume
                ),
                after=lambda e: asyncio.run_coroutine_threadsafe(play_song(ctx, music_manager, ydl_opts), ctx.bot.loop)
            )

    except Exception as e:
        logger.error(f"Erro ao reproduzir música: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            f"⚠️ Ocorreu um erro ao reproduzir a música: {str(e)}",
            0xFF0000
        ))
