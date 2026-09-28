"""Permissao para ver e editar pets."""

from tests.conftest import register


# ─── Permissao de edicao (antes qualquer usuario editava qualquer pet) ───

def test_outro_tutor_nao_edita_pet(client, setup):
    res = client.patch(f"/api/pets/{setup['pet']['id']}", headers=setup["other_tutor"], json={"name": "Invadido"})
    assert res.status_code == 403


def test_vet_de_outro_paciente_nao_edita_pet(client, setup):
    other_vet, _ = register(client, "dr_outro", "vet")
    assert client.patch(f"/api/pets/{setup['pet']['id']}", headers=other_vet, json={"name": "X"}).status_code == 403
    assert client.get(f"/api/pets/{setup['pet']['id']}/chart", headers=other_vet).status_code == 403


def test_dono_e_vet_responsavel_editam(client, setup):
    pet_id = setup["pet"]["id"]
    assert client.patch(f"/api/pets/{pet_id}", headers=setup["tutor"], json={"name": "Thor II"}).json()["name"] == "Thor II"
    assert client.patch(f"/api/pets/{pet_id}", headers=setup["vet"], json={"cancer_type": "Linfoma"}).status_code == 200
