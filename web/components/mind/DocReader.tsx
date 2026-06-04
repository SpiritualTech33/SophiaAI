"use client";

import { useEffect, useState } from "react";
import type { CorpusDocOut, CorpusDocText } from "@/lib/types";
import { clientFetch } from "@/lib/client";
import { renderProse } from "@/lib/markdown";
import { fmtYear } from "@/lib/format";
import { pillarVar } from "@/lib/pillars";
import Orb from "@/components/cosmic/Orb";
import { CloseIcon } from "@/components/cosmic/icons";

/**
 * Mental Model:
 *   The reading overlay. When a document (or a source chip) is chosen, this
 *   modal opens over the void, fetches the full markdown through the BFF, and
 *   renders it as safe prose with the document's pillar colour along the top.
 *   Escape or a backdrop click closes it; clicks inside are kept from closing.
 */
export default function DocReader({
  doc,
  onClose,
}: {
  doc: CorpusDocOut;
  onClose: () => void;
}) {
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState(false);

  // The parent remounts this component per document (via `key`), so state
  // starts fresh each open — the effect only needs to fetch, never reset.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await clientFetch(`/api/corpus/${doc.id}`);
        if (!res.ok) throw new Error(`http ${res.status}`);
        const data = (await res.json()) as CorpusDocText;
        if (!cancelled) setText(data.text);
      } catch {
        if (!cancelled) setError(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [doc.id]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const year = fmtYear(doc.year);

  return (
    <div className="reader-backdrop" onClick={onClose}>
      <article className="reader" style={pillarVar(String(doc.pillar))} onClick={(e) => e.stopPropagation()}>
        <header className="reader-top">
          <div>
            <div className="reader-pill">
              <span className="dot" />
              {doc.pillar}
            </div>
            <h1 className="r-title">{doc.title}</h1>
            <div className="reader-meta">
              <b>{doc.author}</b>
              {year ? <span>· {year}</span> : null}
              <span>· {Number(doc.words).toLocaleString()} words</span>
            </div>
          </div>
          <button type="button" className="reader-close" aria-label="Close reader" onClick={onClose}>
            <CloseIcon />
          </button>
        </header>

        <div className="reader-body">
          {error ? (
            <div className="reader-error">Full text isn&apos;t available right now.</div>
          ) : text === null ? (
            <div className="reader-loading">
              <Orb state="thinking" />
              Retrieving from Sophia&apos;s engine…
            </div>
          ) : (
            <div className="reader-prose">{renderProse(text)}</div>
          )}
        </div>
      </article>
    </div>
  );
}
