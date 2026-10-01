"""Foto do pet: validacao e armazenamento em disco (pasta de uploads)."""

import os
import uuid
from typing import Optional

from ..routers.uploads import UPLOAD_DIR

MAX_PHOTO_MB = 5
PHOTO_URL_PREFIX = "/api/uploads/files/"


def detect_image_type(content: bytes) -> Optional[str]:
    """Descobre o formato pelos primeiros bytes (nao confia na extensao do nome)."""
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def save_photo(content: bytes, ext: str) -> str:
    name = f"pet-{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(content)
    return PHOTO_URL_PREFIX + name


def remove_photo(photo_url: Optional[str]) -> None:
    """Apaga o arquivo antigo, se for uma foto salva por esta API."""
    if not photo_url or not photo_url.startswith(PHOTO_URL_PREFIX):
        return
    name = os.path.basename(photo_url[len(PHOTO_URL_PREFIX):])
    path = os.path.join(UPLOAD_DIR, name)
    if os.path.isfile(path):
        os.remove(path)
