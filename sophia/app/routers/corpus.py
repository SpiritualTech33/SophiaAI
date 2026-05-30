"""
Corpus browsing endpoints for SophiaAI (Phase 15).

Executive Brief:
    GET /api/corpus            — List every source document in Sophia's mind.
    GET /api/corpus/{doc_id}   — Get the full markdown of one document.

    Both endpoints require a valid JWT. They read the CorpusLibrary held on
    app.state (built once at startup), never the filesystem directly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from sophia.app.dependencies import get_authenticated_user
from sophia.app.schemas import CorpusDocOut, CorpusDocText
from sophia.db.models import User

router = APIRouter(tags=["corpus"])


@router.get("/api/corpus", response_model=list[CorpusDocOut])
def list_corpus(
    request: Request,
    user: User = Depends(get_authenticated_user),
) -> list[CorpusDocOut]:
    """
    Executive Brief:
        Return metadata for every document, in manifest order. The Mind panel
        groups these by pillar client-side. No document text is sent here —
        the reader fetches that on demand.
    """
    library = request.app.state.corpus
    return [
        CorpusDocOut(
            id=doc.doc_id,
            title=doc.title,
            author=doc.author,
            year=doc.year,
            words=doc.words,
            pillar=doc.pillar,
            path=doc.path,
        )
        for doc in library.list_documents()
    ]


@router.get("/api/corpus/{doc_id}", response_model=CorpusDocText)
def get_corpus_document(
    doc_id: str,
    request: Request,
    user: User = Depends(get_authenticated_user),
) -> CorpusDocText:
    """
    Executive Brief:
        Return the raw markdown of one document plus a little metadata for the
        reader header. Returns 404 if the id is unknown or the file is missing.
    """
    library = request.app.state.corpus

    document = library.get_document(doc_id)
    text = library.get_document_text(doc_id)
    if document is None or text is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return CorpusDocText(
        id=document.doc_id,
        title=document.title,
        author=document.author,
        pillar=document.pillar,
        text=text,
    )
