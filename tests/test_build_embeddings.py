# tests/test_build_embeddings.py
"""
Unit tests for build_embeddings.py helper functions.
Run: pytest tests/test_build_embeddings.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

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

    loaded = np.load(output_path)
    assert loaded.shape == (5, 384)
    assert loaded.dtype == np.float32
    np.testing.assert_array_almost_equal(loaded, matrix)


# ---------------------------------------------------------------------------
# save_embedding_meta
# ---------------------------------------------------------------------------

def test_save_embedding_meta_writes_required_keys(tmp_path):
    """save_embedding_meta writes JSON with model_name, dimension, chunk_count, generated_at."""
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
    assert data["generated_at"] == "2026-05-21T00:00:00+00:00"


# ---------------------------------------------------------------------------
# embed_chunks_in_batches
# ---------------------------------------------------------------------------

def test_embed_chunks_in_batches_returns_correct_shape():
    """embed_chunks_in_batches returns matrix of shape (n_chunks, dim)."""
    fake_texts = [f"chunk text {i}" for i in range(7)]

    mock_model = MagicMock()
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
    mock_model.encode.side_effect = [
        RuntimeError("GPU exploded"),
        np.random.rand(1, 384).astype(np.float32),
    ]

    result = build_embeddings.embed_chunks_in_batches(
        texts=fake_texts,
        model=mock_model,
        batch_size=2,
    )

    assert result.shape[1] == 384
    assert result.shape[0] < 3
