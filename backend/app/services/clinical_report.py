"""Relatorio clinico unificado (RF-07): junta, num dicionario simples, os dados
do banco relacional (paciente, protocolos, sessoes, documentos) e do MongoDB
(diario do tutor), com as estatisticas do RF-05 e os alertas do RF-06.

O dicionario nao tem objetos do banco: o desenho do PDF (app/reports/pdf.py)
recebe so textos e numeros, entao pode ser testado sem banco nenhum.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..analytics.stats import pain_stats, symptom_frequency, weight_stats
from ..models import Document, Pet
from .palliative import build_palliative
from .patient_history import load_logs, load_sessions, pain_series, weight_series
from .protocols import compute_progress

DIARY_ROWS = 12  # ultimos registros do diario que entram no relatorio


async def collect_report(db: Session, pet: Pet, today: date, generated_at: Optional[datetime] = None) -> dict:
    sessions = [s for s in load_sessions(db, [pet.id])[pet.id] if s.date <= today]
    logs = [log for log in (await load_logs([pet.id]))[pet.id] if log["date"] <= today]

    # RF-05: estatisticas (NumPy)
    w_dates, w_values = weight_series(sessions, logs)
    weight = weight_stats(w_dates, w_values)
    p_dates, p_values = pain_series(logs)
    pain = pain_stats(p_dates, p_values, today)

    # RF-06: alertas e tolerancia de cada sessao
    palliative = build_palliative(pet, sessions, logs, today)
    tolerance = {row["date"]: row["tolerance"] for row in palliative["sessions"]}

    protocols = []
    for proto in sorted(pet.protocols, key=lambda p: p.start_date):
        progress = compute_progress(proto, today)
        protocols.append({
            "name": proto.name,
            "drug": proto.drug_name,
            "dose_mg_m2": proto.dose_mg_m2,
            "planned": proto.planned_sessions,
            "executed": progress.executed_sessions,
            "interval_days": proto.interval_days,
            "start_date": proto.start_date,
            "status": proto.status,
            "next_date": progress.next_session_date,
            "overdue": progress.is_overdue,
        })

    documents = db.query(Document).filter(Document.pet_id == pet.id).all()
    documents.sort(key=lambda d: (d.date or date.min, d.id), reverse=True)  # sem data vai pro fim

    return {
        "generated_at": generated_at or datetime.now(),
        "reference_date": today,
        "pet": {
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "age_years": pet.age_years,
            "age_months": pet.age_months,
            "weight": pet.weight,
            "body_surface_area": pet.body_surface_area,
            "cancer_type": pet.cancer_type,
            "treatment_start_date": pet.treatment_start_date,
        },
        "tutor": _person(pet.tutor),
        "vet": _person(pet.vet),
        "clinic": {"name": pet.clinic.name, "address": pet.clinic.address, "phone": pet.clinic.phone} if pet.clinic else None,
        "level": palliative["level"],
        "alerts": palliative["alerts"],
        "effect": palliative["effect"],
        "protocols": protocols,
        "sessions": [
            {
                "date": s.date,
                "drug": s.drug_name or (s.protocol.drug_name if s.protocol else None),
                "dose_mg_m2": s.dose_mg_m2,
                "dose_mg": s.dose_administered,
                "weight": s.weight_at_session,
                "tolerance": tolerance.get(s.date),
            }
            for s in sessions
        ],
        "weight": _without_average(weight),
        "weight_points": list(zip(w_dates, w_values, (weight or {}).get("moving_average", []))),
        "pain": _without_average(pain),
        "pain_points": list(zip(p_dates, p_values, (pain or {}).get("moving_average", []))),
        "symptoms": symptom_frequency((log.get("symptoms") for log in logs), len(logs)),
        "logs_count": len(logs),
        "diary": [
            {
                "date": log["date"],
                "weight": log.get("weight"),
                "pain": log.get("pain_score"),
                "symptoms": log.get("symptoms") or [],
                "other_symptoms": log.get("other_symptoms"),
                "general_status": log.get("general_status"),
                "appetite": log.get("appetite"),
                "energy_level": log.get("energy_level"),
                "notes": log.get("notes"),
            }
            for log in reversed(logs[-DIARY_ROWS:])  # mais recente primeiro
        ],
        "documents": [{"title": d.title, "doc_type": d.doc_type, "date": d.date} for d in documents],
    }


def _person(user) -> Optional[dict]:
    if user is None:
        return None
    return {"name": user.full_name, "email": user.email, "phone": user.phone, "crmv": user.crmv}


def _without_average(summary: Optional[dict]) -> Optional[dict]:
    if not summary:
        return None
    return {k: v for k, v in summary.items() if k != "moving_average"}
