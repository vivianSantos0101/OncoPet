"""Pydantic schemas v3."""

from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


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

# Limites de validacao (idade/peso nao podem ser negativos)
MAX_AGE_YEARS = 40
MAX_WEIGHT_KG = 150



class PetCreate(BaseModel):
    name: str
    species: str
    breed: str
    weight: float = Field(gt=0, le=MAX_WEIGHT_KG)
    age_years: Optional[int] = Field(default=None, ge=0, le=MAX_AGE_YEARS)
    age_months: Optional[int] = Field(default=None, ge=0, le=11)
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
    weight: Optional[float] = Field(default=None, gt=0, le=MAX_WEIGHT_KG)
    age_years: Optional[int] = Field(default=None, ge=0, le=MAX_AGE_YEARS)
    age_months: Optional[int] = Field(default=None, ge=0, le=11)
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


# ─── Protocolo de quimio (vet only) ──────────────────

ProtocolStatus = Literal["ativo", "concluido", "suspenso"]


class ProtocolCreate(BaseModel):
    pet_id: int
    name: str
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = Field(default=None, gt=0)
    planned_sessions: int = Field(gt=0)
    interval_days: Optional[int] = Field(default=None, gt=0)
    start_date: date
    notes: Optional[str] = None


class ProtocolUpdate(BaseModel):
    name: Optional[str] = None
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = Field(default=None, gt=0)
    planned_sessions: Optional[int] = Field(default=None, gt=0)
    interval_days: Optional[int] = Field(default=None, gt=0)
    status: Optional[ProtocolStatus] = None
    notes: Optional[str] = None


class ProtocolResponse(BaseModel):
    id: int
    pet_id: int
    name: str
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = None
    planned_sessions: int
    interval_days: Optional[int] = None
    start_date: date
    status: ProtocolStatus
    notes: Optional[str] = None
    # Progresso calculado
    executed_sessions: int
    remaining_sessions: int
    progress_percent: float
    last_session_date: Optional[date] = None
    next_session_date: Optional[date] = None
    is_overdue: bool


# ─── Session (vet only) ──────────────────────────────

class SessionCreate(BaseModel):
    pet_id: int
    protocol_id: Optional[int] = None
    date: date
    session_type: str = "quimioterapia"
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = Field(default=None, gt=0)
    weight_at_session: float = Field(gt=0, le=MAX_WEIGHT_KG)
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    pet_id: int
    protocol_id: Optional[int] = None
    date: date
    session_type: str
    drug_name: Optional[str] = None
    dose_mg_m2: Optional[float] = None
    dose_administered: Optional[float] = None
    weight_at_session: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Diario do tutor (MongoDB, RF-02/RF-03) ─────────

# Sintomas que o tutor pode marcar; outros vao em texto livre (other_symptoms)
Symptom = Literal[
    "vomito", "diarreia", "letargia", "inapetencia",
    "febre", "tosse", "dispneia", "lesao_pele",
]


class RecordCreate(BaseModel):
    pet_id: int
    date: date
    weight: Optional[float] = Field(default=None, gt=0, le=MAX_WEIGHT_KG)
    symptoms: List[Symptom] = Field(default_factory=list)
    other_symptoms: Optional[str] = None
    pain_score: Optional[int] = Field(default=None, ge=0, le=10)  # escala de dor 0-10
    general_status: Optional[str] = None
    appetite: Optional[str] = None
    energy_level: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class RecordResponse(BaseModel):
    id: str  # ObjectId do MongoDB
    pet_id: int
    date: date
    weight: Optional[float] = None
    symptoms: List[str] = Field(default_factory=list)
    other_symptoms: Optional[str] = None
    pain_score: Optional[int] = None
    general_status: Optional[str] = None
    appetite: Optional[str] = None
    energy_level: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


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
    weight: float = Field(gt=0, le=MAX_WEIGHT_KG)
    species: str
    dose_mg_m2: float = Field(gt=0)


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


# ─── Estatisticas (RF-05) ─────────────────────────────

class WeightStatPoint(BaseModel):
    date: date
    weight: float
    moving_average: float


class PainStatPoint(BaseModel):
    date: date
    pain: int
    moving_average: float


class WeightSummary(BaseModel):
    first: float
    last: float
    min: float
    max: float
    change_kg: float
    change_percent: float
    trend_kg_per_week: Optional[float] = None
    relevant_loss: bool  # perda >= 5% desde o inicio


class PainSummary(BaseModel):
    mean: float
    last: int
    max: int
    recent_mean: Optional[float] = None     # ultimas 4 semanas
    previous_mean: Optional[float] = None   # 4 semanas anteriores
    recent_change: Optional[float] = None
    trend_per_week: Optional[float] = None
    severe_percent: float                   # % dos registros com dor >= 7


class SymptomCount(BaseModel):
    symptom: str
    count: int
    percent: float


class PetAnalytics(BaseModel):
    pet_id: int
    reference_date: date
    logs_count: int
    weight_points: List[WeightStatPoint]
    weight: Optional[WeightSummary] = None
    pain_points: List[PainStatPoint]
    pain: Optional[PainSummary] = None
    symptoms: List[SymptomCount]

