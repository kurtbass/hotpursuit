from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import discord
from discord.ext import commands
from utils.database import get_status_by_id
import logging

logger = logging.getLogger(__name__)

class OnRestartEvent(commands.Cog):
    """Evento para restaurar o último status ao reiniciar o bot."""

    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self.bot, 'ready_event_triggered'):
            self.bot.ready_event_triggered = False

    async def apply_status(self, status_id):
        """
        Aplica o status com base no ID fornecido.
        :param status_id: ID do status na tabela `status`.
        """
        try:
            status_data = get_status_by_id(status_id)
            if not status_data:
                logger.warning(f"Nenhum status encontrado para o ID {status_id}.")
                return False

            status_type, status_message, status_status = status_data
            status_map = {
                'online': discord.Status.online,
                'dnd': discord.Status.dnd,
                'idle': discord.Status.idle,
                'invisible': discord.Status.invisible
            }

            activity = None
            if status_type == '1':  # Jogando
                activity = discord.Game(name=status_message)
            elif status_type == '2':  # Transmitindo
                activity = discord.Streaming(name=status_message, url="https://www.twitch.tv/seu_canal")
            elif status_type == '3':  # Ouvindo
                activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)
            elif status_type == '4':  # Assistindo
                activity = discord.Activity(type=discord.ActivityType.watching, name=status_message)

            await self.bot.change_presence(activity=activity, status=status_map.get(status_status, discord.Status.online))
            logger.info(f"Status aplicado: {status_message} ({status_status})")
            return True

        except Exception as e:
            logger.error(f"Erro ao aplicar o status do banco de dados: {e}")
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento acionado quando o bot está pronto."""
        if not self.bot.ready_event_triggered:
            self.bot.ready_event_triggered = True

            # Tentar aplicar o status na linha 2
            if await self.apply_status(2):
                logger.info("Status do ID 2 aplicado com sucesso.")
            else:
                # Se falhar, usar o status na linha 1 como fallback
                if await self.apply_status(1):
                    logger.info("Status de fallback (ID 1) aplicado com sucesso.")
                else:
                    logger.warning("Nenhum status foi aplicado. Status padrão do bot será usado.")

async def setup(bot):
    """Adiciona o evento ao bot."""
    await bot.add_cog(OnRestartEvent(bot))
