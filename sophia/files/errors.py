"""
errors.py
=========
SophiaAI — File tool error hierarchy.

Mental Model:
    One base exception (`SophiaFileError`) with three precise subclasses so
    callers can map each failure to the right HTTP status:
        UnsupportedFileTypeError -> 415 Unsupported Media Type
        FileTooLargeError        -> 413 Payload Too Large
        FileParseError           -> 422 Unprocessable Entity
    Library code raises these; it never calls sys.exit (CLAUDE.md convention).
"""

from __future__ import annotations


class SophiaFileError(Exception):
    """Base for every error escaping the sophia.files module."""


class UnsupportedFileTypeError(SophiaFileError):
    """The file extension / output format is not on the allowlist."""


class FileTooLargeError(SophiaFileError):
    """The upload exceeds MAX_UPLOAD_BYTES."""


class FileParseError(SophiaFileError):
    """A supported format could not be decoded (corrupt or malformed file)."""
