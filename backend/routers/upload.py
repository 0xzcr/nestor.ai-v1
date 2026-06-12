import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from supabase import create_client

from config import get_settings
from models.query import UploadResponse
from routers.auth import CurrentUser, get_current_user
from services.ingestion import ingest_pdf, persist_upload_to_temp

router = APIRouter(prefix="", tags=["upload"])

PDF_MAGIC = b"%PDF"


def validate_pdf_file(upload_file: UploadFile, file_size: int, max_upload_bytes: int) -> None:
    if upload_file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported.")
    if file_size > max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 20MB limit.")


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    http_request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    raw = await file.read()
    if not raw.startswith(PDF_MAGIC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF file signature.")
    validate_pdf_file(file, len(raw), http_request.app.state.settings.max_upload_bytes)
    await file.seek(0)

    temp_path = await persist_upload_to_temp(file)

    supabase = create_client(
        http_request.app.state.settings.supabase_url,
        http_request.app.state.settings.supabase_service_key,
    )
    remote_path = f"{current_user.id}/{file.filename}"
    try:
        with open(temp_path, "rb") as handle:
            supabase.storage.from_("uploads").upload(remote_path, handle, {"content-type": "application/pdf"})
    except Exception:
        remote_path = ""

    try:
        chunks = await ingest_pdf(
            temp_path,
            current_user.id,
            file.filename or "upload.pdf",
            http_request.app.state.embed_batch,
            http_request.app.state.qdrant_client,
        )
    except ValueError as exc:
        if str(exc) == "SCANNED_PDF":
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This appears to be a scanned PDF. Please upload a text-based PDF for best results.",
            ) from exc
        raise
    finally:
        if remote_path:
            try:
                supabase.storage.from_("uploads").remove([remote_path])
            except Exception:
                pass

    return UploadResponse(
        filename=file.filename or "upload.pdf",
        chunks_indexed=chunks,
        message="PDF processed successfully. Raw file deleted after chunking.",
    )
