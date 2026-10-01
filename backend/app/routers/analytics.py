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
from ..models import ChemoSession, User
from ..mongodb import get_daily_logs_collection
from ..schemas import PainStatPoint, PetAnalytics, WeightStatPoint
from ..services.daily_logs import list_logs
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

    sessions = db.query(ChemoSession).filter(ChemoSession.pet_id == pet_id).order_by(ChemoSession.date).all()
    logs = await list_logs(get_daily_logs_collection(), pet_id, newest_first=False)
    for log in logs:
        log["date"] = date.fromisoformat(log["date"])

    # Peso: sessoes (relacional) + diario (MongoDB), em ordem de data
    weights = sorted(
        [(s.date, s.weight_at_session) for s in sessions] +
        [(log["date"], log["weight"]) for log in logs if log.get("weight")],
        key=lambda item: item[0],
    )
    w_dates = [d for d, _ in weights]
    w_values = [v for _, v in weights]
    w_stats = weight_stats(w_dates, w_values)

    # Dor: so registros em que a dor foi avaliada
    pain = [(log["date"], log["pain_score"]) for log in logs if log.get("pain_score") is not None]
    p_dates = [d for d, _ in pain]
    p_values = [v for _, v in pain]
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
