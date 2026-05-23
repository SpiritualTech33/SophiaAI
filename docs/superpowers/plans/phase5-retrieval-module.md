# Phase 5 — Retrieval Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable `SophiaRetriever` class that loads the FAISS index, the SentenceTransformer model, and `chunks_index.json` once at startup, then exposes `retrieve(query, top_k)` returning a ranked list of `Chunk` dataclasses with text + provenance + cosine score. This is the first piece of real application code under the new `sophia/` package — everything before was scripts and data.

**Architecture:** A new Python package `sophia/rag/` containing `retriever.py` (class lives here) and `__init__.py` (public exports). The class holds three pieces of state instantiated once: the FAISS `IndexFlatIP`, the `SentenceTransformer` model (must match Phase 3 — `all-MiniLM-L6-v2`, 384 dims), and the in-memory list of chunk dicts from `chunks_index.json`. The list index in that JSON IS the FAISS internal id, so order is preserved at all times. The `retrieve` method embeds the query, L2-normalizes it (so inner product = cosine), runs `index.search`, and maps integer ids back to `Chunk` instances. Single-responsibility methods, dataclasses with Mental Model docstrings, try/except with logger + raise on init failures (this is library code now — no `sys.exit`).

**Tech Stack:** `faiss-cpu` (1.13.2), `numpy` (2.4.6), `sentence-transformers` (5.5.1), `pytest` for tests. No new dependencies.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `sophia/__init__.py` | Create | Top-level package marker |
| `sophia/rag/__init__.py` | Create | Public exports: `SophiaRetriever`, `Chunk` |
| `sophia/rag/retriever.py` | Create | `Chunk` dataclass + `SophiaRetriever` class |
| `tests/test_sophia_retriever.py` | Create | Unit tests with mocked FAISS index + model |

---

## Branch Setup

- [ ] **Step 0: Create feature branch**

```powershell
SophiaAI-venv\Scripts\Activate.ps1
git checkout -b feat/phase5-retriever
```

Activates the venv and creates the feature branch for Phase 5 work. All commits in this plan land on `feat/phase5-retriever`; merge to `master` after final verification.

---

## Task 1: Write the failing tests

**Files:**
- Create: `tests/test_sophia_retriever.py`

- [ ] **Step 1: Write the test file**

```python
# tests/test_sophia_retriever.py
"""
Unit tests for sophia.rag.retriever.

Strategy: mock faiss.read_index and SentenceTransformer so tests run
in milliseconds without downloading the real model or reading the real
2 MB index. Real-data smoke test is in the verification task, not here.

Run: pytest tests/test_sophia_retriever.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Make the project root importable so `sophia.rag` resolves as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.rag import Chunk, SophiaRetriever


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _make_fake_chunks_file(tmp_path: Path, n_chunks: int = 5) -> Path:
    """Write a minimal chunks_index.json with n_chunks rag_chunks."""
    chunks = [
        {
            "chunk_id": f"abc_rag_{i:04d}",
            "source_sha256": "0" * 64,
            "source_path": f"data/sophia_engine/mind/file_{i}.md",
            "pillar": "mind",
            "chunk_index": i,
            "token_count": 384,
            "text": f"Sample wisdom text number {i}.",
        }
        for i in range(n_chunks)
    ]
    payload = {
        "schema_version": "1.0",
        "model": "all-MiniLM-L6-v2",
        "rag_chunks": chunks,
        "pretrain_chunks": [],
    }
    path = tmp_path / "chunks_index.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _make_fake_index_file(tmp_path: Path) -> Path:
    """Create an empty file so existence checks pass; we mock faiss.read_index."""
    path = tmp_path / "sophia_index.faiss"
    path.write_bytes(b"")
    return path


def _patch_dependencies(index_dim: int = 384, model_dim: int = 384, ntotal: int = 5):
    """
    Returns a context manager that patches faiss.read_index and
    SentenceTransformer. The fake index has the given dim and ntotal.
    The fake model reports the given dim via get_sentence_embedding_dimension.
    """
    fake_index = MagicMock()
    fake_index.d = index_dim
    fake_index.ntotal = ntotal

    fake_model = MagicMock()
    fake_model.get_sentence_embedding_dimension.return_value = model_dim
    fake_model.encode.return_value = np.ones((1, model_dim), dtype=np.float32)

    return fake_index, fake_model


# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------

def test_chunk_dataclass_has_required_fields():
    """Chunk exposes text, source_file, pillar, chunk_id, score."""
    chunk = Chunk(
        text="Sample text",
        source_file="mind/file.md",
        pillar="mind",
        chunk_id="abc_rag_0000",
        score=0.91,
    )
    assert chunk.text == "Sample text"
    assert chunk.source_file == "mind/file.md"
    assert chunk.pillar == "mind"
    assert chunk.chunk_id == "abc_rag_0000"
    assert chunk.score == pytest.approx(0.91)


# ---------------------------------------------------------------------------
# SophiaRetriever.__init__
# ---------------------------------------------------------------------------

def test_retriever_loads_index_and_chunks(tmp_path):
    """Init succeeds when index + chunks file + model dims agree."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(
            index_path=index_path,
            chunks_path=chunks_path,
            model_name="sentence-transformers/all-MiniLM-L6-v2",
        )

    assert retriever is not None


def test_retriever_raises_if_index_missing(tmp_path):
    """Missing FAISS index file → FileNotFoundError with clear message."""
    chunks_path = _make_fake_chunks_file(tmp_path)
    missing_index = tmp_path / "does_not_exist.faiss"

    with pytest.raises(FileNotFoundError, match="FAISS index"):
        SophiaRetriever(index_path=missing_index, chunks_path=chunks_path)


def test_retriever_raises_if_chunks_missing(tmp_path):
    """Missing chunks_index.json → FileNotFoundError with clear message."""
    index_path = _make_fake_index_file(tmp_path)
    missing_chunks = tmp_path / "does_not_exist.json"
    fake_index, fake_model = _patch_dependencies()

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        with pytest.raises(FileNotFoundError, match="chunks"):
            SophiaRetriever(index_path=index_path, chunks_path=missing_chunks)


def test_retriever_raises_if_dim_mismatch(tmp_path):
    """index.d != model dim → ValueError pointing to Phase 3+4 rebuild."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=768, ntotal=5)

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        with pytest.raises(ValueError, match="dimension"):
            SophiaRetriever(index_path=index_path, chunks_path=chunks_path)


def test_retriever_raises_if_count_mismatch(tmp_path):
    """index.ntotal != len(rag_chunks) → ValueError with clear message."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=99)

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        with pytest.raises(ValueError, match="ntotal"):
            SophiaRetriever(index_path=index_path, chunks_path=chunks_path)


# ---------------------------------------------------------------------------
# SophiaRetriever.retrieve
# ---------------------------------------------------------------------------

def test_retrieve_returns_top_k_chunks_in_order(tmp_path):
    """search returns scores [0.9, 0.7, 0.5] → 3 Chunks in that order."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)
    fake_index.search.return_value = (
        np.array([[0.9, 0.7, 0.5]], dtype=np.float32),
        np.array([[2, 0, 4]], dtype=np.int64),
    )

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        results = retriever.retrieve("What is wisdom?", top_k=3)

    assert len(results) == 3
    assert [c.score for c in results] == pytest.approx([0.9, 0.7, 0.5])
    assert results[0].chunk_id == "abc_rag_0002"
    assert results[1].chunk_id == "abc_rag_0000"
    assert results[2].chunk_id == "abc_rag_0004"
    assert all(isinstance(c, Chunk) for c in results)


def test_retrieve_normalizes_query_vector(tmp_path):
    """faiss.normalize_L2 is called on the query exactly once."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)
    fake_index.search.return_value = (
        np.array([[0.9]], dtype=np.float32),
        np.array([[0]], dtype=np.int64),
    )

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model), \
         patch("sophia.rag.retriever.faiss.normalize_L2") as mock_normalize:
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        retriever.retrieve("What is wisdom?", top_k=1)

    assert mock_normalize.call_count == 1


def test_retrieve_filters_invalid_ids(tmp_path):
    """FAISS returns -1 for padding when top_k > ntotal — those are dropped."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)
    fake_index.search.return_value = (
        np.array([[0.9, 0.5, -1.0, -1.0]], dtype=np.float32),
        np.array([[1, 3, -1, -1]], dtype=np.int64),
    )

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        results = retriever.retrieve("anything", top_k=4)

    assert len(results) == 2
    assert results[0].chunk_id == "abc_rag_0001"
    assert results[1].chunk_id == "abc_rag_0003"


def test_retrieve_empty_query_returns_empty_list(tmp_path):
    """Empty / whitespace-only query → [] without touching the index."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        results = retriever.retrieve("   ", top_k=5)

    assert results == []
    fake_index.search.assert_not_called()


def test_retrieve_invalid_top_k_raises(tmp_path):
    """top_k <= 0 → ValueError. Public API contract — fail loud."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=5)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=5)

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        with pytest.raises(ValueError, match="top_k"):
            retriever.retrieve("wisdom", top_k=0)


def test_retrieve_maps_source_path_to_source_file(tmp_path):
    """chunks JSON key `source_path` is exposed on Chunk as `source_file`."""
    chunks_path = _make_fake_chunks_file(tmp_path, n_chunks=3)
    index_path = _make_fake_index_file(tmp_path)
    fake_index, fake_model = _patch_dependencies(index_dim=384, model_dim=384, ntotal=3)
    fake_index.search.return_value = (
        np.array([[0.8]], dtype=np.float32),
        np.array([[1]], dtype=np.int64),
    )

    with patch("sophia.rag.retriever.faiss.read_index", return_value=fake_index), \
         patch("sophia.rag.retriever.SentenceTransformer", return_value=fake_model):
        retriever = SophiaRetriever(index_path=index_path, chunks_path=chunks_path)
        results = retriever.retrieve("anything", top_k=1)

    assert results[0].source_file == "data/sophia_engine/mind/file_1.md"
    assert results[0].pillar == "mind"
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
pytest tests/test_sophia_retriever.py -v
```

Expected output: `ModuleNotFoundError: No module named 'sophia'`. Correct — the package does not exist yet. We will create it in Task 2.

---

## Task 2: Implement the `sophia/rag/` package

**Files:**
- Create: `sophia/__init__.py`
- Create: `sophia/rag/__init__.py`
- Create: `sophia/rag/retriever.py`

- [ ] **Step 3: Create the top-level package marker**

```python
# sophia/__init__.py
"""
SophiaAI — application package.

This is the root namespace for all real application code. Anything under
`sophia/` is library code that the FastAPI app, the CLI, and the tests import.
Scripts under `scripts/` are one-shot pipeline builders and should not be
imported from here.

Author: Cosmos De La Cruz
"""
```

A two-line package marker — nothing more is needed at the root yet. Sub-packages (`rag`, `llm`, `tools`, `core`, `db`, `auth`, `app`) will be created in later phases.

- [ ] **Step 4: Create the rag sub-package init**

```python
# sophia/rag/__init__.py
"""
SophiaAI — Retrieval-Augmented Generation package.

Public API:
    SophiaRetriever — loads FAISS index + embedding model + chunk metadata
                      once at startup and exposes .retrieve(query, top_k).
    Chunk          — dataclass describing a single retrieval result
                      (text + source file + pillar + chunk_id + score).

Anything else inside this package is implementation detail and may change.

Author: Cosmos De La Cruz — SophiaAI Phase 5
"""

from sophia.rag.retriever import Chunk, SophiaRetriever

__all__ = ["Chunk", "SophiaRetriever"]
```

This is the file that consumers import from: `from sophia.rag import SophiaRetriever, Chunk`. Internal modules stay hidden.

- [ ] **Step 5: Write the retriever module**

```python
# sophia/rag/retriever.py
"""
retriever.py
============
SophiaAI — Phase 5: Retrieval Module.

Loads the FAISS index (built in Phase 4), the SentenceTransformer model
(must match Phase 3 — all-MiniLM-L6-v2, 384 dims), and the chunk metadata
(chunks_index.json from Phase 2) once at startup. Exposes a single public
method `retrieve(query, top_k)` that returns the top-k most semantically
similar passages as Chunk dataclasses.

Mental Model:
    The list index in chunks_index.json['rag_chunks'] IS the FAISS internal id.
    Never sort, filter, or reorder the chunks list at load time — the 1:1
    mapping with the index must be preserved. If you mutate the order, the
    retriever will silently return the wrong passages.

Usage:
    from sophia.rag import SophiaRetriever
    retriever = SophiaRetriever()
    results = retriever.retrieve("What is wisdom?", top_k=5)
    for c in results:
        print(f"{c.score:.3f} | {c.pillar} | {c.source_file}")
        print(c.text[:200])

Author: Cosmos De La Cruz — SophiaAI Phase 5
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.rag.retriever")


# ---------------------------------------------------------------------------
# Project root + defaults
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_INDEX_PATH = PROJECT_ROOT / "data" / "sophia_index.faiss"
DEFAULT_CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks_index.json"
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """
    Mental Model:
        One retrieval result. Everything Sophia needs to inject a passage
        into an LLM prompt and cite the source it came from.

    Args:
        text:        The raw chunk text (~384 tokens).
        source_file: Relative path to the originating markdown file
                     (e.g. "data/sophia_engine/mind/jung_archetypes.md").
        pillar:      One of "mind" | "philosophy" | "science" | "spirit".
        chunk_id:    Stable id assigned at chunking time
                     (e.g. "c933081f_rag_0000").
        score:       Cosine similarity in [-1, 1]. Higher is closer.
                     With normalized vectors this equals the FAISS
                     inner-product score.
    """

    text: str
    source_file: str
    pillar: str
    chunk_id: str
    score: float


# ---------------------------------------------------------------------------
# Internal loaders
# ---------------------------------------------------------------------------

def _load_faiss_index(index_path: Path) -> faiss.Index:
    """
    Mental Model:
        Reads the binary FAISS index from disk and returns it. Raises a
        clear FileNotFoundError pointing the user at the rebuild script
        if the file is missing — common after a fresh git clone because
        the .faiss file is gitignored.

    Args:
        index_path: Absolute path to sophia_index.faiss.

    Returns:
        faiss.Index: Loaded index ready for .search().

    Raises:
        FileNotFoundError: index_path does not exist.
    """
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {index_path}\n"
            f"Run 'python scripts/build_faiss_index.py' to regenerate it."
        )
    logger.info(f"Loading FAISS index from {index_path} ...")
    return faiss.read_index(str(index_path))


def _load_chunks(chunks_path: Path) -> list[dict]:
    """
    Mental Model:
        Reads chunks_index.json and returns the rag_chunks list verbatim.
        The list order is the FAISS id ordering — DO NOT sort or filter.

    Args:
        chunks_path: Absolute path to chunks_index.json.

    Returns:
        list[dict]: Chunk dicts in their original order.

    Raises:
        FileNotFoundError: chunks_path does not exist.
        ValueError: JSON missing the 'rag_chunks' key.
    """
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"chunks_index.json not found: {chunks_path}\n"
            f"Run 'python scripts/build_chunks.py' to regenerate it."
        )

    with chunks_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if "rag_chunks" not in payload:
        raise ValueError(
            f"chunks_index.json at {chunks_path} is missing the "
            f"'rag_chunks' key. The file is malformed or from an older "
            f"schema — rebuild with scripts/build_chunks.py."
        )

    return payload["rag_chunks"]


def _load_embedding_model(model_name: str) -> SentenceTransformer:
    """
    Mental Model:
        Instantiates the SentenceTransformer. First call downloads the
        model weights into the local HuggingFace cache; subsequent calls
        load from cache (~1-2 seconds on CPU).

    Args:
        model_name: HuggingFace model id
                    (e.g. "sentence-transformers/all-MiniLM-L6-v2").

    Returns:
        SentenceTransformer: Ready to call .encode().
    """
    logger.info(f"Loading SentenceTransformer model '{model_name}' ...")
    return SentenceTransformer(model_name)


def _model_embedding_dimension(model: SentenceTransformer) -> int:
    """
    Mental Model:
        Reports the model's output vector dimension. The sentence-transformers
        API renamed get_sentence_embedding_dimension to get_embedding_dimension
        in newer versions — try both so the code survives the upgrade.

    Args:
        model: A loaded SentenceTransformer.

    Returns:
        int: Embedding dimension (384 for all-MiniLM-L6-v2).
    """
    if hasattr(model, "get_sentence_embedding_dimension"):
        return int(model.get_sentence_embedding_dimension())
    return int(model.get_embedding_dimension())


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class SophiaRetriever:
    """
    Mental Model:
        The bridge between a plain-English question and the corpus.
        Holds three pieces of state instantiated ONCE at startup:
          - FAISS index   (~2 MB, milliseconds to load)
          - Chunks list   (~few MB of JSON in memory)
          - Embedding model (~90 MB, ~2 seconds to load on CPU)

        Each call to retrieve() embeds the query, L2-normalizes it (so
        inner product becomes cosine similarity), runs index.search(),
        and maps the integer ids back to Chunk dataclasses.

        Why a class and not a function: the three loads above are
        expensive. You pay them once when the FastAPI app boots, not
        once per user message.

    Args (constructor):
        index_path:  Path to sophia_index.faiss. Defaults to
                     data/sophia_index.faiss under the project root.
        chunks_path: Path to chunks_index.json. Defaults to
                     data/chunks_index.json under the project root.
        model_name:  HuggingFace model id. Must match the model used
                     to build Phase 3 embeddings. Defaults to
                     sentence-transformers/all-MiniLM-L6-v2.

    Raises (constructor):
        FileNotFoundError: index or chunks file missing.
        ValueError: dimension mismatch between index and model, OR
                    count mismatch between index.ntotal and len(rag_chunks).
    """

    def __init__(
        self,
        index_path: Path = DEFAULT_INDEX_PATH,
        chunks_path: Path = DEFAULT_CHUNKS_PATH,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self._index = _load_faiss_index(index_path)
        self._chunks = _load_chunks(chunks_path)
        self._model = _load_embedding_model(model_name)

        self._verify_consistency()

        logger.info(
            f"SophiaRetriever ready. "
            f"ntotal={self._index.ntotal} | d={self._index.d} | "
            f"chunks={len(self._chunks)} | model={model_name}"
        )

    def _verify_consistency(self) -> None:
        """
        Mental Model:
            Fail loud at startup if Phase 3, Phase 4, and Phase 2 outputs
            are out of sync. A silent mismatch here would produce wrong
            retrievals later that look correct on the surface.

        Raises:
            ValueError: model dim != index dim, OR ntotal != len(chunks).
        """
        model_dim = _model_embedding_dimension(self._model)
        if self._index.d != model_dim:
            raise ValueError(
                f"FAISS index dimension ({self._index.d}) does not match "
                f"the embedding model dimension ({model_dim}). "
                f"Rebuild Phase 3 (build_embeddings.py) and Phase 4 "
                f"(build_faiss_index.py) with the same model."
            )

        if self._index.ntotal != len(self._chunks):
            raise ValueError(
                f"FAISS index ntotal ({self._index.ntotal}) does not match "
                f"the number of rag_chunks in chunks_index.json "
                f"({len(self._chunks)}). The two are out of sync. "
                f"Rebuild Phase 4 from the current Phase 2 + Phase 3 outputs."
            )

    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        """
        Mental Model:
            Embed the query → normalize → FAISS search → map ids to Chunks.

        Args:
            query: User's plain-English question.
            top_k: Maximum number of chunks to return. Must be > 0.
                   If top_k > index.ntotal, FAISS will pad with -1 ids
                   which are filtered out here.

        Returns:
            list[Chunk]: Up to top_k Chunks, highest score first. Empty
                         list if the query is empty / whitespace-only.

        Raises:
            ValueError: top_k <= 0.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}.")

        if not query or not query.strip():
            return []

        query_vector = self._model.encode([query], convert_to_numpy=True)
        query_vector = np.asarray(query_vector, dtype=np.float32)
        faiss.normalize_L2(query_vector)

        scores, ids = self._index.search(query_vector, top_k)

        results: list[Chunk] = []
        for score, chunk_id in zip(scores[0], ids[0]):
            if int(chunk_id) < 0:
                continue
            chunk_dict = self._chunks[int(chunk_id)]
            results.append(
                Chunk(
                    text=chunk_dict["text"],
                    source_file=chunk_dict["source_path"],
                    pillar=chunk_dict["pillar"],
                    chunk_id=chunk_dict["chunk_id"],
                    score=float(score),
                )
            )
        return results
```

- [ ] **Step 6: Run tests to verify they pass**

```powershell
pytest tests/test_sophia_retriever.py -v
```

Expected output:
```
tests/test_sophia_retriever.py::test_chunk_dataclass_has_required_fields PASSED
tests/test_sophia_retriever.py::test_retriever_loads_index_and_chunks PASSED
tests/test_sophia_retriever.py::test_retriever_raises_if_index_missing PASSED
tests/test_sophia_retriever.py::test_retriever_raises_if_chunks_missing PASSED
tests/test_sophia_retriever.py::test_retriever_raises_if_dim_mismatch PASSED
tests/test_sophia_retriever.py::test_retriever_raises_if_count_mismatch PASSED
tests/test_sophia_retriever.py::test_retrieve_returns_top_k_chunks_in_order PASSED
tests/test_sophia_retriever.py::test_retrieve_normalizes_query_vector PASSED
tests/test_sophia_retriever.py::test_retrieve_filters_invalid_ids PASSED
tests/test_sophia_retriever.py::test_retrieve_empty_query_returns_empty_list PASSED
tests/test_sophia_retriever.py::test_retrieve_invalid_top_k_raises PASSED
tests/test_sophia_retriever.py::test_retrieve_maps_source_path_to_source_file PASSED

12 passed in X.XXs
```

- [ ] **Step 7: Commit package + tests**

```powershell
git add sophia/__init__.py sophia/rag/__init__.py sophia/rag/retriever.py tests/test_sophia_retriever.py docs/superpowers/plans/phase5-retrieval-module.md
git commit -m "feat(phase5): add SophiaRetriever class with unit tests"
```

Stages the new package, tests, and plan into one atomic commit so the history shows TDD as a single step.

---

## Task 3: Real-data smoke test

Verify that the retriever produces sensible results against the real FAISS index and the real model. Mocked tests prove the wiring; this proves the math.

- [ ] **Step 8: Confirm Phase 4 artifacts exist**

```powershell
python -c "import faiss; idx = faiss.read_index('data/sophia_index.faiss'); print('ntotal:', idx.ntotal, '| d:', idx.d, '| type:', type(idx).__name__)"
```

Expected:
```
ntotal: 1422 | d: 384 | type: IndexFlatIP
```

If the file is missing (gitignored), run `python scripts/build_embeddings.py` then `python scripts/build_faiss_index.py`.

- [ ] **Step 9: Run the smoke-test inline**

```powershell
python -c "from sophia.rag import SophiaRetriever; r = SophiaRetriever(); res = r.retrieve('What is wisdom?', top_k=5); [print(f'{c.score:.3f} | {c.pillar:10s} | {c.source_file}') for c in res]"
```

Expected: five lines, scores in descending order between roughly 0.5 and 0.8, mostly from `philosophy/` and `spirit/` pillars. The Phase 4 baseline scores were `[0.78, 0.73, 0.71, 0.61, 0.58]` — Phase 5 must reproduce these numbers because the underlying math is identical. A divergence beyond `~0.01` is a bug; investigate before committing.

- [ ] **Step 10: Add a sanity assertion test (optional but recommended)**

If the smoke test passes, append the following to `tests/test_sophia_retriever.py` so the real-data behavior is locked in:

```python
# ---------------------------------------------------------------------------
# Real-data integration test (skips if Phase 4 artifacts are missing)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_REAL_INDEX = _PROJECT_ROOT / "data" / "sophia_index.faiss"
_REAL_CHUNKS = _PROJECT_ROOT / "data" / "chunks_index.json"


@pytest.mark.skipif(
    not _REAL_INDEX.exists() or not _REAL_CHUNKS.exists(),
    reason="Phase 4 artifacts not built locally; skipping integration test.",
)
def test_retrieve_against_real_corpus_returns_top_k_chunks():
    """End-to-end: real FAISS index + real model + real chunks → 5 results."""
    retriever = SophiaRetriever()
    results = retriever.retrieve("What is wisdom?", top_k=5)

    assert len(results) == 5
    assert all(isinstance(c, Chunk) for c in results)
    assert all(c.pillar in {"mind", "philosophy", "science", "spirit"} for c in results)
    # Scores should be sorted descending.
    assert list(c.score for c in results) == sorted(
        (c.score for c in results), reverse=True
    )
    # Top score on this query is empirically > 0.4 on the curated corpus.
    assert results[0].score > 0.4
```

Then re-run:

```powershell
pytest tests/test_sophia_retriever.py -v
```

Expected: 13 passed (or 12 passed + 1 skipped if the index file is absent on CI).

- [ ] **Step 11: Update cosmos_log.md**

Append to `cosmos_log.md`:

```markdown
## Phase 5 — Retrieval Module
**Date:** 2026-05-23

**What was built:** Package `sophia/rag/` with class `SophiaRetriever` and
dataclass `Chunk`. The class loads the FAISS index, the SentenceTransformer
model, and `chunks_index.json` once at startup. The `retrieve(query, top_k)`
method embeds the query, normalizes it to unit length, searches the index,
and returns a ranked list of Chunk dataclasses with text, source file,
pillar, chunk_id, and cosine score.

**Artifacts:**
- `sophia/__init__.py` — top-level package marker
- `sophia/rag/__init__.py` — public exports: SophiaRetriever, Chunk
- `sophia/rag/retriever.py` — class + dataclass + private loaders
- `tests/test_sophia_retriever.py` — 12 mocked unit tests + 1 real-corpus integration test

**Why a class:** loading FAISS + the embedding model is a one-time cost
(~2 seconds on CPU). A class with state pays that cost once at app boot,
not once per user message. Stateless functions would re-load on every call.

**Why a separate dataclass:** `Chunk` is the contract between the retrieval
layer and the orchestrator (Phase 8). Returning dicts would force every
consumer to remember the key names. A dataclass with explicit fields gives
the rest of the app type safety and IDE autocompletion.

**Next step:** Phase 6 — `sophia/llm/groq_client.py` with class GroqClient.
Reads GROQ_API_KEY from .env, exposes chat(messages, model), wraps Groq
exceptions in a custom SophiaLLMError.
```

- [ ] **Step 12: Final commit**

```powershell
git add cosmos_log.md tests/test_sophia_retriever.py
git commit -m "feat(phase5): SophiaRetriever verified against real corpus"
```

Stages the dev-log entry and the integration test into one commit that marks Phase 5 done.

- [ ] **Step 13: Merge to master**

```powershell
git checkout master
git merge --no-ff feat/phase5-retriever -m "merge: Phase 5 — Retrieval Module"
```

Switches to master and merges the feature branch with a merge commit so the phase boundary is visible in `git log --graph`. After this, Phase 6 starts from master.

---

## Self-Review

**Spec coverage (from `developing_plan.md` Phase 5 + `MEMORY.md` Phase 5 spec):**
- ✅ Package `sophia/rag/` with `retriever.py` + `__init__.py` — Steps 3, 4, 5
- ✅ `SophiaRetriever.__init__` loads FAISS index, embedding model, chunks_index.json — `__init__`
- ✅ `retrieve(query, top_k=5) -> list[Chunk]` — `retrieve()`
- ✅ Embeds query → normalizes → searches → returns ranked Chunks — `retrieve()`
- ✅ `Chunk` dataclass with text, source_file, pillar, chunk_id, score — `Chunk`
- ✅ Order preservation (chunks list index == FAISS id) — `_load_chunks` does not sort
- ✅ Dimension consistency check at startup — `_verify_consistency`
- ✅ ntotal vs len(chunks) consistency check at startup — `_verify_consistency`
- ✅ FutureWarning handling for `get_sentence_embedding_dimension` — `_model_embedding_dimension`
- ✅ Empty query → empty list contract — `retrieve()`
- ✅ Invalid top_k → ValueError contract — `retrieve()`
- ✅ Padded -1 ids filtered out — `retrieve()`
- ✅ Library code raises instead of `sys.exit` — every loader
- ✅ ZenCode PRO docstrings with "Mental Model" sections — every public symbol
- ✅ Branch `feat/phase5-retriever` → merge to `master` — Steps 0 and 13

**Test coverage matrix:**

| Behavior | Test |
|---|---|
| Chunk dataclass fields | `test_chunk_dataclass_has_required_fields` |
| Happy-path init | `test_retriever_loads_index_and_chunks` |
| Missing index file | `test_retriever_raises_if_index_missing` |
| Missing chunks file | `test_retriever_raises_if_chunks_missing` |
| Dim mismatch | `test_retriever_raises_if_dim_mismatch` |
| Count mismatch | `test_retriever_raises_if_count_mismatch` |
| Top-k ordering | `test_retrieve_returns_top_k_chunks_in_order` |
| Query normalization | `test_retrieve_normalizes_query_vector` |
| -1 id filtering | `test_retrieve_filters_invalid_ids` |
| Empty query | `test_retrieve_empty_query_returns_empty_list` |
| Invalid top_k | `test_retrieve_invalid_top_k_raises` |
| source_path → source_file mapping | `test_retrieve_maps_source_path_to_source_file` |
| End-to-end against real corpus | `test_retrieve_against_real_corpus_returns_top_k_chunks` |

**Placeholder scan:** No TBD, TODO, or vague steps. All code, commands, and expected output shown literally.

**Type consistency:**
- `Chunk(text: str, source_file: str, pillar: str, chunk_id: str, score: float)` — matches every test instantiation.
- `SophiaRetriever.__init__(index_path: Path, chunks_path: Path, model_name: str) -> None` — matches every test call.
- `SophiaRetriever.retrieve(query: str, top_k: int = 5) -> list[Chunk]` — matches every test call.
- `_load_faiss_index(Path) -> faiss.Index`, `_load_chunks(Path) -> list[dict]`, `_load_embedding_model(str) -> SentenceTransformer` — internal, signatures self-consistent with caller in `__init__`.

**What Phase 5 unlocks:**
- Phase 8 (Orchestrator) imports `from sophia.rag import SophiaRetriever` and calls `retriever.retrieve(query)` to populate the LLM prompt.
- The `sophia/` package now exists — Phases 6, 7, 9, 10, 11 will each add sub-packages following the same `__init__.py` + module layout.
- A working RAG pipeline (corpus → chunks → embeddings → FAISS → retriever) is now end-to-end queryable from Python, even before the LLM and web layers exist.
