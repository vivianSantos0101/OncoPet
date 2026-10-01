"""Sessoes de quimio/radio - somente VET pode criar."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChemoProtocol, ChemoSession, User
from ..schemas import SessionCreate, SessionResponse
from ..auth import get_current_user, require_vet
from ..services.protocols import check_can_add_session, refresh_status_after_session
from .pets import calculate_bsa, ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
def create_session(data: SessionCreate, db: Session = Depends(get_db), user: User = Depends(require_vet)):
    pet = get_pet_or_404(db, data.pet_id)
    ensure_pet_access(pet, user)  # so o vet responsavel registra sessao

    drug_name, dose_mg_m2 = data.drug_name, data.dose_mg_m2

    protocol = None
    if data.protocol_id is not None:
        protocol = db.query(ChemoProtocol).filter(ChemoProtocol.id == data.protocol_id).first()
        if not protocol or protocol.pet_id != pet.id:
            raise HTTPException(status_code=404, detail="Protocolo nao encontrado para este pet")
        error = check_can_add_session(protocol)
        if error:
            raise HTTPException(status_code=400, detail=error)
        # Herda medicamento e dose do protocolo quando nao informados
        drug_name = drug_name or protocol.drug_name
        dose_mg_m2 = dose_mg_m2 or protocol.dose_mg_m2

    dose_administered = None
    if dose_mg_m2:
        bsa = calculate_bsa(data.weight_at_session, pet.species)
        dose_administered = round(bsa * dose_mg_m2, 2)

    session = ChemoSession(
        pet_id=data.pet_id, protocol_id=data.protocol_id,
        date=data.date, session_type=data.session_type,
        drug_name=drug_name, dose_mg_m2=dose_mg_m2,
        dose_administered=dose_administered,
        weight_at_session=data.weight_at_session, notes=data.notes,
        created_by=user.id,
    )
    db.add(session)
    pet.weight = data.weight_at_session
    if protocol is not None:
        db.flush()
        db.refresh(protocol)
        refresh_status_after_session(protocol)
    db.commit()
    db.refresh(session)
    return session


@router.get("/pet/{pet_id}", response_model=List[SessionResponse])
def list_sessions(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_pet_access(get_pet_or_404(db, pet_id), user)
    return db.query(ChemoSession).filter(ChemoSession.pet_id == pet_id).order_by(ChemoSession.date.desc()).all()
