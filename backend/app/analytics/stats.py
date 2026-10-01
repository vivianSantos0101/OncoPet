"""Estatisticas do tratamento: peso, dor e sintomas (NumPy vetorizado)."""

from datetime import date
from typing import Iterable, List, Optional, Sequence

import numpy as np

SEVERE_PAIN = 7          # a partir de 7 a dor e considerada intensa
RELEVANT_WEIGHT_LOSS = 5.0  # perda de peso (%) considerada clinicamente relevante


def days_since_start(dates: Sequence[date]) -> np.ndarray:
    """Dias corridos desde a primeira data (eixo x das regressoes)."""
    ordinals = np.fromiter((d.toordinal() for d in dates), dtype=np.int64, count=len(dates))
    return (ordinals - ordinals.min()).astype(float) if len(ordinals) else ordinals.astype(float)


def moving_average(values: Sequence[float], window: int = 3) -> np.ndarray:
    """Media movel dos ultimos `window` pontos (os primeiros usam o que ha disponivel).

    Vetorizada com soma acumulada: media[i] = (soma[i] - soma[i-window]) / n_i
    """
    v = np.asarray(values, dtype=float)
    if v.size == 0:
        return v
    csum = np.cumsum(v)
    shifted = np.concatenate([np.zeros(window), csum[:-window]])[: v.size]
    counts = np.minimum(np.arange(1, v.size + 1), window)
    return (csum - shifted) / counts


def weekly_trend(dates: Sequence[date], values: Sequence[float]) -> Optional[float]:
    """Inclinacao da reta de regressao linear, em unidades por semana."""
    if len(values) < 2:
        return None
    x = days_since_start(dates)
    if np.ptp(x) == 0:
        return None
    slope_per_day = np.polyfit(x, np.asarray(values, dtype=float), 1)[0]
    return float(slope_per_day * 7)


def weight_stats(dates: Sequence[date], weights: Sequence[float]) -> Optional[dict]:
    if len(weights) == 0:
        return None
    w = np.asarray(weights, dtype=float)
    first, last = float(w[0]), float(w[-1])
    change = last - first
    change_percent = change / first * 100 if first else 0.0
    return {
        "first": round(first, 2),
        "last": round(last, 2),
        "min": round(float(w.min()), 2),
        "max": round(float(w.max()), 2),
        "change_kg": round(change, 2),
        "change_percent": round(change_percent, 1),
        "trend_kg_per_week": _round(weekly_trend(dates, w), 3),
        "relevant_loss": bool(change_percent <= -RELEVANT_WEIGHT_LOSS),
        "moving_average": np.round(moving_average(w), 2).tolist(),
    }


def pain_stats(dates: Sequence[date], scores: Sequence[int], today: date, recent_days: int = 28) -> Optional[dict]:
    if len(scores) == 0:
        return None
    s = np.asarray(scores, dtype=float)
    age = today.toordinal() - np.fromiter((d.toordinal() for d in dates), dtype=np.int64, count=len(dates))
    recent = s[age < recent_days]
    previous = s[(age >= recent_days) & (age < 2 * recent_days)]
    recent_mean = float(recent.mean()) if recent.size else None
    previous_mean = float(previous.mean()) if previous.size else None
    return {
        "mean": round(float(s.mean()), 2),
        "last": int(s[-1]),
        "max": int(s.max()),
        "recent_mean": _round(recent_mean, 2),
        "previous_mean": _round(previous_mean, 2),
        "recent_change": _round(recent_mean - previous_mean, 2) if recent_mean is not None and previous_mean is not None else None,
        "trend_per_week": _round(weekly_trend(dates, s), 3),
        "severe_percent": round(float(np.mean(s >= SEVERE_PAIN) * 100), 1),
        "moving_average": np.round(moving_average(s), 2).tolist(),
    }


def symptom_frequency(symptom_lists: Iterable[List[str]], total_logs: int) -> List[dict]:
    """Quantas vezes cada sintoma apareceu e em que % dos registros."""
    flat = np.array([s for lst in symptom_lists for s in (lst or [])], dtype=object)
    if flat.size == 0 or total_logs == 0:
        return []
    names, counts = np.unique(flat.astype(str), return_counts=True)
    order = np.lexsort((names, -counts))  # mais frequente primeiro; empate em ordem alfabetica
    return [
        {"symptom": str(names[i]), "count": int(counts[i]), "percent": round(float(counts[i] / total_logs * 100), 1)}
        for i in order
    ]


def _round(value: Optional[float], digits: int) -> Optional[float]:
    return None if value is None else round(float(value), digits)
