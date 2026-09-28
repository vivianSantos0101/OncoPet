"""Exames armazenados no MongoDB.

Cada exame e um documento flexivel - campos variam conforme o tipo:
- Hemograma: leucocitos, hemacias, plaquetas, hemoglobina, etc.
- Bioquimico: creatinina, ureia, ALT, AST, albumina, etc.
- Imagem: tipo_imagem, laudo, achados, arquivo_url
- Citologia: descricao, classificacao, margem
- Outro: campos livres

Isso justifica o uso do MongoDB: cada tipo de exame tem schema diferente,
e novos tipos podem ser adicionados sem alterar schema do banco.
"""

from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId

from ..mongodb import get_exams_collection
from ..models import User
from ..auth import get_current_user, require_vet

router = APIRouter(prefix="/api/exams", tags=["exams"])


# ─── Schemas ──────────────────────────────────────────

class ExamCreate(BaseModel):
    pet_id: int
    exam_type: str  # hemograma, bioquimico, imagem, citologia, outro
    date: str  # ISO date string
    lab_name: Optional[str] = None
    file_url: Optional[str] = None
    notes: Optional[str] = None
    # Campos dinamicos - variam por tipo de exame
    data: dict = Field(default_factory=dict)


class ExamResponse(BaseModel):
    id: str
    pet_id: int
    exam_type: str
    date: str
    lab_name: Optional[str] = None
    file_url: Optional[str] = None
    notes: Optional[str] = None
    data: dict
    uploaded_by: int
    created_at: str


# ─── Endpoints ────────────────────────────────────────

@router.post("/", response_model=ExamResponse, status_code=201)
async def create_exam(exam: ExamCreate, user: User = Depends(require_vet)):
    """Vet cadastra resultado de exame (MongoDB)."""
    collection = get_exams_collection()

    document = {
        "pet_id": exam.pet_id,
        "exam_type": exam.exam_type,
        "date": exam.date,
        "lab_name": exam.lab_name,
        "file_url": exam.file_url,
        "notes": exam.notes,
        "data": exam.data,
        "uploaded_by": user.id,
        "created_at": datetime.utcnow().isoformat(),
    }

    result = await collection.insert_one(document)
    document["id"] = str(result.inserted_id)
    document["created_at"] = document["created_at"]
    return ExamResponse(**document)


@router.get("/pet/{pet_id}", response_model=List[ExamResponse])
async def list_exams_by_pet(
    pet_id: int,
    exam_type: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """Lista exames de um pet (tutor e vet podem ver)."""
    collection = get_exams_collection()

    query = {"pet_id": pet_id}
    if exam_type:
        query["exam_type"] = exam_type

    exams = []
    async for doc in collection.find(query).sort("date", -1):
        doc["id"] = str(doc.pop("_id"))
        exams.append(ExamResponse(**doc))

    return exams


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: str, user: User = Depends(get_current_user)):
    """Busca um exame especifico pelo ID."""
    collection = get_exams_collection()

    try:
        doc = await collection.find_one({"_id": ObjectId(exam_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalido")

    if not doc:
        raise HTTPException(status_code=404, detail="Exame nao encontrado")

    doc["id"] = str(doc.pop("_id"))
    return ExamResponse(**doc)


@router.delete("/{exam_id}", status_code=204)
async def delete_exam(exam_id: str, user: User = Depends(require_vet)):
    """Vet pode deletar um exame."""
    collection = get_exams_collection()

    try:
        result = await collection.delete_one({"_id": ObjectId(exam_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalido")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Exame nao encontrado")
