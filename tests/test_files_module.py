"""
Unit tests for the sophia.files tool module — parsing and generation.

Strategy: pure functions, no HTTP, no DB. We exercise the round-trip
contract: render_file() produces bytes that extract_text() can read back,
plus the validation and error paths.

Run: pytest tests/test_files_module.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.files import (
    MAX_UPLOAD_BYTES,
    FileParseError,
    FileTooLargeError,
    RenderedFile,
    UnsupportedFileTypeError,
    extract_text,
    render_file,
)


# ---------------------------------------------------------------------------
# extract_text — plain text formats
# ---------------------------------------------------------------------------

def test_extract_text_from_txt():
    data = "The Tao that can be told is not the eternal Tao.".encode("utf-8")
    assert extract_text(data, "laozi.txt") == "The Tao that can be told is not the eternal Tao."


def test_extract_text_from_md():
    data = "# Wisdom\n\nBe like water.".encode("utf-8")
    text = extract_text(data, "notes.md")
    assert "Wisdom" in text
    assert "Be like water." in text


def test_extract_text_is_case_insensitive_to_extension():
    data = b"hello"
    assert extract_text(data, "NOTE.TXT") == "hello"


# ---------------------------------------------------------------------------
# extract_text — binary formats (round-trip via render_file)
# ---------------------------------------------------------------------------

def test_extract_text_from_pdf_roundtrip():
    rendered = render_file("Compassion is the highest wisdom.", "pdf")
    text = extract_text(rendered.content, "answer.pdf")
    assert "compassion" in text.lower()
    assert "wisdom" in text.lower()


def test_extract_text_from_docx_roundtrip():
    rendered = render_file("Gratitude opens the heart.", "docx")
    text = extract_text(rendered.content, "answer.docx")
    assert "Gratitude opens the heart." in text


# ---------------------------------------------------------------------------
# extract_text — validation and errors
# ---------------------------------------------------------------------------

def test_extract_text_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError):
        extract_text(b"data", "virus.exe")


def test_extract_text_rejects_oversize_payload():
    too_big = b"x" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(FileTooLargeError):
        extract_text(too_big, "huge.txt")


def test_extract_text_raises_parse_error_on_corrupt_pdf():
    with pytest.raises(FileParseError):
        extract_text(b"this is not a real pdf", "broken.pdf")


def test_extract_text_decodes_invalid_utf8_gracefully():
    # Latin-1 bytes that are not valid UTF-8 must not crash the pipeline.
    data = "café".encode("latin-1")
    text = extract_text(data, "accents.txt")
    assert isinstance(text, str)


# ---------------------------------------------------------------------------
# render_file — every output format
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fmt,media_type",
    [
        ("txt", "text/plain"),
        ("md", "text/markdown"),
        ("pdf", "application/pdf"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ],
)
def test_render_file_returns_rendered_file(fmt, media_type):
    rendered = render_file("Sophia speaks in light.", fmt)
    assert isinstance(rendered, RenderedFile)
    assert isinstance(rendered.content, bytes)
    assert len(rendered.content) > 0
    assert rendered.media_type == media_type
    assert rendered.extension == f".{fmt}"


def test_render_pdf_handles_multiline_content():
    """Multi-line / markdown content must not exhaust the horizontal space.

    Regression: rendering more than one line raised FPDFException because the
    cursor stayed at the right margin after each line.
    """
    body = "# Sophia\n\nWisdom flows like water.\nBe still and know."
    rendered = render_file(body, "pdf")
    assert rendered.content[:4] == b"%PDF"
    text = extract_text(rendered.content, "out.pdf")
    assert "Wisdom flows like water." in text


def test_render_txt_is_exact_content():
    rendered = render_file("plain wisdom", "txt")
    assert rendered.content.decode("utf-8") == "plain wisdom"


def test_render_file_rejects_unknown_format():
    with pytest.raises(UnsupportedFileTypeError):
        render_file("content", "exe")
