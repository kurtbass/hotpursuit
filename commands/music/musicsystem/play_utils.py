import asyncio
import discord

from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS

async def play_next(music_manager, bot):
    """
    Reproduz a próxima música da fila, mantendo o volume ajustado.
    """
    music_manager.save_current_to_history()  # Salva a música atual no histórico

    next_song = music_manager.get_next_song()

    if next_song:
        stream_url = next_song['stream_url']
        music_manager.current_song = next_song

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            volume=music_manager.volume
        )
        music_manager.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(music_manager, bot), bot.loop))
    else:
        music_manager.current_song = None
