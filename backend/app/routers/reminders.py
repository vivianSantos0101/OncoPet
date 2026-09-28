"""Lembretes/Agenda - VET cria, TUTOR visualiza e marca como concluido."""

from typing import List
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reminder, Pet, User
from ..schemas import ReminderCreate, ReminderUpdate, ReminderResponse
from ..auth import get_current_user, require_vet

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("/", response_model=ReminderResponse, status_code=201)
def create_reminder(data: ReminderCreate, db: Session = Depends(get_db), user: User = Depends(require_vet)):
    """Vet cria lembrete para um pet (tutor vera a notificacao)."""
    pet = db.query(Pet).filter(Pet.id == data.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet nao encontrado")

    reminder = Reminder(**data.model_dump(), created_by=user.id)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/pet/{pet_id}", response_model=List[ReminderResponse])
def list_reminders_by_pet(pet_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Lista todos os lembretes de um pet (agenda)."""
    return (
        db.query(Reminder)
        .filter(Reminder.pet_id == pet_id)
        .order_by(Reminder.date.asc())
        .all()
    )


@router.get("/upcoming", response_model=List[ReminderResponse])
def get_upcoming_reminders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    days: int = Query(default=7, description="Lembretes nos proximos N dias"),
):
    """Retorna lembretes pendentes dos proximos N dias para o usuario logado.
    - Tutor: ve lembretes dos seus pets
    - Vet: ve lembretes dos pets que ele atende
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    if user.role == "tutor":
        pet_ids = [p.id for p in db.query(Pet).filter(Pet.tutor_id == user.id).all()]
    else:
        pet_ids = [p.id for p in db.query(Pet).filter(Pet.vet_id == user.id).all()]

    if not pet_ids:
        return []

    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.pet_id.in_(pet_ids),
            Reminder.date >= today,
            Reminder.date <= end_date,
            Reminder.is_completed == False,
        )
        .order_by(Reminder.date.asc())
        .all()
    )
    return reminders


@router.get("/today", response_model=List[ReminderResponse])
def get_today_reminders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retorna lembretes de HOJE (para notificacoes pop-up)."""
    today = date.today()

    if user.role == "tutor":
        pet_ids = [p.id for p in db.query(Pet).filter(Pet.tutor_id == user.id).all()]
    else:
        pet_ids = [p.id for p in db.query(Pet).filter(Pet.vet_id == user.id).all()]

    if not pet_ids:
        return []

    return (
        db.query(Reminder)
        .filter(
            Reminder.pet_id.in_(pet_ids),
            Reminder.date == today,
            Reminder.is_completed == False,
        )
        .order_by(Reminder.date.asc())
        .all()
    )


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tutor ou vet pode marcar como concluido ou atualizar."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete nao encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)

    db.commit()
    db.refresh(reminder)
    return reminder
