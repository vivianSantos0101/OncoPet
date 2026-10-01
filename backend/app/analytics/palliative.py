"""Cuidados paliativos (RF-06): cruza o diario do tutor (MongoDB) com as
sessoes de quimioterapia (banco relacional) para destacar metricas criticas.

Funcoes puras com NumPy, como em stats.py: recebem listas e devolvem numeros.
"""

from datetime import date
from typing import List, Optional, Sequence

import numpy as np

from .stats import SEVERE_PAIN

POST_SESSION_DAYS = 3        # efeitos colaterais costumam aparecer do 1o ao 3o dia apos a sessao
STALE_DIARY_DAYS = 10        # sem registro do tutor ha 10 dias ou mais: acompanhamento parado
PAIN_RISE_ALERT = 1.0        # dor recente 1 ponto acima das 4 semanas anteriores
POST_SESSION_PAIN_ALERT = 1.5   # dor 1,5 ponto maior nos dias apos a sessao
RECENT_SESSIONS = 3             # olha a tolerancia das 3 ultimas sessoes
SERIOUS_SYMPTOMS = ("febre", "dispneia")  # podem indicar infeccao/neutropenia ou piora respiratoria

LEVELS = ("estavel", "atencao", "critico")


def _ordinals(dates: Sequence[date]) -> np.ndarray:
    return np.fromiter((d.toordinal() for d in dates), dtype=np.int64, count=len(dates))


def _pain_array(scores: Sequence[Optional[int]]) -> np.ndarray:
    """Dor como float; registro sem dor avaliada vira NaN (fica fora das medias)."""
    return np.array([np.nan if s is None else s for s in scores], dtype=float)


def _mean(values: np.ndarray) -> Optional[float]:
    values = values[~np.isnan(values)]
    return round(float(values.mean()), 2) if values.size else None


def days_after_last_session(log_dates: Sequence[date], session_dates: Sequence[date]) -> np.ndarray:
    """Para cada registro do diario: quantos dias se passaram desde a ultima sessao
    (no mesmo dia ou antes). NaN quando ainda nao tinha havido sessao.

    Vetorizado com np.searchsorted: acha, de uma vez, a posicao de cada registro
    na lista ordenada de sessoes.
    """
    logs = _ordinals(log_dates)
    sessions = np.unique(_ordinals(session_dates))  # ordenado e sem repeticao
    result = np.full(logs.size, np.nan)
    if sessions.size == 0 or logs.size == 0:
        return result
    idx = np.searchsorted(sessions, logs, side="right") - 1
    has_session = idx >= 0
    result[has_session] = logs[has_session] - sessions[idx[has_session]]
    return result


def post_session_mask(log_dates: Sequence[date], session_dates: Sequence[date],
                      window: int = POST_SESSION_DAYS) -> np.ndarray:
    """True para registros feitos do 1o ao `window`-esimo dia depois de uma sessao."""
    gap = days_after_last_session(log_dates, session_dates)
    return (gap >= 1) & (gap <= window)  # NaN compara como False


def post_session_effect(log_dates: Sequence[date], pain_scores: Sequence[Optional[int]],
                        symptom_counts: Sequence[int], session_dates: Sequence[date],
                        window: int = POST_SESSION_DAYS) -> dict:
    """Compara os dias logo apos a sessao com os demais dias do diario."""
    post = post_session_mask(log_dates, session_dates, window)
    pain = _pain_array(pain_scores)
    has_symptom = np.asarray(symptom_counts, dtype=int) > 0

    def group(mask: np.ndarray) -> dict:
        n = int(mask.sum())
        return {
            "logs": n,
            "pain_mean": _mean(pain[mask]),
            "symptom_percent": round(float(has_symptom[mask].mean() * 100), 1) if n else None,
        }

    after, other = group(post), group(~post)
    return {
        "window_days": window,
        "after_session": after,
        "other_days": other,
        "pain_difference": _diff(after["pain_mean"], other["pain_mean"]),
        "symptom_difference": _diff(after["symptom_percent"], other["symptom_percent"], 1),
    }


def session_tolerance(session_dates: Sequence[date], log_dates: Sequence[date],
                      pain_scores: Sequence[Optional[int]], symptom_lists: Sequence[List[str]],
                      baseline_pain: Optional[float] = None,
                      window: int = POST_SESSION_DAYS) -> List[dict]:
    """Como o pet ficou depois de cada sessao.

    Monta uma matriz sessoes x registros (True quando o registro caiu na janela
    pos-sessao) e resolve tudo com operacoes de matriz, sem laco por sessao.
    """
    if len(session_dates) == 0:
        return []
    diff = _ordinals(log_dates)[None, :] - _ordinals(session_dates)[:, None]
    in_window = (diff >= 1) & (diff <= window)                 # (sessoes, registros)

    pain = _pain_array(pain_scores)
    has_symptom = np.array([len(s or []) > 0 for s in symptom_lists], dtype=bool)
    serious = np.array([any(x in SERIOUS_SYMPTOMS for x in (s or [])) for s in symptom_lists], dtype=bool)

    logs_count = in_window.sum(axis=1)
    pain_in_window = np.where(in_window & ~np.isnan(pain)[None, :], pain[None, :], -np.inf)
    max_pain = pain_in_window.max(axis=1, initial=-np.inf)
    symptom_days = (in_window & has_symptom[None, :]).sum(axis=1)
    serious_days = (in_window & serious[None, :]).sum(axis=1)

    rows = []
    for i, session_day in enumerate(session_dates):
        names = sorted({x for j in np.flatnonzero(in_window[i]) for x in (symptom_lists[j] or [])})
        peak = None if np.isinf(max_pain[i]) else int(max_pain[i])
        rows.append({
            "date": session_day,
            "logs": int(logs_count[i]),
            "max_pain": peak,
            "symptom_days": int(symptom_days[i]),
            "symptoms": names,
            "tolerance": classify_tolerance(int(logs_count[i]), peak, int(symptom_days[i]),
                                            int(serious_days[i]), baseline_pain),
        })
    return rows


def classify_tolerance(logs: int, max_pain: Optional[int], symptom_days: int,
                       serious_days: int, baseline_pain: Optional[float]) -> str:
    """boa | moderada | ruim | sem_dados (regras explicadas em docs/MANUAL_PALIATIVO.md)."""
    if logs == 0:
        return "sem_dados"
    if (max_pain is not None and max_pain >= SEVERE_PAIN) or serious_days > 0:
        return "ruim"
    pain_rose = max_pain is not None and baseline_pain is not None and max_pain - baseline_pain >= 2
    if symptom_days > 0 or pain_rose:
        return "moderada"
    return "boa"


def palliative_alerts(pain: Optional[dict], weight: Optional[dict], effect: Optional[dict],
                      sessions: Sequence[dict], days_since_last_log: Optional[int],
                      overdue_protocols: Sequence[str] = (),
                      suspended_protocols: Sequence[str] = ()) -> List[dict]:
    """Lista de alertas {level, code, message}, os criticos primeiro."""
    alerts = []

    def add(level, code, message):
        alerts.append({"level": level, "code": code, "message": message})

    if pain:
        if pain["last"] >= SEVERE_PAIN:
            add("critico", "dor_intensa", f"Dor intensa no último registro ({pain['last']}/10)")
        elif pain.get("recent_mean") is not None and pain["recent_mean"] >= SEVERE_PAIN:
            add("critico", "dor_intensa", f"Dor média de {_br(pain['recent_mean'])} nas últimas 4 semanas")
        if pain.get("recent_change") is not None and pain["recent_change"] >= PAIN_RISE_ALERT:
            add("atencao", "dor_subindo",
                f"Dor subiu {_br(pain['recent_change'])} ponto(s) em relação às 4 semanas anteriores")

    if weight and weight["relevant_loss"]:
        add("critico", "perda_peso", f"Perdeu {_br(abs(weight['change_percent']))}% do peso desde o início")

    if effect:
        if effect["pain_difference"] is not None and effect["pain_difference"] >= POST_SESSION_PAIN_ALERT:
            add("atencao", "dor_pos_sessao",
                f"Dor {_br(effect['pain_difference'])} ponto(s) maior nos {effect['window_days']} dias após as sessões")

    # Tolerancia das ultimas sessoes que tem registro do tutor na janela
    rated = [row for row in sessions if row["tolerance"] != "sem_dados"][-RECENT_SESSIONS:]
    if rated and rated[-1]["tolerance"] == "ruim":
        last = rated[-1]
        details = ([f"dor {last['max_pain']}/10"] if last["max_pain"] is not None and last["max_pain"] >= SEVERE_PAIN else [])
        details += [s for s in last["symptoms"] if s in SERIOUS_SYMPTOMS]
        add("critico", "sessao_mal_tolerada",
            f"Sessão de {last['date'].strftime('%d/%m')} mal tolerada: {', '.join(details)}")
    with_effects = sum(row["tolerance"] in ("moderada", "ruim") for row in rated)
    if len(rated) >= 2 and with_effects >= 2:
        add("atencao", "efeito_colateral",
            f"Efeitos colaterais em {with_effects} das {len(rated)} últimas sessões")

    if days_since_last_log is None:
        add("atencao", "sem_diario", "O tutor ainda não fez nenhum registro no diário")
    elif days_since_last_log >= STALE_DIARY_DAYS:
        add("atencao", "diario_parado", f"Sem registro do tutor há {days_since_last_log} dias")

    for name in overdue_protocols:
        add("atencao", "sessao_atrasada", f"Sessão atrasada no protocolo {name}")
    for name in suspended_protocols:
        add("atencao", "protocolo_suspenso", f"Protocolo {name} suspenso")

    alerts.sort(key=lambda a: -LEVELS.index(a["level"]))  # sort estavel: mantem a ordem dentro do nivel
    return alerts


def overall_level(alerts: Sequence[dict]) -> str:
    """Nivel do paciente = o alerta mais grave (sem alertas: estavel)."""
    if not alerts:
        return "estavel"
    return LEVELS[max(LEVELS.index(a["level"]) for a in alerts)]


def _diff(a: Optional[float], b: Optional[float], digits: int = 2) -> Optional[float]:
    return None if a is None or b is None else round(a - b, digits)


def _br(value: float) -> str:
    """Numero no formato brasileiro, sem casas desnecessarias (1.0 -> '1', 6.5 -> '6,5')."""
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")
