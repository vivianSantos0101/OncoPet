"""Documentos (exames, laudos) - somente o VET responsavel pode criar.

So o tutor dono e o vet responsavel pelo pet podem ver os documentos.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document, User
from ..schemas import DocumentCreate, DocumentResponse
from ..auth import get_current_user, require_vet
from .pets import ensure_pet_access, get_pet_or_404

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=201)
def create_document(data: DocumentCreate, db: Session = Depends(get_db), user: User = Depends(require_vet)):
    from datetime import date as date_type
    ensure_pet_access(get_pet_or_404(db, data.pet_id), user)
    doc_data = data.model_dump()
    if doc_data.get("date"):
        doc_data["date"] = date_type.fromisoformat(doc_data["date"])
    else:
        doc_data["date"] = None
    doc = Document(**doc_data, uploaded_by=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentResponse(
        id=doc.id, pet_id=doc.pet_id, title=doc.title, doc_type=doc.doc_type,
        file_url=doc.file_url, date=str(doc.date) if doc.date else None, notes=doc.notes,
    )


@router.get("/pet/{pet_id}", response_model=List[DocumentResponse])
def list_documents(pet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_pet_access(get_pet_or_404(db, pet_id), user)
    docs = db.query(Document).filter(Document.pet_id == pet_id).order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id, pet_id=d.pet_id, title=d.title, doc_type=d.doc_type,
            file_url=d.file_url, date=str(d.date) if d.date else None, notes=d.notes,
        ))
    return results
