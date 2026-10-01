"""Validacao de idade e peso do pet (nao aceita valores negativos)."""

import pytest


def pet_payload(setup, **overrides):
    payload = {
        "name": "Luna", "species": "cao", "breed": "Poodle",
        "weight": 8.0, "tutor_id": setup["pet"]["tutor_id"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("field,value", [
    ("age_years", -1),
    ("age_years", 41),
    ("age_months", -1),
    ("age_months", 12),
    ("weight", 0),
    ("weight", -5),
    ("weight", 151),
])
def test_cadastro_rejeita_idade_ou_peso_invalido(client, setup, field, value):
    res = client.post("/api/pets/", headers=setup["vet"], json=pet_payload(setup, **{field: value}))
    assert res.status_code == 422
    assert res.json()["detail"][0]["loc"][-1] == field


def test_cadastro_aceita_limites_validos(client, setup):
    res = client.post("/api/pets/", headers=setup["vet"], json=pet_payload(setup, age_years=0, age_months=11))
    assert res.status_code == 201, res.text


def test_edicao_rejeita_idade_negativa(client, setup):
    res = client.patch(f"/api/pets/{setup['pet']['id']}", headers=setup["vet"], json={"age_years": -3})
    assert res.status_code == 422


def test_sessao_rejeita_peso_negativo(client, setup):
    res = client.post("/api/sessions/", headers=setup["vet"], json={
        "pet_id": setup["pet"]["id"], "date": "2026-09-01", "weight_at_session": -2,
    })
    assert res.status_code == 422


def test_registro_do_tutor_rejeita_peso_negativo(client, setup):
    res = client.post("/api/records/", headers=setup["tutor"], json={
        "pet_id": setup["pet"]["id"], "date": "2026-09-01", "weight": -1,
    })
    assert res.status_code == 422
