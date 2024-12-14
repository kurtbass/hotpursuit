from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import os
import logging
from colorama import Fore, Style
from commands.music.musicsystem.music_system import MusicManager

# Configuração de logs
logger = logging.getLogger(__name__)

async def load_commands(bot):
    """
    Carrega comandos do bot a partir das pastas 'commands', 'commands/music' e 'commands/samp'.
    """
    # Inicializa o MusicManager
    music_manager = MusicManager(bot)

    base_path = "./commands"
    logger.info(f"{Fore.CYAN}🔍 Iniciando o carregamento dos comandos no caminho: {base_path}{Style.RESET_ALL}")

    if not os.path.exists(base_path):
        logger.warning(f"{Fore.RED}⚠️ A pasta '{base_path}' não foi encontrada. Nenhum comando será carregado.{Style.RESET_ALL}")
        return

    # Carregar comandos da pasta base (commands)
    await _load_subfolder_commands(bot, base_path, "commands")

    # Verificar e carregar comandos da subpasta 'music'
    music_path = os.path.join(base_path, "music")
    if os.path.exists(music_path):
        logger.info(f"{Fore.YELLOW}🎵 Carregando comandos da subpasta 'music': {music_path}{Style.RESET_ALL}")
        await _load_subfolder_commands(bot, music_path, "commands.music", music_manager=music_manager)
    else:
        logger.warning(f"{Fore.RED}⚠️ A subpasta 'music' não foi encontrada. Nenhum comando de música será carregado.{Style.RESET_ALL}")

    # Verificar e carregar comandos da subpasta 'samp'
    samp_path = os.path.join(base_path, "samp")
    if os.path.exists(samp_path):
        logger.info(f"{Fore.YELLOW}🕹️ Carregando comandos da subpasta 'samp': {samp_path}{Style.RESET_ALL}")
        await _load_subfolder_commands(bot, samp_path, "commands.samp")
    else:
        logger.warning(f"{Fore.RED}⚠️ A subpasta 'samp' não foi encontrada. Nenhum comando relacionado ao SAMP será carregado.{Style.RESET_ALL}")

    logger.info(f"{Fore.CYAN}✅ Carregamento dos comandos concluído.{Style.RESET_ALL}")


async def _load_subfolder_commands(bot, path, module_prefix, music_manager=None):
    """
    Carrega comandos de uma subpasta específica.

    :param bot: Instância do bot.
    :param path: Caminho da subpasta a ser carregada.
    :param module_prefix: Prefixo do módulo para importação.
    :param music_manager: Instância de MusicManager para passar aos módulos de música (opcional).
    """
    for filename in os.listdir(path):
        if filename.endswith(".py") and not filename.startswith("__"):
            command_name = filename[:-3]
            try:
                # Carregar módulo e chamar setup manualmente
                module = __import__(f"{module_prefix}.{command_name}", fromlist=["setup"])
                if hasattr(module, "setup") and callable(module.setup):
                    if music_manager and "music" in module_prefix:
                        await module.setup(bot, music_manager)
                    else:
                        await module.setup(bot)
                    logger.info(f"{Fore.GREEN}✅ Comando '{module_prefix}.{command_name}' carregado com sucesso.{Style.RESET_ALL}")
                else:
                    logger.warning(f"{Fore.RED}⚠️ O comando '{module_prefix}.{command_name}' não possui uma função 'setup'.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}❌ Erro ao carregar o comando '{module_prefix}.{command_name}': {str(e)}{Style.RESET_ALL}")
