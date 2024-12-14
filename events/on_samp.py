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
        self.server_ip = "15.235.123.105"
        self.server_port = 7777
        self.samp_query = SampQueryAPI(self.server_ip, self.server_port)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener ativado quando o bot está pronto. Verifica a categoria e status inicial.
        """
        print("[SAMP LISTENER] Iniciando validação inicial...")

        # Verificar a categoria e os canais
        category_valid = await self.verify_category()
        if not category_valid:
            print("[SAMP LISTENER] Categoria ou canais inválidos. Listener permanecerá desligado.")
            self.status = "off"
            return

        # Buscar informações do servidor
        server_online = await self.fetch_server_info()
        if server_online:
            print("[SAMP LISTENER] Informações do servidor verificadas. Listener ativado.")
            self.status = "on"
        else:
            print("[SAMP LISTENER] Falha ao obter informações do servidor. Listener permanecerá desligado.")
            self.status = "off"

    async def verify_category(self):
        """
        Verifica se a categoria e os canais necessários estão configurados no servidor.
        """
        category_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", ("samp_categoria",))
        if not category_id:
            print("[SAMP LISTENER] Categoria não configurada no banco de dados.")
            return False

        category = discord.utils.get(self.bot.guilds[0].categories, id=category_id[0])
        if not category:
            print("[SAMP LISTENER] Categoria não encontrada no servidor.")
            return False

        required_channels = ["samp_status", "samp_jogadores"]
        for channel_type in required_channels:
            channel_id = fetchone("SELECT id FROM canais WHERE tipodecanal = ?", (channel_type,))
            if not channel_id or not self.bot.get_channel(channel_id[0]):
                print(f"[SAMP LISTENER] Canal '{channel_type}' não encontrado ou configurado incorretamente.")
                return False

        print("[SAMP LISTENER] Categoria e canais configurados corretamente.")
        return True

    async def fetch_server_info(self):
        """
        Obtém informações do servidor SA-MP sob demanda.
        """
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
                    print("[SAMP LISTENER] Informações do servidor obtidas com sucesso.")
                    return True
            else:
                print("[SAMP LISTENER] Servidor SA-MP está offline ou inacessível.")
        except Exception as e:
            print(f"[SAMP LISTENER] Erro ao buscar informações do servidor: {e}")

        self.server_info = None
        self.players = {"online": 0, "max": 0}
        return False

    def get_status(self):
        return self.status

    def get_server_info(self):
        """
        Retorna as informações do servidor.
        """
        return self.server_info

    def get_player_info(self):
        """
        Retorna as informações dos jogadores.
        """
        return self.players


class SampQueryAPI:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(15)

    def is_online(self):
        """
        Verifica se o servidor está online.
        """
        try:
            self.socket.sendto(self._build_packet("i"), (self.ip, self.port))
            data, _ = self.socket.recvfrom(4096)
            return data.startswith(b"SAMP")
        except Exception as e:
            print(f"[SAMPQueryAPI] Erro ao conectar: {e}")
            return False

    def get_info(self):
        """
        Obtém informações do servidor.
        """
        try:
            self.socket.sendto(self._build_packet("i"), (self.ip, self.port))
            data, _ = self.socket.recvfrom(4096)
            return self._parse_info(data)
        except Exception as e:
            print(f"[SAMPQueryAPI] Erro ao buscar informações: {e}")
            return None

    def _build_packet(self, payload):
        """
        Constrói o pacote de consulta para o servidor SA-MP.
        """
        ip_parts = [int(x) for x in self.ip.split(".")]
        port_low = self.port & 0xFF
        port_high = (self.port >> 8) & 0xFF
        return b"SAMP" + bytes(ip_parts) + bytes([port_low, port_high]) + payload.encode()

    def _parse_info(self, data):
        """
        Analisa os dados recebidos do servidor.
        """
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
