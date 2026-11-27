"""Esqueci minha senha: link por e-mail, de uso unico e com validade."""

from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app import emails
from app.database import SessionLocal
from app.models import PasswordResetToken
from app.services.password_reset import hash_token


@pytest.fixture()
def outbox(monkeypatch):
    """Guarda os e-mails em vez de enviar."""
    sent = []
    monkeypatch.setattr(emails, "send_email", lambda to, subject, text, html=None: sent.append(
        {"to": to, "subject": subject, "text": text, "html": html}) or True)
    return sent


def token_from(mail):
    link = next(word for word in mail["text"].split() if "/redefinir-senha?token=" in word)
    assert link.startswith("http://localhost:5173/redefinir-senha?token=")
    return parse_qs(urlparse(link).query)["token"][0]


def login(client, username, password):
    return client.post("/api/auth/login", data={"username": username, "password": password})


def test_fluxo_completo(client, setup, outbox):
    res = client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    assert res.status_code == 200
    assert "Se o e-mail estiver cadastrado" in res.json()["message"]

    assert len(outbox) == 1
    mail = outbox[0]
    assert mail["to"] == "joao@exemplo.com"
    assert "joao" in mail["text"] and "30 minutos" in mail["text"]
    assert "Criar nova senha" in mail["html"]

    token = token_from(mail)
    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "novaSenha9"})
    assert res.status_code == 200, res.text

    assert login(client, "joao", "senha123").status_code == 401   # a senha antiga parou de valer
    assert login(client, "joao", "novaSenha9").status_code == 200


def test_email_desconhecido_tem_a_mesma_resposta(client, setup, outbox):
    """A rota nao revela se o e-mail tem conta."""
    known = client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"}).json()
    unknown = client.post("/api/auth/forgot-password", json={"email": "ninguem@exemplo.com"})
    assert unknown.status_code == 200
    assert unknown.json() == known
    assert [m["to"] for m in outbox] == ["joao@exemplo.com"]


def test_email_sem_diferenca_de_maiusculas(client, setup, outbox):
    client.post("/api/auth/forgot-password", json={"email": "  JOAO@Exemplo.com "})
    assert len(outbox) == 1


def test_link_vale_uma_vez(client, setup, outbox):
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    token = token_from(outbox[0])
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "primeira1"}).status_code == 200
    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "segunda22"})
    assert res.status_code == 400
    assert "inválido ou vencido" in res.json()["detail"]
    assert login(client, "joao", "primeira1").status_code == 200


def test_link_vencido(client, setup, outbox):
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    token = token_from(outbox[0])
    db = SessionLocal()
    row = db.query(PasswordResetToken).filter_by(token_hash=hash_token(token)).one()
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    db.close()
    res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "novaSenha9"})
    assert res.status_code == 400


def test_token_inventado_e_senha_curta(client, setup, outbox):
    assert client.post("/api/auth/reset-password",
                       json={"token": "x" * 43, "new_password": "novaSenha9"}).status_code == 400
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    token = token_from(outbox[0])
    assert client.post("/api/auth/reset-password",
                       json={"token": token, "new_password": "123"}).status_code == 422


def test_banco_guarda_so_o_hash(client, setup, outbox):
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    token = token_from(outbox[0])
    db = SessionLocal()
    stored = [row.token_hash for row in db.query(PasswordResetToken).all()]
    db.close()
    assert token not in stored
    assert hash_token(token) in stored


def test_pedidos_seguidos_mandam_um_email_so(client, setup, outbox):
    for _ in range(3):
        assert client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"}).status_code == 200
    assert len(outbox) == 1


def test_novo_link_invalida_o_antigo_ao_trocar(client, setup, outbox, monkeypatch):
    monkeypatch.setattr("app.services.password_reset.RESET_COOLDOWN_SECONDS", 0)
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    client.post("/api/auth/forgot-password", json={"email": "joao@exemplo.com"})
    first, second = token_from(outbox[0]), token_from(outbox[1])
    assert client.post("/api/auth/reset-password", json={"token": second, "new_password": "novaSenha9"}).status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": first, "new_password": "outraSenha8"}).status_code == 400


@pytest.mark.parametrize("email", [None, "", "sem-arroba", "a@b"])
def test_cadastro_exige_email_valido(client, email):
    body = {"username": "novo", "password": "senha123", "full_name": "Novo", "role": "tutor"}
    if email is not None:
        body["email"] = email
    assert client.post("/api/auth/register", json=body).status_code == 422


def test_email_de_verdade_sem_smtp_vai_para_o_log(capsys, monkeypatch):
    monkeypatch.setattr("app.config.SMTP_HOST", "")
    subject, text, html = emails.password_reset_email("Ana Souza", "dra_ana", "http://x/redefinir-senha?token=abc", 30)
    assert emails.send_email("ana@exemplo.com", subject, text, html) is False
    out = capsys.readouterr().out
    assert "SMTP nao configurado" in out and "token=abc" in out and "Olá, Ana!" in out
