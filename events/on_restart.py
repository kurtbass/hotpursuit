from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
from utils.database import get_status_by_id
import logging

logger = logging.getLogger(__name__)

class OnRestartEvent(commands.Cog):
    """Cog para gerenciar a restauração do último status ao reiniciar o bot."""

    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self.bot, 'ready_event_triggered'):
            self.bot.ready_event_triggered = False

    async def apply_status(self, status_id: int) -> bool:
        """
        Aplica o status ao bot com base no ID fornecido.
        
        :param status_id: ID do status na tabela `status`.
        :return: True se o status foi aplicado com sucesso, False caso contrário.
        """
        try:
            # Recuperar dados do status pelo ID
            status_data = get_status_by_id(status_id)
            if not status_data:
                logger.warning(f"Nenhum status encontrado para o ID {status_id}.")
                return False

            # Desconstruir os dados do status
            status_type, status_message, status_status = status_data

            # Mapear status de presença do Discord
            status_map = {
                'online': discord.Status.online,
                'dnd': discord.Status.dnd,
                'idle': discord.Status.idle,
                'invisible': discord.Status.invisible
            }

            # Definir atividade com base no tipo
            activity = None
            if status_type == '1':  # Jogando
                activity = discord.Game(name=status_message)
            elif status_type == '2':  # Transmitindo
                activity = discord.Streaming(name=status_message, url="https://www.twitch.tv/seu_canal")
            elif status_type == '3':  # Ouvindo
                activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)
            elif status_type == '4':  # Assistindo
                activity = discord.Activity(type=discord.ActivityType.watching, name=status_message)

            # Aplicar presença no bot
            await self.bot.change_presence(
                activity=activity,
                status=status_map.get(status_status, discord.Status.online)
            )
            logger.info(f"✅ Status aplicado com sucesso: '{status_message}' ({status_status}).")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao aplicar o status do ID {status_id}: {e}")
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento disparado quando o bot está pronto."""
        if not self.bot.ready_event_triggered:
            self.bot.ready_event_triggered = True

            logger.info("🔄 Tentando restaurar o último status...")

            # Tentar aplicar o status padrão (ID 2)
            if await self.apply_status(2):
                logger.info("✅ Status principal (ID 2) restaurado com sucesso.")
            else:
                # Caso falhe, usar o status de fallback (ID 1)
                logger.warning("⚠️ Falha ao restaurar o status principal. Tentando aplicar o fallback (ID 1)...")
                if await self.apply_status(1):
                    logger.info("✅ Status de fallback (ID 1) restaurado com sucesso.")
                else:
                    logger.warning("⚠️ Nenhum status pôde ser restaurado. O bot usará o status padrão.")

async def setup(bot):
    """Função para adicionar o cog ao bot."""
    await bot.add_cog(OnRestartEvent(bot))
