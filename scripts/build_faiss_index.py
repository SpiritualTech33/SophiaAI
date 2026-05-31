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


def relative_to_project_root(path: Path) -> str:
    """
    Mental Model:
        The meta sidecar records WHERE the embeddings came from for provenance,
        not for runtime loading. Store that origin as a repo-relative POSIX path
        so the file is portable across machines and never leaks a local username
        or absolute desktop path into version control.

    Args:
        path: The embeddings path the index was built from.

    Returns:
        A forward-slash relative path (e.g. "data/embeddings.npy") when the
        source lives inside the project. Falls back to the absolute string if
        the source sits outside PROJECT_ROOT (e.g. a custom --embeddings dir).
    """
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


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
        embeddings_source=relative_to_project_root(args.embeddings),
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
