"""Foto do pet: envio, troca, remocao e validacao."""

import os

import pytest

from app.routers.uploads import UPLOAD_DIR

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


def upload(client, headers, pet_id, content, name="foto.png", mime="image/png"):
    return client.put(f"/api/pets/{pet_id}/photo", headers=headers, files={"file": (name, content, mime)})


def stored_file(photo_url):
    return os.path.join(UPLOAD_DIR, os.path.basename(photo_url))


@pytest.mark.parametrize("content,ext", [(PNG, ".png"), (JPG, ".jpg"), (WEBP, ".webp")])
def test_tutor_envia_foto_do_proprio_pet(client, setup, content, ext):
    res = upload(client, setup["tutor"], setup["pet"]["id"], content)
    assert res.status_code == 200, res.text
    url = res.json()["photo_url"]
    assert url.startswith("/api/uploads/files/pet-") and url.endswith(ext)
    # a foto e servida pela rota de arquivos
    assert client.get(url).content == content


def test_vet_responsavel_tambem_pode_trocar_a_foto(client, setup):
    assert upload(client, setup["vet"], setup["pet"]["id"], PNG).status_code == 200


def test_outro_tutor_nao_troca_foto(client, setup):
    assert upload(client, setup["other_tutor"], setup["pet"]["id"], PNG).status_code == 403


def test_arquivo_que_nao_e_imagem_e_recusado_mesmo_com_extensao_png(client, setup):
    res = upload(client, setup["tutor"], setup["pet"]["id"], b"%PDF-1.4 falso", name="foto.png")
    assert res.status_code == 400
    assert "JPG, PNG ou WEBP" in res.json()["detail"]


def test_foto_acima_de_5_mb_e_recusada(client, setup):
    big = PNG + b"\x00" * (5 * 1024 * 1024)
    assert upload(client, setup["tutor"], setup["pet"]["id"], big).status_code == 400


def test_trocar_foto_apaga_o_arquivo_antigo(client, setup):
    first = upload(client, setup["tutor"], setup["pet"]["id"], PNG).json()["photo_url"]
    second = upload(client, setup["tutor"], setup["pet"]["id"], JPG).json()["photo_url"]
    assert first != second
    assert not os.path.exists(stored_file(first))
    assert os.path.exists(stored_file(second))


def test_remover_foto(client, setup):
    url = upload(client, setup["tutor"], setup["pet"]["id"], PNG).json()["photo_url"]
    res = client.delete(f"/api/pets/{setup['pet']['id']}/photo", headers=setup["tutor"])
    assert res.status_code == 200 and res.json()["photo_url"] is None
    assert not os.path.exists(stored_file(url))


def test_foto_aparece_na_lista_de_pets(client, setup):
    upload(client, setup["tutor"], setup["pet"]["id"], PNG)
    pets = client.get("/api/pets/", headers=setup["tutor"]).json()
    assert pets[0]["photo_url"].endswith(".png")
