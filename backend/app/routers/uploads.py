from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.core.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"profile_{current_user.id}_{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_PATH / filename
    content = await file.read()
    filepath.write_bytes(content)
    url = f"/uploads/{filename}"
    return {"url": url, "filename": filename}


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    filename = f"file_{current_user.id}_{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_PATH / filename
    content = await file.read()
    filepath.write_bytes(content)
    url = f"/uploads/{filename}"
    return {"url": url, "filename": filename, "original_filename": file.filename}


@router.get("/{filename}")
async def serve_file(filename: str):
    filepath = UPLOAD_PATH / filename
    if not filepath.exists():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)
