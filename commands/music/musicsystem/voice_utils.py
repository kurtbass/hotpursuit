import discord
from utils.database import get_user_volume
import logging

logger = logging.getLogger(__name__)

async def join_voice_channel(ctx, music_manager):
    """
    Junta o bot ao canal de voz do usuário e ajusta o volume com base no banco de dados.

    :param ctx: O contexto do comando.
    :param music_manager: O gerenciador de música compartilhado.
    :return: O objeto VoiceClient conectado ou None se ocorrer um erro.
    """
    # Verificar se o usuário está em um canal de voz
    if ctx.author.voice is None:
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Você precisa estar em um canal de voz para usar este comando.", 0xFF0000
        ))
        return None

    voice_channel = ctx.author.voice.channel

    try:
        # Se o bot não está conectado, conectar ao canal do usuário
        if music_manager.voice_client is None or not music_manager.voice_client.is_connected():
            music_manager.voice_client = await voice_channel.connect()

            # Recuperar o volume do usuário
            user_volume = get_user_volume(ctx.author.id)
            music_manager.volume = user_volume if user_volume is not None else 1.0

            # Ajustar volume caso a fonte de áudio já esteja configurada
            if music_manager.voice_client.source:
                music_manager.voice_client.source.volume = music_manager.volume

            logger.info(f"Conectado ao canal de voz: {voice_channel.name}")

        # Se o bot está conectado, mas em um canal diferente, mover para o canal correto
        elif music_manager.voice_client.channel != voice_channel:
            await music_manager.voice_client.move_to(voice_channel)
            logger.info(f"Movido para o canal de voz: {voice_channel.name}")

    except discord.errors.ClientException as e:
        logger.error(f"Erro ao tentar conectar ao canal de voz: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Não foi possível conectar ao canal de voz. Verifique as permissões do bot.", 0xFF0000
        ))
        return None

    except Exception as e:
        logger.error(f"Erro inesperado ao conectar ao canal de voz: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Ocorreu um erro ao tentar conectar ao canal de voz.", 0xFF0000
        ))
        return None

    return music_manager.voice_client
