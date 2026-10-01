"""Logica de autenticacao JWT com roles.

O token vai num cookie HttpOnly (o navegador envia sozinho e o JavaScript
nao consegue ler). O cabecalho "Authorization: Bearer" continua aceito para
clientes que nao sao o navegador: /docs, testes, scripts e curl.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, AUTH_COOKIE_NAME, COOKIE_SAMESITE, COOKIE_SECURE, SECRET_KEY,
)
from .database import get_db
from .models import User

# auto_error=False: sem cabecalho Authorization, procuramos o token no cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_HEADER = "X-Requested-With"  # o front envia "XMLHttpRequest" em toda requisicao


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def set_auth_cookie(response: Response, token: str) -> None:
    """Grava o token no cookie de sessao (HttpOnly: o JavaScript nao le)."""
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/api", httponly=True,
                           secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessao invalida ou expirada. Entre novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)
        if not token:
            raise credentials_exception
        # Protecao contra CSRF: outro site ate consegue fazer o navegador enviar
        # o cookie, mas nao consegue adicionar este cabecalho
        if request.method not in SAFE_METHODS and request.headers.get(CSRF_HEADER) != "XMLHttpRequest":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requisicao recusada (CSRF)")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def require_vet(current_user: User = Depends(get_current_user)) -> User:
    """Dependency que garante que o user e veterinario."""
    if current_user.role != "vet":
        raise HTTPException(status_code=403, detail="Acesso restrito a veterinarios")
    return current_user


def require_tutor(current_user: User = Depends(get_current_user)) -> User:
    """Dependency que garante que o user e tutor."""
    if current_user.role != "tutor":
        raise HTTPException(status_code=403, detail="Acesso restrito a tutores")
    return current_user
