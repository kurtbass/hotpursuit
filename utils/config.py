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


# Funções utilitárias para banco de dados
def execute_query(query, params=()):
    """
    Executa uma query no banco de dados e retorna o cursor.
    """
    try:
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            logger.debug(f"Query executada com sucesso: {query} | Parâmetros: {params}")
            return cursor
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}' com parâmetros {params}: {e}")
        return None


def fetchone(query, params=()):
    """
    Executa uma query e retorna um único resultado.
    """
    cursor = execute_query(query, params)
    if cursor:
        return cursor.fetchone()
    return None


def fetchall(query, params=()):
    """
    Executa uma query e retorna todos os resultados.
    """
    cursor = execute_query(query, params)
    if cursor:
        return cursor.fetchall()
    return []


# Funções para configurações do bot
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
    result = fetchone('SELECT restart_status, canal, user FROM restart WHERE rowid = 1')
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
    logger.info("Status de reinício restaurado com sucesso.")


# Função para obter o lema
def get_lema():
    """
    Obtém o lema, imagem do lema, e o nome do clã do banco de dados.
    Retorna uma string formatada com o nome do clã, lema e a URL da imagem correspondente.
    """
    lema = get_config("LEMA") or "Potência e Precisão, Sempre na Frente!"  # Lema padrão
    lema_img = get_config("LEMA_IMG")  # Pode ser NULL no banco
    nome_do_cla = get_config("NOME_DO_CLA") or "Hot Pursuit"  # Nome padrão do clã

    # Se a imagem do lema não estiver configurada, use o ícone do servidor
    if not lema_img:
        servidor_id = get_config("SERVIDOR")  # ID do servidor
        if servidor_id:
            lema_img = f"https://cdn.discordapp.com/icons/{servidor_id}/{servidor_id}.png?size=256"
        else:
            lema_img = None  # Não foi possível encontrar uma imagem para exibir

    return lema, lema_img, nome_do_cla


# Função necessária para registrar como extensão
async def setup(bot):
    """
    Adiciona as funções de configuração ao bot como uma extensão.
    """
    logger.info("Módulo 'utils.config' carregado com sucesso.")