"""Rotas de autenticacao."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, Token
from ..auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ja existe")

    if user_data.role not in ("vet", "tutor"):
        raise HTTPException(status_code=400, detail="Role deve ser 'vet' ou 'tutor'")

    user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role,
        crmv=user_data.crmv if user_data.role == "vet" else None,
        clinic_id=user_data.clinic_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")

    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token, user=UserResponse.model_validate(user))
