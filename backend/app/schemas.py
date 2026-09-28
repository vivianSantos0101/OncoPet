"""Pydantic schemas v3."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel


# ─── Auth ─────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str  # "vet" ou "tutor"
    crmv: Optional[str] = None
    clinic_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    crmv: Optional[str] = None
    clinic_id: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Clinic ───────────────────────────────────────────

class ClinicCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class ClinicResponse(ClinicCreate):
    id: int
    class Config:
        from_attributes = True


# ─── Pet ──────────────────────────────────────────────

class PetCreate(BaseModel):
    name: str
    species: str
    breed: str
    weight: float
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    photo_url: Optional[str] = None
    cancer_type: Optional[str] = None
    treatment_start_date: Optional[date] = None
    tutor_id: Optional[int] = None  # se vet cria, precisa informar
    vet_id: Optional[int] = None
    clinic_id: Optional[int] = None


class PetUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    weight: Optional[float] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    photo_url: Optional[str] = None
    cancer_type: Optional[str] = None
    treatment_start_date: Optional[date] = None
    vet_id: Optional[int] = None
    clinic_id: Optional[int] = None


class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    breed: str
    weight: float
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    photo_url: Optional[str] = None
    cancer_type: Optional[str] = None
    treatment_start_date: Optional[date] = None
    tutor_id: int
    vet_id: Optional[int] = None
    clinic_id: Optional[int] = None
    body_surface_area: float
    tutor_name: Optional[str] = None
    vet_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Session (vet only) ──────────────────────────────

class SessionCreate(BaseModel):
    pet_id: int
    date: date
    session_type: str = "quimioterapia"
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = None
    weight_at_session: float
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    pet_id: int
    date: date
    session_type: str
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = None
    dose_administered: Optional[float] = None
    weight_at_session: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Record (tutor only) ─────────────────────────────

class RecordCreate(BaseModel):
    pet_id: int
    date: date
    weight: Optional[float] = None
    symptoms: Optional[str] = None
    general_status: Optional[str] = None
    appetite: Optional[str] = None
    energy_level: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class RecordResponse(BaseModel):
    id: int
    pet_id: int
    date: date
    weight: Optional[float] = None
    symptoms: Optional[str] = None
    general_status: Optional[str] = None
    appetite: Optional[str] = None
    energy_level: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Document (vet only) ─────────────────────────────

class DocumentCreate(BaseModel):
    pet_id: int
    title: str
    doc_type: str
    file_url: str
    date: Optional[str] = None
    notes: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    pet_id: int
    title: str
    doc_type: str
    file_url: str
    date: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Dose Calculator ─────────────────────────────────

class DoseCalculation(BaseModel):
    weight: float
    species: str
    dose_mg_m2: float


class DoseResult(BaseModel):
    weight: float
    species: str
    body_surface_area: float
    dose_mg_m2: float
    dose_administered_mg: float


# ─── Breeds ──────────────────────────────────────────

class BreedsResponse(BaseModel):
    dogs: List[str]
    cats: List[str]


# ─── Chart data ──────────────────────────────────────

class WeightPoint(BaseModel):
    date: date
    weight: float


class StatusPoint(BaseModel):
    date: date
    status: str


class ChartDataResponse(BaseModel):
    weight_history: List[WeightPoint]
    sessions_count: int
    records_count: int
    last_weight: Optional[float] = None
    treatment_days: Optional[int] = None


# ─── Reminder / Agenda ───────────────────────────────

class ReminderCreate(BaseModel):
    pet_id: int
    title: str
    reminder_type: str  # sessao, medicacao, consulta, exame, outro
    date: date
    time: Optional[str] = None  # HH:MM
    recurrence: Optional[str] = None  # nenhuma, diaria, semanal, mensal
    notes: Optional[str] = None


class ReminderUpdate(BaseModel):
    is_completed: Optional[bool] = None
    date: Optional[date] = None
    time: Optional[str] = None
    notes: Optional[str] = None


class ReminderResponse(BaseModel):
    id: int
    pet_id: int
    title: str
    reminder_type: str
    date: date
    time: Optional[str] = None
    recurrence: Optional[str] = None
    notes: Optional[str] = None
    is_completed: bool
    created_by: int

    class Config:
        from_attributes = True
