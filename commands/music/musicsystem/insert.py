from asyncio.log import logger
import yt_dlp as youtube_dl
from yt_dlp import YoutubeDL
import discord

async def insert_music(ctx, query, music_manager, ydl_opts):
    """
    Função para adicionar uma música à fila, seja por nome, URL ou playlist.
    """
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extrai informações da música ou do primeiro item se for uma playlist
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:  # Playlist detectada
                info = info['entries'][0]

            # Coleta os dados necessários para a música
            song = {
                'title': info.get('title', 'Desconhecido'),
                'stream_url': info.get('url', None),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Desconhecido'),
                'url': info.get('webpage_url', 'URL não disponível'),
                'thumbnail': info.get('thumbnail', None),
                'added_by': ctx.author.display_name,
                'channel': ctx.author.voice.channel.name
            }

        if not song['stream_url']:
            raise ValueError("URL de stream não encontrada para a música.")

        # Adiciona a música à fila
        music_manager.add_to_queue(song)

        # Log para depuração
        logger.info(f"Música adicionada à fila: {song['title']}")

    except youtube_dl.DownloadError as e:
        logger.error(f"Erro ao processar o download da música: {e}")
        raise RuntimeError("Não foi possível processar a música devido a um erro de download.") from e

    except Exception as e:
        logger.error(f"Erro ao inserir música: {e}")
        raise RuntimeError("Erro inesperado ao adicionar a música à fila.") from e
