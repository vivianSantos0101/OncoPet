"""Estatisticas do paciente (RF-05).

A rota so busca os dados (sessoes no relacional, diario no MongoDB) e
entrega para a camada analitica (app/analytics), que faz os calculos com
NumPy.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..analytics.stats import pain_stats, symptom_frequency, weight_stats
from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..schemas import PainStatPoint, PetAnalytics, WeightStatPoint
from ..services.patient_history import load_logs, load_sessions, pain_series, weight_series
from .pets import ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/pet/{pet_id}", response_model=PetAnalytics)
async def pet_analytics(
    pet_id: int,
    reference_date: Optional[date] = Query(None, description="Data base para 'ultimas 4 semanas' (padrao: hoje)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pet = get_pet_or_404(db, pet_id)
    ensure_pet_access(pet, user)
    today = reference_date or date.today()

    sessions = load_sessions(db, [pet_id])[pet_id]
    logs = (await load_logs([pet_id]))[pet_id]

    # Peso: sessoes (relacional) + diario (MongoDB), em ordem de data
    w_dates, w_values = weight_series(sessions, logs)
    w_stats = weight_stats(w_dates, w_values)

    # Dor: so registros em que a dor foi avaliada
    p_dates, p_values = pain_series(logs)
    p_stats = pain_stats(p_dates, p_values, today)

    weight_points = [
        WeightStatPoint(date=d, weight=v, moving_average=m)
        for d, v, m in zip(w_dates, w_values, (w_stats or {}).get("moving_average", []))
    ]
    pain_points = [
        PainStatPoint(date=d, pain=v, moving_average=m)
        for d, v, m in zip(p_dates, p_values, (p_stats or {}).get("moving_average", []))
    ]
    if w_stats:
        w_stats.pop("moving_average")
    if p_stats:
        p_stats.pop("moving_average")

    return PetAnalytics(
        pet_id=pet_id,
        reference_date=today,
        logs_count=len(logs),
        weight_points=weight_points,
        weight=w_stats,
        pain_points=pain_points,
        pain=p_stats,
        symptoms=symptom_frequency((log.get("symptoms") for log in logs), len(logs)),
    )
