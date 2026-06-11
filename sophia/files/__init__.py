"""
sophia.files
============
The file tool — Sophia's hands for reading uploads and writing downloads.

Two pure functions behind one interface (one-swap-point boundary, CLAUDE.md):
    extract_text(data, filename) -> str          # read uploads
    render_file(content, fmt)    -> RenderedFile  # write downloads

The chat router wires these deterministically today; the future agent loop
calls the very same functions as tools. Nothing else imports the internals.
"""

from __future__ import annotations

from sophia.files.errors import (
    FileParseError,
    FileTooLargeError,
    SophiaFileError,
    UnsupportedFileTypeError,
)
from sophia.files.generators import (
    SUPPORTED_OUTPUT_FORMATS,
    RenderedFile,
    render_file,
)
from sophia.files.parsers import (
    MAX_UPLOAD_BYTES,
    SUPPORTED_INPUT_EXTENSIONS,
    extract_text,
)

__all__ = [
    "extract_text",
    "render_file",
    "RenderedFile",
    "MAX_UPLOAD_BYTES",
    "SUPPORTED_INPUT_EXTENSIONS",
    "SUPPORTED_OUTPUT_FORMATS",
    "SophiaFileError",
    "FileParseError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
]
