import type { CorpusDocOut, SourceOut } from "./types";

/**
 * Mental Model:
 *   Small pure formatters shared by the chat and the Mind panel. Kept in one
 *   place so a year, a word count, or a document title always reads the same
 *   wherever it appears. Ports of the helpers in chat.js and mind.js.
 */

/** A year as "1959" or "350 BCE"; empty string when unknown. */
export function fmtYear(year: number | null | undefined): string {
  if (year === null || year === undefined) return "";
  return year < 0 ? `${Math.abs(year)} BCE` : String(year);
}

/** A word count as "4.2K" / "12K" / "840". */
export function fmtWords(words: number): string {
  if (words >= 1000) return (words / 1000).toFixed(words >= 10000 ? 0 : 1) + "K";
  return String(words);
}

/** Bucket a conversation by last activity: Today / Yesterday / Earlier. */
export function dateGroup(iso: string): "Today" | "Yesterday" | "Earlier" {
  const then = new Date(iso);
  const today = new Date();
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const startOfThen = new Date(then.getFullYear(), then.getMonth(), then.getDate());
  const diff = Math.round((startOfToday.getTime() - startOfThen.getTime()) / 86400000);
  if (diff <= 0) return "Today";
  if (diff === 1) return "Yesterday";
  return "Earlier";
}

/**
 * Collapse a source list to one entry per distinct document, keeping the
 * first occurrence (highest score) of each file.
 */
export function dedupeSources(sources: SourceOut[]): SourceOut[] {
  const seen = new Map<string, SourceOut>();
  for (const s of sources) {
    if (!seen.has(s.source_file)) seen.set(s.source_file, s);
  }
  return [...seen.values()];
}

/**
 * A human title for a source path. Prefers the corpus document's real title
 * (via a path→doc map); falls back to prettifying the file name.
 */
export function prettyTitle(path: string, byPath: Map<string, CorpusDocOut>): string {
  const doc = byPath.get(path);
  if (doc) return doc.title;
  const file = path.split("/").pop()?.replace(/\.md$/, "") ?? path;
  return file.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Accept a URL only if http/https — rejects javascript: and friends. */
export function safeHttpUrl(url: string): string | null {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:" ? u.href : null;
  } catch {
    return null;
  }
}
