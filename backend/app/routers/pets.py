"""CRUD de pets + racas + calculo de dose."""

from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Pet, User, ChemoSession
from ..mongodb import get_daily_logs_collection
from ..services.daily_logs import list_logs
from ..schemas import (
    PetCreate, PetUpdate, PetResponse, DoseCalculation, DoseResult,
    BreedsResponse, ChartDataResponse, WeightPoint
)
from ..auth import get_current_user, require_vet
from ..breeds import DOG_BREEDS, CAT_BREEDS

router = APIRouter(prefix="/api/pets", tags=["pets"])


def calculate_bsa(weight: float, species: str) -> float:
    if species.lower() in ("gato", "felino", "cat"):
        return 0.101 * (weight ** 0.667)
    return 0.101 * (weight ** 0.734)


def pet_to_response(pet: Pet) -> PetResponse:
    return PetResponse(
        id=pet.id, name=pet.name, species=pet.species, breed=pet.breed,
        weight=pet.weight, age_years=pet.age_years, age_months=pet.age_months,
        photo_url=pet.photo_url, cancer_type=pet.cancer_type,
        treatment_start_date=pet.treatment_start_date,
        tutor_id=pet.tutor_id, vet_id=pet.vet_id, clinic_id=pet.clinic_id,
        body_surface_area=pet.body_surface_area,
        tutor_name=pet.tutor.full_name if pet.tutor else None,
        vet_name=pet.vet.full_name if pet.vet else None,
    )


@router.get("/breeds", response_model=BreedsResponse)
def get_breeds():
    return BreedsResponse(dogs=DOG_BREEDS, cats=CAT_BREEDS)


@router.post("/", response_model=PetResponse, status_code=201)
def create_pet(data: PetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Vet cria pet e atribui a um tutor; tutor cria pro proprio
    if user.role == "tutor":
        tutor_id = user.id
    else:
        tutor_id = data.tutor_id
        if not tutor_id:
            raise HTTPException(status_code=400, detail="tutor_id obrigatorio quando vet cria o pet")

    pet = Pet(
        name=data.name, species=data.species, breed=data.breed,
        weight=data.weight, age_years=data.age_years, age_months=data.age_months,
        photo_url=data.photo_url, cancer_type=data.cancer_type,
        treatment_start_date=data.treatment_start_date,
        tutor_id=tutor_id, vet_id=data.vet_id or (user.id if user.role == "vet" else None),
        clinic_id=data.clinic_id,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet_to_response(pet)


@router.get("/", response_model=List[PetResponse])
def list_pets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Tutor ve so seus pets; vet ve pets atribuidos a ele."""
    if user.role == "tutor":
        pets = db.query(Pet).filter(Pet.tutor_id == user.id).all()
    else:
        pets = db.query(Pet).filter(Pet.vet_id == user.id).all()
    return [pet_to_response(p) for p in pets]


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")
    # Verifica acesso
    if user.role == "tutor" and pet.tutor_id != user.id:
        raise HTTPException(status_code=403, detail="Sem acesso a este pet")
    if user.role == "vet" and pet.vet_id != user.id:
        raise HTTPException(status_code=403, detail="Sem acesso a este pet")
    return pet_to_response(pet)


@router.patch("/{pet_id}", response_model=PetResponse)
def update_pet(pet_id: int, data: PetUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pet, field, value)
    db.commit()
    db.refresh(pet)
    return pet_to_response(pet)


@router.get("/{pet_id}/chart", response_model=ChartDataResponse)
async def get_pet_chart_data(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Dados para grafico: peso das sessoes (relacional) + diario do tutor (MongoDB)."""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")

    sessions = db.query(ChemoSession).filter(ChemoSession.pet_id == pet_id).order_by(ChemoSession.date).all()
    records = await list_logs(get_daily_logs_collection(), pet_id, newest_first=False)

    # Montar historico de peso (sessions + records)
    weight_points = []
    for s in sessions:
        weight_points.append(WeightPoint(date=s.date, weight=s.weight_at_session))
    for r in records:
        if r.get("weight"):
            weight_points.append(WeightPoint(date=date.fromisoformat(r["date"]), weight=r["weight"]))

    weight_points.sort(key=lambda x: x.date)

    treatment_days = None
    if pet.treatment_start_date:
        treatment_days = (date.today() - pet.treatment_start_date).days

    return ChartDataResponse(
        weight_history=weight_points,
        sessions_count=len(sessions),
        records_count=len(records),
        last_weight=weight_points[-1].weight if weight_points else pet.weight,
        treatment_days=treatment_days,
    )


@router.post("/calculate-dose", response_model=DoseResult)
def calculate_dose(data: DoseCalculation, _: User = Depends(get_current_user)):
    bsa = calculate_bsa(data.weight, data.species)
    dose = round(bsa * data.dose_mg_m2, 2)
    return DoseResult(
        weight=data.weight, species=data.species,
        body_surface_area=round(bsa, 4),
        dose_mg_m2=data.dose_mg_m2, dose_administered_mg=dose,
    )
