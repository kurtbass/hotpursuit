from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from utils.database import get_embed_color, get_config
from utils.config import get_lema

def create_embed(title, description, color=None, banner=None):
    """
    Cria uma mensagem embed personalizada com o lema e o nome do clã.

    :param title: Título do embed.
    :param description: Descrição do embed.
    :param color: Cor personalizada para o embed (opcional).
    :param banner: URL da imagem para o banner do embed (opcional).
    :return: Um objeto discord.Embed configurado.
    """
    # Define a cor padrão se nenhuma cor for fornecida
    color = color or get_embed_color()
    embed = discord.Embed(title=title, description=description, color=color)

    # Obtém os valores do lema, imagem do lema e nome do clã
    lema, lema_img, nome_do_cla = get_lema()

    # Adiciona o rodapé com o lema e a imagem do lema (se disponível)
    if lema_img:
        embed.set_footer(text=f"{nome_do_cla} • {lema}", icon_url=lema_img)
    else:
        embed.set_footer(text=f"{nome_do_cla} • {lema}")

    # Adiciona o banner, se fornecido
    if banner:
        embed.set_image(url=banner)

    return embed

def embed_now_playing(song, voice_channel):
    """
    Gera um embed para exibir informações da música atualmente tocando.

    :param song: Dicionário contendo informações da música atual.
    :param voice_channel: O canal de voz onde o bot está conectado.
    :return: Um embed configurado.
    """
    embed = discord.Embed(
        title=f"{get_music_emoji("music_now")} Tocando Agora",
        description=(
            f"**Título:** [{song.get('title', 'Desconhecido')}]({song.get('url', '#')})\n"
            f"{get_music_emoji("music_youtube")}**Canal do YouTube:** {song.get('uploader', 'Desconhecido')}\n"
            f"{get_music_emoji("music_duration")}**Duração:** {format_duration(song.get('duration', 0))}\n"
            f"{get_music_emoji("music_user")}**Adicionado por:** <@{song.get('added_by', 'Desconhecido')}>\n"
            f"**Canal de Voz:** <#{voice_channel.id}>"
        ),
        color=get_embed_color()
    )
    # Adiciona uma imagem (thumbnail) se disponível
    if song.get('thumbnail'):
        embed.set_thumbnail(url=song['thumbnail'])
    return embed

def embed_queue_empty():
    """
    Embed para quando a fila está vazia.
    """
    return create_embed(
        "🎶 Fila Vazia",
        "Adicione mais músicas para continuar a reprodução."
    )

def embed_need_to_be_connected_in_voice_channel():
    """
    Embed para exibir erro caso o usuário não esteja conectado em um canal de voz.
    """
    return create_embed(
        "❌ Erro",
        "Você precisa estar conectado em um canal de voz para usar esse comando."
    )

def embed_dj_error():
    """
    Embed para exibir erro sobre dono da sessão e a tag de DJ.
    """
    return create_embed(
        "🚫 Sem permissão",
        f"Você precisa ser o dono da sessão ou possuir o cargo <@&{get_config('TAG_DJ')}> para executar esse comando."
    )

def embed_already_being_used_only_owner_can_move(current_channel):
    """
    Embed para exibir que o bot já está sendo usado e que apenas o dono da sessão pode chamar o bot..
    """
    return create_embed(
        "❌ Erro",
        f"Já estou tocando música no canal **{current_channel.name}**. Apenas o dono da sessão pode me mover."
    )

def embed_user_not_in_same_channel():
    """
    Embed para exibir erro caso o usuário não esteja na mesma call.
    """
    return create_embed(
        "⚠️ Erro",
        "Você precisa estar no mesmo canal que o bot."
    )

def embed_no_music_paused():
    """
    Embed para exibir erro se tentar resumir não estando pausado.
    """
    return create_embed(
        "⚠️ Erro",
        "Não há nenhuma música pausada no momento."
    )

def embed_remove_usage():
    return create_embed(
        "❌ Uso do Comando",
        "Para remover uma música, forneça o link dela como parâmetro.\nExemplo: `hp!remove <link>`"
    )

def embed_song_removed(song):
    return create_embed(
        "🎶 Música Removida",
        f"A música **{song['title']}** foi removida da fila."
    )


def embed_error(message, error_detail=""):
    """
    Embed para exibir erros.
    """
    return create_embed(
        "Erro",
        f"⚠️ {message}\n{error_detail}"
    )

def embed_queue_song_added(song, voice_channel, added_by, is_playlist=False, playlist_name=None, user=None):
    """
    Embed para exibir música adicionada à fila.
    Se for uma playlist salva, mostra o nome da playlist e usa o avatar do usuário.
    """
    if is_playlist and user:
        banner = user.avatar.url if hasattr(user, 'avatar') and user.avatar else None
        description = (
            f"**Playlist:** {playlist_name}\n"
            f"**Adicionado por:** <@{added_by}>"
        )
    else:
        banner = song.get('thumbnail')
        description = (
            f"**Título:** {song['title']}\n"
            f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
            f"**Duração:** {format_duration(song['duration'])}\n"
            f"**Adicionado por:** <@{added_by}>\n"
            f"**Canal de Voz:** <#{voice_channel.id}>"
        )

    return create_embed(
        "🎶 Música Adicionada",
        description,
        banner=banner
    )

def embed_loop_single():
    """
    Embed para ativar repetição de música atual.
    """
    return create_embed(
        "🔂 Repetição de música ativada",
        "A música atual será repetida."
    )

def embed_loop_all():
    """
    Embed para ativar repetição de todas as músicas.
    """
    return create_embed(
        "🔁 Repetição de todas as músicas ativada",
        "Todas as músicas da fila serão repetidas."
    )

def embed_loop_off():
    """
    Embed para desligar a repetição.
    """
    return create_embed(
        "⏹️ Repetição desligada",
        "Nenhuma música será repetida."
    )

def embed_loop_cancel():
    """
    Embed para cancelar o comando de loop.
    """
    return create_embed(
        "❌ Comando cancelado",
        "Nenhuma alteração foi feita no modo de repetição."
    )

def embed_loop_timeout():
    """
    Embed para tempo esgotado na escolha de opção.
    """
    return create_embed(
        "⏳ Tempo Esgotado",
        "Não foi possível concluir a escolha. Tente novamente."
    )

def embed_shuffle_success():
    """
    Embed para exibir que a fila foi embaralhada com sucesso.
    """
    return create_embed(
        "🎶 Fila Embaralhada",
        "A fila de músicas foi embaralhada com sucesso!"
    )

def embed_shuffle_error_no_songs():
    """
    Embed para exibir erro caso a fila esteja vazia.
    """
    return create_embed(
        "⚠️ Erro",
        "Não há músicas suficientes na fila para embaralhar."
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

def embed_song_skipped(song):
    """
    Embed para exibir que a música foi pulada.
    """
    banner = song.get('thumbnail')
    return create_embed(
        "⏭️ Música Pulada",
        f"**Agora Tocando:** {song['title']}\n"
        f"**Canal:** {song.get('uploader', 'Desconhecido')}\n"
        f"**Duração:** {format_duration(song['duration'])}\n"
        f"**Adicionado por:** <@{song['added_by']}>",
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

def embed_playlist_menu(description=None):
    """
    Gera um embed para o menu principal de playlists.

    :param description: Uma descrição opcional para exibir no embed (ex.: lista de playlists do usuário).
    :return: Um embed configurado.
    """
    embed = discord.Embed(
        title="🎵 Menu de Playlists",
        description=description or (
            "Selecione uma das opções:\n\n"
            "1️⃣ Salvar a playlist atual\n"
            "2️⃣ Carregar uma playlist salva\n"
            "3️⃣ Deletar uma playlist salva\n"
            "4️⃣ Deletar todas as playlists"
        ),
        color=get_embed_color()
    )
    embed.set_footer(text="Digite o número correspondente à opção desejada.")
    return embed

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
        f"**Adicionado por:** <@{song['added_by']}>",
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

def embed_lyrics(title, artist, lyrics):
    """
    Embed para exibir a letra da música em um formato bem estruturado.
    """
    embed = discord.Embed(
        title="",  # Título da música como título principal
        description=(
            f"# {title}\n"
            f"**{artist}**\n\n"  # Artista em negrito
            f"{lyrics}"          # Letra da música
        ),
        color=get_embed_color()  # Utiliza a cor padrão configurada
    )
    embed.set_footer(text=get_config("LEMA"))  # Adiciona o lema como rodapé
    return embed

def embed_radio_menu(radios):
    """
    Gera um embed para exibir o menu de rádios.

    :param radios: Lista de rádios.
    :return: Um embed configurado.
    """
    description = "\n".join([f"**{i+1}.** {radio['name']}" for i, radio in enumerate(radios)]) + "\n**18.** Desligar Rádio"
    return create_embed(
        "🎵 Menu de Rádios",
        f"Escolha uma rádio digitando o número correspondente:\n\n{description}"
    )

def embed_searching_lyrics(title):
    """
    Gera um embed para informar que a letra está sendo pesquisada.

    :param title: Título da música que está sendo pesquisada.
    :return: Um embed configurado.
    """
    embed = discord.Embed(
        title="🔍 Buscando Letra da Música",
        description=f"Aguarde enquanto buscamos a letra para **{title}**.",
        color=get_embed_color()
    )
    return embed

def embed_radio_now_playing(radio_name, stream_url, banner_url, user):
    """
    Gera um embed para exibir informações da rádio atualmente tocando.

    :param radio_name: Nome da rádio.
    :param stream_url: URL do stream.
    :param banner_url: URL do banner da rádio.
    :param user: Usuário que iniciou a reprodução.
    :return: Um embed configurado.
    """
    description = (
        f"🎙️ **Rádio:** {radio_name}\n"
        f"🔗 **Stream:** [Clique aqui para ouvir]({stream_url})\n"
        f"👤 **Solicitada por:** {user.mention}"
    )
    return create_embed(
        "📻 Rádio Tocando Agora",
        description,
        banner=banner_url
    )


def embed_radio_stopped():
    """
    Gera um embed para informar que a rádio foi desligada.

    :return: Um embed configurado.
    """
    return create_embed(
        "🔇 Rádio Desligada",
        "A reprodução foi encerrada. Escolha outra rádio para sintonizar ou continue sua experiência musical!"
    )

