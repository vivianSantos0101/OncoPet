"""Upload de arquivos (imagens, PDFs, documentos)."""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from ..models import User
from ..auth import get_current_user

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".dicom", ".dcm"}
MAX_SIZE_MB = 20


@router.post("/")
async def upload_file(file: UploadFile = File(...), _: User = Depends(get_current_user)):
    """Recebe um arquivo e salva localmente. Retorna a URL de acesso."""
    # Valida extensao
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extensao nao permitida: {ext}")

    # Le conteudo
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"Arquivo muito grande ({size_mb:.1f}MB). Max: {MAX_SIZE_MB}MB")

    # Gera nome unico
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Salva
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "stored_name": unique_name,
        "url": f"/api/uploads/files/{unique_name}",
        "size_mb": round(size_mb, 2),
        "content_type": file.content_type,
    }


@router.get("/files/{filename}")
async def get_file(filename: str):
    """Serve um arquivo salvo."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(file_path)
