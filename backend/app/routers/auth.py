"""Rotas de autenticacao."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, Token
from ..auth import (
    clear_auth_cookie, create_access_token, get_current_user, hash_password, set_auth_cookie, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=201)
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
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
    set_auth_cookie(response, token)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Entra no sistema. O navegador recebe o cookie de sessao; o access_token
    no corpo serve para clientes que usam o cabecalho Authorization (/docs, scripts)."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")

    token = create_access_token(data={"sub": user.username})
    set_auth_cookie(response, token)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    """Usuario da sessao atual (o front chama ao abrir o app)."""
    return user


@router.post("/logout", status_code=204)
def logout():
    """Apaga o cookie de sessao."""
    response = Response(status_code=204)
    clear_auth_cookie(response)
    return response
