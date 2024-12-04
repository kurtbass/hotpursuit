from asyncio.log import logger
import discord
from utils.database import get_user_volume

async def join_voice_channel(ctx, music_manager):
    """
    Junta o bot ao canal de voz do usuário e ajusta o volume com base no banco de dados.
    """
    if ctx.author.voice is None:
        await ctx.send(embed=music_manager.create_embed(
            "Erro", "⚠️ Você precisa estar em um canal de voz para usar este comando.", 0xFF0000
        ))
        return None

    voice_channel = ctx.author.voice.channel
    if music_manager.voice_client is None or not music_manager.voice_client.is_connected():
        try:
            music_manager.voice_client = await voice_channel.connect()
            # Carregar o volume do usuário no momento da conexão
            user_volume = get_user_volume(ctx.author.id)
            music_manager.volume = user_volume / 100 if user_volume is not None else 1.0
        except discord.errors.ClientException as e:
            logger.error(f"Erro ao tentar conectar ao canal de voz: {e}")
            await ctx.send(embed=music_manager.create_embed(
                "Erro", "⚠️ Não foi possível conectar ao canal de voz.", 0xFF0000
            ))
            return None
    elif music_manager.voice_client.channel != voice_channel:
        await music_manager.voice_client.move_to(voice_channel)

    return music_manager.voice_client
