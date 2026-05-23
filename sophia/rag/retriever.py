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
    if hasattr(model, "get_embedding_dimension"):
        return int(model.get_embedding_dimension())
    return int(model.get_sentence_embedding_dimension())


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
