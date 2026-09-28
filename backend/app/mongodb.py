"""Conexao com MongoDB (Motor).

O MongoDB guarda os dados de historico, com esquema flexivel:
- daily_logs: diario do tutor (peso, sintomas, escala de dor) - RF-02/RF-03
- exams: exames com campos que variam por tipo

O banco relacional continua com os dados centrais (tutores, pacientes,
protocolos, sessoes). Os documentos referenciam o paciente por pet_id, que
e o id da tabela pets (RNF-03).
"""

from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URL, MONGODB_DB_NAME

client: AsyncIOMotorClient = None
db = None


async def create_indexes(database):
    """Indices usados nas consultas por paciente e por data."""
    await database.exams.create_index("pet_id")
    await database.exams.create_index("exam_type")
    await database.daily_logs.create_index([("pet_id", 1), ("date", -1)])


async def connect_mongodb():
    """Inicia conexao com MongoDB."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    await create_indexes(db)
    print(f"MongoDB conectado: {MONGODB_DB_NAME}")


async def close_mongodb():
    """Fecha conexao com MongoDB."""
    global client
    if client:
        client.close()


def get_exams_collection():
    """Retorna a collection de exames."""
    return db.exams


def get_daily_logs_collection():
    """Retorna a collection do diario do tutor."""
    return db.daily_logs
