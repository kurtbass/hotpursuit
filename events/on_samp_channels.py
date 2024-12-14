import asyncio
import discord
from discord.ext import commands
from utils.database import fetchone


class SampChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_task = None
        self.current_status = "off"  # Status inicial
        self.update_interval = 180  # Intervalo em segundos entre atualizações
        self.quick_check_interval = 30  # Intervalo mais curto caso os nomes não precisem de mudança
        self.rate_limit_penalty = 5  # Penalidade adicional em segundos ao detectar rate limit
        self.max_attempts = 5  # Tentativas máximas antes de marcar como offline

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener ativado quando o bot está pronto. Inicia o loop de verificação de status.
        """
        print("[SAMP CHANNELS] Inicializando verificação de status do servidor SAMP...")

        # Inicia o loop regular de verificação
        if not self.update_task:
            self.update_task = asyncio.create_task(self.manage_updates())
            print("[SAMP CHANNELS] Loop de verificação de status iniciado.")

    async def manage_updates(self):
        """
        Verifica regularmente o status do listener (on/off) e gerencia as atualizações dos canais.
        """
        while True:
            try:
                # Obtém o cog SampListener
                listener = self.bot.get_cog("SampListener")
                if not listener:
                    print("[SAMP CHANNELS] SampListener não encontrado. Ignorando atualização.")
                    self.current_status = "off"
                    await asyncio.sleep(self.update_interval)
                    continue

                # Verifica o status atual do listener
                status = listener.get_status()
                if status != self.current_status:
                    print(f"[SAMP CHANNELS] Mudança detectada no status do listener: {self.current_status} -> {status}")
                    self.current_status = status

                if status == "on":
                    print("[SAMP CHANNELS] Atualizando canais...")
                    channels_updated = await self.update_channels(listener)
                    if not channels_updated:
                        print("[SAMP CHANNELS] Nenhuma atualização necessária. Verificando o servidor novamente.")
                        server_success = await self.retry_server_update(listener)
                        if not server_success:
                            print("[SAMP CHANNELS] Informações do servidor indisponíveis após tentativas.")
                            await self.set_channels_offline()
                    sleep_interval = self.quick_check_interval if not channels_updated else self.update_interval
                elif status == "off":
                    print("[SAMP CHANNELS] Listener desligado. Parando atualizações dos canais.")
                    await self.set_channels_offline()
                    sleep_interval = self.update_interval
            except discord.errors.HTTPException as e:
                if e.status == 429:
                    retry_after = e.response.json().get("retry_after", self.rate_limit_penalty)
                    sleep_interval = retry_after + self.rate_limit_penalty
                    print(f"[SAMP CHANNELS] Rate limit detectado. Aguardando {sleep_interval} segundos.")
                else:
                    print(f"[SAMP CHANNELS] Erro inesperado da API do Discord: {e}")
                    sleep_interval = self.update_interval
            except Exception as e:
                print(f"[SAMP CHANNELS] Erro durante a gestão de atualizações: {e}")
                sleep_interval = self.update_interval

            # Espera o intervalo determinado antes de verificar novamente
            print(f"[SAMP CHANNELS] Aguardando {sleep_interval} segundos antes da próxima verificação.")
            await asyncio.sleep(sleep_interval)

    async def retry_server_update(self, listener):
        """
        Tenta atualizar as informações do servidor várias vezes antes de marcar como offline.
        """
        for attempt in range(1, self.max_attempts + 1):
            print(f"[SAMP CHANNELS] Tentativa {attempt} de {self.max_attempts} para atualizar informações do servidor...")
            server_success = await listener.fetch_server_info()
            if server_success:
                print("[SAMP CHANNELS] Informações do servidor atualizadas com sucesso.")
                return True
            await asyncio.sleep(self.quick_check_interval)
        return False

    async def update_channels(self, listener):
        """
        Atualiza os canais de status e jogadores com uma pausa entre as atualizações
        e evita mudanças redundantes para reduzir rate limits.
        Retorna True se os canais foram atualizados, False caso contrário.
        """
        try:
            server_info = listener.get_server_info()
            player_info = listener.get_player_info()

            if not server_info:
                print("[SAMP CHANNELS] Nenhuma informação do servidor disponível. Atualizando para offline.")
                await self.set_channels_offline()
                return True

            # Obter IDs dos canais do banco de dados
            status_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_status",))
            players_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_jogadores",))

            if not (status_channel_id and players_channel_id):
                print("[SAMP CHANNELS] Canais necessários não encontrados no banco de dados.")
                return False

            # Obter os canais
            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                print("[SAMP CHANNELS] Um ou mais canais não foram encontrados no servidor.")
                return False

            # Atualizar os canais apenas se necessário
            updated = False
            status_name = f"Status: {'🟢 Online' if server_info else '🔴 Offline'}"
            players_name = f"Jogadores: {player_info.get('online', 0)}/{player_info.get('max', 0)}"

            if status_channel.name != status_name:
                await status_channel.edit(name=status_name)
                print(f"[SAMP CHANNELS] Canal de status atualizado para: {status_name}")
                updated = True
                await asyncio.sleep(5)

            if players_channel.name != players_name:
                await players_channel.edit(name=players_name)
                print(f"[SAMP CHANNELS] Canal de jogadores atualizado para: {players_name}")
                updated = True
                await asyncio.sleep(5)

            return updated
        except Exception as e:
            print(f"[SAMP CHANNELS] Erro ao atualizar canais: {e}")
            return False

    async def set_channels_offline(self):
        """
        Define os canais como offline caso o servidor esteja indisponível.
        """
        try:
            status_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_status",))
            players_channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_jogadores",))

            if not (status_channel_id and players_channel_id):
                print("[SAMP CHANNELS] Canais necessários não encontrados no banco de dados.")
                return

            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                print("[SAMP CHANNELS] Um ou mais canais não foram encontrados no servidor.")
                return

            # Atualizar os canais para offline
            updated = False
            if status_channel.name != "Status: 🔴 Offline":
                await status_channel.edit(name="Status: 🔴 Offline")
                print("[SAMP CHANNELS] Canal de status atualizado para: 🔴 Offline")
                updated = True
                await asyncio.sleep(5)

            if players_channel.name != "Jogadores: 0/0":
                await players_channel.edit(name="Jogadores: 0/0")
                print("[SAMP CHANNELS] Canal de jogadores atualizado para: 0/0")
                updated = True
                await asyncio.sleep(5)

            return updated
        except Exception as e:
            print(f"[SAMP CHANNELS] Erro ao definir canais como offline: {e}")
            return False


# Adicionar o cog ao bot
async def setup(bot):
    await bot.add_cog(SampChannels(bot))
