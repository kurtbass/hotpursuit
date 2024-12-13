import asyncio
import discord
from discord.ext import commands
from utils.database import fetchone


class SampChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_task = None
        self.current_status = "off"  # Status inicial
        self.update_interval = 120  # Intervalo em segundos entre atualizações
        self.quick_check_interval = 10  # Intervalo mais curto caso os nomes não precisem de mudança

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener ativado quando o bot está pronto. Inicia o loop de verificação de status.
        """
        print("[SAMP CHANNELS] Inicializando verificação de status do servidor SAMP...")

        # Inicia o loop regular de verificação
        if not self.update_task:
            await asyncio.sleep(120)
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
                    channels_updated = await self.update_channels(listener)
                    sleep_interval = self.quick_check_interval if not channels_updated else self.update_interval
                elif status == "off":
                    print("[SAMP CHANNELS] Listener desligado. Parando atualizações dos canais.")
                    await self.set_channels_offline()
                    sleep_interval = self.update_interval
            except discord.errors.HTTPException as e:
                # Lida com rate limits e ajusta o tempo de espera
                if e.status == 429 and "retry_after" in e.response.json():
                    retry_after = e.response.json()["retry_after"] + 1  # Adiciona 1 segundo extra
                    print(f"[SAMP CHANNELS] Rate limit detectado. Aguardando {retry_after} segundos antes de tentar novamente.")
                    sleep_interval = retry_after
                else:
                    print(f"[SAMP CHANNELS] Erro inesperado da API do Discord: {e}")
                    sleep_interval = self.update_interval
            except Exception as e:
                print(f"[SAMP CHANNELS] Erro durante a gestão de atualizações: {e}")
                sleep_interval = self.update_interval

            # Espera o intervalo determinado antes de verificar novamente
            await asyncio.sleep(sleep_interval)

    async def update_channels(self, listener):
        """
        Atualiza os canais de status e jogadores com uma pausa entre as atualizações
        e evita mudanças redundantes para reduzir rate limits.
        Retorna True se os canais foram atualizados, False caso contrário.
        """
        try:
            # Obtém informações do servidor e jogadores do listener
            server_info = listener.get_server_info()
            player_info = listener.get_player_info()  # Obter jogadores online e máximo

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

            # Atualizar o canal de status, verificando se há mudança
            status = "🟢 Online" if server_info else "🔴 Offline"
            updated = False

            if status_channel.name != f"Status: {status}":
                await status_channel.edit(name=f"Status: {status}")
                print(f"[SAMP CHANNELS] Canal de status atualizado para: {status}")
                updated = True
                # Pausa para evitar rate limit
                await asyncio.sleep(5)

            # Atualizar o canal de jogadores, verificando se há mudança
            players_name = f"Jogadores: {player_info.get('online', 0)}/{player_info.get('max', 0)}"
            if players_channel.name != players_name:
                await players_channel.edit(name=players_name)
                print(f"[SAMP CHANNELS] Canal de jogadores atualizado para: {players_name}")
                updated = True
                # Pausa para evitar rate limit
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

            # Obter os canais
            status_channel = self.bot.get_channel(status_channel_id[0])
            players_channel = self.bot.get_channel(players_channel_id[0])

            if not (status_channel and players_channel):
                print("[SAMP CHANNELS] Um ou mais canais não foram encontrados no servidor.")
                return

            # Atualizar canais para offline
            updated = False
            if status_channel.name != "Status: Offline":
                await status_channel.edit(name="Status: Offline")
                print("[SAMP CHANNELS] Canal de status atualizado para: Offline")
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
