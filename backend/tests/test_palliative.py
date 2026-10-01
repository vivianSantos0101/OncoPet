"""RF-06: painel de cuidados paliativos (diario do MongoDB x sessoes do relacional)."""

from datetime import date, timedelta

import numpy as np

from app.analytics.palliative import (
    classify_tolerance, days_after_last_session, overall_level, palliative_alerts,
    post_session_effect, session_tolerance,
)
from scripts.seed_demo import seed

D0 = date(2026, 9, 1)


def days(*offsets):
    return [D0 + timedelta(days=o) for o in offsets]


# ─── Calculos ────────────────────────────────────────

def test_dias_desde_a_ultima_sessao():
    gap = days_after_last_session(days(-1, 0, 2, 9, 12), days(0, 10))
    # antes da 1a sessao: NaN | mesmo dia: 0 | 2 dias depois | 9 dias depois | 2 dias apos a 2a
    assert np.isnan(gap[0])
    assert gap[1:].tolist() == [0, 2, 9, 2]
    assert np.isnan(days_after_last_session(days(1), [])).all()


def test_efeito_pos_sessao_compara_com_os_demais_dias():
    effect = post_session_effect(
        log_dates=days(1, 2, 5, 8), pain_scores=[6, 4, 2, None],
        symptom_counts=[2, 1, 0, 0], session_dates=days(0),
    )
    assert effect["after_session"] == {"logs": 2, "pain_mean": 5.0, "symptom_percent": 100.0}
    assert effect["other_days"] == {"logs": 2, "pain_mean": 2.0, "symptom_percent": 0.0}  # sem dor avaliada fica fora da media
    assert effect["pain_difference"] == 3.0
    assert effect["symptom_difference"] == 100.0


def test_tolerancia_de_cada_sessao():
    rows = session_tolerance(
        session_dates=days(0, 14, 28),
        log_dates=days(2, 7, 15, 16),
        pain_scores=[2, 1, 8, 5],
        symptom_lists=[[], [], ["vomito"], ["febre"]],
        baseline_pain=1.0,
    )
    assert [r["tolerance"] for r in rows] == ["boa", "ruim", "sem_dados"]
    assert rows[1]["max_pain"] == 8 and rows[1]["symptoms"] == ["febre", "vomito"]
    assert rows[1]["logs"] == 2 and rows[1]["symptom_days"] == 2
    assert rows[2]["max_pain"] is None


def test_regras_de_tolerancia():
    assert classify_tolerance(0, None, 0, 0, None) == "sem_dados"
    assert classify_tolerance(1, 7, 0, 0, None) == "ruim"          # dor intensa
    assert classify_tolerance(1, 2, 1, 1, None) == "ruim"          # febre/dispneia
    assert classify_tolerance(1, 2, 1, 0, None) == "moderada"      # outro sintoma
    assert classify_tolerance(1, 4, 0, 0, 2.0) == "moderada"       # dor 2 pontos acima do normal
    assert classify_tolerance(1, 3, 0, 0, 2.0) == "boa"


def test_alertas_e_nivel():
    pain = {"last": 8, "recent_mean": 6.0, "recent_change": 1.5}
    weight = {"relevant_loss": True, "change_percent": -6.2}
    effect = {"window_days": 3, "pain_difference": 2.0, "after_session": {}, "other_days": {}}
    sessions = [{"tolerance": "moderada", "date": D0, "max_pain": 3, "symptoms": ["vomito"]},
                {"tolerance": "moderada", "date": D0, "max_pain": 3, "symptoms": ["vomito"]}]
    alerts = palliative_alerts(pain, weight, effect, sessions, days_since_last_log=12,
                               overdue_protocols=["CHOP"], suspended_protocols=[])
    codes = [a["code"] for a in alerts]
    assert codes[:2] == ["dor_intensa", "perda_peso"]          # criticos primeiro
    assert set(codes[2:]) == {"dor_subindo", "dor_pos_sessao", "efeito_colateral", "diario_parado", "sessao_atrasada"}
    assert alerts[1]["message"] == "Perdeu 6,2% do peso desde o início"
    assert overall_level(alerts) == "critico"
    assert overall_level([]) == "estavel"
    assert palliative_alerts(None, None, None, [], days_since_last_log=None)[0]["code"] == "sem_diario"


# ─── Rotas /api/palliative ───────────────────────────

def test_paciente_cruza_sessoes_e_diario(client, setup):
    pet_id = setup["pet"]["id"]
    client.post("/api/sessions/", headers=setup["vet"], json={
        "pet_id": pet_id, "date": "2026-09-01", "weight_at_session": 20.0, "drug_name": "Vincristina"})
    for day, pain, symptoms in [("2026-09-02", 8, ["vomito"]), ("2026-09-10", 2, [])]:
        client.post("/api/records/", headers=setup["tutor"], json={
            "pet_id": pet_id, "date": day, "pain_score": pain, "symptoms": symptoms})

    res = client.get(f"/api/palliative/pet/{pet_id}?reference_date=2026-09-12", headers=setup["vet"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["level"] == "critico"
    assert body["effect"]["after_session"]["pain_mean"] == 8.0
    assert body["effect"]["other_days"]["pain_mean"] == 2.0
    assert body["sessions"] == [{
        "date": "2026-09-01", "drug_name": "Vincristina", "logs": 1, "max_pain": 8,
        "symptom_days": 1, "symptoms": ["vomito"], "tolerance": "ruim",
    }]
    # o tutor tambem pode ver o proprio pet
    assert client.get(f"/api/palliative/pet/{pet_id}", headers=setup["tutor"]).status_code == 200


def test_permissoes(client, setup):
    pet_id = setup["pet"]["id"]
    assert client.get("/api/palliative/overview", headers=setup["tutor"]).status_code == 403
    assert client.get(f"/api/palliative/pet/{pet_id}", headers=setup["other_tutor"]).status_code == 403
    assert client.get("/api/palliative/pet/999", headers=setup["vet"]).status_code == 404


def test_pet_sem_dados(client, setup):
    body = client.get("/api/palliative/overview", headers=setup["vet"]).json()
    patient = body["patients"][0]
    assert patient["level"] == "atencao"
    assert [a["code"] for a in patient["alerts"]] == ["sem_diario"]
    assert patient["last_pain"] is None and patient["sessions_count"] == 0


def test_painel_com_dados_de_demonstracao(client):
    seed(client, today=date(2026, 9, 28))
    token = client.post("/api/auth/login", data={"username": "dra_ana", "password": "oncopet123"}).json()["access_token"]
    body = client.get("/api/palliative/overview?reference_date=2026-09-28",
                      headers={"Authorization": f"Bearer {token}"}).json()

    patients = body["patients"]
    assert body["critico"] + body["atencao"] + body["estavel"] == len(patients) == 7
    order = ["critico", "atencao", "estavel"]
    assert [order.index(p["level"]) for p in patients] == sorted(order.index(p["level"]) for p in patients)

    bela = patients[0]   # caso paliativo do seed: o mais critico da lista
    assert bela["name"] == "Bela" and bela["level"] == "critico"
    codes = {a["code"] for a in bela["alerts"]}
    assert {"dor_intensa", "perda_peso", "sessao_mal_tolerada", "diario_parado"} <= codes

    luna = next(p for p in patients if p["name"] == "Luna")
    assert "sessao_atrasada" in {a["code"] for a in luna["alerts"]}
