"""Registros diarios - somente TUTOR pode criar."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PetRecord, Pet, User
from ..schemas import RecordCreate, RecordResponse
from ..auth import get_current_user, require_tutor

router = APIRouter(prefix="/api/records", tags=["records"])


@router.post("/", response_model=RecordResponse, status_code=201)
def create_record(data: RecordCreate, db: Session = Depends(get_db), user: User = Depends(require_tutor)):
    # Verifica se o pet pertence ao tutor
    pet = db.query(Pet).filter(Pet.id == data.pet_id, Pet.tutor_id == user.id).first()
    if not pet:
        raise HTTPException(status_code=403, detail="Voce nao e tutor deste pet")

    record = PetRecord(
        pet_id=data.pet_id, date=data.date, weight=data.weight,
        symptoms=data.symptoms, general_status=data.general_status,
        appetite=data.appetite, energy_level=data.energy_level,
        photo_url=data.photo_url, notes=data.notes,
        created_by=user.id,
    )
    db.add(record)
    if data.weight:
        pet.weight = data.weight
    db.commit()
    db.refresh(record)
    return record


@router.get("/pet/{pet_id}", response_model=List[RecordResponse])
def list_records(pet_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(PetRecord).filter(PetRecord.pet_id == pet_id).order_by(PetRecord.date.desc()).all()
