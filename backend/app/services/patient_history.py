"""Historico do paciente nos dois bancos: sessoes (relacional) e diario (MongoDB).

Usado pelas estatisticas (RF-05) e pelo painel de cuidados paliativos (RF-06),
para que as duas rotas leiam os dados do mesmo jeito.
"""

from collections import defaultdict
from datetime import date
from typing import Dict, Iterable, List, Tuple

from sqlalchemy.orm import Session

from ..models import ChemoSession
from ..mongodb import get_daily_logs_collection


def load_sessions(db: Session, pet_ids: Iterable[int]) -> Dict[int, List[ChemoSession]]:
    """Sessoes de cada pet, em ordem de data (uma consulta so)."""
    ids = list(pet_ids)
    result: Dict[int, List[ChemoSession]] = defaultdict(list)
    if not ids:
        return result
    rows = (db.query(ChemoSession).filter(ChemoSession.pet_id.in_(ids))
            .order_by(ChemoSession.date, ChemoSession.id).all())
    for row in rows:
        result[row.pet_id].append(row)
    return result


async def load_logs(pet_ids: Iterable[int]) -> Dict[int, List[dict]]:
    """Registros do diario de cada pet, em ordem de data, com `date` ja convertido."""
    ids = list(pet_ids)
    result: Dict[int, List[dict]] = defaultdict(list)
    if not ids:
        return result
    cursor = get_daily_logs_collection().find({"pet_id": {"$in": ids}}).sort("date", 1)
    async for doc in cursor:
        doc["date"] = date.fromisoformat(doc["date"])
        result[doc["pet_id"]].append(doc)
    return result


def weight_series(sessions: List[ChemoSession], logs: List[dict]) -> Tuple[List[date], List[float]]:
    """Peso das sessoes + peso do diario, em ordem de data."""
    points = sorted(
        [(s.date, s.weight_at_session) for s in sessions] +
        [(log["date"], log["weight"]) for log in logs if log.get("weight")],
        key=lambda item: item[0],
    )
    return [d for d, _ in points], [v for _, v in points]


def pain_series(logs: List[dict]) -> Tuple[List[date], List[int]]:
    """So os registros em que a dor foi avaliada."""
    points = [(log["date"], log["pain_score"]) for log in logs if log.get("pain_score") is not None]
    return [d for d, _ in points], [v for _, v in points]
