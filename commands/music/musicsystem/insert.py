from utils.database import get_embed_color
from asyncio.log import logger
import yt_dlp as youtube_dl
from yt_dlp import YoutubeDL
import discord

async def insert_music(ctx, query, music_manager, ydl_opts):
    """
    Adiciona uma música ou o primeiro item de uma playlist à fila de reprodução.

    :param ctx: Contexto do comando.
    :param query: Nome ou URL da música/playlist.
    :param music_manager: Gerenciador de músicas.
    :param ydl_opts: Opções do YoutubeDL.
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
        music_manager.add_to_queue(song)

        # Feedback ao usuário
        await ctx.send(embed=music_manager.create_embed(
            "🎵 Música Adicionada à Fila",
            f"**Título:** {song['title']}\n"
            f"**Duração:** {song['duration'] // 60}:{str(song['duration'] % 60).zfill(2)}\n"
            f"**Adicionado por:** {ctx.author.mention}",
            get_embed_color()
        ))

        # Log para depuração
        logger.info(f"Música adicionada à fila: {song['title']}")

    except youtube_dl.DownloadError as e:
        logger.error(f"Erro ao processar o download da música: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            "⚠️ Não foi possível processar a música devido a um erro de download.",
            get_embed_color()
        ))

    except Exception as e:
        logger.error(f"Erro ao inserir música: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro",
            "⚠️ Ocorreu um erro inesperado ao adicionar a música à fila.",
            get_embed_color()
        ))
