import discord
from commands.music.musicsystem.embeds import embed_error
from utils.database import get_user_volume, set_user_volume
import logging

logger = logging.getLogger(__name__)

async def join_voice_channel(ctx, music_manager):
    """
    Junta o bot ao canal de voz do usuário e ajusta o volume com base no banco de dados.

    :param ctx: O contexto do comando.
    :param music_manager: O gerenciador de música compartilhado.
    :return: O objeto VoiceClient conectado ou None se ocorrer um erro.
    """
    if ctx.author.voice is None:
        # Usuário não está em um canal de voz
        await ctx.send(embed=embed_error("user_not_in_voice_channel"))
        return None

    voice_channel = ctx.author.voice.channel

    try:
        # Conectar ao canal de voz se ainda não estiver conectado
        if music_manager.voice_client is None or not music_manager.voice_client.is_connected():
            music_manager.voice_client = await voice_channel.connect()

        # Configurar o volume do usuário ou usar o volume padrão
        user_volume = get_user_volume(ctx.author.id)
        if user_volume is None:
            user_volume = 1.0  # Valor padrão caso o volume não exista no banco
            set_user_volume(ctx.author.id, user_volume)  # Salvar o volume padrão para o usuário
        music_manager.volume = user_volume

        # Certificar que o volume seja aplicado ao áudio atual, se houver
        if music_manager.voice_client.source and hasattr(music_manager.voice_client.source, 'volume'):
            music_manager.voice_client.source.volume = music_manager.volume

        logger.info(f"Conectado ao canal de voz: {voice_channel.name} com volume inicial de {music_manager.volume * 100:.1f}%")

        # Mover o bot para o canal correto se já estiver conectado
        if music_manager.voice_client.channel != voice_channel:
            await music_manager.voice_client.move_to(voice_channel)
            logger.info(f"Movido para o canal de voz: {voice_channel.name}")

    except discord.errors.ClientException as e:
        logger.error(f"Erro ao tentar conectar ou mover ao canal de voz: {e}")
        await ctx.send(embed=embed_error("voice_channel_connection_error"))
        return None

    except discord.errors.Forbidden:
        logger.error("Permissões insuficientes para conectar ou mover o bot ao canal de voz.")
        await ctx.send(embed=embed_error("voice_channel_permission_error"))
        return None

    return music_manager.voice_client
