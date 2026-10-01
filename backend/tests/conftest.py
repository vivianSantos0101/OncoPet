"""Fixtures dos testes.

Usa SQLite em arquivo temporario no lugar do PostgreSQL e um MongoDB em
memoria (mongomock-motor) no lugar do MongoDB real, entao roda sem Docker.
"""

import os
import tempfile

_db_file = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from mongomock_motor import AsyncMongoMockClient  # noqa: E402

from app import mongodb  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # MongoDB em memoria, limpo a cada teste
    mongodb.db = AsyncMongoMockClient()["oncopet_test"]
    # Sem "with": nao dispara o lifespan que conecta no MongoDB real
    yield TestClient(app)


def register(client, username, role):
    res = client.post("/api/auth/register", json={
        "username": username, "password": "senha123",
        "full_name": username.title(), "role": role,
    })
    assert res.status_code == 201, res.text
    body = res.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]


@pytest.fixture()
def setup(client):
    """Cria vet, tutor e um pet (cao, 20kg) do tutor atendido pelo vet."""
    vet_headers, vet = register(client, "dra_ana", "vet")
    tutor_headers, tutor = register(client, "joao", "tutor")
    other_headers, _ = register(client, "maria", "tutor")
    res = client.post("/api/pets/", headers=vet_headers, json={
        "name": "Thor", "species": "cao", "breed": "Labrador Retriever",
        "weight": 20.0, "tutor_id": tutor["id"],
    })
    assert res.status_code == 201, res.text
    return {
        "vet": vet_headers, "tutor": tutor_headers, "other_tutor": other_headers,
        "pet": res.json(),
    }
