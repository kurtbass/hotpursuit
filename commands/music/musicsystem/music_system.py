import re
from utils.database import execute_query, get_user_volume
from commands.music.musicsystem.embeds import create_embed, embed_now_playing, embed_queue_empty, embed_error, embed_stop_music
import asyncio
import discord
from yt_dlp import YoutubeDL
from utils.database import get_config
import logging
from commands.music.musicsystem.ffmpeg_options import FFMPEG_OPTIONS
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from commands.music.musicsystem.embeds import embed_lyrics, embed_error  # Embeds para exibir letras e erros
import random

logger = logging.getLogger(__name__)

class MusicManager:
    """
    Gerenciador centralizado para músicas e lógica de fila.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.voice_client = None
        self.music_queue = []  # Fila de músicas
        self.song_history = []  # Histórico de músicas tocadas na sessão
        self.current_song = None  # Música atualmente tocando
        self.volume = 1.0  # Volume padrão (100%)
        self.dj_role_id = get_config("TAG_DJ")  # ID da role de DJ, padrão é None
        self.loop_mode = "none"  # Modos de loop: "none", "single", "all"

    def add_to_queue(self, song, added_by_id):
        """
        Adiciona uma música à fila e registra quem a adicionou.
        """
        song['added_by'] = added_by_id
        self.music_queue.append(song)
        logger.info(f"Música adicionada à fila: {song.get('title', 'Desconhecido')} por {added_by_id}")

    def get_session_owner_id(self):
        """
        Retorna o ID de quem iniciou a sessão (primeira música da fila).
        """
        return self.music_queue[0].get('added_by', None) if self.music_queue else None

    def get_next_song(self):
        """
        Retorna a próxima música da fila.
        """
        if self.loop_mode == "single" and self.current_song:
            return self.current_song  # Repetir a música atual
        elif self.loop_mode == "all" and self.current_song:
            self.music_queue.append(self.current_song)  # Adicionar ao final da fila

        return self.music_queue.pop(0) if self.music_queue else None

    def get_previous_song(self):
        """
        Retorna e remove a última música do histórico.
        """
        return self.song_history.pop() if self.song_history else None

    def set_current_song(self, song):
        """
        Define a música atual e move a anterior para o histórico.
        """
        if self.current_song:
            self.song_history.append(self.current_song)
        self.current_song = song

    def resolve_stream_url(self, song):
        """
        Resolve a `stream_url` da música se ainda não foi resolvida.
        """
        if 'stream_url' not in song or not song['stream_url']:
            try:
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': False}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    song['stream_url'] = info.get('url')
                    song['thumbnail'] = info.get('thumbnail', song.get('thumbnail'))
            except Exception as e:
                logger.error(f"Erro ao resolver URL do stream: {e}")
                raise RuntimeError("Não foi possível reproduzir esta música.")

    def clear_queue(self):
        """Limpa a fila de músicas."""
        self.music_queue.clear()

    def clear_history(self):
        """Limpa o histórico de músicas tocadas."""
        self.song_history.clear()

    def get_queue(self):
        """Retorna uma cópia da fila de músicas."""
        return list(self.music_queue)

    def get_history(self):
        """Retorna uma cópia do histórico de músicas."""
        return list(self.song_history)

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
                    logger.info("Modo 'all': Fila re-populada a partir do histórico.")
                    next_song = self.get_next_song()
                else:
                    logger.info("Fila vazia. Nenhuma música para reproduzir.")
                    self.current_song = None
                    await ctx.send(embed=embed_queue_empty())
                    return

            # Verificar conexão ao canal de voz
            if not self.voice_client or not self.voice_client.is_connected():
                try:
                    logger.info("Reconectando ao canal de voz...")
                    self.voice_client = await ctx.author.voice.channel.connect()

                    # Aplicar o volume do banco de dados
                    user_volume = get_user_volume(ctx.author.id)
                    self.volume = user_volume if user_volume is not None else 1.0

                except discord.ClientException as e:
                    if "Already connected to a voice channel" in str(e):
                        logger.warning("Já conectado ao canal de voz. Continuando...")
                    else:
                        logger.error(f"Erro ao tentar reconectar ao canal de voz: {e}")
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
                    logger.error(f"Erro durante a reprodução: {error}")
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
                            logger.info(f"Modo 'single': Clone da música atual '{self.current_song.get('title', 'Desconhecido')}' re-adicionado à fila.")
                    asyncio.create_task(add_clone())

        except discord.ClientException as e:
            logger.error(f"Erro no cliente Discord: {e}")
            if "Not connected to voice" in str(e):
                await ctx.send(embed=embed_error("Não conectado ao canal de voz."))
                self.voice_client = None
        except Exception as e:
            logger.error(f"Erro ao reproduzir a próxima música: {e}")
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
            logger.error(f"Erro ao parar a música: {e}")
            await ctx.send(embed=embed_error(str(e)))

    def adjust_volume(self, volume):
        """Ajusta o volume da reprodução atual."""
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            if self.voice_client and self.voice_client.source:
                self.voice_client.source.volume = self.volume
            logger.info(f"Volume ajustado para: {volume * 100}%")
        else:
            logger.warning("Volume fora do intervalo permitido.")

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
            logger.warning(f"Modo de loop inválido: {mode}")
            return

        self.loop_mode = mode
        logger.info(f"Modo de loop ajustado para: {mode}")

        if mode == "none":
            # Remover todos os clones da música atual
            if self.music_queue and self.current_song:
                self.music_queue = [
                    song for song in self.music_queue if song != self.current_song
                ]
                logger.info("Modo 'none': Clones removidos da fila.")

        elif mode == "single" and self.current_song:
            # Adicionar clone da música atual na fila como próximo
            if not self.music_queue or self.music_queue[0] != self.current_song:
                self.music_queue.insert(0, self.current_song)
                logger.info(f"Modo 'single': Clone da música atual '{self.current_song.get('title', 'Desconhecido')}' adicionado à fila.")

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
            logger.info("Fila de músicas embaralhada com sucesso.")

    async def fetch_lyrics(self, ctx):
        """
        Busca e exibe as letras da música atual usando Playwright assíncrono.
        """
        if not self.current_song:
            await ctx.send(embed=embed_error("Nenhuma música está tocando no momento."))
            return

        # Filtrar título da música para melhorar a pesquisa
        original_title = self.current_song.get('title', 'Desconhecido')
        title = self.filter_title(original_title)
        logger.info(f"Buscando letras para: {title}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Criar URL de pesquisa
                base_url = "https://www.letras.mus.br/"
                formatted_title = title.replace(" ", "%20")
                search_url = f"{base_url}?q={formatted_title}#gsc.tab=0&gsc.q={formatted_title}"

                logger.info(f"Acessando URL: {search_url}")
                await page.goto(search_url, timeout=60000)

                # Fechar modal de anúncios, se presente
                modal_close = page.locator('path[d="M12,2C6.47,2,2,6.47,2,12c0,5.53,4.47,10,10,10s10-4.47,10-10C22,6.47,17.53,2,12,2z M17,15.59L15.59,17L12,13.41L8.41,17 L7,15.59L10.59,12L7,8.41L8.41,7L12,10.59L15.59,7L17,8.41L13.41,12L17,15.59z"]')
                if await modal_close.is_visible():
                    await modal_close.click()
                    logger.info("Modal de anúncios fechado.")

                # Esperar os links de resultado aparecerem
                logger.info("Procurando letras...")
                await page.wait_for_selector('a.gs-title[data-ctorig]', timeout=15000)
                result = page.locator('a.gs-title[data-ctorig]')
                if await result.count() > 0:
                    lyrics_url = await result.first.get_attribute('data-ctorig')
                    logger.info(f"URL encontrado: {lyrics_url}")
                else:
                    raise Exception("Nenhum resultado encontrado.")

                # Navegar até a página de letras e extrair o conteúdo
                await page.goto(lyrics_url, timeout=60000)
                await page.wait_for_selector("div.lyric-original", timeout=15000)

                title_element = await page.locator("h1.textStyle-primary").inner_text()
                artist_element = await page.locator("h2.textStyle-secondary").inner_text()
                lyrics = await page.locator("div.lyric-original").inner_text()

                # Envia o embed com a letra
                await ctx.send(embed=embed_lyrics(title_element, artist_element, lyrics))

            except Exception as e:
                logger.error(f"Erro ao buscar letras: {e}")
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
        logger.info(f"Título filtrado para pesquisa: {title}")
        return title
    
    def format_duration(seconds):
        """
        Formata a duração em segundos para o formato HH:MM:SS.
        """
        # Garantir que seconds seja um número inteiro
        if not isinstance(seconds, (int, float)):
            seconds = 0
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"                 