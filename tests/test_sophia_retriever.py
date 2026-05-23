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
    Returns a fake (index, model) tuple. The fake index has the given dim
    and ntotal. The fake model reports the given dim via
    get_sentence_embedding_dimension and returns an arbitrary unit-shape
    vector from .encode().
    """
    fake_index = MagicMock()
    fake_index.d = index_dim
    fake_index.ntotal = ntotal

    fake_model = MagicMock()
    fake_model.get_embedding_dimension.return_value = model_dim
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
