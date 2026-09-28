"""Modelos ORM - OncoPet v3."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class User(Base):
    """Usuario do sistema - pode ser 'vet' ou 'tutor'."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False)  # "vet" ou "tutor"
    crmv = Column(String(20), nullable=True)  # so para vets
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clinic = relationship("Clinic", back_populates="vets")
    # Pets que este user e tutor
    pets_as_tutor = relationship("Pet", back_populates="tutor", foreign_keys="Pet.tutor_id")


class Clinic(Base):
    """Clinica veterinaria."""
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    vets = relationship("User", back_populates="clinic")


class Pet(Base):
    """Paciente animal."""
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    species = Column(String(50), nullable=False)
    breed = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)
    age_years = Column(Integer, nullable=True)
    age_months = Column(Integer, nullable=True)
    photo_url = Column(String(500), nullable=True)
    cancer_type = Column(String(150), nullable=True)
    treatment_start_date = Column(Date, nullable=True)
    tutor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vet_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True)

    tutor = relationship("User", back_populates="pets_as_tutor", foreign_keys=[tutor_id])
    vet = relationship("User", foreign_keys=[vet_id])
    clinic = relationship("Clinic")
    sessions = relationship("ChemoSession", back_populates="pet", cascade="all, delete-orphan")
    records = relationship("PetRecord", back_populates="pet", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="pet", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="pet", cascade="all, delete-orphan")

    @property
    def body_surface_area(self) -> float:
        if self.species.lower() in ("gato", "felino", "cat"):
            return round(0.101 * (self.weight ** 0.667), 4)
        return round(0.101 * (self.weight ** 0.734), 4)


class ChemoSession(Base):
    """Sessao de quimioterapia/radioterapia - registrada pelo VET."""
    __tablename__ = "chemo_sessions"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    date = Column(Date, nullable=False)
    session_type = Column(String(50), nullable=False, default="quimioterapia")  # quimioterapia, radioterapia
    drug_name = Column(String(150), nullable=True)
    dose_mg_m2 = Column(Float, nullable=True)
    dose_administered = Column(Float, nullable=True)
    weight_at_session = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    pet = relationship("Pet", back_populates="sessions")


class PetRecord(Base):
    """Registro de acompanhamento - feito pelo TUTOR (diario)."""
    __tablename__ = "pet_records"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    date = Column(Date, nullable=False)
    weight = Column(Float, nullable=True)
    symptoms = Column(Text, nullable=True)
    general_status = Column(String(50), nullable=True)
    appetite = Column(String(50), nullable=True)
    energy_level = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    pet = relationship("Pet", back_populates="records")


class Document(Base):
    """Documentos anexados (exames, laudos) - pelo VET."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    title = Column(String(200), nullable=False)
    doc_type = Column(String(50), nullable=False)  # exame_sangue, exame_imagem, laudo, outro
    file_url = Column(String(500), nullable=False)
    date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    pet = relationship("Pet", back_populates="documents")


class Reminder(Base):
    """Lembrete/agenda para o pet - criado pelo VET, visivel para o TUTOR."""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    title = Column(String(200), nullable=False)
    reminder_type = Column(String(50), nullable=False)  # sessao, medicacao, consulta, exame, outro
    date = Column(Date, nullable=False)
    time = Column(String(5), nullable=True)  # HH:MM formato
    recurrence = Column(String(30), nullable=True)  # nenhuma, diaria, semanal, mensal
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    pet = relationship("Pet", back_populates="reminders")
