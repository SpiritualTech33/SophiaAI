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


# ---------------------------------------------------------------------------
# relative_to_project_root
# ---------------------------------------------------------------------------

def test_relative_to_project_root_strips_absolute_prefix():
    """A path inside the project becomes a repo-relative POSIX string."""
    absolute = build_faiss_index.PROJECT_ROOT / "data" / "embeddings.npy"

    result = build_faiss_index.relative_to_project_root(absolute)

    assert result == "data/embeddings.npy"


def test_relative_to_project_root_falls_back_outside_root(tmp_path):
    """A path outside the project is returned unchanged as its string form."""
    outside = tmp_path / "embeddings.npy"

    result = build_faiss_index.relative_to_project_root(outside)

    assert result == str(outside)
