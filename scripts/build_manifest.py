"""
build_manifest.py — Build the corpus manifest for SophiaAI.

The manifest is the single source of truth that every downstream pipeline
(fine-tuning, RAG indexing, evaluation) uses to enumerate the corpus.

For every .md file under data/sophia_engine/ we record:
  - path:         relative path from the project root (stable identifier)
  - pillar:       one of {mind, philosophy, spirit, science}
  - filename:     just the basename
  - word_count:   whitespace-separated tokens in the body
  - char_count:   character count of the body
  - sha256:       hash of the full file contents (change detector)
  - frontmatter:  parsed YAML frontmatter, or null if the file has none

Why a manifest at all?
    Without one, every downstream tool would have to walk the filesystem
    on its own, and there would be no shared notion of "what the corpus
    is right now". The manifest is a frozen photograph — a single moment
    of truth that pipelines can trust.

Run from the project root, with the venv activated:

    python scripts/build_manifest.py

Output: data/corpus_manifest.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path

import frontmatter


# ── Constants ───────────────────────────────────────────────────────────
# PROJECT_ROOT resolves to the SophiaAI/ folder, regardless of where the
# script is invoked from. Using __file__ + .resolve() means the script can
# be called from any cwd without breaking — a small ZenCode courtesy.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIRECTORY = PROJECT_ROOT / "data" / "sophia_engine"
MANIFEST_OUTPUT_PATH = PROJECT_ROOT / "data" / "corpus_manifest.json"

# The four canonical pillars of the corpus, in the conceptual order
# perceive → reason → feel → verify. Order is preserved in the summary
# report so the human reader sees the same shape every run.
CANONICAL_PILLARS = ("mind", "philosophy", "spirit", "science")

# Bump this when the manifest schema changes in a backward-incompatible
# way. Downstream pipelines can branch on schema_version if needed.
MANIFEST_SCHEMA_VERSION = 1


# ── Data shapes ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CorpusEntry:
    """One record per .md file in the corpus.

    Frozen so that no downstream code can mutate an entry by accident —
    the manifest is meant to be read, not edited in place.
    """

    path: str
    pillar: str
    filename: str
    word_count: int
    char_count: int
    sha256: str
    frontmatter: dict | None


@dataclass(frozen=True)
class Manifest:
    """The full document that gets serialized to JSON.

    Contains both per-file entries and aggregate counts so a human can
    glance at the manifest itself (without loading any other tool) and
    understand the shape of the corpus.
    """

    schema_version: int
    generated_at: str
    corpus_root: str
    total_files: int
    total_words: int
    entries: list[CorpusEntry]


# ── Pure helpers ────────────────────────────────────────────────────────
def find_all_markdown_files(corpus_directory: Path) -> list[Path]:
    """Locate every .md file in the corpus and return them in a stable order.

    Mental Model:
        Walks the corpus directory tree recursively and collects every
        markdown file. The result is sorted alphabetically by path so
        that two runs over the same corpus produce byte-identical
        manifests. Determinism is the foundation of reproducibility.

    Args:
        corpus_directory: The root of the corpus tree (data/sophia_engine).

    Returns:
        A sorted list of absolute paths to every .md file found.
    """
    return sorted(corpus_directory.rglob("*.md"))


def detect_pillar_for_file(file_path: Path, corpus_directory: Path) -> str:
    """Infer which pillar (mind/philosophy/spirit/science) a file belongs to.

    Mental Model:
        The pillar is encoded structurally — it is simply the first
        directory under the corpus root. No string parsing or guessing
        is needed. This works because the corpus enforces the four-pillar
        layout as a contract.

    Args:
        file_path: Absolute path to a .md file inside the corpus.
        corpus_directory: The root of the corpus tree.

    Returns:
        The pillar name (e.g. "philosophy", "science").
    """
    path_relative_to_corpus = file_path.relative_to(corpus_directory)
    return path_relative_to_corpus.parts[0]


def compute_sha256_hex_digest(text: str) -> str:
    """Compute a SHA-256 fingerprint of a UTF-8 string.

    Mental Model:
        Used as a change detector. If a single character of the file
        changes, the hash is completely different. Downstream pipelines
        can compare hashes to know which files need reprocessing — like
        a forensic detective fingerprinting each document.

    Args:
        text: Any UTF-8 string (typically the full contents of a file).

    Returns:
        A 64-character hexadecimal string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_entry_from_file(file_path: Path) -> CorpusEntry:
    """Read one corpus file from disk and produce a structured CorpusEntry.

    Mental Model:
        Reads the raw file, attempts to parse YAML frontmatter, and
        extracts counts and a fingerprint. If the frontmatter is
        malformed, we log a warning and treat the entire file as body
        text — the pipeline must never die because of one bad file.
        It must report, recover, and continue. This is resilience by
        design, not by accident.

    Args:
        file_path: Absolute path to a single .md file in the corpus.

    Returns:
        A frozen CorpusEntry with path, pillar, counts, hash, and
        optional frontmatter dict.
    """
    raw_file_text = file_path.read_text(encoding="utf-8")
    path_relative_to_project_root = file_path.relative_to(PROJECT_ROOT).as_posix()

    try:
        parsed_document = frontmatter.loads(raw_file_text)
        body_text = parsed_document.content
        frontmatter_metadata = (
            dict(parsed_document.metadata) if parsed_document.metadata else None
        )
    except Exception as frontmatter_parse_failure:
        # We deliberately catch broadly: any failure inside the YAML
        # parser is treated as "this file has no usable metadata". The
        # warning surfaces the path so the human can fix the source.
        print(
            f"  WARNING: frontmatter parse failed for "
            f"{path_relative_to_project_root} "
            f"({frontmatter_parse_failure.__class__.__name__})"
        )
        body_text = raw_file_text
        frontmatter_metadata = None

    return CorpusEntry(
        path=path_relative_to_project_root,
        pillar=detect_pillar_for_file(file_path, CORPUS_DIRECTORY),
        filename=file_path.name,
        word_count=len(body_text.split()),
        char_count=len(body_text),
        # We hash the full raw file (not just the body) so that any edit
        # to the frontmatter also flips the fingerprint. One file, one
        # signature, one truth.
        sha256=compute_sha256_hex_digest(raw_file_text),
        frontmatter=frontmatter_metadata,
    )


# ── Orchestration ───────────────────────────────────────────────────────
def build_complete_manifest() -> Manifest:
    """Walk the corpus and produce the full manifest in memory.

    Mental Model:
        The conductor function. It does not perform the work itself —
        it delegates to the specialists (find files, build entries) and
        assembles the final document with timestamps and aggregate
        counts. This is "One Function, One Responsibility" applied at
        the orchestration layer.

    Returns:
        A Manifest object ready to be serialized to JSON.
    """
    all_markdown_files = find_all_markdown_files(CORPUS_DIRECTORY)
    corpus_entries = [build_entry_from_file(file_path) for file_path in all_markdown_files]

    return Manifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        corpus_root=CORPUS_DIRECTORY.relative_to(PROJECT_ROOT).as_posix(),
        total_files=len(corpus_entries),
        total_words=sum(entry.word_count for entry in corpus_entries),
        entries=corpus_entries,
    )


# ── I/O boundary ────────────────────────────────────────────────────────
def serialize_non_json_native_value(value: object) -> str:
    """Translate Python-only types into JSON-friendly strings at the boundary.

    Mental Model:
        PyYAML auto-converts ISO-like strings (dates, datetimes, times)
        in the frontmatter into native Python objects. JSON has no
        native concept of a date, so we convert them to ISO 8601 strings
        here — the universal interchange format for temporal data.

        ZenCode principle: convert at the boundary, not throughout the
        code. One translator at the edge, not a hundred translators
        scattered everywhere.

    Args:
        value: Any object that the default JSON encoder cannot serialize.

    Returns:
        An ISO 8601 string representation of the temporal value.

    Raises:
        TypeError: If the value is of a type we do not know how to
            serialize. The error message names the exact type so the
            human can decide whether to extend this translator.
    """
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()

    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable. "
        f"Extend serialize_non_json_native_value() to handle this type."
    )


def write_manifest_to_disk(manifest: Manifest, output_path: Path) -> None:
    """Serialize the manifest to a JSON file on disk.

    Mental Model:
        The single point in the program where state crosses the boundary
        from memory to filesystem. We use indent=2 because the manifest
        is meant to be human-readable; ensure_ascii=False because the
        corpus is bilingual (ES/EN) and we want native characters, not
        escaped sequences.

    Args:
        manifest: The fully-built Manifest object to write.
        output_path: Where the JSON file should be created. The parent
            directory will be created if it does not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as json_file_handle:
        json.dump(
            asdict(manifest),
            json_file_handle,
            indent=2,
            ensure_ascii=False,
            default=serialize_non_json_native_value,
        )


# ── Reporting ───────────────────────────────────────────────────────────
def print_corpus_summary_report(manifest: Manifest) -> None:
    """Print a human-readable summary of the corpus to the terminal.

    Mental Model:
        The "telescope" — after generating the manifest, we want a quick
        glance at the shape of the corpus. How many files? How many words?
        Is the balance across pillars healthy? Any files in unexpected
        locations? The report answers these in three seconds of reading.

    Args:
        manifest: The fully-built Manifest object to summarize.
    """
    print()
    print(f"Corpus manifest written.")
    print(f"  Files:  {manifest.total_files}")
    print(f"  Words:  {manifest.total_words:,}")
    print()
    print("By pillar:")

    for pillar_name in CANONICAL_PILLARS:
        entries_in_this_pillar = [
            entry for entry in manifest.entries if entry.pillar == pillar_name
        ]
        words_in_this_pillar = sum(entry.word_count for entry in entries_in_this_pillar)

        # Guard against zero division on an empty corpus — better to print
        # 0.0% than to crash on a freshly initialized repo.
        share_of_total_corpus = (
            (words_in_this_pillar / manifest.total_words * 100)
            if manifest.total_words
            else 0
        )

        print(
            f"  {pillar_name:<11} "
            f"{len(entries_in_this_pillar):>3} files  "
            f"{words_in_this_pillar:>8,} words  "
            f"({share_of_total_corpus:5.1f}%)"
        )

    # Any file outside the four canonical pillars is a structural anomaly.
    # We surface it loudly so the human can decide where it really belongs.
    entries_in_unknown_pillars = [
        entry for entry in manifest.entries if entry.pillar not in CANONICAL_PILLARS
    ]
    if entries_in_unknown_pillars:
        print(
            f"\nWARNING — {len(entries_in_unknown_pillars)} "
            f"file(s) in unexpected pillar(s):"
        )
        for entry in entries_in_unknown_pillars:
            print(f"  {entry.path}  (pillar='{entry.pillar}')")


# ── Entry point ─────────────────────────────────────────────────────────
def main() -> None:
    """Run the full Phase 1 pipeline: scan, build, write, report.

    Mental Model:
        The orchestration of orchestrations. Four steps, each delegated
        to a single-responsibility helper. If you want to know what this
        script does at a glance, read these four lines.
    """
    print(f"Scanning corpus at {CORPUS_DIRECTORY.relative_to(PROJECT_ROOT)} ...")

    manifest = build_complete_manifest()
    write_manifest_to_disk(manifest, MANIFEST_OUTPUT_PATH)

    print(f"Saved to {MANIFEST_OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print_corpus_summary_report(manifest)


if __name__ == "__main__":
    main()
