"""
generators.py
=============
SophiaAI — Write side of the file tool.

Mental Model:
    One public function, `render_file(content, fmt) -> RenderedFile`, turns a
    Sophia answer (plain text / markdown) into a downloadable file in the
    requested format. Each format has its own single-responsibility renderer.
    Generation is pure-Python (fpdf2, python-docx) — no system binaries — so it
    runs anywhere the API runs, Windows included.

    Supported out: txt, md, pdf, docx.

Philosophy: ZenCode PRO + CEO of Water — explicit, portable, one job each.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from sophia.files.errors import UnsupportedFileTypeError

# Output format -> the MIME type the browser needs to handle the download.
_MEDIA_TYPE_BY_FORMAT = {
    "txt": "text/plain",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

SUPPORTED_OUTPUT_FORMATS = tuple(_MEDIA_TYPE_BY_FORMAT)


@dataclass(frozen=True)
class RenderedFile:
    """A generated file ready to stream to the client.

    content     — the file bytes.
    media_type  — MIME type for the Content-Type / download.
    extension   — dot-prefixed extension for the download filename.
    """

    content: bytes
    media_type: str
    extension: str


def render_file(content: str, fmt: str) -> RenderedFile:
    """
    Mental Model:
        The single entry point for generating a downloadable file. Validates the
        format, dispatches to the matching renderer, and returns the bytes plus
        the metadata the HTTP layer needs.

    Args:
        content: The text to render (Sophia's answer; may be markdown).
        fmt: One of SUPPORTED_OUTPUT_FORMATS ("txt", "md", "pdf", "docx").

    Returns:
        RenderedFile: bytes + media_type + extension.

    Raises:
        UnsupportedFileTypeError: fmt is not a supported output format.
    """
    fmt = fmt.lower()
    if fmt not in _MEDIA_TYPE_BY_FORMAT:
        raise UnsupportedFileTypeError(
            f"Unsupported output format '{fmt}'. "
            f"Accepted: {', '.join(SUPPORTED_OUTPUT_FORMATS)}."
        )

    if fmt in ("txt", "md"):
        body = content.encode("utf-8")
    elif fmt == "pdf":
        body = _render_pdf(content)
    else:  # docx
        body = _render_docx(content)

    return RenderedFile(
        content=body,
        media_type=_MEDIA_TYPE_BY_FORMAT[fmt],
        extension=f".{fmt}",
    )


def _render_pdf(content: str) -> bytes:
    """Lay the text out as wrapped paragraphs in an A4 PDF via fpdf2."""
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    # Latin-1 is fpdf2's core-font encoding; replace anything outside it so
    # exotic glyphs degrade gracefully instead of raising.
    safe = content.encode("latin-1", errors="replace").decode("latin-1")
    for line in safe.split("\n"):
        # multi_cell with an empty string draws nothing, so feed blank lines a
        # space to preserve paragraph spacing.
        pdf.multi_cell(0, 8, line if line else " ")
    return bytes(pdf.output())


def _render_docx(content: str) -> bytes:
    """Write each line as a paragraph in a .docx via python-docx."""
    import docx

    document = docx.Document()
    for line in content.split("\n"):
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
