"""Relatorio clinico em PDF (RF-07).

Unifica o relacional (paciente, protocolos, sessoes, documentos) e o MongoDB
(diario do tutor), com as estatisticas (RF-05) e os alertas (RF-06).
"""

import re
import unicodedata
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..reports.pdf import render_report
from ..services.clinical_report import collect_report
from .pets import ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/reports", tags=["relatorios"])


def report_filename(pet_name: str, day: date) -> str:
    """'Relatório Luna' -> relatorio-luna-2026-09-30.pdf (sem acento nem espaco)."""
    ascii_name = unicodedata.normalize("NFKD", pet_name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or "paciente"
    return f"relatorio-{slug}-{day.isoformat()}.pdf"


@router.get(
    "/pet/{pet_id}",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "Relatório em PDF"}},
)
async def pet_report(
    pet_id: int,
    reference_date: Optional[date] = Query(None, description="Considera os dados ate esta data (padrao: hoje)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Relatório clínico unificado do paciente, em PDF (tutor dono e vet responsável)."""
    pet = get_pet_or_404(db, pet_id)
    ensure_pet_access(pet, user)
    today = reference_date or date.today()
    pdf = render_report(await collect_report(db, pet, today))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report_filename(pet.name, today)}"'},
    )
