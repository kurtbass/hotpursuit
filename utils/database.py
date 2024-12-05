
import sqlite3
import logging
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
import os
import random

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.critical("DATABASE_URL não está definida. Verifique o arquivo .env ou as variáveis de ambiente.")

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

def execute_query(query: str, params: Tuple = (), log: bool = True) -> Optional[int]:
    """
    Executa uma query no banco de dados e retorna o número de linhas afetadas.

    :param query: Query SQL a ser executada.
    :param params: Parâmetros para a query.
    :param log: Define se a execução da query deve ser registrada no log.
    :return: Número de linhas afetadas ou None em caso de erro.
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

    :param query: Query SQL a ser executada.
    :param params: Parâmetros para a query.
    :param log: Define se a execução da query deve ser registrada no log.
    :return: Resultado único como uma tupla, ou None se não houver resultado.
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

    :param query: Query SQL a ser executada.
    :param params: Parâmetros para a query.
    :param log: Define se a execução da query deve ser registrada no log.
    :return: Lista de tuplas contendo os resultados.
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

def get_config(key: str) -> Optional[str]:
    """
    Obtém um valor da tabela 'configs' pelo seu key.
    """
    query = 'SELECT value FROM configs WHERE key = ?'
    result = fetchone(query, (key,))
    if result:
        return result[0]
    logger.warning(f"Configuração não encontrada para a chave: {key}")
    return None

def get_prefix() -> str:
    """
    Obtém o prefixo do bot armazenado na tabela 'configs'.
    """
    prefix = get_config("PREFIXO")
    if prefix:
        return prefix
    return "!"

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
    return float(result[0]) / 100 if result else 1.0

def set_user_volume(user_id: int, volume: float) -> None:
    """
    Define o volume do usuário, atualizando-o se já existir.
    """
    query = """
    INSERT INTO volume (user, volume)
    VALUES (?, ?)
    ON CONFLICT(user) DO UPDATE SET volume = excluded.volume
    """
    execute_query(query, (user_id, volume))

# Funções para gerenciamento de formulários

def insert_formulario(nomecompleto: str, nick: str, idade: int, datadenascimento: str):
    """
    Insere um novo formulário na tabela de 'formularios'.
    """
    query = """
    INSERT INTO formularios (nomecompleto, nick, idade, datadenascimento)
    VALUES (?, ?, ?, ?)
    """
    params = (nomecompleto, nick, idade, datadenascimento)
    return execute_query(query, params)

def get_all_formularios() -> List[Tuple]:
    """
    Retorna todos os formulários da tabela 'formularios'.
    """
    query = "SELECT * FROM formularios"
    return fetchall(query)

def get_formulario_by_id(idform: int) -> Optional[Tuple]:
    """
    Retorna um formulário específico pelo 'idform'.
    """
    query = "SELECT * FROM formularios WHERE idform = ?"
    return fetchone(query, (idform,))

def update_formulario(idform: int, nomecompleto: Optional[str] = None, idade: Optional[int] = None) -> Optional[int]:
    """
    Atualiza os dados de um formulário específico.
    """
    query = "UPDATE formularios SET nomecompleto = ?, idade = ? WHERE idform = ?"
    params = (nomecompleto, idade, idform)
    return execute_query(query, params)

def delete_formulario(idform: int) -> Optional[int]:
    """
    Exclui um formulário específico pelo 'idform'.
    """
    query = "DELETE FROM formularios WHERE idform = ?"
    return execute_query(query, (idform,))

import random

import discord

import discord

import discord

def get_embed_color() -> discord.Colour:
    """
    Obtém a cor da tabela 'configs' com a key 'EMBED_COLOR'.
    Se não houver valor válido, retorna uma cor aleatória como `discord.Colour`.
    """
    query = "SELECT value FROM configs WHERE key = ?"
    result = fetchone(query, ("EMBED_COLOR",))

    if result and result[0]:
        color_value = result[0].strip()
        
        # Valida se é um hexadecimal válido
        if color_value.startswith("0x"):
            color_value = color_value[2:]  # Remove o prefixo '0x'
        
        try:
            if len(color_value) == 6:
                return discord.Colour(int(color_value, 16))
        except ValueError:
            pass  # Silencia erros de valor inválido

    # Gera e retorna uma cor aleatória
    return discord.Colour.random()
