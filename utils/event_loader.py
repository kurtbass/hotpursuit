import os
import logging
from colorama import Fore, Style

logger = logging.getLogger(__name__)

async def load_events(bot):
    """
    Carrega eventos do bot a partir da pasta 'events'.
    """
    events_path = "./events"
    logger.info(f"{Fore.CYAN}Verificando a pasta de eventos: {events_path}{Style.RESET_ALL}")

    if not os.path.exists(events_path):
        logger.warning(f"{Fore.RED}Pasta '{events_path}' não encontrada. Nenhum evento será carregado.{Style.RESET_ALL}")
        return

    for filename in os.listdir(events_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            event_name = filename[:-3]
            try:
                await bot.load_extension(f"events.{event_name}")
                logger.info(f"{Fore.GREEN}Evento '{event_name}' carregado com sucesso.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Falha ao carregar o evento '{event_name}': {e}{Style.RESET_ALL}")
