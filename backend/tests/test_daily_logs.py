"""RF-02/RF-03: diario do tutor no MongoDB (peso, sintomas e escala de dor)."""

import asyncio

from app import mongodb


def log_payload(setup, **overrides):
    payload = {
        "pet_id": setup["pet"]["id"], "date": "2026-09-10", "weight": 19.4,
        "symptoms": ["vomito", "letargia"], "pain_score": 3,
        "general_status": "regular", "notes": "Dormiu a tarde toda.",
    }
    payload.update(overrides)
    return payload


def mongo_docs(pet_id):
    async def fetch():
        return [d async for d in mongodb.db.daily_logs.find({"pet_id": pet_id})]
    return asyncio.run(fetch())


def test_registro_vai_para_o_mongodb(client, setup):
    res = client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup))
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["symptoms"] == ["vomito", "letargia"]
    assert body["pain_score"] == 3
    assert len(body["id"]) == 24  # ObjectId

    docs = mongo_docs(setup["pet"]["id"])
    assert len(docs) == 1
    assert docs[0]["date"] == "2026-09-10"
    assert docs[0]["pet_id"] == setup["pet"]["id"]


def test_peso_do_diario_atualiza_o_cadastro_do_pet(client, setup):
    client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, weight=18.7))
    pet = client.get(f"/api/pets/{setup['pet']['id']}", headers=setup["tutor"]).json()
    assert pet["weight"] == 18.7


def test_escala_de_dor_vai_de_0_a_10(client, setup):
    for value in (-1, 11):
        res = client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, pain_score=value))
        assert res.status_code == 422
    assert client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, pain_score=0)).status_code == 201


def test_sintoma_fora_da_lista_e_rejeitado(client, setup):
    res = client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, symptoms=["espirro"]))
    assert res.status_code == 422


def test_registro_sem_sintomas_e_sem_dor(client, setup):
    res = client.post("/api/records/", headers=setup["tutor"], json={
        "pet_id": setup["pet"]["id"], "date": "2026-09-10", "weight": 19.0,
    })
    assert res.status_code == 201
    assert res.json()["symptoms"] == [] and res.json()["pain_score"] is None


def test_integridade_pet_precisa_existir_e_ser_do_tutor(client, setup):
    # pet inexistente no banco relacional nao gera documento no MongoDB (RNF-03)
    assert client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, pet_id=999)).status_code == 403
    assert client.post("/api/records/", headers=setup["other_tutor"], json=log_payload(setup)).status_code == 403
    assert client.post("/api/records/", headers=setup["vet"], json=log_payload(setup)).status_code == 403
    assert mongo_docs(999) == [] and mongo_docs(setup["pet"]["id"]) == []


def test_listagem_mais_recente_primeiro_e_permissoes(client, setup):
    for day in ("2026-09-01", "2026-09-15", "2026-09-08"):
        client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, date=day))
    url = f"/api/records/pet/{setup['pet']['id']}"

    dates = [r["date"] for r in client.get(url, headers=setup["tutor"]).json()]
    assert dates == ["2026-09-15", "2026-09-08", "2026-09-01"]
    assert len(client.get(url, headers=setup["vet"]).json()) == 3
    assert client.get(url, headers=setup["other_tutor"]).status_code == 403
    assert client.get("/api/records/pet/999", headers=setup["vet"]).status_code == 404


def test_grafico_de_peso_usa_o_diario_do_mongodb(client, setup):
    client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, date="2026-09-01", weight=20.0))
    client.post("/api/records/", headers=setup["tutor"], json=log_payload(setup, date="2026-09-08", weight=19.2))
    chart = client.get(f"/api/pets/{setup['pet']['id']}/chart", headers=setup["vet"]).json()
    assert chart["records_count"] == 2
    assert [p["weight"] for p in chart["weight_history"]] == [20.0, 19.2]
    assert chart["last_weight"] == 19.2
