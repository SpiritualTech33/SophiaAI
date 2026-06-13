"""
Image generation endpoints for SophiaAI.

Executive Brief:
    POST /api/images/generate — Generate an image from a text prompt and
                                 store it like an uploaded file. Returns its
                                 id, filename, mime type, and a /api/files/
                                 {id}/raw URL the frontend can render.

    Requires a valid JWT. The heavy lifting (calling the image-gen provider)
    lives in the sophia.image_gen tool module; this router is the thin HTTP
    boundary that maps provider errors to status codes and persists the
    result via the same UserFile storage as sophia.app.routers.files.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_authenticated_user, get_db_session
from sophia.app.schemas import ImageGenerateOut, ImageGenerateRequest
from sophia.db.models import User
from sophia.db.service import create_user_file
from sophia.image_gen import ImageGenerationError, generate_image

logger = logging.getLogger("sophia.app.routers.images")

router = APIRouter(tags=["images"])

_GENERATED_MIME_TYPE = "image/jpeg"
_GENERATED_EXTENSION = "jpg"


def _upload_dir(request: Request) -> Path:
    """Resolve the per-app upload directory, defaulting under the project data dir."""
    configured = getattr(request.app.state, "upload_dir", None)
    base = Path(configured) if configured else Path("data") / "user_uploads"
    return base


@router.post("/api/images/generate", response_model=ImageGenerateOut, status_code=201)
def generate_image_endpoint(
    body: ImageGenerateRequest,
    request: Request,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> ImageGenerateOut:
    """
    Executive Brief:
        Generate an image for the given prompt, store it under the user's
        upload directory, and persist its metadata as a UserFile (so it can
        be served via GET /api/files/{id}/raw like any other attachment).
        An empty prompt maps to 422; a provider failure maps to 502.
    """
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt cannot be empty")

    try:
        image_bytes = generate_image(prompt)
    except ImageGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error))

    user_dir = _upload_dir(request) / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_path = user_dir / f"{uuid.uuid4().hex}.{_GENERATED_EXTENSION}"
    stored_path.write_bytes(image_bytes)

    filename = f"{prompt[:40]}.{_GENERATED_EXTENSION}"
    record = create_user_file(
        session,
        user_id=user.id,
        conversation_id=None,
        original_filename=filename,
        stored_path=str(stored_path),
        mime_type=_GENERATED_MIME_TYPE,
        extracted_text="",
        size_bytes=len(image_bytes),
    )

    logger.info("User %s generated image for prompt '%s'.", user.id, prompt)
    return ImageGenerateOut(
        id=record.id,
        filename=filename,
        mime=record.mime_type,
        url=f"/api/files/{record.id}/raw",
    )
