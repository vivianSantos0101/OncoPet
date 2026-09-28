"""Diario do tutor no MongoDB (colecao daily_logs) - RF-02/RF-03.

Cada documento referencia o paciente pelo id da tabela pets do banco
relacional (pet_id). A API valida esse id no banco relacional antes de
gravar, para manter a integridade entre os dois bancos (RNF-03).
"""

from datetime import date, datetime, timezone
from typing import List, Optional

from ..schemas import RecordCreate, RecordResponse


def to_document(data: RecordCreate, created_by: int) -> dict:
    doc = data.model_dump()
    doc["date"] = data.date.isoformat()  # 'AAAA-MM-DD': ordena como texto
    doc["created_by"] = created_by
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    return doc


def to_response(doc: dict) -> RecordResponse:
    return RecordResponse(
        id=str(doc["_id"]),
        pet_id=doc["pet_id"],
        date=date.fromisoformat(doc["date"]),
        weight=doc.get("weight"),
        symptoms=doc.get("symptoms") or [],
        other_symptoms=doc.get("other_symptoms"),
        pain_score=doc.get("pain_score"),
        general_status=doc.get("general_status"),
        appetite=doc.get("appetite"),
        energy_level=doc.get("energy_level"),
        photo_url=doc.get("photo_url"),
        notes=doc.get("notes"),
    )


async def list_logs(collection, pet_id: int, newest_first: bool = True, limit: Optional[int] = None) -> List[dict]:
    cursor = collection.find({"pet_id": pet_id}).sort("date", -1 if newest_first else 1)
    if limit:
        cursor = cursor.limit(limit)
    return [doc async for doc in cursor]
