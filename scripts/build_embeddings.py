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
    dimension: int,
) -> np.ndarray:
    """
    Mental Model:
        Encodes a list of text strings into a float32 matrix.
        Processes in batches so memory stays manageable on CPU.
        One bad batch never kills the run — it logs a warning and skips.
        The tqdm bar shows real-time progress over batches.

        Result is np.vstack of all successful batch outputs.
        If all batches fail, returns an empty (0, dimension) array.

    Args:
        texts:      List of raw text strings to encode.
        model:      Loaded SentenceTransformer instance.
        batch_size: Number of texts per encoding call. Default 32.
        dimension:  Embedding dimension — used for the empty fallback array shape.

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
        return np.empty((0, dimension), dtype=np.float32)

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

    if args.batch_size < 1:
        logger.error(f"--batch-size must be >= 1, got {args.batch_size}.")
        sys.exit(1)

    try:
        rag_chunks = load_rag_chunks(args.chunks)
    except Exception as error:
        logger.error(str(error))
        sys.exit(1)

    if not rag_chunks:
        logger.error("chunks_index.json contains zero RAG chunks. Nothing to embed.")
        sys.exit(1)

    try:
        texts = [chunk["text"] for chunk in rag_chunks]
    except KeyError as error:
        logger.error(f"Chunk is missing required key {error}. Re-run build_chunks.py.")
        sys.exit(1)

    logger.info(f"Loading model: {args.model} ...")
    try:
        model = SentenceTransformer(args.model)
    except Exception as error:
        logger.error(f"Failed to load model '{args.model}': {error}")
        sys.exit(1)

    dimension = model.get_sentence_embedding_dimension()
    logger.info(f"Model ready. Dimension: {dimension}. Chunks to embed: {len(texts):,}.")

    embedding_matrix = embed_chunks_in_batches(
        texts=texts,
        model=model,
        batch_size=args.batch_size,
        dimension=dimension,
    )

    if embedding_matrix.shape[0] == 0:
        logger.error("No embeddings were produced. Check warnings above.")
        sys.exit(1)

    logger.info(
        f"Embedding complete | "
        f"Matrix shape: {embedding_matrix.shape} | "
        f"dtype: {embedding_matrix.dtype}"
    )

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
        f"  embeddings.npy      → {args.output}\n"
        f"  embedding_meta.json → {args.meta}"
    )


if __name__ == "__main__":
    main()
