from asyncio.log import logger
import yt_dlp as youtube_dl
import asyncio
from utils.database import get_config
from yt_dlp import YoutubeDL  # Importando o YoutubeDL corretamente

async def process_playlist(ctx, playlist_url, music_manager, ydl_opts):
    """
    Função para processar uma playlist e adicionar suas músicas à fila, uma por vez.
    """
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extração de informações da playlist
            info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    song = {
                        'title': entry.get('title', 'Desconhecido'),
                        'stream_url': entry.get('url', ''),
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Desconhecido'),
                        'url': entry.get('webpage_url', 'URL não disponível'),
                        'added_by': ctx.author.display_name,
                        'thumbnail': entry.get('thumbnail', None),
                        'channel': ctx.author.voice.channel.name
                    }
                    music_manager.add_to_queue(song)
                    await asyncio.sleep(1)  # Atraso para não sobrecarregar

        embed = music_manager.create_embed(
            "🎶 Playlist Adicionada à Fila",
            f"**Playlist:** {playlist_url}\n"
            "As músicas da playlist foram adicionadas à fila.",
            0xFF8000
        )
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Erro ao processar a playlist: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", f"⚠️ Não foi possível processar a playlist.\n{str(e)}", 0xFF0000
        ))
