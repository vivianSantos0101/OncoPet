"""Diario do tutor (MongoDB) - tutor registra, tutor e veterinario consultam."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_tutor
from ..database import get_db
from ..models import Pet, User
from ..mongodb import get_daily_logs_collection
from ..schemas import RecordCreate, RecordResponse
from ..services.daily_logs import list_logs, to_document, to_response
from .pets import ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/records", tags=["records"])


@router.post("/", response_model=RecordResponse, status_code=201)
async def create_record(data: RecordCreate, db: Session = Depends(get_db), user: User = Depends(require_tutor)):
    # Integridade entre os bancos: o pet precisa existir no relacional e ser do tutor
    pet = db.query(Pet).filter(Pet.id == data.pet_id, Pet.tutor_id == user.id).first()
    if not pet:
        raise HTTPException(status_code=403, detail="Voce nao e tutor deste pet")

    doc = to_document(data, created_by=user.id)
    result = await get_daily_logs_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    # O peso mais recente tambem fica no cadastro do pet (usado no calculo de dose)
    if data.weight:
        pet.weight = data.weight
        db.commit()

    return to_response(doc)


@router.get("/pet/{pet_id}", response_model=List[RecordResponse])
async def list_records(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_pet_access(get_pet_or_404(db, pet_id), user)

    docs = await list_logs(get_daily_logs_collection(), pet_id)
    return [to_response(d) for d in docs]
