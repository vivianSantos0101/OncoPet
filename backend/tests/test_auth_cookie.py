"""Sessao em cookie HttpOnly (o token nao fica no localStorage do navegador)."""

from fastapi.testclient import TestClient

from app.config import AUTH_COOKIE_NAME
from app.main import app
from tests.conftest import register

AJAX = {"X-Requested-With": "XMLHttpRequest"}


def login(client, username="dra_ana", password="senha123"):
    return client.post("/api/auth/login", data={"username": username, "password": password})


def test_login_grava_cookie_httponly(client):
    register(client, "dra_ana", "vet")
    res = login(client)
    assert res.status_code == 200
    cookie = res.headers["set-cookie"]
    assert cookie.startswith(f"{AUTH_COOKIE_NAME}=")
    assert "HttpOnly" in cookie                 # JavaScript nao le
    assert "samesite=lax" in cookie.lower()     # outro site nao envia em POST
    assert "Path=/api" in cookie
    assert "Max-Age=28800" in cookie            # 8 horas


def test_me_funciona_so_com_o_cookie(client):
    register(client, "dra_ana", "vet")
    login(client)
    res = client.get("/api/auth/me")            # sem cabecalho Authorization
    assert res.status_code == 200
    assert res.json()["username"] == "dra_ana" and res.json()["role"] == "vet"


def test_sem_sessao_da_401(client):
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(AUTH_COOKIE_NAME, "token-falso", path="/api")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_apaga_o_cookie(client):
    register(client, "dra_ana", "vet")
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_cadastro_ja_entra_logado(client):
    res = client.post("/api/auth/register", json={
        "username": "joao", "password": "senha123", "full_name": "Joao", "role": "tutor"})
    assert AUTH_COOKIE_NAME in res.headers["set-cookie"]
    assert client.get("/api/auth/me").json()["username"] == "joao"


def test_csrf_alteracao_com_cookie_exige_cabecalho(client):
    register(client, "dra_ana", "vet")
    login(client)
    body = {"name": "Clinica Teste"}
    # Formulario de outro site: o navegador manda o cookie, mas nao o cabecalho
    assert client.post("/api/clinics/", json=body).status_code == 403
    # O front do OncoPet sempre manda o cabecalho
    assert client.post("/api/clinics/", json=body, headers=AJAX).status_code == 201
    # Leitura nao precisa do cabecalho
    assert client.get("/api/clinics/").status_code == 200


def test_cabecalho_authorization_continua_valendo(client):
    """Para /docs, scripts e curl (sem cookie e sem o cabecalho anti-CSRF)."""
    headers, _ = register(client, "dra_ana", "vet")
    fresh = TestClient(app)
    assert fresh.get("/api/auth/me", headers=headers).status_code == 200
    assert fresh.post("/api/clinics/", json={"name": "Clinica"}, headers=headers).status_code == 201
