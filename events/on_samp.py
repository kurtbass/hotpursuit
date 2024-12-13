import socket
import struct
import asyncio
import discord
from discord.ext import commands
from utils.database import fetchone


class SampListener(commands.Cog):
    def __init__(self, bot):
        """
        Inicializa o cog SampListener.
        """
        self.bot = bot
        self.status = "off"  # Inicializa o status como 'off'
        self.server_info = None  # Armazena informações gerais do servidor
        self.players = {"online": 0, "max": 0}  # Armazena jogadores online e máximo
        self.update_task = None
        self.server_ip = "15.235.123.105"
        self.server_port = 7777
        self.samp_query = SampQueryAPI(self.server_ip, self.server_port)
        self.max_retries = 10  # Máximo de tentativas antes de marcar como offline
        self.retry_interval = 5  # Intervalo (em segundos) entre as tentativas bem-sucedidas
        self.failed_retry_interval = 30  # Intervalo após tentativas falhas
        self.success = False  # Indica o estado da última atualização

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener ativado quando o bot está pronto. Verifica a categoria e inicia o processo de atualização.
        """
        print("[SAMP LISTENER] Verificando a configuração da categoria SAMP...")
        self.status = await self.verify_category()
        print(f"[SAMP LISTENER] Status inicial: {self.status}")

        if self.status == "on" and not self.update_task:
            self.update_task = asyncio.create_task(self.update_server_info_loop())
            print("[SAMP LISTENER] Loop de atualização iniciado.")

    async def verify_category(self):
        """
        Verifica se a categoria e os canais necessários estão configurados no servidor.
        """
        category_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_categoria",))
        if not category_id:
            print("[SAMP LISTENER] Categoria não configurada no banco de dados.")
            return "off"

        category = discord.utils.get(self.bot.guilds[0].categories, id=category_id[0])
        if not category:
            print("[SAMP LISTENER] Categoria não encontrada no servidor.")
            return "off"

        required_channels = ["samp_status", "samp_jogadores"]
        for channel_type in required_channels:
            channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", (channel_type,))
            if not channel_id or not self.bot.get_channel(channel_id[0]):
                print(f"[SAMP LISTENER] Canal '{channel_type}' não encontrado ou configurado incorretamente.")
                return "off"

        print("[SAMP LISTENER] Categoria e canais configurados corretamente.")
        return "on"

    async def update_server_info_loop(self):
        """
        Atualiza as informações do servidor periodicamente.
        """
        while True:
            try:
                success = await self.try_update_server_info()
                if not success:
                    print("[SAMP LISTENER] Falhou em obter informações do servidor após múltiplas tentativas.")
                    self.server_info = None
                    self.players = {"online": 0, "max": 0}
                self.success = success
            except Exception as e:
                print(f"[SAMP LISTENER] Erro durante o loop de atualização: {e}")
                self.success = False

            # Define o intervalo com base no sucesso ou falha
            interval = self.retry_interval if self.success else self.failed_retry_interval
            await asyncio.sleep(interval)

    async def try_update_server_info(self):
        """
        Tenta atualizar as informações do servidor com múltiplas tentativas.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.samp_query.is_online():
                    info = self.samp_query.get_info()
                    if info:
                        self.server_info = {
                            "state": "Online",
                            "hostname": info["hostname"],
                            "gamemode": info["gamemode"],
                            "mapname": info["mapname"],
                        }
                        self.players = {
                            "online": info["players"],
                            "max": info["maxplayers"]
                        }
                        return True
            except socket.timeout:
                if attempt == self.max_retries:
                    print(f"[SAMP LISTENER] Timeout após {self.max_retries} tentativas.")
                else:
                    # Não exibe nada para tentativas intermediárias
                    await asyncio.sleep(self.retry_interval)

        # Todas as tentativas falharam
        print("[SAMP LISTENER] Todas as tentativas de conexão falharam.")
        return False

    def get_status(self):
        return self.status

    def get_server_info(self):
        return self.server_info

    def get_player_info(self):
        return self.players


class SampQueryAPI:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(5)

    def is_online(self):
        try:
            self.socket.sendto(self._build_packet("i"), (self.ip, self.port))
            data, _ = self.socket.recvfrom(4096)
            return data.startswith(b"SAMP")
        except Exception as e:
            print(f"[SAMPQueryAPI] Erro ao conectar: {e}")
            return False

    def get_info(self):
        try:
            self.socket.sendto(self._build_packet("i"), (self.ip, self.port))
            data, _ = self.socket.recvfrom(4096)
            return self._parse_info(data)
        except Exception as e:
            print(f"[SAMPQueryAPI] Erro ao buscar informações: {e}")
            return None

    def _build_packet(self, payload):
        ip_parts = [int(x) for x in self.ip.split(".")]
        port_low = self.port & 0xFF
        port_high = (self.port >> 8) & 0xFF
        return b"SAMP" + bytes(ip_parts) + bytes([port_low, port_high]) + payload.encode()

    def _parse_info(self, data):
        try:
            offset = 11
            password = data[offset]
            offset += 1
            players = struct.unpack("<H", data[offset:offset + 2])[0]
            offset += 2
            maxplayers = struct.unpack("<H", data[offset:offset + 2])[0]
            offset += 2
            hostname_length = struct.unpack("<I", data[offset:offset + 4])[0]
            offset += 4
            hostname = data[offset:offset + hostname_length].decode(errors="replace")
            offset += hostname_length
            gamemode_length = struct.unpack("<I", data[offset:offset + 4])[0]
            offset += 4
            gamemode = data[offset:offset + gamemode_length].decode(errors="replace")
            offset += gamemode_length
            mapname_length = struct.unpack("<I", data[offset:offset + 4])[0]
            offset += 4
            mapname = data[offset:offset + mapname_length].decode(errors="replace")

            return {
                "hostname": hostname,
                "gamemode": gamemode,
                "players": players,
                "maxplayers": maxplayers,
                "mapname": mapname,
            }
        except Exception as e:
            print(f"[SAMPQueryAPI] Erro ao analisar dados: {e}")
            return None


async def setup(bot):
    await bot.add_cog(SampListener(bot))
