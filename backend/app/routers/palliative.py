"""Painel de cuidados paliativos (RF-06).

Cruza o diario do tutor (MongoDB) com as sessoes de quimioterapia (banco
relacional) e destaca os pacientes que precisam de atencao. Os calculos ficam
em app/analytics/palliative.py; aqui so buscamos os dados e montamos a resposta.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..analytics.palliative import LEVELS
from ..auth import get_current_user, require_vet
from ..database import get_db
from ..models import Pet, User
from ..schemas import PalliativeOverview, PalliativePatient, PetPalliative
from ..services.palliative import build_palliative
from ..services.patient_history import load_logs, load_sessions
from .pets import ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/palliative", tags=["cuidados paliativos"])

REFERENCE_DATE = Query(None, description="Data usada como 'hoje' (padrao: hoje)")


@router.get("/overview", response_model=PalliativeOverview)
async def overview(
    reference_date: Optional[date] = REFERENCE_DATE,
    db: Session = Depends(get_db),
    user: User = Depends(require_vet),
):
    """Todos os pacientes do veterinario, dos mais criticos para os estaveis."""
    today = reference_date or date.today()
    pets = db.query(Pet).filter(Pet.vet_id == user.id).all()
    ids = [p.id for p in pets]
    sessions, logs = load_sessions(db, ids), await load_logs(ids)

    patients = []
    for pet in pets:
        data = build_palliative(pet, sessions[pet.id], logs[pet.id], today)
        pain, weight, effect = data["pain"] or {}, data["weight"] or {}, data["effect"]
        patients.append(PalliativePatient(
            pet_id=pet.id, name=pet.name, species=pet.species, breed=pet.breed,
            photo_url=pet.photo_url, cancer_type=pet.cancer_type,
            tutor_name=pet.tutor.full_name if pet.tutor else None,
            level=data["level"], alerts=data["alerts"],
            last_pain=pain.get("last"), recent_pain_mean=pain.get("recent_mean"),
            pain_recent_change=pain.get("recent_change"),
            weight_change_percent=weight.get("change_percent"),
            days_since_last_log=data["days_since_last_log"],
            sessions_count=data["sessions_count"],
            pain_after_session=effect["after_session"]["pain_mean"] if effect else None,
            pain_other_days=effect["other_days"]["pain_mean"] if effect else None,
        ))

    # Mais grave primeiro; no mesmo nivel, mais alertas e mais dor recente primeiro
    patients.sort(key=lambda p: (
        -LEVELS.index(p.level), -len(p.alerts),
        -(p.recent_pain_mean if p.recent_pain_mean is not None else -1), p.name,
    ))
    counts = {level: sum(p.level == level for p in patients) for level in LEVELS}
    return PalliativeOverview(reference_date=today, patients=patients, **counts)


@router.get("/pet/{pet_id}", response_model=PetPalliative)
async def pet_palliative(
    pet_id: int,
    reference_date: Optional[date] = REFERENCE_DATE,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Alertas do paciente e como ele ficou depois de cada sessao."""
    pet = get_pet_or_404(db, pet_id)
    ensure_pet_access(pet, user)
    today = reference_date or date.today()
    data = build_palliative(pet, load_sessions(db, [pet_id])[pet_id], (await load_logs([pet_id]))[pet_id], today)
    return PetPalliative(
        pet_id=pet_id, reference_date=today, level=data["level"], alerts=data["alerts"],
        effect=data["effect"], sessions=data["sessions"],
    )
