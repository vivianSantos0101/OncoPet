"""Controle de acesso por pet: so o tutor dono e o vet responsavel.

Antes desta correcao, varias rotas so exigiam login: qualquer usuario logado
via (ou alterava) documentos, sessoes, lembretes, protocolos e exames de
qualquer pet.
"""

import pytest

from tests.conftest import register

LIST_ROUTES = [
    "/api/documents/pet/{id}",
    "/api/sessions/pet/{id}",
    "/api/records/pet/{id}",
    "/api/reminders/pet/{id}",
    "/api/protocols/pet/{id}",
    "/api/exams/pet/{id}",
]


@pytest.fixture()
def other_vet(client, setup):
    headers, _ = register(client, "dr_outro", "vet")
    return headers


# ─── Leitura ─────────────────────────────────────────

@pytest.mark.parametrize("route", LIST_ROUTES)
def test_listagens_so_para_dono_e_vet_responsavel(client, setup, other_vet, route):
    url = route.format(id=setup["pet"]["id"])
    assert client.get(url, headers=setup["tutor"]).status_code == 200
    assert client.get(url, headers=setup["vet"]).status_code == 200
    assert client.get(url, headers=setup["other_tutor"]).status_code == 403
    assert client.get(url, headers=other_vet).status_code == 403


@pytest.mark.parametrize("route", LIST_ROUTES)
def test_pet_inexistente_da_404(client, setup, route):
    assert client.get(route.format(id=999), headers=setup["vet"]).status_code == 404


# ─── Escrita por vet que nao atende o pet ────────────

def test_vet_de_outro_paciente_nao_cria_registros(client, setup, other_vet):
    pet_id = setup["pet"]["id"]
    attempts = {
        "/api/documents/": {"pet_id": pet_id, "title": "Hemograma", "doc_type": "exame_sangue", "file_url": "/x.pdf"},
        "/api/sessions/": {"pet_id": pet_id, "date": "2026-09-01", "weight_at_session": 20.0},
        "/api/reminders/": {"pet_id": pet_id, "title": "Consulta", "reminder_type": "consulta", "date": "2026-10-01"},
        "/api/protocols/": {"pet_id": pet_id, "name": "CHOP", "planned_sessions": 4, "start_date": "2026-09-01"},
        "/api/exams/": {"pet_id": pet_id, "exam_type": "hemograma", "date": "2026-09-01"},
    }
    for url, body in attempts.items():
        assert client.post(url, headers=other_vet, json=body).status_code == 403, url
        assert client.post(url, headers=setup["vet"], json=body).status_code == 201, url


def test_alterar_protocolo_de_outro_paciente(client, setup, other_vet):
    proto = client.post("/api/protocols/", headers=setup["vet"], json={
        "pet_id": setup["pet"]["id"], "name": "CHOP", "planned_sessions": 4, "start_date": "2026-09-01",
    }).json()
    url = f"/api/protocols/{proto['id']}"
    assert client.patch(url, headers=other_vet, json={"status": "suspenso"}).status_code == 403
    assert client.get(url, headers=other_vet).status_code == 403
    assert client.patch(url, headers=setup["vet"], json={"status": "suspenso"}).status_code == 200


def test_concluir_lembrete_de_outro_pet(client, setup, other_vet):
    reminder = client.post("/api/reminders/", headers=setup["vet"], json={
        "pet_id": setup["pet"]["id"], "title": "Remédio", "reminder_type": "medicacao", "date": "2026-10-01",
    }).json()
    url = f"/api/reminders/{reminder['id']}"
    assert client.patch(url, headers=setup["other_tutor"], json={"is_completed": True}).status_code == 403
    assert client.patch(url, headers=other_vet, json={"is_completed": True}).status_code == 403
    assert client.patch(url, headers=setup["tutor"], json={"is_completed": True}).json()["is_completed"] is True


def test_exame_individual(client, setup, other_vet):
    exam = client.post("/api/exams/", headers=setup["vet"], json={
        "pet_id": setup["pet"]["id"], "exam_type": "hemograma", "date": "2026-09-01", "data": {"plaquetas": 250},
    }).json()
    url = f"/api/exams/{exam['id']}"
    assert client.get(url, headers=setup["other_tutor"]).status_code == 403
    assert client.get(url, headers=setup["tutor"]).json()["data"] == {"plaquetas": 250}
    assert client.delete(url, headers=other_vet).status_code == 403
    assert client.delete(url, headers=setup["vet"]).status_code == 204
    assert client.get(url, headers=setup["vet"]).status_code == 404
