import sqlite3
import logging
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
import os
import random
import discord

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está definida. Verifique o arquivo .env ou as variáveis de ambiente.")

def get_db_connection() -> sqlite3.Connection:
    """
    Cria e retorna uma conexão com o banco de dados.
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        return conn
    except sqlite3.Error as e:
        logger.critical(f"Erro ao conectar ao banco de dados: {e}")
        raise

def check_database():
    """
    Verifica se as tabelas obrigatórias estão presentes no banco de dados.
    """
    required_tables = ["configs", "formularios", "volume"]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                logger.error(f"Tabela obrigatória '{table}' não encontrada no banco de dados.")
                raise RuntimeError(f"Tabela '{table}' está faltando no banco de dados.")

def execute_query(query: str, params: Tuple = (), log: bool = True) -> Optional[int]:
    """
    Executa uma query no banco de dados e retorna o número de linhas afetadas.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if log:
                logger.debug(f"Query executada: {query} | Parâmetros: {params} | Linhas afetadas: {cursor.rowcount}")
            return cursor.rowcount
    except sqlite3.Error as e:
        if log:
            logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetchone(query: str, params: Tuple = (), log: bool = True) -> Optional[Tuple]:
    """
    Executa uma query e retorna um único resultado ou None.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            if log:
                logger.debug(f"Query executada: {query} | Parâmetros: {params} | Resultado: {result}")
            return result
    except sqlite3.Error as e:
        if log:
            logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetchall(query: str, params: Tuple = (), log: bool = True) -> List[Tuple]:
    """
    Executa uma query e retorna todos os resultados.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            if log:
                logger.debug(f"Query executada: {query} | Parâmetros: {params} | Resultados: {results}")
            return results
    except sqlite3.Error as e:
        if log:
            logger.error(f"Erro ao executar a query '{query}': {e}")
        return []

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Obtém um valor da tabela 'configs' pelo seu key.
    """
    query = 'SELECT value FROM configs WHERE key = ?'
    result = fetchone(query, (key,))
    if result:
        return result[0]
    logger.warning(f"Configuração não encontrada para a chave: {key}")
    return default

def get_prefix() -> str:
    """
    Obtém o prefixo do bot armazenado na tabela 'configs'.
    """
    return get_config("PREFIXO", "!")

def get_status_by_id(status_id: int) -> Optional[Tuple]:
    """
    Obtém os dados do status pelo ID na tabela 'status'.
    """
    query = 'SELECT status_type, status_message, status_status FROM status WHERE id = ?'
    return fetchone(query, (status_id,))

def get_restart_data() -> Tuple[int, Optional[str], Optional[str]]:
    """
    Obtém os dados de reinício do bot armazenados na tabela 'restart'.
    """
    query = 'SELECT restart_status, canal, user FROM restart WHERE rowid = 1'
    result = fetchone(query)
    return result if result else (0, None, None)

# Funções para gerenciamento de volume
def get_user_volume(user_id: int) -> float:
    """
    Obtém o volume do usuário. Retorna 1.0 (padrão) se não estiver definido.
    """
    query = "SELECT volume FROM volume WHERE user = ?"
    result = fetchone(query, (user_id,))
    logger.debug(f"Volume para o usuário {user_id}: {result}")
    return result[0] / 100 if result else 1.0

def set_user_volume(user_id: int, volume: int) -> None:
    """
    Define o volume do usuário, atualizando-o se já existir.

    :param user_id: ID do usuário.
    :param volume: Volume como inteiro (0 a 100).
    """
    if not 0 <= volume <= 100:
        raise ValueError("O volume deve estar entre 0 e 100")  # Ajuste da validação

    query = """
    INSERT INTO volume (user, volume)
    VALUES (?, ?)
    ON CONFLICT(user) DO UPDATE SET volume = excluded.volume
    """
    execute_query(query, (user_id, volume))
    logger.info(f"Volume ajustado para {volume}% para o usuário {user_id}.")

# Cor do embed
def get_embed_color() -> discord.Colour:
    """
    Obtém a cor da tabela 'configs' com a key 'EMBED_COLOR'.
    Se não houver valor válido, retorna uma cor aleatória como `discord.Colour`.
    """
    query = "SELECT value FROM configs WHERE key = ?"
    result = fetchone(query, ("EMBED_COLOR",))

    if result and result[0]:
        color_value = result[0].strip()
        if color_value.startswith("0x"):
            color_value = color_value[2:]
        try:
            if len(color_value) == 6:
                return discord.Colour(int(color_value, 16))
        except ValueError:
            pass
    return discord.Colour.random()

def get_emoji_from_table(table_name: str, identifier: str) -> Optional[str]:
    """
    Obtém o código do emoji de uma tabela específica baseado no identifier.
    
    :param table_name: Nome da tabela onde o emoji está armazenado.
    :param identifier: Identificador único do emoji.
    :return: Código do emoji (<:name:id> ou <a:name:id>) ou None se não encontrado.
    """
    query = f"SELECT emoji_code FROM {table_name} WHERE identifier = ?"
    result = fetchone(query, (identifier,))
    if result:
        return result[0]
    logger.warning(f"Emoji não encontrado na tabela '{table_name}' para o identificador '{identifier}'.")
    return None

def get_music_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_music'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_music", identifier)

def get_error_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_errors'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_errors", identifier)

def get_fun_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_fun'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_fun", identifier)

def get_number_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_numbers'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_numbers", identifier)

def get_clan_management_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_clan_management'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_clan_management", identifier)

def get_server_staff_emoji(identifier: str) -> Optional[str]:
    """
    Obtém um emoji da tabela 'emojis_server_staff'.
    
    :param identifier: Identificador único do emoji.
    :return: Código do emoji ou None se não encontrado.
    """
    return get_emoji_from_table("emojis_server_staff", identifier)

