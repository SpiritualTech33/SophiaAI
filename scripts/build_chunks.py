#!/usr/bin/env python3
"""
build_chunks.py
===============
SophiaAI — Phase 2: Chunking and Tokenization.

Reads corpus_manifest.json and slices every file in sophia_engine into
token-aligned chunks for two downstream consumers:

  RAG pipeline  — smaller chunks with overlap for precise retrieval
  Pretraining   — larger chunks with light overlap for Colab training

Base model: google/gemma-3-4b-it (configurable via --model)
Output:      data/chunks_index.json

Usage:
    python scripts/build_chunks.py
    python scripts/build_chunks.py --model google/gemma-3-4b-it
    python scripts/build_chunks.py --purpose rag
    python scripts/build_chunks.py --purpose pretrain
    python scripts/build_chunks.py --purpose both     (default)
    python scripts/build_chunks.py --rag-size 256 --pretrain-size 512

Requirements:
    - data/corpus_manifest.json must exist (run build_manifest.py first)
    - HuggingFace login required for Gemma:
        huggingface-cli login
        (Accept the license at https://huggingface.co/google/gemma-3-4b-it first)
    - All packages in requirements.txt installed in SophiaAI-venv

Author: Cosmos De La Cruz — SophiaAI Phase 2
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import frontmatter
from tqdm import tqdm
from transformers import AutoTokenizer, PreTrainedTokenizerBase


# ---------------------------------------------------------------------------
# Logging — structured, human-readable, ZenCode style
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_chunks")


# ---------------------------------------------------------------------------
# Project root — all paths resolve relative to this anchor
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Defaults — tuned for Gemma 3 4B on Colab Free (T4, 16 GB VRAM)
#
# RAG chunks:
#   384 tokens — large enough for a coherent paragraph, small enough for
#   precise semantic retrieval. 64-token overlap prevents hard cuts through
#   sentences at chunk boundaries.
#
# Pretrain chunks:
#   1024 tokens — fills a good portion of the model's context window without
#   exhausting Colab Free's RAM. 128-token overlap adds continuity between
#   training examples from the same document.
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME = "google/gemma-3-4b-it"
DEFAULT_RAG_CHUNK_SIZE_TOKENS = 384
DEFAULT_RAG_OVERLAP_TOKENS = 64
DEFAULT_PRETRAIN_CHUNK_SIZE_TOKENS = 1024
DEFAULT_PRETRAIN_OVERLAP_TOKENS = 128
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "corpus_manifest.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "chunks_index.json"


# ---------------------------------------------------------------------------
# Data structures — every field has a clear purpose, no hidden state
# ---------------------------------------------------------------------------

@dataclass
class ChunkConfig:
    """
    Mental Model:
        Configuration for a single chunking pass. The purpose field
        distinguishes RAG chunks (small + overlap, precision-optimized)
        from pretrain chunks (large + light overlap, throughput-optimized).

    Args:
        purpose: "rag" or "pretrain" — drives naming and downstream routing.
        chunk_size_tokens: Maximum tokens per chunk.
        overlap_tokens: Tokens shared between consecutive chunks.
                        Must be less than chunk_size_tokens.

    Raises:
        ValueError: If overlap >= chunk_size, or if purpose is invalid.
    """

    purpose: str
    chunk_size_tokens: int
    overlap_tokens: int

    def __post_init__(self) -> None:
        if self.purpose not in ("rag", "pretrain"):
            raise ValueError(
                f"ChunkConfig.purpose must be 'rag' or 'pretrain', got '{self.purpose}'."
            )
        if self.overlap_tokens >= self.chunk_size_tokens:
            raise ValueError(
                f"overlap_tokens ({self.overlap_tokens}) must be strictly less than "
                f"chunk_size_tokens ({self.chunk_size_tokens}) for purpose='{self.purpose}'."
            )


@dataclass
class ChunkRecord:
    """
    Mental Model:
        A single text chunk, fully traceable back to its source file via sha256.
        The chunk_id is deterministic: {sha256_prefix}_{purpose}_{index:04d}.
        Same corpus + same config = identical chunk_ids across runs. This
        stability matters for downstream systems that index chunks by ID.

    Args:
        chunk_id:       Deterministic unique identifier for this chunk.
        source_sha256:  SHA256 of the source file (from manifest). Foreign key.
        source_path:    Relative path to the source file. For human readability.
        pillar:         Sophia's pillar: mind | philosophy | spirit | science.
        chunk_index:    Zero-based position of this chunk within its source file.
        token_count:    Actual tokens in this chunk (last chunk may be shorter).
        text:           Decoded chunk text, ready for embedding or training.
    """

    chunk_id: str
    source_sha256: str
    source_path: str
    pillar: str
    chunk_index: int
    token_count: int
    text: str


@dataclass
class FileProcessingResult:
    """
    Mental Model:
        The outcome of processing a single corpus file. Separates success
        from failure without raising — so one bad file never kills the pipeline.
        On failure, was_skipped=True and skip_reason explains what happened.

    Args:
        source_path:    Relative path of the processed file.
        rag_chunks:     RAG-purpose chunks produced from this file.
        pretrain_chunks: Pretrain-purpose chunks produced from this file.
        was_skipped:    True if no chunks were produced (file issue or empty).
        skip_reason:    Human-readable explanation when was_skipped is True.
    """

    source_path: str
    rag_chunks: list[ChunkRecord] = field(default_factory=list)
    pretrain_chunks: list[ChunkRecord] = field(default_factory=list)
    was_skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class ChunksIndex:
    """
    Mental Model:
        The output artifact of this script. A complete, self-describing index
        of all chunks derived from the corpus, keyed by purpose.

        This file is the bridge between Phase 2 and all downstream phases:
          Phase 3 (pretraining on Colab)  → reads pretrain_chunks
          Phase 6 (RAG pipeline)          → reads rag_chunks

        References the corpus manifest via source_sha256 on each ChunkRecord,
        so downstream phases can always trace a chunk back to its origin file.

    Args:
        schema_version:          Integer version for forward compatibility.
        model:                   HuggingFace model whose tokenizer was used.
        generated_at:            ISO 8601 UTC timestamp.
        rag_config:              The ChunkConfig used for RAG chunks.
        pretrain_config:         The ChunkConfig used for pretrain chunks.
        total_files_processed:   Number of files that produced at least one chunk.
        total_files_skipped:     Number of files skipped (empty, missing, errored).
        total_rag_chunks:        Total RAG chunks across all files.
        total_pretrain_chunks:   Total pretrain chunks across all files.
        rag_chunks:              All RAG ChunkRecords.
        pretrain_chunks:         All pretrain ChunkRecords.
    """

    schema_version: int
    model: str
    generated_at: str
    rag_config: ChunkConfig
    pretrain_config: ChunkConfig
    total_files_processed: int
    total_files_skipped: int
    total_rag_chunks: int
    total_pretrain_chunks: int
    rag_chunks: list[ChunkRecord]
    pretrain_chunks: list[ChunkRecord]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_corpus_manifest(manifest_path: Path) -> dict:
    """
    Mental Model:
        Reads and validates the JSON manifest produced by build_manifest.py.
        Validates that the expected top-level keys are present before returning,
        so downstream functions can trust the structure they receive.

    Args:
        manifest_path: Absolute path to corpus_manifest.json.

    Returns:
        dict: Full parsed manifest. Key 'entries' holds the file list.

    Raises:
        FileNotFoundError: Manifest does not exist on disk.
        ValueError: Manifest exists but is missing required structure.
        json.JSONDecodeError: Manifest exists but is not valid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}\n"
            f"Run 'python scripts/build_manifest.py' first to generate it."
        )

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest_data = json.load(manifest_file)

    # Validate required keys — fail fast and clearly rather than failing deep
    required_keys = {"entries", "total_files", "total_words"}
    missing_keys = required_keys - set(manifest_data.keys())
    if missing_keys:
        raise ValueError(
            f"Manifest at '{manifest_path}' is missing required keys: {missing_keys}.\n"
            f"The manifest may be from an older schema version. "
            f"Re-run 'python scripts/build_manifest.py' to regenerate it."
        )

    logger.info(
        f"Manifest loaded: {manifest_data['total_files']} files | "
        f"{manifest_data['total_words']:,} words."
    )
    return manifest_data


def load_tokenizer_for_model(model_name: str) -> PreTrainedTokenizerBase:
    """
    Mental Model:
        Downloads (or loads from HuggingFace cache) the tokenizer for the
        specified model. Only the tokenizer is needed locally — the full model
        weights stay on Colab. Tokenizer files are a few MB, not gigabytes.

        Gemma 3 requires accepting a license on HuggingFace before download.
        If authentication fails, we print a clear step-by-step recovery
        instruction. A confused error message at startup wastes hours.

    Args:
        model_name: HuggingFace model identifier, e.g. "google/gemma-3-4b-it".

    Returns:
        PreTrainedTokenizerBase: Loaded tokenizer, ready to encode and decode.

    Raises:
        SystemExit(1): On any unrecoverable tokenizer load failure.
                       We exit here because chunking without a tokenizer
                       is not possible — there is nothing to recover from.
    """
    logger.info(f"Loading tokenizer for model: {model_name} ...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info(f"Tokenizer ready. Vocab size: {tokenizer.vocab_size:,}")
        return tokenizer

    except OSError as os_error:
        # OSError from transformers almost always means auth failure for gated models
        logger.error(
            f"\n{'=' * 60}\n"
            f"TOKENIZER LOAD FAILED for '{model_name}'\n"
            f"{'=' * 60}\n"
            f"Error: {os_error}\n\n"
            f"If this is a HuggingFace authentication error:\n"
            f"  1. Go to https://huggingface.co/{model_name}\n"
            f"  2. Accept the license agreement (one-time step).\n"
            f"  3. Run: huggingface-cli login\n"
            f"  4. Paste your HuggingFace token when prompted.\n"
            f"  5. Re-run this script.\n\n"
            f"If you are offline, ensure the model is already cached locally.\n"
            f"{'=' * 60}"
        )
        sys.exit(1)

    except Exception as unexpected_error:
        logger.error(
            f"Unexpected error loading tokenizer for '{model_name}': {unexpected_error}"
        )
        sys.exit(1)


def extract_body_content_from_markdown(raw_file_content: str) -> str:
    """
    Mental Model:
        Strips the YAML frontmatter from a markdown file and returns only
        the body content. Frontmatter is metadata (title, date, category) —
        not semantic content. Chunking it would pollute embeddings and
        inject metadata noise into training examples.

        Uses python-frontmatter for robust YAML parsing. Falls back to
        the full content if parsing fails — impure text beats lost content.

    Args:
        raw_file_content: Full file text, potentially including YAML frontmatter.

    Returns:
        str: Body content only, stripped of leading/trailing whitespace.
             If no frontmatter is present, returns content unchanged.
    """
    try:
        parsed_document = frontmatter.loads(raw_file_content)
        return parsed_document.content.strip()
    except Exception:
        # Frontmatter parsing failure is non-fatal — return full content
        return raw_file_content.strip()


# ---------------------------------------------------------------------------
# Core chunking logic
# ---------------------------------------------------------------------------

def compute_sliding_window_boundaries(
    total_token_count: int,
    config: ChunkConfig,
) -> list[tuple[int, int]]:
    """
    Mental Model:
        Produces (start, end) index pairs for a sliding window over a
        token sequence. The stride is: chunk_size - overlap.
        This ensures consecutive chunks share 'overlap' tokens at their
        boundary — preventing hard semantic cuts mid-sentence.

        Think of reading with a moving magnifying glass: each new position
        steps forward by 'stride', but starts a few tokens back from where
        the last window ended. No meaning is lost at the seams.

    Args:
        total_token_count: Length of the full token ID list for the document.
        config: ChunkConfig carrying chunk_size_tokens and overlap_tokens.

    Returns:
        list[tuple[int, int]]: (start_index, end_index) pairs.
                               The final chunk end_index equals total_token_count.
                               Returns [] if total_token_count is 0.

    Scale Note:
        O(n / stride) iterations — effectively O(n / chunk_size) for small overlaps.
        Safe for any document size in this corpus.
    """
    if total_token_count == 0:
        return []

    stride = config.chunk_size_tokens - config.overlap_tokens
    boundaries: list[tuple[int, int]] = []
    start_index = 0

    while start_index < total_token_count:
        end_index = min(start_index + config.chunk_size_tokens, total_token_count)
        boundaries.append((start_index, end_index))

        # Stop once we've captured the final token
        if end_index == total_token_count:
            break

        start_index += stride

    return boundaries


def produce_chunk_records_from_file(
    manifest_entry: dict,
    tokenizer: PreTrainedTokenizerBase,
    config: ChunkConfig,
) -> list[ChunkRecord]:
    """
    Mental Model:
        Produces a list of ChunkRecords for one corpus file under one config.

        Pipeline for a single file:
          1. Resolve the absolute file path from the manifest's relative path.
          2. Read the file and strip YAML frontmatter.
          3. Tokenize the body content (no special tokens — added by trainer).
          4. Compute sliding window boundaries over the token IDs.
          5. Decode each window back to text.
          6. Wrap in ChunkRecord with deterministic chunk_id.

        chunk_id format: {sha256[:8]}_{purpose}_{chunk_index:04d}
        Deterministic: same corpus + same config = same IDs every run.

    Args:
        manifest_entry: One entry from corpus_manifest.json['entries'].
        tokenizer: Loaded Gemma tokenizer.
        config: ChunkConfig (rag or pretrain) for this pass.

    Returns:
        list[ChunkRecord]: All chunks for this file. Empty if file is
                           unreadable, empty, or produces zero tokens.

    Note:
        Does not raise. All exceptions are caught, logged, and return [].
        One bad file must never halt the pipeline.
    """
    source_path_relative = manifest_entry.get("path", "")
    source_sha256 = manifest_entry.get("sha256", "unknown")
    source_pillar = manifest_entry.get("pillar", "unknown")
    sha256_prefix = source_sha256[:8]

    # Resolve to absolute path — manifest stores paths relative to project root
    absolute_file_path = PROJECT_ROOT / source_path_relative

    if not absolute_file_path.exists():
        logger.warning(
            f"File in manifest not found on disk: {absolute_file_path}. "
            f"Was it deleted after the manifest was built? Skipping."
        )
        return []

    try:
        raw_content = absolute_file_path.read_text(encoding="utf-8")
    except OSError as read_error:
        logger.warning(
            f"Could not read '{absolute_file_path}': {read_error}. Skipping."
        )
        return []

    body_content = extract_body_content_from_markdown(raw_content)

    if not body_content:
        logger.warning(
            f"Empty body after frontmatter strip: '{source_path_relative}'. "
            f"Nothing to chunk — skipping."
        )
        return []

    # Tokenize once. add_special_tokens=False because BOS/EOS are added
    # by the training data collator at training time, not at chunking time.
    token_ids: list[int] = tokenizer.encode(body_content, add_special_tokens=False)

    if not token_ids:
        logger.warning(
            f"Tokenizer produced zero tokens for '{source_path_relative}'. Skipping."
        )
        return []

    chunk_boundaries = compute_sliding_window_boundaries(len(token_ids), config)

    chunk_records: list[ChunkRecord] = []
    for chunk_index, (start_token, end_token) in enumerate(chunk_boundaries):
        window_token_ids = token_ids[start_token:end_token]
        chunk_text = tokenizer.decode(window_token_ids, skip_special_tokens=True)

        chunk_records.append(
            ChunkRecord(
                chunk_id=f"{sha256_prefix}_{config.purpose}_{chunk_index:04d}",
                source_sha256=source_sha256,
                source_path=source_path_relative,
                pillar=source_pillar,
                chunk_index=chunk_index,
                token_count=len(window_token_ids),
                text=chunk_text,
            )
        )

    return chunk_records


def process_single_corpus_file(
    manifest_entry: dict,
    tokenizer: PreTrainedTokenizerBase,
    rag_config: ChunkConfig,
    pretrain_config: ChunkConfig,
    active_purposes: set[str],
) -> FileProcessingResult:
    """
    Mental Model:
        Orchestrator for a single file. Calls produce_chunk_records_from_file
        once per active purpose (rag, pretrain, or both). Wraps results in a
        FileProcessingResult — never raises, always returns something.

        The separation of concerns here is deliberate:
          This function decides what to run.
          produce_chunk_records_from_file decides how to chunk.
          build_full_chunks_index decides how to aggregate.

    Args:
        manifest_entry:  One entry from corpus_manifest.json['entries'].
        tokenizer:       Loaded Gemma tokenizer.
        rag_config:      ChunkConfig for RAG purpose.
        pretrain_config: ChunkConfig for pretrain purpose.
        active_purposes: Set of {"rag"}, {"pretrain"}, or {"rag", "pretrain"}.

    Returns:
        FileProcessingResult: Contains chunk lists for each active purpose,
                              plus skip metadata if no chunks were produced.
    """
    source_path = manifest_entry.get("path", "unknown")
    result = FileProcessingResult(source_path=source_path)

    try:
        if "rag" in active_purposes:
            result.rag_chunks = produce_chunk_records_from_file(
                manifest_entry, tokenizer, rag_config
            )

        if "pretrain" in active_purposes:
            result.pretrain_chunks = produce_chunk_records_from_file(
                manifest_entry, tokenizer, pretrain_config
            )

        total_chunks_produced = len(result.rag_chunks) + len(result.pretrain_chunks)
        if total_chunks_produced == 0:
            result.was_skipped = True
            result.skip_reason = "No chunks produced — file may be empty or unreadable."

    except Exception as unexpected_error:
        # Catch-all: one bad file must never kill the entire pipeline.
        # Log the error and mark as skipped — the show goes on.
        result.was_skipped = True
        result.skip_reason = str(unexpected_error)
        logger.warning(
            f"Unexpected error processing '{source_path}': {unexpected_error}. "
            f"Skipping this file."
        )

    return result


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def build_full_chunks_index(
    manifest_data: dict,
    tokenizer: PreTrainedTokenizerBase,
    rag_config: ChunkConfig,
    pretrain_config: ChunkConfig,
    active_purposes: set[str],
    model_name: str,
) -> ChunksIndex:
    """
    Mental Model:
        Main pipeline loop. Iterates over every file in the manifest,
        delegates to process_single_corpus_file, and assembles the full
        ChunksIndex. Shows a tqdm progress bar so progress is visible.

        This function is the conductor — it coordinates and aggregates,
        but does not perform the chunking work itself.

    Args:
        manifest_data:    Full parsed manifest from load_corpus_manifest.
        tokenizer:        Loaded Gemma tokenizer.
        rag_config:       ChunkConfig for RAG purpose.
        pretrain_config:  ChunkConfig for pretrain purpose.
        active_purposes:  Which purposes to run this pass.
        model_name:       Stored in the index metadata for traceability.

    Returns:
        ChunksIndex: Complete index, ready for JSON serialization.

    Scale Note:
        Memory: all chunks are held in RAM during this call.
        For 134 files × ~356k words, expect chunks_index.json to be
        roughly 20–80 MB depending on chunk size and overlap settings.
        This is comfortably within Colab Free's RAM budget.
    """
    corpus_entries = manifest_data.get("entries", [])
    all_rag_chunks: list[ChunkRecord] = []
    all_pretrain_chunks: list[ChunkRecord] = []
    skipped_file_count = 0

    logger.info(
        f"Pipeline starting | "
        f"Files: {len(corpus_entries)} | "
        f"Purposes: {active_purposes} | "
        f"RAG size: {rag_config.chunk_size_tokens} tokens "
        f"(overlap: {rag_config.overlap_tokens}) | "
        f"Pretrain size: {pretrain_config.chunk_size_tokens} tokens "
        f"(overlap: {pretrain_config.overlap_tokens})"
    )

    for manifest_entry in tqdm(corpus_entries, desc="Chunking corpus", unit="file"):
        file_result = process_single_corpus_file(
            manifest_entry=manifest_entry,
            tokenizer=tokenizer,
            rag_config=rag_config,
            pretrain_config=pretrain_config,
            active_purposes=active_purposes,
        )

        if file_result.was_skipped:
            skipped_file_count += 1
            continue

        all_rag_chunks.extend(file_result.rag_chunks)
        all_pretrain_chunks.extend(file_result.pretrain_chunks)

    files_processed = len(corpus_entries) - skipped_file_count

    logger.info(
        f"Pipeline complete | "
        f"Processed: {files_processed} files | "
        f"Skipped: {skipped_file_count} files | "
        f"RAG chunks: {len(all_rag_chunks):,} | "
        f"Pretrain chunks: {len(all_pretrain_chunks):,}"
    )

    return ChunksIndex(
        schema_version=1,
        model=model_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        rag_config=rag_config,
        pretrain_config=pretrain_config,
        total_files_processed=files_processed,
        total_files_skipped=skipped_file_count,
        total_rag_chunks=len(all_rag_chunks),
        total_pretrain_chunks=len(all_pretrain_chunks),
        rag_chunks=all_rag_chunks,
        pretrain_chunks=all_pretrain_chunks,
    )


# ---------------------------------------------------------------------------
# Serialization and output
# ---------------------------------------------------------------------------

def serialize_chunks_index(chunks_index: ChunksIndex) -> dict:
    """
    Mental Model:
        Converts the ChunksIndex dataclass tree to a plain dict for JSON.
        dataclasses.asdict() recursively handles nested dataclasses
        (ChunkConfig, ChunkRecord), so no manual traversal is needed.

    Args:
        chunks_index: The assembled ChunksIndex dataclass.

    Returns:
        dict: JSON-serializable representation of the full index.
    """
    return asdict(chunks_index)


def save_chunks_index_to_disk(serialized_index: dict, output_path: Path) -> None:
    """
    Mental Model:
        Writes the serialized index to disk as UTF-8 JSON with 2-space indent.
        Creates parent directories if they do not exist (idempotent).
        Reports the output file size so the scale of the artifact is visible.

    Args:
        serialized_index: Plain dict from serialize_chunks_index.
        output_path:      Absolute path for the output JSON file.

    Raises:
        OSError: If the file cannot be written. Propagated with a clear message
                 so the user knows whether it is a permissions or disk issue.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(serialized_index, output_file, ensure_ascii=False, indent=2)

        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"Chunks index saved: {output_path} ({file_size_mb:.2f} MB)"
        )

    except OSError as write_error:
        logger.error(
            f"Failed to write chunks index to '{output_path}': {write_error}.\n"
            f"Check disk space and write permissions."
        )
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_cli_arguments() -> argparse.Namespace:
    """
    Mental Model:
        Defines the command-line interface. All defaults are tuned for
        Gemma 3 4B on Colab Free. Every parameter is overridable without
        touching the code — future Cosmos can adjust chunk sizes as
        experiments reveal better values.

    Returns:
        argparse.Namespace: Parsed args with all defaults applied.
    """
    parser = argparse.ArgumentParser(
        prog="build_chunks.py",
        description=(
            "SophiaAI Phase 2 — Tokenize and chunk the sophia_engine corpus.\n"
            f"Default model: {DEFAULT_MODEL_NAME}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help=f"HuggingFace model ID for tokenizer. Default: {DEFAULT_MODEL_NAME}",
    )
    parser.add_argument(
        "--rag-size",
        type=int,
        default=DEFAULT_RAG_CHUNK_SIZE_TOKENS,
        help=f"Max tokens per RAG chunk. Default: {DEFAULT_RAG_CHUNK_SIZE_TOKENS}",
    )
    parser.add_argument(
        "--rag-overlap",
        type=int,
        default=DEFAULT_RAG_OVERLAP_TOKENS,
        help=f"Overlap tokens for RAG chunks. Default: {DEFAULT_RAG_OVERLAP_TOKENS}",
    )
    parser.add_argument(
        "--pretrain-size",
        type=int,
        default=DEFAULT_PRETRAIN_CHUNK_SIZE_TOKENS,
        help=f"Max tokens per pretrain chunk. Default: {DEFAULT_PRETRAIN_CHUNK_SIZE_TOKENS}",
    )
    parser.add_argument(
        "--pretrain-overlap",
        type=int,
        default=DEFAULT_PRETRAIN_OVERLAP_TOKENS,
        help=f"Overlap tokens for pretrain chunks. Default: {DEFAULT_PRETRAIN_OVERLAP_TOKENS}",
    )
    parser.add_argument(
        "--purpose",
        type=str,
        choices=["rag", "pretrain", "both"],
        default="both",
        help="Which chunk type(s) to produce. Default: both",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Path to corpus_manifest.json. Default: {DEFAULT_MANIFEST_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output path for chunks_index.json. Default: {DEFAULT_OUTPUT_PATH}",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Mental Model:
        Entry point and top-level orchestrator. Parses CLI args, builds
        configs, loads inputs, runs the pipeline, saves the output.
        Every sub-step is delegated to a single-responsibility function.

        This function sees the whole system — it does not touch tokenization,
        file reading, or chunking directly. It coordinates and steps aside.

        Exit codes:
          0 — success, chunks_index.json written to disk.
          1 — unrecoverable startup error (missing manifest, tokenizer failure).
    """
    args = parse_cli_arguments()

    # Map --purpose arg to a set of strings for downstream checks
    active_purposes: set[str] = (
        {"rag", "pretrain"} if args.purpose == "both" else {args.purpose}
    )

    # Build and validate configs — __post_init__ catches bad values immediately
    rag_config = ChunkConfig(
        purpose="rag",
        chunk_size_tokens=args.rag_size,
        overlap_tokens=args.rag_overlap,
    )
    pretrain_config = ChunkConfig(
        purpose="pretrain",
        chunk_size_tokens=args.pretrain_size,
        overlap_tokens=args.pretrain_overlap,
    )

    # Load required inputs — both can exit(1) with clear messages on failure
    manifest_data = load_corpus_manifest(args.manifest)
    tokenizer = load_tokenizer_for_model(args.model)

    # Run the chunking pipeline
    chunks_index = build_full_chunks_index(
        manifest_data=manifest_data,
        tokenizer=tokenizer,
        rag_config=rag_config,
        pretrain_config=pretrain_config,
        active_purposes=active_purposes,
        model_name=args.model,
    )

    # Serialize and write to disk
    serialized_index = serialize_chunks_index(chunks_index)
    save_chunks_index_to_disk(serialized_index, args.output)

    logger.info(
        "Phase 2 complete. Sophia's corpus is chunked, tokenized, and ready.\n"
        f"  RAG chunks   → Phase 6 (RAG pipeline)\n"
        f"  Pretrain chunks → Phase 3 (Colab training)"
    )


if __name__ == "__main__":
    main()
