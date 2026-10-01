"""Regras de negocio de protocolos de quimioterapia (RF-04).

Fica fora dos routers para manter as rotas REST finas (RNF-04).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from ..models import ChemoProtocol

STATUS_ATIVO = "ativo"
STATUS_CONCLUIDO = "concluido"
STATUS_SUSPENSO = "suspenso"
VALID_STATUSES = (STATUS_ATIVO, STATUS_CONCLUIDO, STATUS_SUSPENSO)


@dataclass
class ProtocolProgress:
    executed_sessions: int
    remaining_sessions: int
    progress_percent: float
    last_session_date: Optional[date]
    next_session_date: Optional[date]
    is_overdue: bool


def compute_progress(protocol: ChemoProtocol, today: Optional[date] = None) -> ProtocolProgress:
    """Calcula planejadas x executadas e a data prevista da proxima sessao."""
    today = today or date.today()
    executed = len(protocol.sessions)
    planned = protocol.planned_sessions
    remaining = max(planned - executed, 0)
    percent = round(min(executed / planned, 1.0) * 100, 1) if planned else 0.0

    last_date = max((s.date for s in protocol.sessions), default=None)

    next_date = None
    if protocol.status == STATUS_ATIVO and remaining > 0:
        if last_date is None:
            next_date = protocol.start_date
        elif protocol.interval_days:
            next_date = last_date + timedelta(days=protocol.interval_days)

    return ProtocolProgress(
        executed_sessions=executed,
        remaining_sessions=remaining,
        progress_percent=percent,
        last_session_date=last_date,
        next_session_date=next_date,
        is_overdue=next_date is not None and next_date < today,
    )


def check_can_add_session(protocol: ChemoProtocol) -> Optional[str]:
    """Retorna mensagem de erro se o protocolo nao aceita nova sessao, senao None."""
    if protocol.status != STATUS_ATIVO:
        return f"Protocolo esta '{protocol.status}' e nao aceita novas sessoes"
    if len(protocol.sessions) >= protocol.planned_sessions:
        return "Todas as sessoes planejadas deste protocolo ja foram executadas"
    return None


def refresh_status_after_session(protocol: ChemoProtocol) -> None:
    """Marca o protocolo como concluido quando atinge as sessoes planejadas."""
    if protocol.status == STATUS_ATIVO and len(protocol.sessions) >= protocol.planned_sessions:
        protocol.status = STATUS_CONCLUIDO
