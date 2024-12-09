from asyncio.log import logger
from commands.music.musicsystem.embeds import embed_error, embed_queue_song_added
import yt_dlp as youtube_dl
from yt_dlp import YoutubeDL

async def insert_music(ctx, query, music_manager, ydl_opts, added_by_id):
    """
    Adiciona uma música ou o primeiro item de uma playlist à fila de reprodução.

    :param ctx: Contexto do comando.
    :param query: Nome ou URL da música/playlist.
    :param music_manager: Gerenciador de músicas.
    :param ydl_opts: Opções do YoutubeDL.
    :param added_by_id: ID do usuário que adicionou a música.
    """
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extrai informações da música ou da playlist
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:  # Se for uma playlist, pega a primeira música
                info = info['entries'][0]

            # Dados da música
            song = {
                'title': info.get('title', 'Desconhecido'),
                'stream_url': info.get('url'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Desconhecido'),
                'url': info.get('webpage_url', 'URL não disponível'),
                'thumbnail': info.get('thumbnail'),
                'added_by': ctx.author.display_name,
                'channel': ctx.author.voice.channel.name
            }

        # Verifica se o URL de stream foi obtido
        if not song['stream_url']:
            raise ValueError("URL de stream não encontrada para a música.")

        # Adiciona a música à fila
        music_manager.add_to_queue(song, added_by_id)

        # Feedback ao usuário
        await ctx.send(embed=embed_queue_song_added(song, ctx.author))

        # Log para depuração
        logger.info(f"Música adicionada à fila: {song['title']}")

    except youtube_dl.DownloadError as e:
        logger.error(f"Erro ao processar o download da música: {e}")
        await ctx.send(embed=embed_error("download_error"))

    except Exception as e:
        logger.error(f"Erro ao inserir música: {e}")
        await ctx.send(embed=embed_error("unexpected_error"))
