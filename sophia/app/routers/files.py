"""
File upload and generation endpoints for SophiaAI.

Executive Brief:
    POST /api/files/upload    — Upload a file for Sophia to read. Parses it to
                                text, stores it, returns its id + metadata.
    POST /api/files/generate  — Render text (a Sophia answer) into a downloadable
                                file (txt / md / pdf / docx).

    Both require a valid JWT. The heavy lifting (parsing, rendering) lives in the
    sophia.files tool module; this router is the thin HTTP boundary that maps
    file errors to status codes and enforces per-user ownership on storage.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_authenticated_user, get_db_session
from sophia.app.schemas import FileGenerateRequest, FileUploadOut
from sophia.db.models import User
from sophia.db.service import create_user_file, get_user_file
from sophia.files import (
    FileParseError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    extract_text,
    render_file,
)
from sophia.vision import (
    ImageTooLargeError,
    UnsupportedImageTypeError,
    encode_image_content,
)

logger = logging.getLogger("sophia.app.routers.files")

router = APIRouter(tags=["files"])

# Map each file-tool error to the HTTP status that fits it.
_STATUS_BY_ERROR = {
    UnsupportedFileTypeError: 415,
    FileTooLargeError: 413,
    FileParseError: 422,
}

# Same mapping for the image path (vision tool errors).
_IMAGE_STATUS_BY_ERROR = {
    UnsupportedImageTypeError: 415,
    ImageTooLargeError: 413,
}


def _upload_dir(request: Request) -> Path:
    """Resolve the per-app upload directory, defaulting under the project data dir."""
    configured = getattr(request.app.state, "upload_dir", None)
    base = Path(configured) if configured else Path("data") / "user_uploads"
    return base


@router.post("/api/files/upload", response_model=FileUploadOut, status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> FileUploadOut:
    """
    Executive Brief:
        Read the uploaded bytes, parse them to text (txt/md/pdf/docx), store the
        raw file under a per-user directory with a generated name (never the
        client's filename — path-traversal safe), persist the metadata + cached
        text, and return the new file's id. File-tool errors map to 413/415/422.
    """
    raw = await file.read()
    original_name = file.filename or "upload"
    mime_type = file.content_type or "application/octet-stream"

    if mime_type.startswith("image/"):
        try:
            encode_image_content(raw, mime_type)
        except tuple(_IMAGE_STATUS_BY_ERROR) as error:
            raise HTTPException(status_code=_IMAGE_STATUS_BY_ERROR[type(error)], detail=str(error))
        text = ""
    else:
        try:
            text = extract_text(raw, original_name)
        except tuple(_STATUS_BY_ERROR) as error:
            raise HTTPException(status_code=_STATUS_BY_ERROR[type(error)], detail=str(error))

    extension = Path(original_name).suffix.lower()
    user_dir = _upload_dir(request) / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_path = user_dir / f"{uuid.uuid4().hex}{extension}"
    stored_path.write_bytes(raw)

    record = create_user_file(
        session,
        user_id=user.id,
        conversation_id=None,
        original_filename=original_name,
        stored_path=str(stored_path),
        mime_type=mime_type,
        extracted_text=text,
        size_bytes=len(raw),
    )

    logger.info("User %s uploaded '%s' (%d chars).", user.id, original_name, len(text))
    return FileUploadOut(
        id=record.id,
        filename=original_name,
        mime=record.mime_type,
        chars=len(text),
    )


@router.get("/api/files/{file_id}/raw")
def get_file_raw(
    file_id: int,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> Response:
    """
    Executive Brief:
        Stream a file's raw bytes back, owner-scoped. Used by the frontend to
        display image previews and Sophia-generated images inline. Returns
        404 if the file does not exist or belongs to a different user.
    """
    record = get_user_file(session, file_id, user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")

    data = Path(record.stored_path).read_bytes()
    return Response(content=data, media_type=record.mime_type)


@router.post("/api/files/generate")
def generate_file(
    body: FileGenerateRequest,
    user: User = Depends(get_authenticated_user),
) -> Response:
    """
    Executive Brief:
        Render the given text into the requested format and return it as a
        download (Content-Disposition: attachment). An unsupported format maps
        to 415. Generated files are streamed, not persisted.
    """
    try:
        rendered = render_file(body.content, body.format)
    except UnsupportedFileTypeError as error:
        raise HTTPException(status_code=415, detail=str(error))

    filename = f"sophia{rendered.extension}"
    return Response(
        content=rendered.content,
        media_type=rendered.media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
