"""Configuracao do banco de dados SQLAlchemy + PostgreSQL."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency que fornece uma sessao do banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
