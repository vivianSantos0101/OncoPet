"""Sessoes de quimio/radio - somente VET pode criar."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChemoSession, Pet, User
from ..schemas import SessionCreate, SessionResponse
from ..auth import get_current_user, require_vet
from .pets import calculate_bsa

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
def create_session(data: SessionCreate, db: Session = Depends(get_db), user: User = Depends(require_vet)):
    pet = db.query(Pet).filter(Pet.id == data.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")

    dose_administered = None
    if data.dose_mg_m2:
        bsa = calculate_bsa(data.weight_at_session, pet.species)
        dose_administered = round(bsa * data.dose_mg_m2, 2)

    session = ChemoSession(
        pet_id=data.pet_id, date=data.date, session_type=data.session_type,
        drug_name=data.drug_name, dose_mg_m2=data.dose_mg_m2,
        dose_administered=dose_administered,
        weight_at_session=data.weight_at_session, notes=data.notes,
        created_by=user.id,
    )
    db.add(session)
    pet.weight = data.weight_at_session
    db.commit()
    db.refresh(session)
    return session


@router.get("/pet/{pet_id}", response_model=List[SessionResponse])
def list_sessions(pet_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ChemoSession).filter(ChemoSession.pet_id == pet_id).order_by(ChemoSession.date.desc()).all()
