"""Painel de cuidados paliativos (RF-06): junta os dados de um paciente e
chama a camada analitica. Nao faz calculo estatistico aqui (RNF-04).
"""

from datetime import date
from typing import List

from ..analytics.palliative import (
    overall_level, palliative_alerts, post_session_effect, session_tolerance,
)
from ..analytics.stats import pain_stats, weight_stats
from ..models import ChemoSession, Pet
from .patient_history import pain_series, weight_series
from .protocols import STATUS_SUSPENSO, compute_progress


def build_palliative(pet: Pet, sessions: List[ChemoSession], logs: List[dict], today: date) -> dict:
    """Metricas criticas de um paciente ate a data `today` (inclusive)."""
    sessions = [s for s in sessions if s.date <= today]
    logs = [log for log in logs if log["date"] <= today]

    weight = weight_stats(*weight_series(sessions, logs))
    if weight:
        weight.pop("moving_average")
    p_dates, p_values = pain_series(logs)
    pain = pain_stats(p_dates, p_values, today)
    if pain:
        pain.pop("moving_average")

    log_dates = [log["date"] for log in logs]
    log_pain = [log.get("pain_score") for log in logs]
    log_symptoms = [log.get("symptoms") or [] for log in logs]
    session_dates = [s.date for s in sessions]

    effect = None
    tolerance = []
    if sessions and logs:
        effect = post_session_effect(log_dates, log_pain, [len(s) for s in log_symptoms], session_dates)
        tolerance = session_tolerance(session_dates, log_dates, log_pain, log_symptoms,
                                      baseline_pain=effect["other_days"]["pain_mean"])
        for row, session in zip(tolerance, sessions):
            row["drug_name"] = session.drug_name or (session.protocol.drug_name if session.protocol else None)

    days_since_last_log = (today - log_dates[-1]).days if logs else None
    overdue = [p.name for p in pet.protocols if compute_progress(p, today).is_overdue]
    suspended = [p.name for p in pet.protocols if p.status == STATUS_SUSPENSO]

    alerts = palliative_alerts(pain, weight, effect, tolerance, days_since_last_log, overdue, suspended)
    return {
        "pet": pet,
        "level": overall_level(alerts),
        "alerts": alerts,
        "pain": pain,
        "weight": weight,
        "effect": effect,
        "sessions": tolerance,
        "days_since_last_log": days_since_last_log,
        "sessions_count": len(sessions),
        "logs_count": len(logs),
    }
