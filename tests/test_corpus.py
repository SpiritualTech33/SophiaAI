"""
Unit tests for the CorpusLibrary (Phase 15).

Strategy: exercise the real manifest shipped in the repo. These are fast —
one JSON read, no AI, no network. The traversal guard is tested with a
hand-built manifest pointing outside the corpus root.

Run: pytest tests/test_corpus.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.corpus import CorpusLibrary, DEFAULT_CORPUS_ROOT


def test_lists_every_document():
    """list_documents returns the 137 corpus files with metadata."""
    library = CorpusLibrary()
    docs = library.list_documents()
    assert len(docs) == 137
    first = docs[0]
    assert first.doc_id
    assert first.title
    assert first.pillar in {"mind", "philosophy", "science", "spirit"}


def test_get_document_text_returns_markdown():
    """get_document_text returns the raw markdown for a known id."""
    library = CorpusLibrary()
    some_doc = library.list_documents()[0]
    text = library.get_document_text(some_doc.doc_id)
    assert text is not None
    assert len(text) > 0


def test_unknown_id_returns_none():
    """Unknown ids return None from both metadata and text lookups."""
    library = CorpusLibrary()
    assert library.get_document("not-a-real-sha") is None
    assert library.get_document_text("not-a-real-sha") is None


def test_traversal_guard_blocks_escape(tmp_path):
    """A manifest entry pointing outside the corpus root raises PermissionError."""
    secret = tmp_path / "secret.txt"
    secret.write_text("classified", encoding="utf-8")

    manifest = tmp_path / "corpus_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": "../../../../../../etc/passwd",
                        "pillar": "mind",
                        "filename": "evil.md",
                        "word_count": 1,
                        "sha256": "evil-id",
                        "frontmatter": {"title": "Evil", "author": "X", "date": 2026},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    library = CorpusLibrary(manifest_path=manifest, corpus_root=DEFAULT_CORPUS_ROOT)
    with pytest.raises(PermissionError):
        library.get_document_text("evil-id")


def test_missing_manifest_raises():
    """A nonexistent manifest path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        CorpusLibrary(manifest_path=Path("does/not/exist.json"))
