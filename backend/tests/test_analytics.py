"""RF-05: estatisticas com NumPy (camada analitica e rota)."""

from datetime import date, timedelta

import pytest

from app.analytics.stats import (
    moving_average, pain_stats, symptom_frequency, weekly_trend, weight_stats,
)
from scripts.seed_demo import seed

D0 = date(2026, 9, 1)


def days(*offsets):
    return [D0 + timedelta(days=o) for o in offsets]


# ─── Calculos (valores conferiveis a mao) ────────────

def test_media_movel_de_3_pontos():
    assert moving_average([1, 2, 3, 4, 5]).tolist() == [1, 1.5, 2, 3, 4]
    assert moving_average([]).tolist() == []


def test_tendencia_semanal_por_regressao_linear():
    # perde 0,1 kg por dia -> -0,7 kg por semana
    dates = days(*range(15))
    weights = [20 - 0.1 * i for i in range(15)]
    assert weekly_trend(dates, weights) == pytest.approx(-0.7)
    assert weekly_trend(days(0), [20]) is None           # um ponto so
    assert weekly_trend(days(0, 0), [20, 21]) is None    # mesmo dia


def test_resumo_de_peso_e_perda_relevante():
    stats = weight_stats(days(0, 7, 14), [20.0, 19.4, 18.8])
    assert stats["change_kg"] == -1.2
    assert stats["change_percent"] == -6.0
    assert stats["relevant_loss"] is True          # perdeu mais de 5%
    assert stats["trend_kg_per_week"] == pytest.approx(-0.6)
    assert weight_stats([], []) is None


def test_resumo_de_dor_compara_ultimas_4_semanas_com_as_anteriores():
    today = D0 + timedelta(days=60)
    dates = [today - timedelta(days=d) for d in (50, 40, 10, 3)]
    stats = pain_stats(dates, [2, 4, 6, 8], today)
    assert stats["recent_mean"] == 7.0       # 6 e 8
    assert stats["previous_mean"] == 3.0     # 2 e 4
    assert stats["recent_change"] == 4.0
    assert stats["severe_percent"] == 25.0   # so o 8 e >= 7
    assert stats["trend_per_week"] > 0
    assert pain_stats([], [], today) is None


def test_frequencia_de_sintomas():
    freq = symptom_frequency([["vomito", "letargia"], ["vomito"], []], total_logs=3)
    assert freq == [
        {"symptom": "vomito", "count": 2, "percent": 66.7},
        {"symptom": "letargia", "count": 1, "percent": 33.3},
    ]
    assert symptom_frequency([[], []], 2) == []


# ─── Rota /api/analytics ─────────────────────────────

def test_rota_junta_sessoes_do_relacional_e_diario_do_mongo(client, setup):
    pet_id = setup["pet"]["id"]
    client.post("/api/sessions/", headers=setup["vet"], json={"pet_id": pet_id, "date": "2026-09-01", "weight_at_session": 20.0})
    for day, weight, pain, symptoms in [("2026-09-05", 19.8, 2, []), ("2026-09-12", 19.5, 5, ["vomito"]), ("2026-09-19", 19.1, 8, ["vomito", "letargia"])]:
        client.post("/api/records/", headers=setup["tutor"], json={
            "pet_id": pet_id, "date": day, "weight": weight, "pain_score": pain, "symptoms": symptoms,
        })
    res = client.get(f"/api/analytics/pet/{pet_id}?reference_date=2026-09-20", headers=setup["vet"])
    assert res.status_code == 200, res.text
    body = res.json()

    assert [p["weight"] for p in body["weight_points"]] == [20.0, 19.8, 19.5, 19.1]  # sessao + diario
    assert body["weight"]["change_kg"] == -0.9
    assert body["weight"]["trend_kg_per_week"] < 0
    assert [p["pain"] for p in body["pain_points"]] == [2, 5, 8]
    assert body["pain_points"][-1]["moving_average"] == 5.0
    assert body["pain"]["severe_percent"] == 33.3
    assert body["symptoms"][0] == {"symptom": "vomito", "count": 2, "percent": 66.7}
    assert body["logs_count"] == 3


def test_pet_sem_dados_nao_quebra(client, setup):
    body = client.get(f"/api/analytics/pet/{setup['pet']['id']}", headers=setup["tutor"]).json()
    assert body["weight"] is None and body["pain"] is None and body["symptoms"] == []


def test_permissoes(client, setup):
    url = f"/api/analytics/pet/{setup['pet']['id']}"
    assert client.get(url, headers=setup["tutor"]).status_code == 200
    assert client.get(url, headers=setup["other_tutor"]).status_code == 403
    assert client.get("/api/analytics/pet/999", headers=setup["vet"]).status_code == 404


def test_cenarios_dos_dados_de_demonstracao(client):
    seed(client, today=date(2026, 9, 28))
    token = client.post("/api/auth/login", data={"username": "dra_ana", "password": "oncopet123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    get = lambda pet_id: client.get(f"/api/analytics/pet/{pet_id}?reference_date=2026-09-28", headers=headers).json()

    thor, luna = get(1), get(2)
    assert thor["weight"]["trend_kg_per_week"] < 0     # linfoma: perdendo peso
    assert luna["pain"]["trend_per_week"] > 0           # osteossarcoma: dor subindo
    assert luna["pain"]["recent_mean"] > luna["pain"]["previous_mean"]
