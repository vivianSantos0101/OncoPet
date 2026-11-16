"""Rota de saude e identificacao da copia do backend (load balancer)."""

from app.config import INSTANCE_NAME


def test_health_responde_sem_login(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "instance": INSTANCE_NAME}


def test_toda_resposta_diz_qual_copia_respondeu(client):
    assert client.get("/api/health").headers["X-Backend-Instance"] == INSTANCE_NAME
    # vale tambem para erro (aqui, 401 sem login)
    res = client.get("/api/pets/")
    assert res.status_code == 401
    assert res.headers["X-Backend-Instance"] == INSTANCE_NAME
