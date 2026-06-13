"""
errors.py
=========
SophiaAI — Vision tool error hierarchy.

Mental Model:
    One base exception (`SophiaVisionError`) with two precise subclasses so
    callers can map each failure to the right HTTP status:
        UnsupportedImageTypeError -> 415 Unsupported Media Type
        ImageTooLargeError        -> 413 Payload Too Large
    Library code raises these; it never calls sys.exit (CLAUDE.md convention).
"""

from __future__ import annotations


class SophiaVisionError(Exception):
    """Base for every error escaping the sophia.vision module."""


class UnsupportedImageTypeError(SophiaVisionError):
    """The image mime type is not on the allowlist."""


class ImageTooLargeError(SophiaVisionError):
    """The image exceeds MAX_IMAGE_SIZE_BYTES."""
