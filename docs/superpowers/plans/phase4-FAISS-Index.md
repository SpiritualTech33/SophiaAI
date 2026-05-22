# Phase 4 — FAISS Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load `data/embeddings.npy` (1422 × 384 float32 matrix), normalize each vector to unit length, build a `faiss.IndexFlatIP` over the matrix, and write the index to `data/sophia_index.faiss` plus a sidecar `data/faiss_index_meta.json`.

**Architecture:** A single standalone script (`scripts/build_faiss_index.py`) that mirrors the conventions of `scripts/build_embeddings.py`. Loads the matrix, normalizes in place via `faiss.normalize_L2`, builds an exact inner-product index (cosine similarity on unit vectors), and writes both binary index and JSON sidecar. Single-responsibility functions, dataclass for meta, argparse CLI, try/except with logger + sys.exit on failure, ZenCode PRO docstrings.

**Tech Stack:** `faiss-cpu` (1.13.2), `numpy` (2.4.6), `argparse`, `pytest`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `scripts/build_faiss_index.py` | Create | Full FAISS index build pipeline |
| `tests/test_build_faiss_index.py` | Create | Unit tests for helper functions |
| `data/sophia_index.faiss` | Produced by script | Binary FAISS IndexFlatIP file |
| `data/faiss_index_meta.json` | Produced by script | index_type, dimension, total_vectors, generated_at, embeddings_source |

---

## Branch Setup

- [ ] **Step 0: Create feature branch**

```powershell
SophiaAI-venv\Scripts\Activate.ps1
git checkout -b feat/phase4-faiss
```

Creates and switches to the feature branch for Phase 4 work. All commits in this plan land on `feat/phase4-faiss`; merge to `master` after final verification.

---

## Task 1: Write the failing tests

**Files:**
- Create: `tests/test_build_faiss_index.py`

- [ ] **Step 1: Write the test file**

```python
# tests/test_build_faiss_index.py
"""
Unit tests for build_faiss_index.py helper functions.
Run: pytest tests/test_build_faiss_index.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_faiss_index


# ---------------------------------------------------------------------------
# load_embeddings
# ---------------------------------------------------------------------------

def test_load_embeddings_returns_float32_matrix(tmp_path):
    """load_embeddings reads a .npy file and returns a float32 ndarray."""
    matrix = np.random.rand(10, 384).astype(np.float32)
    npy_path = tmp_path / "embeddings.npy"
    np.save(str(npy_path), matrix)

    result = build_faiss_index.load_embeddings(npy_path)

    assert isinstance(result, np.ndarray)
    assert result.shape == (10, 384)
    assert result.dtype == np.float32


def test_load_embeddings_raises_on_missing_file(tmp_path):
    """load_embeddings raises FileNotFoundError if the .npy file does not exist."""
    with pytest.raises(FileNotFoundError):
        build_faiss_index.load_embeddings(tmp_path / "nonexistent.npy")


def test_load_embeddings_raises_on_non_2d_matrix(tmp_path):
    """load_embeddings raises ValueError if the loaded array is not 2-dimensional."""
    bad_matrix = np.random.rand(10).astype(np.float32)
    npy_path = tmp_path / "bad.npy"
    np.save(str(npy_path), bad_matrix)

    with pytest.raises(ValueError, match="2-dimensional"):
        build_faiss_index.load_embeddings(npy_path)


def test_load_embeddings_casts_to_float32(tmp_path):
    """load_embeddings casts non-float32 arrays to float32 (FAISS requirement)."""
    matrix_f64 = np.random.rand(5, 384).astype(np.float64)
    npy_path = tmp_path / "embeddings_f64.npy"
    np.save(str(npy_path), matrix_f64)

    result = build_faiss_index.load_embeddings(npy_path)

    assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

def test_build_index_returns_indexflatip_with_all_vectors():
    """build_index returns an IndexFlatIP containing every vector from the matrix."""
    matrix = np.random.rand(20, 384).astype(np.float32)

    index = build_faiss_index.build_index(matrix)

    assert isinstance(index, faiss.IndexFlatIP)
    assert index.d == 384
    assert index.ntotal == 20


def test_build_index_vectors_are_normalized():
    """build_index normalizes vectors in place — each row in the indexed matrix has L2 norm ~1."""
    matrix = (np.random.rand(8, 384).astype(np.float32) * 100.0) + 1.0

    index = build_faiss_index.build_index(matrix)

    # After build_index, the caller's matrix should be normalized.
    norms = np.linalg.norm(matrix, axis=1)
    np.testing.assert_allclose(norms, np.ones(8), atol=1e-5)
    assert index.ntotal == 8


def test_build_index_search_returns_self_as_top_hit():
    """A normalized vector searched against the index should return itself as top hit with score ~1.0."""
    matrix = np.random.rand(5, 384).astype(np.float32)

    index = build_faiss_index.build_index(matrix)

    # Query with first vector (already normalized inside build_index)
    query = matrix[0:1]
    scores, ids = index.search(query, k=1)

    assert ids[0][0] == 0
    assert scores[0][0] == pytest.approx(1.0, abs=1e-4)


# ---------------------------------------------------------------------------
# save_index
# ---------------------------------------------------------------------------

def test_save_index_writes_file_that_round_trips(tmp_path):
    """save_index writes a FAISS file that can be read back with the same ntotal and d."""
    matrix = np.random.rand(6, 384).astype(np.float32)
    index = build_faiss_index.build_index(matrix)
    output_path = tmp_path / "sophia_index.faiss"

    build_faiss_index.save_index(index, output_path)

    assert output_path.exists()
    loaded_index = faiss.read_index(str(output_path))
    assert loaded_index.d == 384
    assert loaded_index.ntotal == 6


# ---------------------------------------------------------------------------
# save_index_meta
# ---------------------------------------------------------------------------

def test_save_index_meta_writes_required_keys(tmp_path):
    """save_index_meta writes JSON with index_type, dimension, total_vectors, generated_at, embeddings_source."""
    meta = build_faiss_index.FaissIndexMeta(
        index_type="IndexFlatIP",
        dimension=384,
        total_vectors=1422,
        generated_at="2026-05-22T00:00:00+00:00",
        embeddings_source="data/embeddings.npy",
    )
    output_path = tmp_path / "faiss_index_meta.json"

    build_faiss_index.save_index_meta(meta, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["index_type"] == "IndexFlatIP"
    assert data["dimension"] == 384
    assert data["total_vectors"] == 1422
    assert data["generated_at"] == "2026-05-22T00:00:00+00:00"
    assert data["embeddings_source"] == "data/embeddings.npy"
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
SophiaAI-venv\Scripts\Activate.ps1
pytest tests/test_build_faiss_index.py -v
```

Expected output: `ModuleNotFoundError: No module named 'build_faiss_index'`. Correct — script does not exist yet.

---

## Task 2: Implement `scripts/build_faiss_index.py`

**Files:**
- Create: `scripts/build_faiss_index.py`

- [ ] **Step 3: Write the script**

```python
#!/usr/bin/env python3
"""
build_faiss_index.py
====================
SophiaAI — Phase 4: FAISS Index.

Reads data/embeddings.npy, normalizes every vector to unit length,
builds a faiss.IndexFlatIP (exact inner product = cosine similarity
on unit vectors), and writes two artifacts:

  data/sophia_index.faiss     — binary FAISS index file
  data/faiss_index_meta.json  — index type, dimension, count, timestamp, source

Usage:
    python scripts/build_faiss_index.py
    python scripts/build_faiss_index.py --embeddings data/embeddings.npy
    python scripts/build_faiss_index.py --output data/sophia_index.faiss

Requirements:
    - data/embeddings.npy must exist (run build_embeddings.py first)
    - faiss-cpu and numpy installed in SophiaAI-venv

Author: Cosmos De La Cruz — SophiaAI Phase 4
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_faiss_index")


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "embeddings.npy"
DEFAULT_INDEX_PATH = PROJECT_ROOT / "data" / "sophia_index.faiss"
DEFAULT_META_PATH = PROJECT_ROOT / "data" / "faiss_index_meta.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FaissIndexMeta:
    """
    Mental Model:
        Sidecar file that records what produced the sophia_index.faiss file.
        Any downstream phase (retriever) can read this to verify the index
        was built from the expected embedding matrix and dimension.

    Args:
        index_type:        FAISS class name (e.g. "IndexFlatIP").
        dimension:         Vector length (384 for all-MiniLM-L6-v2).
        total_vectors:     Number of vectors indexed.
        generated_at:      ISO 8601 UTC timestamp.
        embeddings_source: Path to the .npy file that fed this index.
    """

    index_type: str
    dimension: int
    total_vectors: int
    generated_at: str
    embeddings_source: str


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_embeddings(embeddings_path: Path) -> np.ndarray:
    """
    Mental Model:
        Reads the embedding matrix from disk and returns a contiguous
        float32 ndarray that FAISS can consume directly. Casts dtype if
        needed because FAISS only accepts float32. Validates 2-D shape.

    Args:
        embeddings_path: Absolute path to embeddings.npy.

    Returns:
        np.ndarray: Float32 array of shape (n_vectors, dimension).

    Raises:
        FileNotFoundError: File does not exist.
        ValueError: Loaded array is not 2-dimensional.
    """
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {embeddings_path}\n"
            f"Run 'python scripts/build_embeddings.py' first."
        )

    matrix = np.load(str(embeddings_path))

    if matrix.ndim != 2:
        raise ValueError(
            f"Expected a 2-dimensional matrix, got shape {matrix.shape} "
            f"from {embeddings_path}."
        )

    if matrix.dtype != np.float32:
        logger.warning(
            f"Embeddings dtype is {matrix.dtype}, casting to float32 for FAISS."
        )
        matrix = matrix.astype(np.float32)

    # FAISS requires C-contiguous arrays
    if not matrix.flags["C_CONTIGUOUS"]:
        matrix = np.ascontiguousarray(matrix)

    logger.info(
        f"Loaded embeddings: shape={matrix.shape} | dtype={matrix.dtype} "
        f"| source={embeddings_path.name}"
    )
    return matrix


def save_index(index: faiss.Index, output_path: Path) -> None:
    """
    Mental Model:
        Writes the FAISS index to a binary file. Creates parent directories
        if needed. Reports file size on success.

    Args:
        index:       Built FAISS index.
        output_path: Absolute path for the output .faiss file.

    Raises:
        OSError: On any write failure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        faiss.write_index(index, str(output_path))
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"FAISS index saved: {output_path} "
            f"| ntotal={index.ntotal} | d={index.d} | {size_mb:.2f} MB"
        )
    except OSError as error:
        logger.error(f"Failed to write FAISS index to '{output_path}': {error}")
        raise


def save_index_meta(meta: FaissIndexMeta, output_path: Path) -> None:
    """
    Mental Model:
        Writes FaissIndexMeta as a human-readable JSON sidecar.
        Any engineer reading the repo can know exactly what produced the
        index without opening code.

    Args:
        meta:        Populated FaissIndexMeta dataclass.
        output_path: Absolute path for the output JSON file.

    Raises:
        OSError: On any write failure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(meta), f, indent=2, ensure_ascii=False)
        logger.info(f"FAISS index metadata saved: {output_path}")
    except OSError as error:
        logger.error(f"Failed to write metadata to '{output_path}': {error}")
        raise


# ---------------------------------------------------------------------------
# Index pipeline
# ---------------------------------------------------------------------------

def build_index(matrix: np.ndarray) -> faiss.IndexFlatIP:
    """
    Mental Model:
        Normalizes every row of the matrix to unit length (in place) and
        builds an IndexFlatIP. With unit vectors, inner product equals
        cosine similarity, which is the standard similarity for sentence
        embeddings. Flat means exact search — no approximation. For 1,422
        vectors the speed is irrelevant; for the discipline of correct
        building it matters.

    Args:
        matrix: Float32 array of shape (n_vectors, dimension). Modified
                in place by faiss.normalize_L2.

    Returns:
        faiss.IndexFlatIP: Index containing all n_vectors normalized rows.
    """
    n_vectors, dimension = matrix.shape

    logger.info(f"Normalizing {n_vectors:,} vectors to unit length (L2)...")
    faiss.normalize_L2(matrix)

    logger.info(f"Building IndexFlatIP with dimension={dimension}...")
    index = faiss.IndexFlatIP(dimension)
    index.add(matrix)

    logger.info(f"Index built. ntotal={index.ntotal} | d={index.d}")
    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_cli_arguments() -> argparse.Namespace:
    """
    Mental Model:
        Defines the command-line interface. All defaults point to standard
        data/ paths. Every parameter is overridable without touching code.

    Returns:
        argparse.Namespace: Parsed args with all defaults applied.
    """
    parser = argparse.ArgumentParser(
        prog="build_faiss_index.py",
        description=(
            "SophiaAI Phase 4 — Build FAISS IndexFlatIP from embeddings.npy."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--embeddings",
        type=Path,
        default=DEFAULT_EMBEDDINGS_PATH,
        help=f"Path to embeddings.npy. Default: {DEFAULT_EMBEDDINGS_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"Output path for sophia_index.faiss. Default: {DEFAULT_INDEX_PATH}",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        default=DEFAULT_META_PATH,
        help=f"Output path for faiss_index_meta.json. Default: {DEFAULT_META_PATH}",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Mental Model:
        Entry point. Loads matrix, builds index, saves index + sidecar.
        Each step is delegated to a single-responsibility function.
        Exits with code 1 on unrecoverable startup errors so CI can
        detect failure correctly.

        Exit codes:
          0 — sophia_index.faiss and faiss_index_meta.json written.
          1 — missing embeddings file, malformed matrix, or write failure.
    """
    args = parse_cli_arguments()

    try:
        matrix = load_embeddings(args.embeddings)
    except (FileNotFoundError, ValueError) as error:
        logger.error(str(error))
        sys.exit(1)
    except Exception as error:
        logger.error(f"Unexpected error loading embeddings: {error}")
        sys.exit(1)

    if matrix.shape[0] == 0:
        logger.error("Embeddings matrix has zero rows. Nothing to index.")
        sys.exit(1)

    try:
        index = build_index(matrix)
    except Exception as error:
        logger.error(f"Failed to build FAISS index: {error}")
        sys.exit(1)

    try:
        save_index(index, args.output)
    except OSError:
        sys.exit(1)

    meta = FaissIndexMeta(
        index_type=type(index).__name__,
        dimension=index.d,
        total_vectors=index.ntotal,
        generated_at=datetime.now(timezone.utc).isoformat(),
        embeddings_source=str(args.embeddings),
    )

    try:
        save_index_meta(meta, args.meta)
    except OSError:
        sys.exit(1)

    logger.info(
        "Phase 4 complete. Sophia's vector index is ready for retrieval.\n"
        f"  sophia_index.faiss    → {args.output}\n"
        f"  faiss_index_meta.json → {args.meta}"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```powershell
pytest tests/test_build_faiss_index.py -v
```

Expected output:
```
tests/test_build_faiss_index.py::test_load_embeddings_returns_float32_matrix PASSED
tests/test_build_faiss_index.py::test_load_embeddings_raises_on_missing_file PASSED
tests/test_build_faiss_index.py::test_load_embeddings_raises_on_non_2d_matrix PASSED
tests/test_build_faiss_index.py::test_load_embeddings_casts_to_float32 PASSED
tests/test_build_faiss_index.py::test_build_index_returns_indexflatip_with_all_vectors PASSED
tests/test_build_faiss_index.py::test_build_index_vectors_are_normalized PASSED
tests/test_build_faiss_index.py::test_build_index_search_returns_self_as_top_hit PASSED
tests/test_build_faiss_index.py::test_save_index_writes_file_that_round_trips PASSED
tests/test_build_faiss_index.py::test_save_index_meta_writes_required_keys PASSED

9 passed in X.XXs
```

- [ ] **Step 5: Commit script + tests**

```powershell
git add scripts/build_faiss_index.py tests/test_build_faiss_index.py docs/superpowers/plans/phase4-FAISS-Index.md
git commit -m "feat(phase4): add build_faiss_index.py with unit tests"
```

Stages and commits the new script, tests, and plan file together so the history shows TDD as one atomic step.

---

## Task 3: Run the script and verify artifacts

- [ ] **Step 6: Confirm embeddings.npy exists locally**

```powershell
python -c "import numpy as np; m = np.load('data/embeddings.npy'); print('shape:', m.shape, '| dtype:', m.dtype)"
```

Expected:
```
shape: (1422, 384) | dtype: float32
```

If file is missing (gitignored), run `python scripts/build_embeddings.py` first.

- [ ] **Step 7: Run the FAISS build script**

```powershell
python scripts/build_faiss_index.py
```

Expected log output (approximate):
```
HH:MM:SS | INFO     | Loaded embeddings: shape=(1422, 384) | dtype=float32 | source=embeddings.npy
HH:MM:SS | INFO     | Normalizing 1,422 vectors to unit length (L2)...
HH:MM:SS | INFO     | Building IndexFlatIP with dimension=384...
HH:MM:SS | INFO     | Index built. ntotal=1422 | d=384
HH:MM:SS | INFO     | FAISS index saved: data/sophia_index.faiss | ntotal=1422 | d=384 | X.XX MB
HH:MM:SS | INFO     | FAISS index metadata saved: data/faiss_index_meta.json
HH:MM:SS | INFO     | Phase 4 complete. Sophia's vector index is ready for retrieval.
```

- [ ] **Step 8: Verify the index file round-trips**

```powershell
python -c "import faiss, json; idx = faiss.read_index('data/sophia_index.faiss'); print('ntotal:', idx.ntotal, '| d:', idx.d, '| type:', type(idx).__name__); meta = json.load(open('data/faiss_index_meta.json')); print('meta:', meta)"
```

Expected:
```
ntotal: 1422 | d: 384 | type: IndexFlatIP
meta: {'index_type': 'IndexFlatIP', 'dimension': 384, 'total_vectors': 1422, 'generated_at': '...', 'embeddings_source': '...embeddings.npy'}
```

- [ ] **Step 9: Smoke-test a real semantic search**

```powershell
python -c "import faiss, numpy as np; from sentence_transformers import SentenceTransformer; m = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); q = m.encode(['What is wisdom?'], convert_to_numpy=True).astype(np.float32); faiss.normalize_L2(q); idx = faiss.read_index('data/sophia_index.faiss'); s, i = idx.search(q, 5); print('top5 scores:', s[0]); print('top5 ids:', i[0])"
```

Expected: five scores in descending order between roughly 0.2 and 0.7, and five integer ids in range `[0, 1421]`. Sanity check that retrieval works end to end before Phase 5.

- [ ] **Step 10: Update `data/.gitignore` if needed**

Check whether `sophia_index.faiss` is already gitignored:

```powershell
git check-ignore -v data/sophia_index.faiss
```

If the command prints a `.gitignore` line, it is ignored. If it prints nothing, add the entry. Open `.gitignore` (or `data/.gitignore` if one exists) and append:

```
data/sophia_index.faiss
```

The binary index file is regenerable from `embeddings.npy` and should not be committed. The sidecar `faiss_index_meta.json` (small JSON) stays tracked.

- [ ] **Step 11: Update cosmos_log.md**

Append to `cosmos_log.md`:

```markdown
## Phase 4 — FAISS Index
**Date:** 2026-05-22

**What was built:** `scripts/build_faiss_index.py`. Loads
`data/embeddings.npy`, normalizes every vector to unit length with
`faiss.normalize_L2`, builds an `IndexFlatIP` (exact inner-product
search = cosine similarity on unit vectors), and writes
`data/sophia_index.faiss` plus `data/faiss_index_meta.json`.

**Artifacts:**
- `data/sophia_index.faiss` — 1422 × 384 IndexFlatIP, binary, gitignored
- `data/faiss_index_meta.json` — index_type, dimension, total_vectors, generated_at, embeddings_source

**Why IndexFlatIP:** Exact search. 1,422 vectors is trivial size — no
approximation needed. Inner product on L2-normalized vectors equals
cosine similarity, the standard metric for sentence embeddings.

**Next step:** Phase 5 — build `sophia/rag/retriever.py` with the
`SophiaRetriever` class that loads the FAISS index, the embedding
model, and `chunks_index.json` once at startup and exposes
`retrieve(query, top_k)`.
```

- [ ] **Step 12: Final commit**

```powershell
git add data/faiss_index_meta.json cosmos_log.md .gitignore
git commit -m "feat(phase4): build FAISS IndexFlatIP — 1422 vectors at 384 dims"
```

Stages the tracked sidecar metadata, the updated dev log, and the gitignore change (if any) into one commit that marks Phase 4 done.

- [ ] **Step 13: Merge to master**

```powershell
git checkout master
git merge --no-ff feat/phase4-faiss -m "merge: Phase 4 — FAISS index"
```

Switches to master and merges the feature branch with a merge commit so the phase boundary is visible in `git log --graph`. After this, Phase 5 starts from master.

---

## Self-Review

**Spec coverage (from `developing_plan.md` Phase 4 + `MEMORY.md` Phase 4 spec):**
- ✅ Script `scripts/build_faiss_index.py` — Task 2
- ✅ Load `embeddings.npy` with `np.load()` — `load_embeddings()`
- ✅ Normalize each vector to unit length via `faiss.normalize_L2` — `build_index()`
- ✅ Build `IndexFlatIP` with `faiss.IndexFlatIP(384)` — `build_index()`
- ✅ Add all vectors via `index.add(matrix)` — `build_index()`
- ✅ Write to disk via `faiss.write_index` — `save_index()`
- ✅ Output `data/sophia_index.faiss` — default `--output`
- ✅ Sidecar `data/faiss_index_meta.json` with `index_type`, `dimension`, `total_vectors`, `generated_at`, `embeddings_source` — `FaissIndexMeta` + `save_index_meta()`
- ✅ Argparse CLI with overridable paths — `parse_cli_arguments()`
- ✅ Logger + sys.exit on failures — `main()`
- ✅ ZenCode PRO docstrings with "Mental Model" sections — every function
- ✅ Branch `feat/phase4-faiss` → merge to `master` — Steps 0 and 13

**Placeholder scan:** No TBD, TODO, vague steps. All code, commands, and expected output shown literally.

**Type consistency:**
- `FaissIndexMeta` defined in Task 2 with fields `index_type`, `dimension`, `total_vectors`, `generated_at`, `embeddings_source` — matches the test usage in Task 1 exactly.
- `load_embeddings` signature `(Path) -> np.ndarray` — matches the test calls.
- `build_index` signature `(np.ndarray) -> faiss.IndexFlatIP` — matches the test calls.
- `save_index` signature `(faiss.Index, Path) -> None` — matches the test calls.
- `save_index_meta` signature `(FaissIndexMeta, Path) -> None` — matches the test calls.
