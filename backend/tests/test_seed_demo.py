"""O script de dados de demonstracao roda inteiro contra a API."""

from datetime import date

import pytest

from scripts.seed_demo import PATIENTS, SeedError, seed


def login(client, username):
    res = client.post("/api/auth/login", data={"username": username, "password": "oncopet123"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_seed_cria_todos_os_dados(client):
    totals = seed(client, today=date(2026, 9, 28))

    assert totals["pets"] == len(PATIENTS)
    assert totals["protocols"] == sum(len(p["protocols"]) for p in PATIENTS)
    assert totals["sessions"] == sum(pr["executed"] for p in PATIENTS for pr in p["protocols"])
    assert totals["records"] > 50
    assert totals["documents"] == sum(len(p["documents"]) for p in PATIENTS)


def test_seed_gera_situacoes_variadas_de_protocolo(client):
    seed(client, today=date(2026, 9, 28))
    vet = login(client, "dra_ana")
    marcos = login(client, "dr_marcos")

    statuses = set()
    overdue = 0
    for headers in (vet, marcos):
        for pet in client.get("/api/pets/", headers=headers).json():
            for proto in client.get(f"/api/protocols/pet/{pet['id']}", headers=headers).json():
                statuses.add(proto["status"])
                overdue += proto["is_overdue"]
    assert statuses == {"ativo", "concluido", "suspenso"}
    assert overdue >= 1


def test_seed_nao_duplica_dados(client):
    seed(client)
    with pytest.raises(SeedError, match="ja existe"):
        seed(client)
