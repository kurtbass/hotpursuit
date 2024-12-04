from asyncio.log import logger
import yt_dlp as youtube_dl
import asyncio
from utils.database import get_config
import discord
from yt_dlp import YoutubeDL  # Importando o YoutubeDL corretamente

async def insert_music(ctx, query, music_manager, ydl_opts):
    """
    Função para adicionar uma música à fila, seja por nome, URL ou playlist.
    """
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extração de informações da música
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                # Se for uma playlist, pega o primeiro item
                info = info['entries'][0]
            
            stream_url = info['url']
            title = info.get('title', 'Desconhecido')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Desconhecido')
            video_url = info.get('webpage_url', 'URL não disponível')
            thumbnail = info.get('thumbnail', None)

        # Adicionando a música à fila
        song = {
            'title': title,
            'stream_url': stream_url,
            'duration': duration,
            'uploader': uploader,
            'url': video_url,
            'added_by': ctx.author.display_name,
            'thumbnail': thumbnail,
            'channel': ctx.author.voice.channel.name
        }
        music_manager.add_to_queue(song)

        # Formatação de duração para exibição
        duration_formatted = f"{duration // 60}:{duration % 60:02d}"
        
        embed = music_manager.create_embed(
            title="🎶 Adicionado à Fila",
            description=(f"**Música:** [{title}]({video_url})\n"
                         f"**Canal do YouTube:** {uploader}\n"
                         f"**Duração:** {duration_formatted} minutos"),
            banner=thumbnail
        )
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Erro ao inserir música: {e}")
        await ctx.send(embed=music_manager.create_embed(
            "Erro", f"⚠️ Não foi possível adicionar a música.\n{str(e)}", 0xFF0000
        ))
