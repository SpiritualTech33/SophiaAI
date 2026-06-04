import type { CorpusDocOut, SourceOut, WebResult } from "@/lib/types";
import { dedupeSources, prettyTitle, safeHttpUrl } from "@/lib/format";
import { pillarVar } from "@/lib/pillars";
import { BookIcon, GlobeIcon } from "@/components/cosmic/icons";

/**
 * Mental Model:
 *   The provenance beneath a Sophia answer. The mode badge says where she
 *   looked (corpus book vs web globe). Source chips name the documents she
 *   drew from — one per distinct file, tinted by pillar; clicking one opens
 *   that document in Sophia's Mind. Web links are the pages she consulted when
 *   she stepped beyond the corpus, rendered only for safe http(s) URLs.
 */

export function ModeBadge({ searchMode }: { searchMode: string }) {
  const isWeb = /web/i.test(searchMode || "");
  return (
    <span className="badge">
      {isWeb ? <GlobeIcon /> : <BookIcon />}
      <span>{searchMode || "corpus"}</span>
    </span>
  );
}

export function SourceChips({
  sources,
  byPath,
  onOpen,
}: {
  sources: SourceOut[];
  byPath: Map<string, CorpusDocOut>;
  onOpen: (path: string) => void;
}) {
  const unique = dedupeSources(sources);
  if (unique.length === 0) return null;

  return (
    <div className="src-cite">
      <div className="src-label">Drawn from Sophia&apos;s mind</div>
      <div className="src-row">
        {unique.map((s) => (
          <button
            key={s.source_file}
            type="button"
            className="src-chip"
            style={pillarVar(String(s.pillar))}
            onClick={() => onOpen(s.source_file)}
          >
            <span className="dot" />
            <span className="ct">{prettyTitle(s.source_file, byPath)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function WebResults({ results }: { results: WebResult[] }) {
  const links = results
    .map((r) => ({ href: safeHttpUrl(r.url), title: r.title }))
    .filter((r): r is { href: string; title: string } => r.href !== null);
  if (links.length === 0) return null;

  return (
    <div className="web-cite">
      <div className="src-label">From the web</div>
      <ul className="web-list">
        {links.map((r) => (
          <li key={r.href}>
            <a href={r.href} target="_blank" rel="noopener noreferrer">
              {r.title || r.href}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
