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

Run from the project root:

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


# ── Constants ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "data" / "sophia_engine"
MANIFEST_PATH = PROJECT_ROOT / "data" / "corpus_manifest.json"
PILLARS = ("mind", "philosophy", "spirit", "science")
SCHEMA_VERSION = 1


# ── Data shapes ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class CorpusEntry:
    """One record per .md file in the corpus."""
    path: str
    pillar: str
    filename: str
    word_count: int
    char_count: int
    sha256: str
    frontmatter: dict | None


@dataclass(frozen=True)
class Manifest:
    """The full document that gets serialized to JSON."""
    schema_version: int
    generated_at: str
    corpus_root: str
    total_files: int
    total_words: int
    entries: list[CorpusEntry]


# ── Pure helpers ────────────────────────────────────────────────────
def find_corpus_files(corpus_dir: Path) -> list[Path]:
    """Return every .md file under the corpus, sorted for deterministic output."""
    return sorted(corpus_dir.rglob("*.md"))


def detect_pillar(file_path: Path, corpus_dir: Path) -> str:
    """The pillar is the first directory under corpus_dir."""
    relative = file_path.relative_to(corpus_dir)
    return relative.parts[0]


def compute_sha256(text: str) -> str:
    """Hash a UTF-8 string and return its hex digest."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_entry(file_path: Path) -> CorpusEntry:
    """Read one file from disk and turn it into a CorpusEntry.

    If the frontmatter is malformed YAML, we log a warning, skip the
    frontmatter parsing, and treat the whole file as the body. The
    pipeline must never die because of one bad file — it must report,
    recover, and continue.
    """
    raw_text = file_path.read_text(encoding="utf-8")
    relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

    try:
        parsed = frontmatter.loads(raw_text)
        body = parsed.content
        metadata = dict(parsed.metadata) if parsed.metadata else None
    except Exception as exc:
        print(f"  WARNING: frontmatter parse failed for {relative_path} ({exc.__class__.__name__})")
        body = raw_text
        metadata = None

    return CorpusEntry(
        path=relative_path,
        pillar=detect_pillar(file_path, CORPUS_DIR),
        filename=file_path.name,
        word_count=len(body.split()),
        char_count=len(body),
        sha256=compute_sha256(raw_text),
        frontmatter=metadata,
    )


# ── Orchestration ───────────────────────────────────────────────────
def build_manifest() -> Manifest:
    """Walk the corpus and produce the full manifest in memory."""
    files = find_corpus_files(CORPUS_DIR)
    entries = [build_entry(f) for f in files]
    return Manifest(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        corpus_root=CORPUS_DIR.relative_to(PROJECT_ROOT).as_posix(),
        total_files=len(entries),
        total_words=sum(e.word_count for e in entries),
        entries=entries,
    )


def _json_default(value: object) -> str:
    """Translate Python-only types into JSON-friendly strings at the I/O boundary.

    PyYAML auto-converts ISO-like strings (dates, datetimes, times) in the
    frontmatter into native Python objects. JSON has no native concept of
    a date, so we convert them to ISO 8601 strings here — the universal
    interchange format for temporal data.
    """
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_manifest(manifest: Manifest, output_path: Path) -> None:
    """Serialize the manifest to JSON on disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(
            asdict(manifest),
            handle,
            indent=2,
            ensure_ascii=False,
            default=_json_default,
        )


def print_summary(manifest: Manifest) -> None:
    """Print a human-readable report so we can see the shape of the corpus."""
    print(f"\nCorpus manifest written.")
    print(f"  Files:  {manifest.total_files}")
    print(f"  Words:  {manifest.total_words:,}")
    print()
    print("By pillar:")
    for pillar in PILLARS:
        entries_in_pillar = [e for e in manifest.entries if e.pillar == pillar]
        words_in_pillar = sum(e.word_count for e in entries_in_pillar)
        share = (words_in_pillar / manifest.total_words * 100) if manifest.total_words else 0
        print(
            f"  {pillar:<11} "
            f"{len(entries_in_pillar):>3} files  "
            f"{words_in_pillar:>8,} words  "
            f"({share:5.1f}%)"
        )

    unknown = [e for e in manifest.entries if e.pillar not in PILLARS]
    if unknown:
        print(f"\nWARNING — {len(unknown)} file(s) in unexpected pillar(s):")
        for entry in unknown:
            print(f"  {entry.path}  (pillar='{entry.pillar}')")


# ── Entry point ─────────────────────────────────────────────────────
def main() -> None:
    print(f"Scanning corpus at {CORPUS_DIR.relative_to(PROJECT_ROOT)} ...")
    manifest = build_manifest()
    write_manifest(manifest, MANIFEST_PATH)
    print(f"Saved to {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    print_summary(manifest)


if __name__ == "__main__":
    main()
