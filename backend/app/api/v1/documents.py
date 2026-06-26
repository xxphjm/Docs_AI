from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.util.setting import settings
from backend.app.ingest import Ingest
from backend.app.schemas.document import DocumentUploadResponse


router = APIRouter(prefix="/documents", tags=["documents"])


def _safe_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(default=settings.default_collection_name),
) -> DocumentUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}_{_safe_filename(file.filename)}"
    file_path = settings.upload_dir / saved_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ingest = Ingest(pdf_path=str(file_path), collection_name=collection_name)
    ingest.add_vector_db()

    return DocumentUploadResponse(
        filename=file.filename,
        collection_name=collection_name,
    )

