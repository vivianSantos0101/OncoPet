"""Recuperacao de senha: link de uso unico, que expira, enviado por e-mail.

Fluxo:
1. create_reset_tokens: para cada conta com o e-mail informado, gera um token
   aleatorio. O banco guarda so o hash SHA-256 dele; o token em si vai so no
   e-mail. Quem ler a tabela nao consegue usar os links ja enviados.
2. reset_password: confere o hash, a validade e se ja foi usado; troca a senha
   e invalida todos os links pendentes daquela conta.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import hash_password
from ..config import RESET_COOLDOWN_SECONDS, RESET_TOKEN_MINUTES
from ..models import PasswordResetToken, User


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_reset_tokens(db: Session, email: str, now: datetime | None = None) -> list[tuple[User, str]]:
    """Cria um token para cada conta com esse e-mail e devolve [(usuario, token)].

    Uma conta que pediu ha menos de RESET_COOLDOWN_SECONDS fica de fora, para
    ninguem usar a rota para encher a caixa de entrada de outra pessoa.
    """
    now = now or datetime.utcnow()
    users = db.query(User).filter(func.lower(User.email) == normalize_email(email)).all()
    created = []
    for user in users:
        recent = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id,
                    PasswordResetToken.created_at > now - timedelta(seconds=RESET_COOLDOWN_SECONDS))
            .first()
        )
        if recent:
            continue
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=now + timedelta(minutes=RESET_TOKEN_MINUTES),
            created_at=now,
        ))
        created.append((user, token))
    db.commit()
    return created


def reset_password(db: Session, token: str, new_password: str, now: datetime | None = None) -> User | None:
    """Troca a senha. Devolve o usuario, ou None se o token for invalido, vencido ou ja usado."""
    now = now or datetime.utcnow()
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_token(token)).first()
    if row is None or row.used_at is not None or row.expires_at < now:
        return None

    user = row.user
    user.hashed_password = hash_password(new_password)
    # Invalida este link e qualquer outro pendente da mesma conta
    (db.query(PasswordResetToken)
       .filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
       .update({"used_at": now}, synchronize_session=False))
    db.commit()
    return user
