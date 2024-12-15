import asyncio
import discord
from discord.ext import commands
from utils.database import fetchone
import logging

logger = logging.getLogger(__name__)

class SampChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_task = None
        self.current_status = "off"  # Status inicial do servidor
        self.update_interval = 300  # Intervalo padrão entre atualizações (em segundos)
        self.quick_check_interval = 30  # Intervalo curto para verificações rápidas
        self.rate_limit_penalty = 5  # Penalidade adicional ao detectar rate limit
        self.max_attempts = 5  # Máximo de tentativas antes de marcar como offline

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener ativado quando o bot está pronto.
        Inicia o loop de verificação de status.
        """
        logger.info("[SAMP CHANNELS] Iniciando verificação do status do servidor SA-MP...")

        if not self.update_task:
            self.update_task = asyncio.create_task(self.manage_updates())
            logger.info("[SAMP CHANNELS] Loop de atualização iniciado.")

    async def manage_updates(self):
        """
        Gerencia a verificação do status do servidor e atualiza os canais.
        """
        while True:
            try:
                # Obter o cog SampListener
                listener = self.bot.get_cog("SampListener")
                if not listener:
                    logger.warning("[SAMP CHANNELS] SampListener não encontrado. Ignorando atualização.")
                    self.current_status = "off"
                    await asyncio.sleep(self.update_interval)
                    continue

                # Tentar obter informações do servidor
                logger.info("[SAMP CHANNELS] Verificando informações do servidor SA-MP...")
                server_success = await listener.fetch_server_info()

                if not server_success:
                    logger.warning("[SAMP CHANNELS] Não foi possível obter informações do servidor. Marcando como offline.")
                    self.current_status = "off"
                else:
                    self.current_status = "on"

                # Atualizar os canais
                logger.info("[SAMP CHANNELS] Atualizando canais...")
                channels_updated = await self.update_channels(listener)

                # Determinar o intervalo de espera
                sleep_interval = self.quick_check_interval if not channels_updated else self.update_interval
            except discord.errors.HTTPException as e:
                if e.status == 429:
                    retry_after = e.response.json().get("retry_after", self.rate_limit_penalty)
                    sleep_interval = retry_after + self.rate_limit_penalty
                    logger.warning(f"[SAMP CHANNELS] Rate limit detectado. Aguardando {sleep_interval} segundos.")
                else:
                    logger.error(f"[SAMP CHANNELS] Erro inesperado da API do Discord: {e}")
                    sleep_interval = self.update_interval
            except Exception as e:
                logger.error(f"[SAMP CHANNELS] Erro durante a gestão de atualizações: {e}")
                sleep_interval = self.update_interval

            logger.info(f"[SAMP CHANNELS] Aguardando {sleep_interval} segundos antes da próxima verificação.")
            await asyncio.sleep(sleep_interval)

    async def update_channels(self, listener):
        """
        Atualiza os canais de status e jogadores com base nas informações do servidor.
        Retorna True se os canais foram atualizados, False caso contrário.
        """
        try:
            server_info = listener.get_server_info()
            player_info = listener.get_player_info()

            if not server_info:
                logger.warning("[SAMP CHANNELS] Nenhuma informação do servidor disponível. Definindo canais como offline.")
                await self.set_channels_offline()
                return True

            # Buscar IDs dos canais no banco de dados
            status_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_status",))
            players_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_jogadores",))

            if not (status_channel_id and players_channel_id):
                logger.error("[SAMP CHANNELS] IDs dos canais necessários não encontrados no banco de dados.")
                return False

            # Obter canais no Discord
            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                logger.error("[SAMP CHANNELS] Um ou mais canais não foram encontrados no servidor.")
                return False

            # Atualizar canais apenas se necessário
            updated = False
            status_name = f"Status: {'🟢 Online' if server_info else '🔴 Offline'}"
            players_name = f"Jogadores: {player_info.get('online', 0)}/{player_info.get('max', 0)}"

            if status_channel.name != status_name:
                await status_channel.edit(name=status_name)
                logger.info(f"[SAMP CHANNELS] Canal de status atualizado para: {status_name}")
                updated = True
                await asyncio.sleep(5)

            if players_channel.name != players_name:
                await players_channel.edit(name=players_name)
                logger.info(f"[SAMP CHANNELS] Canal de jogadores atualizado para: {players_name}")
                updated = True
                await asyncio.sleep(5)

            return updated
        except Exception as e:
            logger.error(f"[SAMP CHANNELS] Erro ao atualizar canais: {e}")
            return False

    async def set_channels_offline(self):
        """
        Atualiza os canais para refletir o status offline.
        """
        try:
            status_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_status",))
            players_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_jogadores",))

            if not (status_channel_id and players_channel_id):
                logger.error("[SAMP CHANNELS] IDs dos canais necessários não encontrados no banco de dados.")
                return

            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                logger.error("[SAMP CHANNELS] Um ou mais canais não foram encontrados no servidor.")
                return

            # Atualizar canais para offline
            updated = False
            if status_channel.name != "Status: 🔴 Offline":
                await status_channel.edit(name="Status: 🔴 Offline")
                logger.info("[SAMP CHANNELS] Canal de status atualizado para: 🔴 Offline")
                updated = True
                await asyncio.sleep(5)

            if players_channel.name != "Jogadores: 0/0":
                await players_channel.edit(name="Jogadores: 0/0")
                logger.info("[SAMP CHANNELS] Canal de jogadores atualizado para: 0/0")
                updated = True
                await asyncio.sleep(5)

            return updated
        except Exception as e:
            logger.error(f"[SAMP CHANNELS] Erro ao definir canais como offline: {e}")
            return False


# Adicionar o cog ao bot
async def setup(bot):
    await bot.add_cog(SampChannels(bot))
