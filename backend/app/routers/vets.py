"""Listagem de vets - tutor pode ver vets para atribuir ao pet."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/vets", tags=["vets"])


@router.get("/", response_model=List[UserResponse])
def list_vets(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Lista todos os veterinarios cadastrados."""
    return db.query(User).filter(User.role == "vet").all()
