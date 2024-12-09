import sqlite3
import logging
import discord
from dotenv import load_dotenv
import os

# Configuração de logs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está definida no arquivo .env. Verifique suas configurações.")

# Configurações do Discord Bot
TOKEN = os.getenv('DISCORD_TOKEN')  # Token do bot
if not TOKEN:
    raise ValueError("O TOKEN do bot não foi encontrado no arquivo .env. Verifique suas configurações.")

# Configuração de Intents do Discord
INTENTS = discord.Intents.default()
INTENTS.message_content = True  # Ativar leitura de conteúdo de mensagens

def execute_query(query, params=()):
    """
    Executa uma query no banco de dados e retorna o cursor.
    """
    try:
        logger.info(f"Conectando ao banco de dados em {DATABASE_URL}")
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}' com parâmetros {params}: {e}")
        return None

def fetchone(query, params=()):
    """
    Executa uma query e retorna um único resultado.
    """
    cursor = execute_query(query, params)
    return cursor.fetchone() if cursor else None

def fetchall(query, params=()):
    """
    Executa uma query e retorna todos os resultados.
    """
    cursor = execute_query(query, params)
    return cursor.fetchall() if cursor else []

def get_config(key):
    """
    Obtém um valor da tabela 'configs' pelo seu key.
    """
    result = fetchone('SELECT value FROM configs WHERE key = ?', (key,))
    if not result:
        logger.warning(f"Configuração não encontrada para a chave: {key}")
    return result[0] if result else None

def get_prefix():
    """
    Obtém o prefixo do bot armazenado na tabela 'configs'.
    """
    result = get_config('PREFIXO')
    if not result:
        logger.warning("Prefixo não encontrado no banco de dados. Usando o valor padrão '!'.")
    return result if result else '!'

def get_restart_data():
    """
    Obtém o status de reinício da tabela 'restart'.
    """
    return fetchone('SELECT restart_status, canal, user FROM restart WHERE rowid = 1') or (0, None, None)

def clear_restart_status():
    """
    Restaura o status de reinício na tabela 'restart'.
    """
    execute_query('''
        UPDATE restart
        SET restart_status = 0, canal = NULL, user = NULL
        WHERE rowid = 1
    ''')
    logger.info("Status de reinício restaurado com sucesso.")

async def setup(bot):
    """
    Função necessária para registrar como extensão.
    Este módulo não adiciona Cogs, mas pode ser usado para inicializar logs ou testar conexões.
    """
    logger.info("Módulo 'utils.config' carregado com sucesso.")
