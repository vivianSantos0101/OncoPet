"""Conexao com MongoDB para armazenamento de exames.

MongoDB armazena documentos semi-estruturados (exames com campos variaveis).
SQLite continua sendo o banco principal para dados relacionais.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URL, MONGODB_DB_NAME

client: AsyncIOMotorClient = None
db = None


async def connect_mongodb():
    """Inicia conexao com MongoDB."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    # Cria indice no campo pet_id para buscas rapidas
    await db.exams.create_index("pet_id")
    await db.exams.create_index("exam_type")
    print(f"MongoDB conectado: {MONGODB_DB_NAME}")


async def close_mongodb():
    """Fecha conexao com MongoDB."""
    global client
    if client:
        client.close()


def get_exams_collection():
    """Retorna a collection de exames."""
    return db.exams
