"""Rotas de autenticacao."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import emails
from ..config import APP_URL, RESET_TOKEN_MINUTES
from ..database import get_db
from ..models import User
from ..schemas import (
    ForgotPasswordRequest, MessageResponse, ResetPasswordRequest, Token, UserCreate, UserResponse,
)
from ..services.password_reset import create_reset_tokens, normalize_email, reset_password
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
        email=normalize_email(user_data.email),
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


# ─── Esqueci minha senha ─────────────────────────────

FORGOT_MESSAGE = (
    "Se o e-mail estiver cadastrado, enviamos um link para criar uma nova senha. "
    "Ele vale por {minutes} minutos."
)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db)):
    """Manda para o e-mail do cadastro um link para criar uma nova senha.

    A resposta e sempre a mesma, exista ou nao uma conta com esse e-mail:
    assim a rota nao serve para descobrir quem esta cadastrado.
    O e-mail sai em segundo plano, depois da resposta.
    """
    for user, token in create_reset_tokens(db, data.email):
        link = f"{APP_URL}/redefinir-senha?token={token}"
        subject, text, html = emails.password_reset_email(user.full_name, user.username, link, RESET_TOKEN_MINUTES)
        background_tasks.add_task(emails.send_email, user.email, subject, text, html)
    return MessageResponse(message=FORGOT_MESSAGE.format(minutes=RESET_TOKEN_MINUTES))


@router.post("/reset-password", response_model=MessageResponse)
def reset_password_route(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Troca a senha usando o token do link. O token vale uma vez so."""
    if reset_password(db, data.token, data.new_password) is None:
        raise HTTPException(
            status_code=400,
            detail="Link inválido ou vencido. Peça um novo em \"Esqueci minha senha\".",
        )
    return MessageResponse(message="Senha alterada. Entre com a nova senha.")
