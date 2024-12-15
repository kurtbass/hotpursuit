from utils.database import (
    get_emoji_from_table,
    get_fun_emoji,
    get_music_emoji,
    get_error_emoji,
    get_number_emoji,
    get_clan_management_emoji,
    get_server_staff_emoji
)
import logging
from colorama import Fore, Style

logger = logging.getLogger(__name__)

async def setup(bot):
    """
    Configura o evento 'on_ready' para o bot.
    """
    @bot.event
    async def on_ready():
        """
        Evento acionado quando o bot está pronto para operar.
        """
        logger.info(f"{Fore.GREEN}✅ Bot conectado com sucesso!{Style.RESET_ALL}")
        logger.info(f"{Fore.BLUE}🤖 Logado como: {bot.user.name}#{bot.user.discriminator}{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}🆔 ID do bot: {bot.user.id}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}🌐 Conectado em {len(bot.guilds)} servidores.{Style.RESET_ALL}")
