import sqlite3
import logging
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
import os

# Configuração de logs
logger = logging.getLogger(__name__)

# Localização do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection() -> sqlite3.Connection:
    """
    Cria e retorna uma conexão com o banco de dados.
    """
    try:
        return sqlite3.connect(DATABASE_URL)
    except sqlite3.Error as e:
        logger.critical(f"Erro ao conectar ao banco de dados: {e}")
        raise

def execute_query(query: str, params: Tuple = ()) -> Optional[int]:
    """
    Executa uma query no banco de dados e retorna o número de linhas afetadas.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            rows_affected = cursor.rowcount
            logger.debug(f"Query executada: {query} | Linhas afetadas: {rows_affected}")
            return rows_affected
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetchone(query: str, params: Tuple = ()) -> Optional[Tuple]:
    """
    Executa uma query e retorna um único resultado.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            logger.debug(f"Resultado da fetchone: {result}")
            return result
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetchall(query: str, params: Tuple = ()) -> List[Tuple]:
    """
    Executa uma query e retorna todos os resultados.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Resultados da fetchall: {results}")
            return results
    except sqlite3.Error as e:
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
        logger.info(f"Prefixo obtido do banco de dados: {prefix}")
        return prefix
    logger.warning("Prefixo não encontrado, usando padrão (!).")
    return "!"

def get_status_by_id(status_id: int) -> Optional[Tuple]:
    """
    Obtém os dados do status pelo ID na tabela 'status'.
    """
    query = 'SELECT status_type, status_message, status_status FROM status WHERE id = ?'
    result = fetchone(query, (status_id,))
    if result:
        logger.info(f"Status carregado: {result}")
        return result
    logger.warning(f"Nenhum status encontrado com o ID: {status_id}")
    return None

def get_restart_data() -> Tuple[int, Optional[str], Optional[str]]:
    """
    Obtém os dados de reinício do bot armazenados na tabela 'restart'.
    """
    query = 'SELECT restart_status, canal, user FROM restart WHERE rowid = 1'
    result = fetchone(query)
    if result:
        logger.info(f"Dados de reinício carregados: {result}")
        return result
    logger.warning("Nenhum dado de reinício encontrado. Usando valores padrão.")
    return (0, None, None)

# Novas funções para gerenciamento de volume

def get_user_volume(user_id: int) -> float:
    """
    Obtém o volume do usuário pelo ID. Retorna 1.0 (100%) se não encontrado.
    """
    query = "SELECT volume FROM volume WHERE user = ?"
    result = fetchone(query, (user_id,))
    if result:
        logger.info(f"Volume carregado para o usuário {user_id}: {result[0]}")
        return int(result[0]) / 100  # Converter de inteiro (0-100) para decimal (0.0-1.0)
    logger.warning(f"Nenhum volume encontrado para o usuário {user_id}, usando padrão.")
    return 1.0  # Volume padrão (100%

def set_user_volume(user_id: int, volume: int) -> None:
    """
    Define ou atualiza o volume de um usuário na tabela 'volume'.
    """
    try:
        query = """
        INSERT INTO volume (user, volume)
        VALUES (?, ?)
        ON CONFLICT(user) DO UPDATE SET volume = excluded.volume
        """
        execute_query(query, (user_id, volume))
        logger.info(f"Volume atualizado para o usuário {user_id}: {volume}%")
    except Exception as e:
        logger.error(f"Erro ao definir volume para o usuário {user_id}: {e}")

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
