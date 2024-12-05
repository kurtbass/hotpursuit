from utils.database import get_embed_color
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
    if ctx.author.voice is None:
        # Usuário não está em um canal de voz
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Você precisa estar em um canal de voz para usar este comando.", get_embed_color()
        ))
        return None

    voice_channel = ctx.author.voice.channel

    try:
        # Conectar ao canal de voz se ainda não estiver conectado
        if music_manager.voice_client is None or not music_manager.voice_client.is_connected():
            music_manager.voice_client = await voice_channel.connect()

            # Configurar o volume do usuário ou usar o volume padrão
            user_volume = get_user_volume(ctx.author.id)
            music_manager.volume = user_volume if user_volume is not None else 1.0

            if music_manager.voice_client.source:
                music_manager.voice_client.source.volume = music_manager.volume

            logger.info(f"Conectado ao canal de voz: {voice_channel.name}")

        # Mover o bot para o canal correto se já estiver conectado
        elif music_manager.voice_client.channel != voice_channel:
            await music_manager.voice_client.move_to(voice_channel)
            logger.info(f"Movido para o canal de voz: {voice_channel.name}")

    except discord.errors.ClientException as e:
        logger.error(f"Erro ao tentar conectar ou mover ao canal de voz: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Não foi possível conectar ou mover para o canal de voz. Verifique as permissões do bot.", get_embed_color()
        ))
        return None

    except discord.errors.Forbidden:
        logger.error("Permissões insuficientes para conectar ou mover o bot ao canal de voz.")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ O bot não tem permissão para conectar ou mover para este canal de voz.", get_embed_color()
        ))
        return None

    except Exception as e:
        logger.error(f"Erro inesperado ao conectar ao canal de voz: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Ocorreu um erro inesperado ao tentar conectar ao canal de voz.", get_embed_color()
        ))
        return None

    return music_manager.voice_client
