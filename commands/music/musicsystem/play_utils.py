import asyncio
import discord
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
import logging

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT = 10  # Tempo em segundos antes de desconectar por inatividade

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
                after=lambda _: bot.loop.create_task(play_next(music_manager, bot))
            )

            # Log da música em reprodução
            logger.info(f"Reproduzindo agora: {next_song['title']}")
            if music_manager.current_song:
                logger.debug(f"Detalhes da música: {music_manager.current_song}")

        else:
            # Não há mais músicas na fila, interrompe a reprodução
            music_manager.current_song = None
            logger.info("Fila vazia. Nenhuma música para reproduzir.")

            # Aguardar antes de desconectar por inatividade
            await asyncio.sleep(INACTIVITY_TIMEOUT)

            # Verifica se o bot ainda está conectado e desconecta
            if music_manager.voice_client and music_manager.voice_client.is_connected():
                await music_manager.voice_client.disconnect()
                music_manager.voice_client = None
                logger.info("Bot desconectado do canal de voz por inatividade.")

    except discord.ClientException as e:
        logger.error(f"Erro no cliente Discord durante a reprodução: {e}")
        if music_manager.voice_client and music_manager.voice_client.is_connected():
            await music_manager.voice_client.disconnect()
            music_manager.voice_client = None
            logger.info("Bot desconectado do canal de voz devido a erro do cliente.")

    except Exception as e:
        logger.error(f"Erro inesperado ao reproduzir a próxima música: {e}")
        # Desconecta o bot se ocorrer um erro crítico durante a reprodução
        if music_manager.voice_client and music_manager.voice_client.is_connected():
            await music_manager.voice_client.disconnect()
            music_manager.voice_client = None
            logger.info("Bot desconectado do canal de voz devido a erro.")
