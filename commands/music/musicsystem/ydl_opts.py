YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'default_search': 'ytsearch',
    'age_limit': None,  # Removendo a restrição de idade
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'noplaylist': False,  # Permite baixar playlist inteira
    'extractor_args': {
        'youtube': ['--no-warnings'],  # Ignora avisos no YouTube
    },
    'prefer_ffmpeg': True,  # Preferir FFmpeg sobre outras opções
    'geo_bypass': True,
}