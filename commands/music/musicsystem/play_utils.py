import asyncio
import discord
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
import logging

logger = logging.getLogger(__name__)

async def play_next(music_manager, bot):
    """
    Reproduz a próxima música da fila, mantendo o volume ajustado.
    Caso não haja músicas na fila, a reprodução será encerrada.
    """
    try:
        # Salva a música atual no histórico antes de avançar
        music_manager.save_current_to_history()

        # Obtém a próxima música na fila
        next_song = music_manager.get_next_song()

        if next_song:
            # Resolve o URL de stream da próxima música, caso ainda não tenha sido resolvido
            if not next_song.get('stream_url'):
                music_manager.resolve_stream_url(next_song)

            # Atualiza a música atual no gerenciador
            music_manager.current_song = next_song
            stream_url = next_song['stream_url']

            # Configura e inicia a reprodução
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
                volume=music_manager.volume
            )
            music_manager.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    play_next(music_manager, bot), bot.loop
                ).result()
            )
            logger.info(f"Reproduzindo agora: {next_song['title']}")

        else:
            # Não há mais músicas na fila, interrompe a reprodução
            music_manager.current_song = None
            logger.info("Fila vazia. Nenhuma música para reproduzir.")
            if music_manager.voice_client.is_connected():
                await asyncio.sleep(5)  # Tempo antes de sair do canal
                await music_manager.voice_client.disconnect()
                music_manager.voice_client = None
                logger.info("Bot desconectado do canal de voz por inatividade.")

    except Exception as e:
        logger.error(f"Erro ao reproduzir a próxima música: {e}")
        # Desconecta o bot se ocorrer um erro crítico durante a reprodução
        if music_manager.voice_client and music_manager.voice_client.is_connected():
            await music_manager.voice_client.disconnect()
            music_manager.voice_client = None
            logger.info("Bot desconectado do canal de voz devido a erro.")
