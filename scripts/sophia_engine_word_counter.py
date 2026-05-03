"""
Word Counter — SophiaAI Knowledge Base
=======================================
Counts words per category in data/sophia_engine/, skipping YAML frontmatter.
Run: python scripts/sophia_engine_word_counter.py
"""

import re
from pathlib import Path
from collections import defaultdict


# ─── Parsing ──────────────────────────────────────────────────────────────────


def strip_yaml_frontmatter(raw_markdown_text: str) -> str:
    """
    Mental Model:
        YAML frontmatter lives between the first and second '---' delimiters.
        We skip everything before the closing '---' and return only the body.
        If no frontmatter is found, the full text is returned unchanged.

    Args:
        raw_markdown_text: The full contents of a markdown file.

    Returns:
        The markdown body without YAML frontmatter.
    """
    frontmatter_delimiter = "---"

    if not raw_markdown_text.startswith(frontmatter_delimiter):
        return raw_markdown_text

    closing_delimiter_position = raw_markdown_text.find(frontmatter_delimiter, 3)

    if closing_delimiter_position == -1:
        # No closing delimiter found — treat whole file as body
        return raw_markdown_text

    return raw_markdown_text[closing_delimiter_position + 3 :]


def count_words_in_text(body_text: str) -> int:
    """
    Mental Model:
        Splits the text into word tokens using a simple word-boundary regex.
        Matches any sequence of alphanumeric characters (including underscores).

    Args:
        body_text: Plain text with no YAML frontmatter.

    Returns:
        Integer count of word tokens found in the text.
    """
    word_tokens = re.findall(r"\b\w+\b", body_text)
    return len(word_tokens)


# ─── Collection ───────────────────────────────────────────────────────────────


def collect_word_counts_by_category(raw_data_directory: Path) -> dict:
    """
    Mental Model:
        Walks all .md files under raw_data_directory recursively.
        Each file's parent folder name is treated as its category.
        Strips frontmatter, counts words, and accumulates per category.

    Args:
        raw_data_directory: Path to the data/raw/ folder.

    Returns:
        A dict keyed by category name, each value a dict with
        'word_count' and 'file_count'.

    Raises:
        FileNotFoundError: If raw_data_directory does not exist.
    """
    if not raw_data_directory.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_data_directory}\n"
            f"Expected at: {raw_data_directory.resolve()}"
        )

    category_stats = defaultdict(lambda: {"word_count": 0, "file_count": 0})

    for markdown_file in sorted(raw_data_directory.rglob("*.md")):
        category_name = markdown_file.parent.name
        raw_text = markdown_file.read_text(encoding="utf-8", errors="ignore")

        body_text = strip_yaml_frontmatter(raw_text)
        word_count = count_words_in_text(body_text)

        category_stats[category_name]["word_count"] += word_count
        category_stats[category_name]["file_count"] += 1

    return dict(category_stats)


# ─── Display ──────────────────────────────────────────────────────────────────


def display_word_count_report(category_stats: dict) -> None:
    """
    Mental Model:
        Renders a formatted table sorted by word count descending.
        Each row shows category name, file count, word count, and percentage.
        A total row is appended at the bottom.

    Args:
        category_stats: Output of collect_word_counts_by_category().

    Returns:
        None. Prints directly to stdout.
    """
    total_words = sum(stats["word_count"] for stats in category_stats.values())
    total_files = sum(stats["file_count"] for stats in category_stats.values())

    categories_sorted_by_word_count = sorted(
        category_stats.items(),
        key=lambda item: item[1]["word_count"],
        reverse=True,
    )

    column_header = f"\n  {'CATEGORY':<16} {'FILES':>6}   {'WORDS':>8}   {'SHARE':>6}"
    separator_line = "  " + "-" * 44

    print(column_header)
    print(separator_line)

    for category_name, stats in categories_sorted_by_word_count:
        word_count = stats["word_count"]
        file_count = stats["file_count"]
        percentage = (word_count / total_words * 100) if total_words else 0

        print(
            f"  {category_name:<16} {file_count:>6}   {word_count:>8}   {percentage:>5.1f}%"
        )

    print(separator_line)
    print(f"  {'TOTAL':<16} {total_files:>6}   {total_words:>8}   100.0%\n")


# ─── Entry Point ──────────────────────────────────────────────────────────────


def main() -> None:
    """
    Mental Model:
        Resolves the raw data path relative to this script's location,
        collects stats, and renders the report.
        Script can be run from any working directory.
    """
    scripts_directory = Path(__file__).parent
    raw_data_directory = scripts_directory.parent / "data" / "sophia_engine"

    category_stats = collect_word_counts_by_category(raw_data_directory)
    display_word_count_report(category_stats)


if __name__ == "__main__":
    main()
