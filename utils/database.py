import sqlite3
import logging
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
import os

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

def execute_query(query: str, params: Tuple = ()) -> Optional[int]:
    """
    Executa uma query no banco de dados e retorna o número de linhas afetadas.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetch_one_or_none(query: str, params: Tuple = ()) -> Optional[Tuple]:
    """
    Executa uma query e retorna um único resultado ou None.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}': {e}")
        return None

def fetch_all(query: str, params: Tuple = ()) -> List[Tuple]:
    """
    Executa uma query e retorna todos os resultados.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar a query '{query}': {e}")
        return []

def get_config(key: str) -> Optional[str]:
    """
    Obtém um valor da tabela 'configs' pelo seu key.
    """
    query = 'SELECT value FROM configs WHERE key = ?'
    result = fetch_one_or_none(query, (key,))
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
    return fetch_one_or_none(query, (status_id,))

def get_restart_data() -> Tuple[int, Optional[str], Optional[str]]:
    """
    Obtém os dados de reinício do bot armazenados na tabela 'restart'.
    """
    query = 'SELECT restart_status, canal, user FROM restart WHERE rowid = 1'
    result = fetch_one_or_none(query)
    return result if result else (0, None, None)

# Novas funções para gerenciamento de volume

def get_user_volume(user_id: int) -> float:
    """
    Obtém o volume do usuário. Retorna 1.0 (padrão) se não estiver definido.
    """
    query = "SELECT volume FROM volume WHERE user = ?"
    result = fetch_one_or_none(query, (user_id,))
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
    return fetch_all(query)

def get_formulario_by_id(idform: int) -> Optional[Tuple]:
    """
    Retorna um formulário específico pelo 'idform'.
    """
    query = "SELECT * FROM formularios WHERE idform = ?"
    return fetch_one_or_none(query, (idform,))

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
