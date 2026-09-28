"""Testes do RF-04: protocolos com sessoes planejadas x executadas."""

from datetime import date, timedelta

from app.services.protocols import compute_progress
from app.models import ChemoProtocol, ChemoSession


def create_protocol(client, setup, **overrides):
    payload = {
        "pet_id": setup["pet"]["id"], "name": "Doxorrubicina solo",
        "drug_name": "Doxorrubicina", "dose_mg_m2": 30,
        "planned_sessions": 3, "interval_days": 21, "start_date": "2026-09-01",
    }
    payload.update(overrides)
    return client.post("/api/protocols/", headers=setup["vet"], json=payload)


def add_session(client, setup, protocol_id, day, **overrides):
    payload = {
        "pet_id": setup["pet"]["id"], "protocol_id": protocol_id,
        "date": day, "weight_at_session": 20.0,
    }
    payload.update(overrides)
    return client.post("/api/sessions/", headers=setup["vet"], json=payload)


# ─── API ──────────────────────────────────────────────

def test_vet_cria_protocolo_com_progresso_zerado(client, setup):
    res = create_protocol(client, setup)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "ativo"
    assert body["executed_sessions"] == 0
    assert body["remaining_sessions"] == 3
    assert body["progress_percent"] == 0.0
    assert body["next_session_date"] == "2026-09-01"


def test_tutor_nao_cria_protocolo(client, setup):
    res = client.post("/api/protocols/", headers=setup["tutor"], json={
        "pet_id": setup["pet"]["id"], "name": "X", "planned_sessions": 1,
        "start_date": "2026-09-01",
    })
    assert res.status_code == 403


def test_planned_sessions_precisa_ser_positivo(client, setup):
    assert create_protocol(client, setup, planned_sessions=0).status_code == 422


def test_sessao_vinculada_conta_como_executada_e_herda_dose(client, setup):
    protocol = create_protocol(client, setup).json()
    res = add_session(client, setup, protocol["id"], "2026-09-01")
    assert res.status_code == 201, res.text
    session = res.json()
    assert session["protocol_id"] == protocol["id"]
    assert session["drug_name"] == "Doxorrubicina"
    assert session["dose_mg_m2"] == 30
    assert session["dose_administered"] > 0

    body = client.get(f"/api/protocols/{protocol['id']}", headers=setup["vet"]).json()
    assert body["executed_sessions"] == 1
    assert body["remaining_sessions"] == 2
    assert body["progress_percent"] == 33.3
    assert body["next_session_date"] == "2026-09-22"


def test_protocolo_conclui_e_bloqueia_sessao_extra(client, setup):
    protocol = create_protocol(client, setup, planned_sessions=2).json()
    add_session(client, setup, protocol["id"], "2026-09-01")
    add_session(client, setup, protocol["id"], "2026-09-22")

    body = client.get(f"/api/protocols/{protocol['id']}", headers=setup["vet"]).json()
    assert body["status"] == "concluido"
    assert body["progress_percent"] == 100.0
    assert body["next_session_date"] is None

    res = add_session(client, setup, protocol["id"], "2026-10-13")
    assert res.status_code == 400


def test_protocolo_suspenso_nao_aceita_sessao(client, setup):
    protocol = create_protocol(client, setup).json()
    res = client.patch(f"/api/protocols/{protocol['id']}", headers=setup["vet"], json={"status": "suspenso"})
    assert res.status_code == 200
    assert add_session(client, setup, protocol["id"], "2026-09-01").status_code == 400


def test_nao_reduz_planejado_abaixo_do_executado(client, setup):
    protocol = create_protocol(client, setup).json()
    add_session(client, setup, protocol["id"], "2026-09-01")
    add_session(client, setup, protocol["id"], "2026-09-22")
    res = client.patch(f"/api/protocols/{protocol['id']}", headers=setup["vet"], json={"planned_sessions": 1})
    assert res.status_code == 400


def test_sessao_com_protocolo_de_outro_pet_e_rejeitada(client, setup):
    protocol = create_protocol(client, setup).json()
    other_pet = client.post("/api/pets/", headers=setup["vet"], json={
        "name": "Mia", "species": "gato", "breed": "Siames", "weight": 4.0,
        "tutor_id": setup["pet"]["tutor_id"],
    }).json()
    res = client.post("/api/sessions/", headers=setup["vet"], json={
        "pet_id": other_pet["id"], "protocol_id": protocol["id"],
        "date": "2026-09-01", "weight_at_session": 4.0,
    })
    assert res.status_code == 404


def test_sessao_sem_protocolo_continua_funcionando(client, setup):
    res = client.post("/api/sessions/", headers=setup["vet"], json={
        "pet_id": setup["pet"]["id"], "date": "2026-09-01", "weight_at_session": 20.0,
    })
    assert res.status_code == 201
    assert res.json()["protocol_id"] is None


def test_tutor_ve_protocolo_do_proprio_pet_mas_nao_de_outro(client, setup):
    create_protocol(client, setup)
    url = f"/api/protocols/pet/{setup['pet']['id']}"
    assert len(client.get(url, headers=setup["tutor"]).json()) == 1
    assert client.get(url, headers=setup["other_tutor"]).status_code == 403


# ─── Regra de progresso (sem banco) ──────────────────

def make_protocol(planned=4, interval=14, start=date(2026, 9, 1), status="ativo", session_dates=()):
    protocol = ChemoProtocol(
        name="P", planned_sessions=planned, interval_days=interval,
        start_date=start, status=status,
    )
    protocol.sessions = [ChemoSession(date=d, weight_at_session=10) for d in session_dates]
    return protocol


def test_proxima_sessao_atrasada():
    last = date(2026, 9, 1)
    p = make_protocol(session_dates=[last])
    progress = compute_progress(p, today=last + timedelta(days=20))
    assert progress.next_session_date == date(2026, 9, 15)
    assert progress.is_overdue is True


def test_sem_intervalo_nao_preve_proxima_data_apos_primeira_sessao():
    p = make_protocol(interval=None, session_dates=[date(2026, 9, 1)])
    assert compute_progress(p).next_session_date is None
