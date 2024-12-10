import os
import logging
from colorama import Fore, Style
from commands.music.musicsystem.music_system import MusicManager

logger = logging.getLogger(__name__)

async def load_commands(bot):
    """
    Carrega comandos do bot a partir da pasta 'commands' e 'commands/music'.
    """
    # Inicialize o MusicManager aqui, passando o bot como argumento
    music_manager = MusicManager(bot)

    base_path = "./commands"
    logger.info(f"{Fore.CYAN}Iniciando o carregamento dos comandos do caminho: {base_path}{Style.RESET_ALL}")

    if not os.path.exists(base_path):
        logger.warning(f"{Fore.RED}A pasta '{base_path}' não foi encontrada. Nenhum comando será carregado.{Style.RESET_ALL}")
        return

    # Carregar comandos da pasta base (commands)
    logger.info(f"{Fore.YELLOW}Carregando comandos da pasta base: {base_path}{Style.RESET_ALL}")
    for filename in os.listdir(base_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            command_name = filename[:-3]
            try:
                await bot.load_extension(f"commands.{command_name}")
                logger.info(f"{Fore.GREEN}Comando 'commands.{command_name}' carregado com sucesso.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Erro ao carregar o comando 'commands.{command_name}': {e}{Style.RESET_ALL}")

    # Verificar e carregar comandos da subpasta 'music'
    music_path = os.path.join(base_path, "music")
    if os.path.exists(music_path):
        logger.info(f"{Fore.YELLOW}Carregando comandos da subpasta: {music_path}{Style.RESET_ALL}")
        for filename in os.listdir(music_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                command_name = filename[:-3]
                try:
                    # Carregar módulo e chamar setup manualmente
                    module = __import__(f"commands.music.{command_name}", fromlist=["setup"])
                    if hasattr(module, "setup"):
                        await module.setup(bot, music_manager)  # Passar o MusicManager
                        logger.info(f"{Fore.GREEN}Comando 'commands.music.{command_name}' carregado com sucesso.{Style.RESET_ALL}")
                    else:
                        logger.warning(f"{Fore.RED}O comando 'commands.music.{command_name}' não possui uma função 'setup'.{Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"{Fore.RED}Erro ao carregar o comando 'commands.music.{command_name}': {e}{Style.RESET_ALL}")
    else:
        logger.warning(f"{Fore.RED}A subpasta 'music' não foi encontrada dentro de '{base_path}'. Nenhum comando de música será carregado.{Style.RESET_ALL}")

    logger.info(f"{Fore.CYAN}Carregamento dos comandos concluído.{Style.RESET_ALL}")
