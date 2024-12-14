from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import re
from utils.database import execute_query, get_user_volume, set_user_volume
from commands.music.musicsystem.embeds import create_embed, embed_now_playing, embed_queue_empty, embed_error, embed_queue_song_added, embed_stop_music
import asyncio
import discord
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl
from utils.database import get_config
import logging
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from commands.music.musicsystem.embeds import embed_lyrics, embed_error  # Embeds para exibir letras e erros
from colorama import Fore, Style
import random
from urllib.parse import quote

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT = 10  # Tempo em segundos antes de desconectar por inatividade


class MusicManager:
    def __init__(self, bot):
        """
        Inicializa o gerenciador de música.
        """
        self.bot = bot
        self.voice_channel = None  # Canal de voz atual
        self.voice_client = None  # Cliente de voz do bot
        self.music_queue = []  # Fila de músicas
        self.song_history = []  # Histórico de músicas tocadas na sessão
        self.current_song = None  # Música atualmente tocando
        self.volume = 1.0  # Volume padrão (100%)
        self.dj_role_id = get_config("TAG_DJ")  # ID da role de DJ, padrão é None
        self.loop_mode = "none"  # Modos de loop: "none", "single", "all"

    async def insert_music(self, ctx, query, ydl_opts, added_by_id):
        """
        Insere uma música na fila com base em uma consulta.
        """
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:  # Verifica se é uma playlist
                    info = info["entries"][0]  # Apenas pega a primeira entrada

                song = {
                    "title": info.get("title", "Título Desconhecido"),
                    "url": info.get("url"),
                    "uploader": info.get("uploader", "Uploader Desconhecido"),
                    "added_by": added_by_id,
                    "duration": info.get("duration", 0),
                }

                # Adiciona a música à fila
                self.add_to_queue(song, added_by_id)

                # Feedback ao usuário
                await ctx.send(embed=embed_queue_song_added(song, ctx.author.voice.channel, added_by=added_by_id))

                # Log para depuração
                logger.info(f"{Fore.GREEN}[MUSIC]{Style.RESET_ALL} Música adicionada à fila: {song['title']} por {ctx.author.name}.")

        except youtube_dl.DownloadError as e:
            logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Erro ao processar o download da música: {e}")
            await ctx.send(embed=embed_error("Erro ao baixar a música.", str(e)))

        except Exception as e:
            logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Erro ao inserir música: {e}")
            await ctx.send(embed=embed_error("Erro inesperado ao inserir a música.", str(e)))

    async def disconnect_on_inactivity(self, inactivity_timeout=300):
        """
        Aguarda o tempo de inatividade e desconecta o bot se ainda estiver inativo.

        :param inactivity_timeout: Tempo em segundos antes de desconectar por inatividade.
        """
        await asyncio.sleep(inactivity_timeout)
        if self.voice_client and not self.voice_client.is_playing():
            await self.voice_client.disconnect()
            self.voice_client = None
            logger.info(f"{Fore.YELLOW}[VOICE]{Style.RESET_ALL} Bot desconectado do canal de voz por inatividade.")

    def add_to_queue(self, song, added_by_id):
        """
        Adiciona uma música à fila e registra quem a adicionou.
        """
        song['added_by'] = added_by_id
        self.music_queue.append(song)  # Usa `self.music_queue` consistentemente
        logger.info(f"{Fore.BLUE}[QUEUE]{Style.RESET_ALL} Música adicionada à fila: {song.get('title', 'Desconhecido')} por {added_by_id}.")

    async def play_radio(self, radio_name, stream_url, added_by):
        """
        Reproduz uma rádio e define a rádio como a "música atual".

        :param radio_name: Nome da rádio.
        :param stream_url: URL do stream da rádio.
        :param added_by: ID do usuário que adicionou a rádio.
        """
        try:
            # Atualiza o current_song para representar a rádio
            self.current_song = {
                "title": radio_name,
                "url": stream_url,
                "added_by": added_by,
                "type": "radio"  # Identificador para diferenciar músicas e rádios
            }

            # Configura e inicia a reprodução
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(stream_url, options="-vn"),
                volume=self.volume
            )

            # Para qualquer música/rádio sendo reproduzida e começa a nova reprodução
            if self.voice_client.is_playing():
                self.voice_client.stop()

            self.voice_client.play(source, after=None)

            logger.info(f"{Fore.MAGENTA}[RADIO]{Style.RESET_ALL} Rádio '{radio_name}' está sendo reproduzida.")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Erro ao tentar reproduzir a rádio {radio_name}: {e}")
            raise e

    def stop_radio(self):
        """
        Para a reprodução de rádio e limpa o current_song.
        """
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        self.current_song = None
        logger.info(f"{Fore.YELLOW}[RADIO]{Style.RESET_ALL} Rádio foi desligada.")

    async def join_voice_channel(self, ctx):
        """
        Junta o bot ao canal de voz do usuário e ajusta o volume com base no banco de dados.

        :param ctx: Contexto do comando.
        :return: O objeto VoiceClient conectado ou None se ocorrer um erro.
        """
        if ctx.author.voice is None:
            await ctx.send(embed=embed_error("Você precisa estar conectado a um canal de voz."))
            return None

        voice_channel = ctx.author.voice.channel

        try:
            if self.voice_client is None or not self.voice_client.is_connected():
                self.voice_client = await voice_channel.connect()
                logger.info(f"{Fore.CYAN}[VOICE]{Style.RESET_ALL} Conectado ao canal de voz: {voice_channel.name}")
            elif self.voice_client.channel != voice_channel:
                await self.voice_client.move_to(voice_channel)
                logger.info(f"{Fore.CYAN}[VOICE]{Style.RESET_ALL} Movido para o canal de voz: {voice_channel.name}")

            # Ajustar o volume com base no banco de dados ou padrão
            user_volume = get_user_volume(ctx.author.id)
            self.volume = user_volume if user_volume is not None else 1.0

            if self.voice_client.source and hasattr(self.voice_client.source, "volume"):
                self.voice_client.source.volume = self.volume
            logger.info(f"{Fore.GREEN}[VOLUME]{Style.RESET_ALL} Volume ajustado para: {self.volume * 100:.1f}%")

        except discord.ClientException as e:
            logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Erro ao conectar ou mover para o canal de voz: {e}")
            await ctx.send(embed=embed_error("Erro ao conectar ao canal de voz. Verifique as permissões."))

        except discord.Forbidden:
            logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Permissões insuficientes para conectar ao canal de voz.")
            await ctx.send(embed=embed_error("Permissões insuficientes para conectar ao canal de voz."))
            return None

        return self.voice_client
    
    def set_current_song(self, song):
        """
        Define a música atual e move a anterior para o histórico.
        """
        if self.current_song:
            # Adiciona a música atual ao histórico antes de definir a próxima
            self.song_history.append(self.current_song)
        self.current_song = song
        logger.info(f"[MUSIC] Música atual definida: {song.get('title', 'Desconhecido')}")

    async def play_next(self, ctx):
        """
        Avança para a próxima música da fila e inicia a reprodução.
        """
        try:
            # Salvar a música atual no histórico apenas se o modo não for "single"
            if self.loop_mode != "single":
                self.save_current_to_history()

            # Obter a próxima música
            next_song = self.get_next_song()

            if not next_song:
                # Se o modo for "all", re-popula a fila a partir do histórico
                if self.loop_mode == "all" and self.song_history:
                    self.music_queue = self.song_history.copy()
                    self.clear_history()
                    logger.info("[MUSIC] Modo 'all': Fila re-populada a partir do histórico.")
                    next_song = self.get_next_song()
                else:
                    logger.info("[MUSIC] Fila vazia. Nenhuma música para reproduzir.")
                    self.current_song = None
                    await ctx.send(embed=embed_queue_empty())
                    return

            # Verificar conexão ao canal de voz
            if not self.voice_client or not self.voice_client.is_connected():
                try:
                    logger.info("[VOICE] Reconectando ao canal de voz...")
                    self.voice_client = await ctx.author.voice.channel.connect()

                    # Aplicar o volume do banco de dados
                    user_volume = get_user_volume(ctx.author.id)
                    self.volume = user_volume if user_volume is not None else 1.0

                except discord.ClientException as e:
                    if "Already connected to a voice channel" in str(e):
                        logger.warning("[VOICE] Já conectado ao canal de voz. Continuando...")
                    else:
                        logger.error(f"[ERROR] Erro ao tentar reconectar ao canal de voz: {e}")
                        return

            # Garantir que o volume está atualizado antes de reproduzir
            user_volume = get_user_volume(ctx.author.id)
            if user_volume is not None:
                self.volume = user_volume

            # Resolver URL e iniciar a reprodução
            self.resolve_stream_url(next_song)
            self.set_current_song(next_song)

            # Configurar e tocar a próxima música
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(next_song['stream_url'], **FFMPEG_OPTIONS),
                volume=self.volume
            )

            def after_playing(error):
                if error:
                    logger.error(f"[ERROR] Erro durante a reprodução: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), ctx.bot.loop)

            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            self.voice_client.play(source, after=after_playing)

            # Informar sobre a música atual
            voice_channel = self.voice_client.channel if self.voice_client else ctx.author.voice.channel
            await ctx.send(embed=embed_now_playing(next_song, voice_channel))

            # Adicionar música clone no modo 'single' para garantir o loop contínuo
            if self.loop_mode == "single":
                duration = next_song.get('duration', 0)
                if duration > 2:
                    async def add_clone():
                        await asyncio.sleep(duration - 2)  # Aguarde até 2 segundos antes do final
                        if self.loop_mode == "single" and self.current_song == next_song:
                            self.music_queue.insert(0, self.current_song.copy())
                            logger.info(f"[MUSIC] Modo 'single': Clone da música '{self.current_song.get('title', 'Desconhecido')}' re-adicionado à fila.")
                    asyncio.create_task(add_clone())

        except discord.ClientException as e:
            logger.error(f"[ERROR] Erro no cliente Discord: {e}")
            if "Not connected to voice" in str(e):
                await ctx.send(embed=embed_error("Não conectado ao canal de voz."))
                self.voice_client = None
        except Exception as e:
            logger.error(f"[ERROR] Erro ao reproduzir a próxima música: {e}")
            await ctx.send(embed=embed_error(str(e)))

    def save_current_to_history(self):
        """Move a música atualmente tocando para o histórico."""
        if self.current_song:
            self.song_history.append(self.current_song)
            self.current_song = None

    def get_total_duration(self):
        """Calcula a duração total das músicas na fila."""
        return sum(song.get('duration', 0) or 0 for song in self.music_queue)

    async def stop_music(self, ctx):
        """Para a música atual e limpa a fila."""
        try:
            if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
                self.voice_client.stop()
            self.clear_queue()
            await ctx.send(embed=embed_stop_music())
        except Exception as e:
            logger.error(f"[ERROR] Erro ao parar a música: {e}")
            await ctx.send(embed=embed_error(str(e)))

    def adjust_volume(self, volume):
        """Ajusta o volume da reprodução atual."""
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            if self.voice_client and self.voice_client.source:
                self.voice_client.source.volume = self.volume
            logger.info(f"[VOLUME] Volume ajustado para: {volume * 100}%")
        else:
            logger.warning("[VOLUME] Volume fora do intervalo permitido.")

    def is_queue_empty(self):
        """Verifica se a fila de músicas está vazia."""
        return len(self.music_queue) == 0

    def is_playing(self):
        """Verifica se uma música está sendo reproduzida atualmente."""
        return self.voice_client and self.voice_client.is_playing()

    def set_loop_mode(self, mode):
        """
        Define o modo de loop: "single", "all", "none".
        """
        if mode not in ["single", "all", "none"]:
            logger.warning(f"[LOOP] Modo de loop inválido: {mode}")
            return

        self.loop_mode = mode
        logger.info(f"[LOOP] Modo de loop ajustado para: {mode}")

        if mode == "none":
            # Remover todos os clones da música atual
            if self.music_queue and self.current_song:
                self.music_queue = [
                    song for song in self.music_queue if song != self.current_song
                ]
                logger.info("[LOOP] Modo 'none': Clones removidos da fila.")

        elif mode == "single" and self.current_song:
            # Adicionar clone da música atual na fila como próximo
            if not self.music_queue or self.music_queue[0] != self.current_song:
                self.music_queue.insert(0, self.current_song)
                logger.info(f"[LOOP] Modo 'single': Clone da música '{self.current_song.get('title', 'Desconhecido')}' adicionado à fila.")

    def get_loop_mode(self):
        """
        Retorna o modo de loop atual.
        """
        return self.loop_mode

    def shuffle_queue(self):
        """
        Embaralha a fila de músicas, mantendo a música atual no topo se ela existir.
        """
        if self.music_queue:
            random.shuffle(self.music_queue)
            logger.info("[QUEUE] Fila de músicas embaralhada com sucesso.")

    async def fetch_lyrics(self, ctx):
        """
        Busca e exibe as letras da música atual usando Playwright assíncrono.
        """
        if not self.current_song:
            await ctx.send(embed=embed_error("Nenhuma música está tocando no momento."))
            return

        original_title = self.current_song.get('title', 'Desconhecido')
        title = self.filter_title(original_title)
        logger.info(f"[LYRICS] Buscando letras para: {title}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                base_url = "https://www.letras.mus.br/"
                formatted_title = quote(title)
                search_url = f"{base_url}?q={formatted_title}#gsc.tab=0&gsc.q={formatted_title}"

                logger.info(f"[LYRICS] Acessando URL: {search_url}")
                await page.goto(search_url, timeout=60000)

                await page.wait_for_selector('a.gs-title[data-ctorig]', timeout=15000)
                result = page.locator('a.gs-title[data-ctorig]')
                lyrics_url = await result.first.get_attribute('data-ctorig')

                await page.goto(lyrics_url, timeout=60000)
                await page.wait_for_selector("div.lyric-original", timeout=15000)

                title_element = await page.locator("h1.textStyle-primary").inner_text()
                artist_element = await page.locator("h2.textStyle-secondary").inner_text()
                lyrics = await page.locator("div.lyric-original").inner_text()

                await ctx.send(embed=embed_lyrics(title_element, artist_element, lyrics))

            except Exception as e:
                logger.error(f"[ERROR] Erro ao buscar letras: {e}")
                await ctx.send(embed=embed_error(f"Erro ao buscar letras para **{title}**."))
            finally:
                await browser.close()

    def filter_title(self, title):
        """
        Remove palavras irrelevantes do título para melhorar a pesquisa.
        """
        filters = [
            r"(?i)\b(vídeo oficial|HD UPGRADE|oficial|Official Music Video|do dvd|ao vivo|lyric video|acústico|versão ao vivo|versão acústica)\b",
            r"[-|–|:]\s*$"
        ]
        for pattern in filters:
            title = re.sub(pattern, "", title).strip()
        logger.info(f"[LYRICS] Título filtrado para pesquisa: {title}")
        return title

    def format_duration(seconds):
        """
        Formata a duração em segundos para o formato HH:MM:SS.
        """
        if not isinstance(seconds, (int, float)):
            seconds = 0
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    def get_next_song(self):
        """
        Retorna a próxima música da fila, considerando o modo de loop.
        """
        if self.loop_mode == "single" and self.current_song:
            return self.current_song  # Repetir a música atual
        elif self.loop_mode == "all" and self.current_song:
            self.music_queue.append(self.current_song)  # Adicionar ao final da fila
        return self.music_queue.pop(0) if self.music_queue else None

    def clear_history(self):
        """
        Limpa o histórico de músicas tocadas.
        """
        self.song_history.clear()
        logger.info("[HISTORY] Histórico de músicas limpo com sucesso.")

    def get_history(self):
        """
        Retorna uma cópia do histórico de músicas.
        """
        return list(self.song_history)
    
    def resolve_stream_url(self, song):
        """
        Resolve a URL do stream de uma música, se ainda não estiver resolvida.
        """
        if 'stream_url' not in song or not song['stream_url']:
            try:
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': False}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    song['stream_url'] = info.get('url')
                    song['thumbnail'] = info.get('thumbnail', song.get('thumbnail'))
                    logger.info(f"[STREAM] URL de stream resolvida para: {song['title']}")
            except Exception as e:
                logger.error(f"[ERROR] Erro ao resolver URL do stream: {e}")
                raise RuntimeError("Não foi possível reproduzir esta música.")




