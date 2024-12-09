import discord
from utils.database import get_embed_color, get_config

def create_embed(title, description, color=None, banner=None):
    """
    Cria uma mensagem embed personalizada.
    """
    color = color or get_embed_color()
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=get_config("LEMA"))
    if banner:
        embed.set_image(url=banner)
    return embed

def embed_now_playing(song, voice_channel):
    """
    Embed para a música atualmente tocando.
    """
    banner = song.get('thumbnail')
    return create_embed(
        "🎵 Tocando Agora",
        f"**Título:** {song['title']}\n"
        f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
        f"**Duração:** {format_duration(song['duration'])}\n"
        f"**Adicionado por:** {song['added_by']}\n"
        f"**Canal de Voz:** <#{voice_channel.id}>",
        banner=banner
    )

def embed_queue_empty():
    """
    Embed para quando a fila está vazia.
    """
    return create_embed(
        "🎶 Fila Vazia",
        "Adicione mais músicas para continuar a reprodução."
    )

def embed_error(message):
    """
    Embed para exibir erros.
    """
    return create_embed(
        "Erro",
        f"⚠️ {message}"
    )

def embed_queue_song_added(song, added_by, is_playlist=False, playlist_name=None, user=None):
    """
    Embed para exibir música adicionada à fila.
    Se for uma playlist salva, mostra o nome da playlist e usa o avatar do usuário.
    """
    if is_playlist and user:
        banner = user.avatar.url if hasattr(user, 'avatar') and user.avatar else None
        description = (
            f"**Playlist:** {playlist_name}\n"
            f"**Adicionado por:** {added_by}"
        )
    else:
        banner = song.get('thumbnail')
        description = (
            f"**Título:** {song['title']}\n"
            f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
            f"**Duração:** {format_duration(song['duration'])}\n"
            f"**Adicionado por:** {added_by}"
        )

    return create_embed(
        "🎶 Música Adicionada",
        description,
        banner=banner
    )

def embed_queue_cleared():
    """
    Embed para exibir que a fila foi limpa com sucesso.
    """
    return create_embed(
        "🎵 Fila Limpa",
        "✅ A fila de músicas foi limpa com sucesso."
    )

def embed_stop_music():
    """
    Embed para exibir que a música foi parada e a fila limpa.
    """
    return create_embed(
        "⏹ Música Parada",
        "Fila limpa."
    )

def embed_connected(channel_name):
    """
    Embed para exibir que o bot entrou no canal de voz.
    """
    return create_embed(
        "Conectado",
        f"✅ Entrei no canal **{channel_name}**."
    )

def embed_disconnected(channel_name):
    """
    Embed para exibir que o bot saiu do canal de voz.
    """
    return create_embed(
        "Desconectado",
        f"⛔ Saí do canal **{channel_name}**."
    )

def embed_volume_set(volume):
    """
    Embed para exibir que o volume foi ajustado.
    """
    return create_embed(
        "🔊 Volume Ajustado",
        f"O volume foi ajustado para **{volume}%**."
    )

def embed_current_volume(volume):
    """
    Embed para exibir o volume atual.
    """
    return create_embed(
        "🔊 Volume Atual",
        f"O volume atual é **{int(volume)}%**."
    )

def embed_music_resumed():
    """
    Embed para exibir que a música foi retomada.
    """
    return create_embed(
        "▶️ Música Retomada",
        "A música pausada foi retomada."
    )

def embed_music_paused(song):
    """
    Embed para exibir que a música foi pausada.
    """
    banner = song.get('thumbnail')
    return create_embed(
        "⏸️ Música Pausada",
        f"A música **{song['title']}** foi pausada.",
        banner=banner
    )

def embed_permission_denied(message):
    """
    Embed para indicar permissão negada.
    """
    return create_embed(
        "Permissão Negada",
        f"⚠️ {message}"
    )

def embed_skip(song):
    """
    Embed para exibir que a música foi pulada.
    """
    banner = song.get('thumbnail')
    return create_embed(
        "⏭️ Música Pulada",
        f"**Agora Tocando:** {song['title']}\n"
        f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
        f"**Duração:** {format_duration(song['duration'])}\n"
        f"**Adicionado por:** {song['added_by']}",
        banner=banner
    )

def embed_playlist_added(title, uploader, valid_songs, total_duration, thumbnail, user):
    """
    Embed para exibir que uma playlist foi adicionada à fila.
    """
    return create_embed(
        "🎶 Playlist Adicionada",
        f"**Título:** {title}\n"
        f"**Uploader:** {uploader}\n"
        f"**Quantidade de Músicas:** {valid_songs}\n"
        f"**Duração Total:** {format_duration(total_duration)}\n"
        f"**Adicionada por:** {user.mention}",
        banner=thumbnail
    )

def embed_playlist_menu():
    """
    Embed para o menu principal de playlists.
    """
    return create_embed(
        "🎶 Gerenciamento de Playlists",
        "1⃣ **Salvar playlist atual**\n"
        "2⃣ **Carregar uma playlist**\n"
        "3⃣ **Apagar uma playlist**\n"
        "4⃣ **Apagar todas as suas playlists**\n\n"
        "Digite o número referente à opção desejada."
    )

def embed_save_playlist():
    """
    Embed para solicitar o nome da playlist a ser salva.
    """
    return create_embed(
        "🎶 Salvar Playlist",
        "Digite o nome da sua playlist:"
    )

def embed_playlist_saved(playlist_name, total_duration, user):
    """
    Embed para exibir que a playlist foi salva.
    """
    return create_embed(
        "🎉 Playlist Salva",
        f"Playlist salva como **{playlist_name}**.\n"
        f"**Duração Total:** {format_duration(total_duration)}\n"
        f"Criada por: {user.mention}"
    )

def embed_playlist_loaded(playlist_name, song_count, total_duration, user):
    """
    Embed para exibir que a playlist foi carregada.
    """
    return create_embed(
        "🎶 Playlist Carregada",
        f"**Título:** {playlist_name}\n"
        f"**Quantidade de Músicas:** {song_count}\n"
        f"**Duração Total:** {format_duration(total_duration)}\n"
        f"**Adicionada por:** {user.mention}"
    )

def embed_previous_song(song):
    """
    Embed para exibir a música anterior tocada.
    """
    banner = song.get('thumbnail')
    return create_embed(
        "⏮️ Voltando para a Música Anterior",
        f"**Título:** {song['title']}\n"
        f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
        f"**Duração:** {format_duration(song['duration'])}\n"
        f"**Adicionado por:** {song['added_by']}",
        banner=banner
    )

def embed_queue_page(page, total_pages, description):
    """
    Embed para exibir uma página da fila de músicas.
    """
    return create_embed(
        "🎶 Fila de Reprodução",
        description,
        color=get_embed_color()
    ).set_footer(text=f"Página {page}/{total_pages}")

def embed_download_error():
    """
    Embed para exibir erro de download.
    """
    return create_embed(
        "Erro de Download",
        "⚠️ Não foi possível processar a música devido a um erro de download."
    )

def embed_unexpected_error():
    """
    Embed para exibir erro inesperado.
    """
    return create_embed(
        "Erro Inesperado",
        "⚠️ Ocorreu um erro inesperado."
    )

def embed_all_playlists_deleted():
    """
    Embed para exibir que todas as playlists foram apagadas.
    """
    return create_embed(
        "🎉 Todas as Playlists Apagadas",
        "Todas as suas playlists foram apagadas com sucesso."
    )

def embed_play_usage():
    """
    Embed para exibir o uso correto do comando play.
    """
    return create_embed(
        "Como Usar o Comando play",
        "⚠️ **Uso do Comando play** ⚠️\n\n"
        "**Opções de uso:**\n"
        "- Link do YouTube: `https://youtube.com/watch?v=<ID>`\n"
        "- Nome da Música: Exemplo: `Bohemian Rhapsody`\n"
        "- Playlist do YouTube: `https://youtube.com/playlist?list=<ID>`\n\n"
        "**Exemplos de Comando:**\n"
        "- `!play https://youtube.com/watch?v=xxxxxx`\n"
        "- `!play Nome da Música`\n"
        "- `!play https://youtube.com/playlist?list=xxxxxx`"
    )

def format_duration(seconds):
    """
    Formata a duração em segundos para o formato HH:MM:SS.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
