"""Migracao do diario antigo (pet_records) para o MongoDB."""

import mongomock
from sqlalchemy import create_engine, text

from scripts.migrate_records_to_mongo import migrate


def legacy_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE pet_records (
                id INTEGER PRIMARY KEY, pet_id INTEGER, date DATE, weight FLOAT,
                symptoms TEXT, general_status VARCHAR, appetite VARCHAR,
                energy_level VARCHAR, photo_url VARCHAR, notes TEXT, created_by INTEGER
            )"""))
        conn.execute(text("""
            INSERT INTO pet_records VALUES
            (1, 7, '2026-08-01', 20.5, 'Vomitou uma vez', 'regular', 'reduzido', 'baixo', NULL, NULL, 3),
            (2, 7, '2026-08-08', 20.1, NULL, 'bom', 'normal', 'normal', NULL, 'Tudo bem', 3)
        """))
    return engine


def test_copia_registros_antigos_para_o_mongo(tmp_path):
    mongo_db = mongomock.MongoClient()["oncopet"]
    result = migrate(legacy_engine(tmp_path), mongo_db)

    assert result == {"migrated": 2, "skipped": 0, "table_found": True}
    docs = list(mongo_db.daily_logs.find({"pet_id": 7}).sort("date", 1))
    assert [d["date"] for d in docs] == ["2026-08-01", "2026-08-08"]
    assert docs[0]["other_symptoms"] == "Vomitou uma vez"
    assert docs[0]["symptoms"] == [] and docs[0]["pain_score"] is None


def test_rodar_de_novo_nao_duplica(tmp_path):
    engine = legacy_engine(tmp_path)
    mongo_db = mongomock.MongoClient()["oncopet"]
    migrate(engine, mongo_db)
    assert migrate(engine, mongo_db) == {"migrated": 0, "skipped": 2, "table_found": True}
    assert mongo_db.daily_logs.count_documents({}) == 2


def test_sem_tabela_antiga_nao_faz_nada(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'novo.db'}")
    assert migrate(engine, mongomock.MongoClient()["oncopet"])["table_found"] is False
