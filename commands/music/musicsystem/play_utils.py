import asyncio
import discord
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
import logging
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT = 10  # Tempo em segundos antes de desconectar por inatividade

async def resolve_stream_url(song):
    """
    Resolve o URL de stream para a música fornecida.
    """
    try:
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': False}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song['url'], download=False)
            song['stream_url'] = info.get('url')
            song['thumbnail'] = info.get('thumbnail', song.get('thumbnail'))
            logger.info(f"Stream URL resolvido para a música: {song['title']}")
    except Exception as e:
        logger.error(f"Erro ao resolver o URL do stream: {e}")
        raise

async def disconnect_on_inactivity(music_manager):
    """
    Aguarda o tempo de inatividade e desconecta o bot se ainda estiver inativo.
    """
    await asyncio.sleep(INACTIVITY_TIMEOUT)
    if music_manager.voice_client and music_manager.voice_client.is_connected():
        await music_manager.voice_client.disconnect()
        music_manager.voice_client = None
        logger.info("Bot desconectado do canal de voz por inatividade.")
