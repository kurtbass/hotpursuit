import asyncio
import logging
from utils.config import TOKEN, INTENTS, get_config
from utils.database import get_prefix
from utils.event_loader import load_events
from utils.command_loader import load_commands
from discord.ext import commands
from colorama import init, Fore, Style
import sys

# Inicializar o Colorama para saída colorida no terminal
init(autoreset=True)

# Configuração de logs
logging.basicConfig(level=logging.INFO, format=f"%(asctime)s {Fore.YELLOW}[%(levelname)s]{Style.RESET_ALL} %(message)s")
logger = logging.getLogger(__name__)

# Obter prefixo do banco de dados com fallback para "!" se não estiver configurado
prefix = get_prefix() or "!"
bot = commands.Bot(command_prefix=prefix, intents=INTENTS)

@bot.event
async def on_ready():
    """
    Evento acionado quando o bot está pronto.
    """
    logger.info(f"{Fore.GREEN}Bot conectado como {bot.user}!{Style.RESET_ALL}")

async def main():
    """
    Função principal para inicializar o bot.
    """
    try:
        async with bot:
            await load_events(bot)  # Carrega eventos do bot
            await load_commands(bot)  # Carrega comandos do bot
            await bot.start(TOKEN)  # Inicia o bot
    except asyncio.CancelledError:
        logger.warning(f"{Fore.CYAN}Tarefa cancelada. Desconectando...{Style.RESET_ALL}")
    except KeyboardInterrupt:
        logger.warning(f"{Fore.CYAN}Bot encerrado manualmente. Desconectando...{Style.RESET_ALL}")
    except Exception as e:
        logger.critical(f"{Fore.RED}Erro crítico na execução do bot: {e}{Style.RESET_ALL}")
    finally:
        logger.info(f"{Fore.CYAN}Encerrando o bot.{Style.RESET_ALL}")
        await bot.close()  # Garante que o bot desconecta corretamente

# Executar o bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{Fore.CYAN}Execução interrompida pelo usuário.{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}Erro inesperado ao iniciar o bot: {e}{Style.RESET_ALL}")
