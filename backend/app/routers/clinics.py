"""Clinicas - VET pode criar, todos podem listar."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Clinic, User
from ..schemas import ClinicCreate, ClinicResponse
from ..auth import get_current_user, require_vet

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


@router.post("/", response_model=ClinicResponse, status_code=201)
def create_clinic(data: ClinicCreate, db: Session = Depends(get_db), _: User = Depends(require_vet)):
    clinic = Clinic(**data.model_dump())
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return clinic


@router.get("/", response_model=List[ClinicResponse])
def list_clinics(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Clinic).all()
