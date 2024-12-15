from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import asyncio
import logging
from utils.config import TOKEN, INTENTS, get_config
from utils.database import get_prefix
from utils.event_loader import load_events
from utils.command_loader import load_commands
from discord.ext import commands
from colorama import init, Fore, Style

# Inicializar o Colorama para saída colorida no terminal
init(autoreset=True)

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s {Fore.YELLOW}[%(levelname)s]{Style.RESET_ALL} %(message)s"
)
logger = logging.getLogger(__name__)

# Obter prefixo do banco de dados com fallback para "!" se não estiver configurado
prefix: str = get_prefix() or "!"
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
        if not TOKEN:
            raise ValueError("O TOKEN do bot não está configurado. Verifique o arquivo .env ou as variáveis de ambiente.")
        
        async with bot:
            logger.info(f"{Fore.CYAN}Iniciando o carregamento de eventos e comandos...{Style.RESET_ALL}")
            
            # Carregar eventos
            try:
                await load_events(bot)
                logger.info(f"{Fore.GREEN}Eventos carregados com sucesso.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Erro ao carregar eventos: {e}{Style.RESET_ALL}")

            # Carregar comandos
            try:
                await load_commands(bot)
                logger.info(f"{Fore.GREEN}Comandos carregados com sucesso.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Erro ao carregar comandos: {e}{Style.RESET_ALL}")

            logger.info(f"{Fore.CYAN}Iniciando o bot...{Style.RESET_ALL}")
            await bot.start(TOKEN)
    except asyncio.CancelledError:
        logger.warning(f"{Fore.CYAN}Tarefa cancelada. Desconectando...{Style.RESET_ALL}")
    except KeyboardInterrupt:
        logger.warning(f"{Fore.CYAN}Bot encerrado manualmente. Desconectando...{Style.RESET_ALL}")
    except ValueError as ve:
        logger.critical(f"{Fore.RED}Erro de configuração: {ve}{Style.RESET_ALL}")
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
