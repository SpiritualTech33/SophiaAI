# Phase 3 — Embeddings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed all 1,422 RAG chunks from `chunks_index.json` using `all-MiniLM-L6-v2` and write the resulting matrix to `data/embeddings.npy` plus a metadata sidecar at `data/embedding_meta.json`.

**Architecture:** A single standalone script (`scripts/build_embeddings.py`) that loads the RAG chunks, encodes them in batches of 32 via SentenceTransformer, and writes numpy + JSON artifacts to disk. Follows the same ZenCode PRO conventions as `build_chunks.py`: single-responsibility functions, dataclass for meta, tqdm progress bar, try/except per batch, argparse CLI.

**Tech Stack:** `sentence-transformers` (all-MiniLM-L6-v2), `numpy`, `tqdm`, `argparse`, `pytest`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `scripts/build_embeddings.py` | Create | Full embedding pipeline script |
| `tests/test_build_embeddings.py` | Create | Unit tests for helper functions |
| `data/embeddings.npy` | Produced by script | Float32 matrix, shape (1422, 384) |
| `data/embedding_meta.json` | Produced by script | Model name, dimension, chunk count, timestamp |

---

## Task 1: Write the failing tests

**Files:**
- Create: `tests/test_build_embeddings.py`

- [ ] **Step 1: Write the test file**

```python
# tests/test_build_embeddings.py
"""
Unit tests for build_embeddings.py helper functions.
Run: pytest tests/test_build_embeddings.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_embeddings


# ---------------------------------------------------------------------------
# load_rag_chunks
# ---------------------------------------------------------------------------

def test_load_rag_chunks_returns_list_of_dicts(tmp_path):
    """load_rag_chunks reads rag_chunks from chunks_index.json."""
    fake_index = {
        "rag_chunks": [
            {"chunk_id": "abc_rag_0000", "text": "Hello Sophia.", "pillar": "mind"},
            {"chunk_id": "abc_rag_0001", "text": "Wisdom is virtue.", "pillar": "philosophy"},
        ]
    }
    index_path = tmp_path / "chunks_index.json"
    index_path.write_text(json.dumps(fake_index), encoding="utf-8")

    result = build_embeddings.load_rag_chunks(index_path)

    assert len(result) == 2
    assert result[0]["chunk_id"] == "abc_rag_0000"
    assert result[1]["text"] == "Wisdom is virtue."


def test_load_rag_chunks_raises_on_missing_file(tmp_path):
    """load_rag_chunks raises FileNotFoundError if path does not exist."""
    with pytest.raises(FileNotFoundError):
        build_embeddings.load_rag_chunks(tmp_path / "nonexistent.json")


def test_load_rag_chunks_raises_on_missing_key(tmp_path):
    """load_rag_chunks raises ValueError if rag_chunks key is absent."""
    bad_index = {"pretrain_chunks": []}
    index_path = tmp_path / "chunks_index.json"
    index_path.write_text(json.dumps(bad_index), encoding="utf-8")

    with pytest.raises(ValueError, match="rag_chunks"):
        build_embeddings.load_rag_chunks(index_path)


# ---------------------------------------------------------------------------
# save_embeddings
# ---------------------------------------------------------------------------

def test_save_embeddings_writes_npy(tmp_path):
    """save_embeddings writes a float32 numpy array that round-trips correctly."""
    matrix = np.random.rand(5, 384).astype(np.float32)
    output_path = tmp_path / "embeddings.npy"

    build_embeddings.save_embeddings(matrix, output_path)

    loaded = np.load(str(output_path))
    assert loaded.shape == (5, 384)
    assert loaded.dtype == np.float32
    np.testing.assert_array_almost_equal(loaded, matrix)


# ---------------------------------------------------------------------------
# save_embedding_meta
# ---------------------------------------------------------------------------

def test_save_embedding_meta_writes_required_keys(tmp_path):
    """save_embedding_meta writes JSON with model_name, dimension, chunk_count, generated_at."""
    from dataclasses import asdict
    meta = build_embeddings.EmbeddingMeta(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        chunk_count=1422,
        generated_at="2026-05-21T00:00:00+00:00",
    )
    output_path = tmp_path / "embedding_meta.json"

    build_embeddings.save_embedding_meta(meta, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert data["dimension"] == 384
    assert data["chunk_count"] == 1422
    assert "generated_at" in data


# ---------------------------------------------------------------------------
# embed_chunks_in_batches
# ---------------------------------------------------------------------------

def test_embed_chunks_in_batches_returns_correct_shape():
    """embed_chunks_in_batches returns matrix of shape (n_chunks, dim)."""
    fake_texts = [f"chunk text {i}" for i in range(7)]

    # Mock SentenceTransformer so no model download needed in tests
    mock_model = MagicMock()
    # encode() called twice: batch of 4 then batch of 3
    mock_model.encode.side_effect = [
        np.random.rand(4, 384).astype(np.float32),
        np.random.rand(3, 384).astype(np.float32),
    ]

    result = build_embeddings.embed_chunks_in_batches(
        texts=fake_texts,
        model=mock_model,
        batch_size=4,
    )

    assert result.shape == (7, 384)
    assert result.dtype == np.float32
    assert mock_model.encode.call_count == 2


def test_embed_chunks_in_batches_skips_bad_batch():
    """embed_chunks_in_batches logs a warning and continues if one batch fails."""
    fake_texts = ["chunk a", "chunk b", "chunk c"]

    mock_model = MagicMock()
    # First batch raises, second succeeds
    mock_model.encode.side_effect = [
        RuntimeError("GPU exploded"),
        np.random.rand(2, 384).astype(np.float32),
    ]

    result = build_embeddings.embed_chunks_in_batches(
        texts=fake_texts,
        model=mock_model,
        batch_size=1,  # triggers first batch of 1 (fails), then rest
    )

    # Only 2 vectors from the successful batch — shape (2, 384)
    assert result.shape[1] == 384
    assert result.shape[0] < 3  # less than all 3 because first batch failed
```

- [ ] **Step 2: Run tests to verify they fail**

```
SophiaAI-venv\Scripts\Activate.ps1
pytest tests/test_build_embeddings.py -v
```

Expected output: `ModuleNotFoundError: No module named 'build_embeddings'` — correct, script does not exist yet.

---

## Task 2: Implement `scripts/build_embeddings.py`

**Files:**
- Create: `scripts/build_embeddings.py`

- [ ] **Step 3: Write the script**

```python
#!/usr/bin/env python3
"""
build_embeddings.py
===================
SophiaAI — Phase 3: Embedding.

Reads data/chunks_index.json, encodes every RAG chunk using
sentence-transformers/all-MiniLM-L6-v2, and writes two artifacts:

  data/embeddings.npy       — float32 matrix, shape (n_chunks, 384)
  data/embedding_meta.json  — model name, dimension, count, timestamp

Usage:
    python scripts/build_embeddings.py
    python scripts/build_embeddings.py --batch-size 64
    python scripts/build_embeddings.py --model sentence-transformers/all-MiniLM-L6-v2

Requirements:
    - data/chunks_index.json must exist (run build_chunks.py first)
    - All packages in requirements.txt installed in SophiaAI-venv

Author: Cosmos De La Cruz — SophiaAI Phase 3
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

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_embeddings")


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32
DEFAULT_CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks_index.json"
DEFAULT_EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "embeddings.npy"
DEFAULT_META_PATH = PROJECT_ROOT / "data" / "embedding_meta.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EmbeddingMeta:
    """
    Mental Model:
        Sidecar file that records what produced the embeddings.npy matrix.
        Any downstream phase that loads the matrix can read this file to
        verify it was produced by the expected model and dimension.

    Args:
        model_name:   HuggingFace model ID used for encoding.
        dimension:    Vector length (384 for all-MiniLM-L6-v2).
        chunk_count:  Number of RAG chunks embedded — equals rows in matrix.
        generated_at: ISO 8601 UTC timestamp.
    """

    model_name: str
    dimension: int
    chunk_count: int
    generated_at: str


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_rag_chunks(chunks_path: Path) -> list[dict]:
    """
    Mental Model:
        Reads chunks_index.json and returns the list of RAG chunk dicts.
        Only rag_chunks are embedded — pretrain_chunks are not used here.
        Validates structure before returning so callers can trust what they get.

    Args:
        chunks_path: Absolute path to chunks_index.json.

    Returns:
        list[dict]: Each dict is one RAG chunk with at least 'text' and 'chunk_id'.

    Raises:
        FileNotFoundError: File does not exist.
        ValueError: File exists but 'rag_chunks' key is missing.
        json.JSONDecodeError: File is not valid JSON.
    """
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Chunks index not found: {chunks_path}\n"
            f"Run 'python scripts/build_chunks.py' first."
        )

    with chunks_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "rag_chunks" not in data:
        raise ValueError(
            f"'rag_chunks' key missing in {chunks_path}. "
            f"Re-run 'python scripts/build_chunks.py' to regenerate."
        )

    rag_chunks = data["rag_chunks"]
    logger.info(f"Loaded {len(rag_chunks):,} RAG chunks from {chunks_path.name}.")
    return rag_chunks


def save_embeddings(matrix: np.ndarray, output_path: Path) -> None:
    """
    Mental Model:
        Writes the embedding matrix to disk as a numpy .npy file.
        Creates parent directories if needed. Reports file size on success.

    Args:
        matrix:      Float32 array of shape (n_chunks, dimension).
        output_path: Absolute path for the output .npy file.

    Raises:
        OSError: On any write failure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        np.save(str(output_path), matrix)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"Embeddings saved: {output_path} "
            f"| shape: {matrix.shape} | {size_mb:.2f} MB"
        )
    except OSError as error:
        logger.error(f"Failed to write embeddings to '{output_path}': {error}")
        raise


def save_embedding_meta(meta: EmbeddingMeta, output_path: Path) -> None:
    """
    Mental Model:
        Writes EmbeddingMeta as a human-readable JSON sidecar.
        Any engineer picking up this repo can read this file and know
        exactly what produced the embedding matrix, without opening code.

    Args:
        meta:        Populated EmbeddingMeta dataclass.
        output_path: Absolute path for the output JSON file.

    Raises:
        OSError: On any write failure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(meta), f, indent=2, ensure_ascii=False)
        logger.info(f"Embedding metadata saved: {output_path}")
    except OSError as error:
        logger.error(f"Failed to write metadata to '{output_path}': {error}")
        raise


# ---------------------------------------------------------------------------
# Embedding pipeline
# ---------------------------------------------------------------------------

def embed_chunks_in_batches(
    texts: list[str],
    model: SentenceTransformer,
    batch_size: int,
) -> np.ndarray:
    """
    Mental Model:
        Encodes a list of text strings into a float32 matrix.
        Processes in batches so memory stays manageable on CPU.
        One bad batch never kills the run — it logs a warning and skips.
        The tqdm bar shows real-time progress over batches.

        Result is np.vstack of all successful batch outputs.
        If all batches fail, returns an empty (0, 384) array.

    Args:
        texts:      List of raw text strings to encode.
        model:      Loaded SentenceTransformer instance.
        batch_size: Number of texts per encoding call. Default 32.

    Returns:
        np.ndarray: Float32 array of shape (n_successful, dim).
    """
    all_vectors: list[np.ndarray] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    batch_iter = range(0, len(texts), batch_size)
    for batch_start in tqdm(batch_iter, total=total_batches, desc="Embedding chunks", unit="batch"):
        batch_texts = texts[batch_start: batch_start + batch_size]

        try:
            batch_vectors = model.encode(
                batch_texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            ).astype(np.float32)
            all_vectors.append(batch_vectors)

        except Exception as error:
            logger.warning(
                f"Batch {batch_start // batch_size + 1}/{total_batches} failed: {error}. "
                f"Skipping {len(batch_texts)} chunks."
            )

    if not all_vectors:
        logger.error("All batches failed. No embeddings produced.")
        # Return empty array with correct second dimension
        return np.empty((0, 384), dtype=np.float32)

    return np.vstack(all_vectors).astype(np.float32)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_cli_arguments() -> argparse.Namespace:
    """
    Mental Model:
        Defines the command-line interface. All defaults are safe for CPU.
        Every parameter is overridable without touching the code.

    Returns:
        argparse.Namespace: Parsed args with all defaults applied.
    """
    parser = argparse.ArgumentParser(
        prog="build_embeddings.py",
        description=(
            "SophiaAI Phase 3 — Embed RAG chunks with sentence-transformers.\n"
            f"Default model: {DEFAULT_MODEL_NAME}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help=f"SentenceTransformer model. Default: {DEFAULT_MODEL_NAME}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Chunks per encoding batch. Default: {DEFAULT_BATCH_SIZE}",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
        help=f"Path to chunks_index.json. Default: {DEFAULT_CHUNKS_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_EMBEDDINGS_PATH,
        help=f"Output path for embeddings.npy. Default: {DEFAULT_EMBEDDINGS_PATH}",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        default=DEFAULT_META_PATH,
        help=f"Output path for embedding_meta.json. Default: {DEFAULT_META_PATH}",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Mental Model:
        Entry point. Loads chunks, loads model, embeds, saves artifacts.
        Each step is delegated to a single-responsibility function.
        Exits with code 1 on unrecoverable startup errors so CI pipelines
        can detect failure correctly.

        Exit codes:
          0 — embeddings.npy and embedding_meta.json written successfully.
          1 — missing chunks file, or zero embeddings produced.
    """
    args = parse_cli_arguments()

    # Load RAG chunks — exits with clear error if file missing or malformed
    try:
        rag_chunks = load_rag_chunks(args.chunks)
    except (FileNotFoundError, ValueError, Exception) as error:
        logger.error(str(error))
        sys.exit(1)

    if not rag_chunks:
        logger.error("chunks_index.json contains zero RAG chunks. Nothing to embed.")
        sys.exit(1)

    texts = [chunk["text"] for chunk in rag_chunks]

    # Load embedding model
    logger.info(f"Loading model: {args.model} ...")
    try:
        model = SentenceTransformer(args.model)
    except Exception as error:
        logger.error(f"Failed to load model '{args.model}': {error}")
        sys.exit(1)

    dimension = model.get_sentence_embedding_dimension()
    logger.info(f"Model ready. Dimension: {dimension}. Chunks to embed: {len(texts):,}.")

    # Embed all chunks in batches
    embedding_matrix = embed_chunks_in_batches(
        texts=texts,
        model=model,
        batch_size=args.batch_size,
    )

    if embedding_matrix.shape[0] == 0:
        logger.error("No embeddings were produced. Check warnings above.")
        sys.exit(1)

    logger.info(
        f"Embedding complete | "
        f"Matrix shape: {embedding_matrix.shape} | "
        f"dtype: {embedding_matrix.dtype}"
    )

    # Save matrix and sidecar metadata
    save_embeddings(embedding_matrix, args.output)

    meta = EmbeddingMeta(
        model_name=args.model,
        dimension=dimension,
        chunk_count=embedding_matrix.shape[0],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    save_embedding_meta(meta, args.meta)

    logger.info(
        "Phase 3 complete. Sophia's corpus is embedded and ready for FAISS indexing.\n"
        f"  embeddings.npy     → {args.output}\n"
        f"  embedding_meta.json → {args.meta}"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_build_embeddings.py -v
```

Expected output:
```
tests/test_build_embeddings.py::test_load_rag_chunks_returns_list_of_dicts PASSED
tests/test_build_embeddings.py::test_load_rag_chunks_raises_on_missing_file PASSED
tests/test_build_embeddings.py::test_load_rag_chunks_raises_on_missing_key PASSED
tests/test_build_embeddings.py::test_save_embeddings_writes_npy PASSED
tests/test_build_embeddings.py::test_save_embedding_meta_writes_required_keys PASSED
tests/test_build_embeddings.py::test_embed_chunks_in_batches_returns_correct_shape PASSED
tests/test_build_embeddings.py::test_embed_chunks_in_batches_skips_bad_batch PASSED

7 passed in X.XXs
```

- [ ] **Step 5: Commit**

```bash
git add scripts/build_embeddings.py tests/test_build_embeddings.py docs/superpowers/plans/2026-05-21-phase3-embeddings.md
git commit -m "feat(phase3): add build_embeddings.py with unit tests"
```

---

## Task 3: Run the script and verify artifacts

- [ ] **Step 6: Run the embedding script**

```
SophiaAI-venv\Scripts\Activate.ps1
python scripts/build_embeddings.py
```

Expected log output (approximate):
```
HH:MM:SS | INFO     | Loaded 1,422 RAG chunks from chunks_index.json.
HH:MM:SS | INFO     | Loading model: sentence-transformers/all-MiniLM-L6-v2 ...
HH:MM:SS | INFO     | Model ready. Dimension: 384. Chunks to embed: 1,422.
Embedding chunks: 100%|████████████████| 45/45 [00:XX<00:00, X.XXbatch/s]
HH:MM:SS | INFO     | Embedding complete | Matrix shape: (1422, 384) | dtype: float32
HH:MM:SS | INFO     | Embeddings saved: data/embeddings.npy | shape: (1422, 384) | X.XX MB
HH:MM:SS | INFO     | Embedding metadata saved: data/embedding_meta.json
HH:MM:SS | INFO     | Phase 3 complete. Sophia's corpus is embedded and ready for FAISS indexing.
```

- [ ] **Step 7: Verify artifacts on disk**

```powershell
python -c "import numpy as np, json; m = np.load('data/embeddings.npy'); print('shape:', m.shape, '| dtype:', m.dtype); meta = json.load(open('data/embedding_meta.json')); print('meta:', meta)"
```

Expected:
```
shape: (1422, 384) | dtype: float32
meta: {'model_name': 'sentence-transformers/all-MiniLM-L6-v2', 'dimension': 384, 'chunk_count': 1422, 'generated_at': '...'}
```

- [ ] **Step 8: Update cosmos_log.md**

Append to `cosmos_log.md`:
```markdown
## Phase 3 — Embeddings
**Date:** 2026-05-21

**What was built:** `scripts/build_embeddings.py`. Encodes all 1,422 RAG chunks
from `chunks_index.json` using `sentence-transformers/all-MiniLM-L6-v2` (384 dims).
Outputs `data/embeddings.npy` (float32 matrix, shape 1422×384) and
`data/embedding_meta.json`. Batch size 32, try/except per batch.

**Artifacts:**
- `data/embeddings.npy` — embedding matrix, ready for FAISS
- `data/embedding_meta.json` — model name, dimension, chunk count, timestamp

**Next step:** Phase 4 — build the FAISS index from `embeddings.npy`.
```

- [ ] **Step 9: Final commit**

```bash
git add data/embedding_meta.json cosmos_log.md
git commit -m "feat(phase3): run embeddings — 1422 chunks at 384 dims"
```

> Note: `data/embeddings.npy` is typically gitignored (large binary). If it is not in `.gitignore` yet, add it. The `embedding_meta.json` (small JSON) is tracked.

---

## Self-Review

**Spec coverage:**
- ✅ Script `scripts/build_embeddings.py` — Task 2
- ✅ Model `all-MiniLM-L6-v2` — hardcoded as default, overridable via `--model`
- ✅ Loads `chunks_index.json` — `load_rag_chunks()`
- ✅ tqdm progress bar — in `embed_chunks_in_batches()`
- ✅ Batch size 32 — default, overridable via `--batch-size`
- ✅ try/except per batch — in `embed_chunks_in_batches()`
- ✅ `data/embeddings.npy` — `save_embeddings()`
- ✅ `data/embedding_meta.json` with model name, dimension, timestamp — `save_embedding_meta()`

**Placeholder scan:** No TBD, TODO, or vague steps. All code shown in full.

**Type consistency:** `EmbeddingMeta` defined in Task 2, referenced in tests (Task 1) via `build_embeddings.EmbeddingMeta` — consistent. `embed_chunks_in_batches` signature matches mock usage in tests.
