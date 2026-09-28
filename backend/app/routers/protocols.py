"""Protocolos de quimioterapia (RF-04) - vet cria/edita, tutor consulta."""

from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChemoProtocol, Pet, User
from ..schemas import ProtocolCreate, ProtocolUpdate, ProtocolResponse
from ..auth import get_current_user, require_vet
from ..services.protocols import compute_progress

router = APIRouter(prefix="/api/protocols", tags=["protocols"])


def to_response(protocol: ChemoProtocol) -> ProtocolResponse:
    progress = compute_progress(protocol)
    return ProtocolResponse(
        id=protocol.id, pet_id=protocol.pet_id, name=protocol.name,
        drug_name=protocol.drug_name, dose_mg_m2=protocol.dose_mg_m2,
        planned_sessions=protocol.planned_sessions, interval_days=protocol.interval_days,
        start_date=protocol.start_date, status=protocol.status, notes=protocol.notes,
        **asdict(progress),
    )


def get_pet_or_404(db: Session, pet_id: int) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")
    return pet


def check_pet_access(pet: Pet, user: User) -> None:
    if user.role == "tutor" and pet.tutor_id != user.id:
        raise HTTPException(status_code=403, detail="Sem acesso a este pet")


def get_protocol_or_404(db: Session, protocol_id: int) -> ChemoProtocol:
    protocol = db.query(ChemoProtocol).filter(ChemoProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocolo nao encontrado")
    return protocol


@router.post("/", response_model=ProtocolResponse, status_code=201)
def create_protocol(data: ProtocolCreate, db: Session = Depends(get_db), user: User = Depends(require_vet)):
    get_pet_or_404(db, data.pet_id)
    protocol = ChemoProtocol(**data.model_dump(), status="ativo", created_by=user.id)
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    return to_response(protocol)


@router.get("/pet/{pet_id}", response_model=List[ProtocolResponse])
def list_protocols(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_pet_access(get_pet_or_404(db, pet_id), user)
    protocols = (
        db.query(ChemoProtocol)
        .filter(ChemoProtocol.pet_id == pet_id)
        .order_by(ChemoProtocol.start_date.desc())
        .all()
    )
    return [to_response(p) for p in protocols]


@router.get("/{protocol_id}", response_model=ProtocolResponse)
def get_protocol(protocol_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    protocol = get_protocol_or_404(db, protocol_id)
    check_pet_access(protocol.pet, user)
    return to_response(protocol)


@router.patch("/{protocol_id}", response_model=ProtocolResponse)
def update_protocol(
    protocol_id: int, data: ProtocolUpdate,
    db: Session = Depends(get_db), _: User = Depends(require_vet),
):
    protocol = get_protocol_or_404(db, protocol_id)
    changes = data.model_dump(exclude_unset=True)

    planned = changes.get("planned_sessions")
    if planned is not None and planned < len(protocol.sessions):
        raise HTTPException(
            status_code=400,
            detail=f"Ja existem {len(protocol.sessions)} sessoes executadas; "
                   "o total planejado nao pode ser menor",
        )

    for field, value in changes.items():
        setattr(protocol, field, value)
    db.commit()
    db.refresh(protocol)
    return to_response(protocol)
