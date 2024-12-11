from utils.database import get_emoji_from_table, get_fun_emoji, get_music_emoji, get_error_emoji, get_number_emoji, get_clan_management_emoji, get_server_staff_emoji
import sqlite3
import logging
import discord
from dotenv import load_dotenv
import os
from colorama import Fore, Style

# Configuração de logs
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s - {Fore.CYAN}%(name)s{Style.RESET_ALL} - %(levelname)s - %(message)s'
)

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.critical(f"{Fore.RED}DATABASE_URL não está definida no arquivo .env. Verifique suas configurações.{Style.RESET_ALL}")
    raise ValueError("DATABASE_URL não está definida no arquivo .env.")

# Configurações do Discord Bot
TOKEN = os.getenv('DISCORD_TOKEN')  # Token do bot
if not TOKEN:
    logger.critical(f"{Fore.RED}O TOKEN do bot não foi encontrado no arquivo .env. Verifique suas configurações.{Style.RESET_ALL}")
    raise ValueError("O TOKEN do bot não foi encontrado no arquivo .env.")

# Configuração de Intents do Discord
INTENTS = discord.Intents.default()
INTENTS.message_content = True  # Ativar leitura de conteúdo de mensagens

def execute_query(query, params=()):
    """
    Executa uma query no banco de dados e retorna o cursor.
    """
    try:
        logger.debug(f"{Fore.CYAN}Conectando ao banco de dados: {DATABASE_URL}{Style.RESET_ALL}")
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"{Fore.GREEN}Query executada com sucesso: {query} | Parâmetros: {params}{Style.RESET_ALL}")
            return cursor
    except sqlite3.Error as e:
        logger.error(f"{Fore.RED}Erro ao executar a query '{query}' com parâmetros {params}: {e}{Style.RESET_ALL}")
        return None

def fetchone(query, params=()):
    """
    Executa uma query e retorna um único resultado.
    """
    cursor = execute_query(query, params)
    if cursor:
        result = cursor.fetchone()
        logger.debug(f"{Fore.YELLOW}Resultado fetchone: {result}{Style.RESET_ALL}")
        return result
    return None

def fetchall(query, params=()):
    """
    Executa uma query e retorna todos os resultados.
    """
    cursor = execute_query(query, params)
    if cursor:
        results = cursor.fetchall()
        logger.debug(f"{Fore.YELLOW}Resultados fetchall: {results}{Style.RESET_ALL}")
        return results
    return []

def get_config(key):
    """
    Obtém um valor da tabela 'configs' pelo seu key.
    """
    result = fetchone('SELECT value FROM configs WHERE key = ?', (key,))
    if not result:
        logger.warning(f"{Fore.RED}Configuração não encontrada para a chave: {key}{Style.RESET_ALL}")
    return result[0] if result else None

def get_prefix():
    """
    Obtém o prefixo do bot armazenado na tabela 'configs'.
    """
    result = get_config('PREFIXO')
    if not result:
        logger.warning(f"{Fore.YELLOW}Prefixo não encontrado no banco de dados. Usando o valor padrão '!'.{Style.RESET_ALL}")
    return result if result else '!'

def get_restart_data():
    """
    Obtém o status de reinício da tabela 'restart'.
    """
    result = fetchone('SELECT restart_status, canal, user FROM restart WHERE rowid = 1')
    logger.debug(f"{Fore.CYAN}Dados de reinício obtidos: {result}{Style.RESET_ALL}")
    return result or (0, None, None)

def clear_restart_status():
    """
    Restaura o status de reinício na tabela 'restart'.
    """
    execute_query('''
        UPDATE restart
        SET restart_status = 0, canal = NULL, user = NULL
        WHERE rowid = 1
    ''')
    logger.info(f"{Fore.GREEN}Status de reinício restaurado com sucesso.{Style.RESET_ALL}")

async def setup(bot):
    """
    Função necessária para registrar como extensão.
    Este módulo não adiciona Cogs, mas pode ser usado para inicializar logs ou testar conexões.
    """
    logger.info(f"{Fore.CYAN}Módulo 'utils.config' carregado com sucesso.{Style.RESET_ALL}")
