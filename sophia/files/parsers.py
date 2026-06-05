"""
parsers.py
==========
SophiaAI — Read side of the file tool.

Mental Model:
    One public function, `extract_text(data, filename) -> str`, turns an
    uploaded file's raw bytes into plain text Sophia can read. Format is chosen
    by the filename extension (the only signal we trust — browser MIME types
    lie). Each format has its own single-responsibility extractor; one bad file
    raises a precise error instead of killing the request.

    Supported in: .txt, .md, .pdf, .docx. Everything else is rejected up front.

Philosophy: ZenCode PRO + CEO of Water — explicit, bulletproof, one job each.
"""

from __future__ import annotations

import io
import logging
import os

from sophia.files.errors import (
    FileParseError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger("sophia.files.parsers")

# 10 MB ceiling — generous for documents, a hard stop against abuse.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# The only extensions we accept for reading. Lower-case, dot-prefixed.
SUPPORTED_INPUT_EXTENSIONS = (".txt", ".md", ".pdf", ".docx")


def extract_text(data: bytes, filename: str) -> str:
    """
    Mental Model:
        The single entry point for reading an uploaded file. Validates size and
        type, dispatches to the matching extractor, and returns plain text.

    Args:
        data: Raw file bytes.
        filename: Original name — used only to read the extension.

    Returns:
        str: The file's text content.

    Raises:
        FileTooLargeError: data exceeds MAX_UPLOAD_BYTES.
        UnsupportedFileTypeError: extension is not on the allowlist.
        FileParseError: a supported format could not be decoded.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
        )

    extension = os.path.splitext(filename)[1].lower()

    if extension in (".txt", ".md"):
        return _extract_plain_text(data)
    if extension == ".pdf":
        return _extract_pdf(data)
    if extension == ".docx":
        return _extract_docx(data)

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{extension or filename}'. "
        f"Accepted: {', '.join(SUPPORTED_INPUT_EXTENSIONS)}."
    )


def _extract_plain_text(data: bytes) -> str:
    """Decode UTF-8, falling back to Latin-1 so odd encodings never crash."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed; falling back to latin-1.")
        return data.decode("latin-1", errors="replace")


def _extract_pdf(data: bytes) -> str:
    """Extract text from every page of a PDF via pypdf."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()
    except Exception as error:  # noqa: BLE001 — any pypdf failure is a parse error
        raise FileParseError(f"Could not read PDF: {error}") from error


def _extract_docx(data: bytes) -> str:
    """Extract text from every paragraph of a .docx via python-docx."""
    try:
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip()
    except Exception as error:  # noqa: BLE001 — any docx failure is a parse error
        raise FileParseError(f"Could not read DOCX: {error}") from error
