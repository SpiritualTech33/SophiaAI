"""
corpus.py
=========
SophiaAI — Phase 15: Corpus Library (read-only browser of Sophia's mind).

Loads ``corpus_manifest.json`` once at startup and exposes the 137 source
documents of ``data/sophia_engine`` to the web layer: a metadata list for the
"Sophia's Mind" panel, and on-demand raw markdown for the document reader.

Mental Model:
    The manifest is the source of truth for *which* files exist and their
    metadata (title, author, year, words, pillar). Each document is addressed
    by its ``source_sha256`` — an opaque, stable id. The web layer never sees
    or sends a filesystem path, so a caller cannot ask for an arbitrary file.
    Even so, ``get_document_text`` re-verifies that the resolved path stays
    inside the corpus root before reading. Two locks on the same door.

Author: Cosmos De La Cruz — SophiaAI Phase 15
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.core.corpus")


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "corpus_manifest.json"
DEFAULT_CORPUS_ROOT = PROJECT_ROOT / "data" / "sophia_engine"


@dataclass
class CorpusDocument:
    """
    Mental Model:
        One source document as the Mind panel needs it. ``doc_id`` is the
        manifest's ``sha256`` — opaque and stable, used by the reader to
        request the full text. ``path`` stays server-side only.

    Args:
        doc_id:  sha256 of the file content. The public, opaque handle.
        title:   Human title from frontmatter, falling back to the filename.
        author:  Frontmatter author, or "Unknown".
        year:    Frontmatter date as an int, or None when absent.
        words:   Word count from the manifest.
        pillar:  One of "mind" | "philosophy" | "science" | "spirit".
        path:    Project-relative path to the markdown file (server-side only).
    """

    doc_id: str
    title: str
    author: str
    year: int | None
    words: int
    pillar: str
    path: str


class CorpusLibrary:
    """
    Mental Model:
        Loads the corpus manifest once and answers two questions:
          - "What does Sophia know?"  -> list_documents()
          - "Show me this text."      -> get_document_text(doc_id)

        Construction is cheap (one JSON read), so it is built at FastAPI
        startup and shared on app.state, mirroring SophiaRetriever.

    Args (constructor):
        manifest_path: Path to corpus_manifest.json. Defaults to
                       data/corpus_manifest.json under the project root.
        corpus_root:   Directory that every document MUST live under.
                       Defaults to data/sophia_engine. Used as the
                       path-traversal boundary.

    Raises (constructor):
        FileNotFoundError: manifest_path does not exist.
        ValueError: manifest is missing the 'entries' key.
    """

    def __init__(
        self,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
        corpus_root: Path = DEFAULT_CORPUS_ROOT,
    ) -> None:
        self._corpus_root = corpus_root.resolve()
        self._documents = self._load_manifest(manifest_path)
        self._by_id = {doc.doc_id: doc for doc in self._documents}

        logger.info(
            f"CorpusLibrary ready. documents={len(self._documents)} | "
            f"root={self._corpus_root}"
        )

    def _load_manifest(self, manifest_path: Path) -> list[CorpusDocument]:
        """
        Mental Model:
            Read the manifest and map each entry to a CorpusDocument. One bad
            entry must never kill the load — log a warning and skip it so the
            panel still shows every healthy document.

        Raises:
            FileNotFoundError: manifest_path missing.
            ValueError: manifest has no 'entries' list.
        """
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"corpus_manifest.json not found: {manifest_path}\n"
                f"Run 'python scripts/build_manifest.py' to regenerate it."
            )

        with manifest_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        if "entries" not in payload:
            raise ValueError(
                f"corpus_manifest.json at {manifest_path} is missing the "
                f"'entries' key. The file is malformed or from an older schema."
            )

        documents: list[CorpusDocument] = []
        for entry in payload["entries"]:
            try:
                frontmatter = entry.get("frontmatter") or {}
                raw_year = frontmatter.get("date")
                documents.append(
                    CorpusDocument(
                        doc_id=entry["sha256"],
                        title=frontmatter.get("title") or entry["filename"],
                        author=frontmatter.get("author") or "Unknown",
                        year=int(raw_year) if isinstance(raw_year, int) else None,
                        words=int(entry.get("word_count", 0)),
                        pillar=entry["pillar"],
                        path=entry["path"],
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                logger.warning(f"Skipping malformed manifest entry: {error}")
                continue

        return documents

    def list_documents(self) -> list[CorpusDocument]:
        """
        Mental Model:
            Every document, in manifest order. The web layer groups them by
            pillar; order within a pillar is the manifest's (alphabetical).
        """
        return list(self._documents)

    def get_document(self, doc_id: str) -> CorpusDocument | None:
        """Return one document's metadata, or None if the id is unknown."""
        return self._by_id.get(doc_id)

    def get_document_text(self, doc_id: str) -> str | None:
        """
        Mental Model:
            Resolve doc_id -> manifest path -> absolute path, then verify the
            absolute path is inside the corpus root before reading. Returns the
            raw markdown, or None if the id is unknown or the file is missing.

        Raises:
            PermissionError: the resolved path escapes the corpus root. This
                should be unreachable (ids map to trusted manifest paths) but
                is enforced as defense in depth.
        """
        document = self._by_id.get(doc_id)
        if document is None:
            return None

        absolute_path = (PROJECT_ROOT / document.path).resolve()

        if not absolute_path.is_relative_to(self._corpus_root):
            raise PermissionError(
                f"Refusing to read '{absolute_path}': outside corpus root "
                f"'{self._corpus_root}'."
            )

        if not absolute_path.exists():
            logger.warning(f"Document file missing on disk: {absolute_path}")
            return None

        return absolute_path.read_text(encoding="utf-8")
