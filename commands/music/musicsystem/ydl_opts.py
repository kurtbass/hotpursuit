from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
YDL_OPTS = {
    'format': 'bestaudio/best',  # Baixa o melhor áudio disponível
    'quiet': True,  # Suprime saídas de logs detalhados do yt_dlp
    'default_search': 'ytsearch',  # Busca diretamente no YouTube se o link for inválido
    'age_limit': 0,  # Permite conteúdo sem restrições de idade
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',  # Extrai o áudio do vídeo
        'preferredcodec': 'mp3',  # Converte para o formato MP3
        'preferredquality': '192',  # Define a qualidade do áudio como 192 kbps
    }],
    'noplaylist': False,  # Permite processar playlists inteiras
    'extract_flat': False,  # Garante extração detalhada, incluindo URLs de streaming
    'extractor_args': {
        'youtube': ['--no-warnings'],  # Ignora avisos do YouTube
    },
    'prefer_ffmpeg': True,  # Prefere FFmpeg como ferramenta de processamento
    'geo_bypass': True,  # Ignora restrições geográficas
    'ignoreerrors': True,  # Ignora erros para continuar processando outras músicas
    'skip_download': True,  # Apenas obtém metadados (não baixa arquivos)
}