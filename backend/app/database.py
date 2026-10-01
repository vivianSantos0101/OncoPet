"""Configuracao do banco de dados SQLAlchemy + PostgreSQL."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

# SQLite (usado nos testes) precisa liberar o uso entre threads do TestClient
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency que fornece uma sessao do banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
