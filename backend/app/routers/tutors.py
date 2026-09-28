"""Listagem de tutores - VET pode listar tutores para atribuir pets."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserResponse
from ..auth import get_current_user, require_vet

router = APIRouter(prefix="/api/tutors", tags=["tutors"])


@router.get("/", response_model=List[UserResponse])
def list_tutors(db: Session = Depends(get_db), _: User = Depends(require_vet)):
    """Vet lista todos os tutores cadastrados."""
    return db.query(User).filter(User.role == "tutor").all()
