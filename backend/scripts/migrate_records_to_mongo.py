"""Copia o diario antigo (tabela pet_records do banco relacional) para o MongoDB.

Antes do RF-02/RF-03 os registros do tutor ficavam na tabela pet_records.
Agora ficam na colecao daily_logs do MongoDB. Este script copia o que ja
existia, sem apagar a tabela antiga, e pode ser rodado mais de uma vez
(registros ja copiados sao ignorados).

Uso (com Postgres e Mongo no ar):
    cd backend
    source .venv/bin/activate
    python scripts/migrate_records_to_mongo.py
"""

import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text  # noqa: E402

LEGACY_TABLE = "pet_records"


def _iso(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return str(value)[:10]


def migrate(engine, mongo_db) -> dict:
    """Copia pet_records -> daily_logs. mongo_db e um banco pymongo (sincrono)."""
    if not inspect(engine).has_table(LEGACY_TABLE):
        return {"migrated": 0, "skipped": 0, "table_found": False}

    migrated = skipped = 0
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT * FROM {LEGACY_TABLE} ORDER BY id")).mappings().all()

    for row in rows:
        if mongo_db.daily_logs.find_one({"migrated_from_sql_id": row["id"]}):
            skipped += 1
            continue
        mongo_db.daily_logs.insert_one({
            "pet_id": row["pet_id"],
            "date": _iso(row["date"]),
            "weight": row["weight"],
            # antes os sintomas eram texto livre; viram "outros sintomas"
            "symptoms": [],
            "other_symptoms": row["symptoms"],
            "pain_score": None,
            "general_status": row["general_status"],
            "appetite": row["appetite"],
            "energy_level": row["energy_level"],
            "photo_url": row["photo_url"],
            "notes": row["notes"],
            "created_by": row["created_by"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "migrated_from_sql_id": row["id"],
        })
        migrated += 1

    mongo_db.daily_logs.create_index([("pet_id", 1), ("date", -1)])
    return {"migrated": migrated, "skipped": skipped, "table_found": True}


def main():
    from pymongo import MongoClient

    from app.config import MONGODB_DB_NAME, MONGODB_URL
    from app.database import engine

    result = migrate(engine, MongoClient(MONGODB_URL)[MONGODB_DB_NAME])
    if not result["table_found"]:
        print(f"Tabela {LEGACY_TABLE} nao encontrada: nada para migrar.")
        return
    print(f"Registros copiados para o MongoDB: {result['migrated']}")
    print(f"Ja copiados antes (ignorados):     {result['skipped']}")
    print(f"A tabela {LEGACY_TABLE} foi mantida. Depois de conferir, pode remove-la com:")
    print(f"  DROP TABLE {LEGACY_TABLE};")


if __name__ == "__main__":
    main()
