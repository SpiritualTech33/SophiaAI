"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CorpusDocOut } from "@/lib/types";
import GlassPanel from "@/components/cosmic/GlassPanel";
import { SearchIcon, ChevronIcon } from "@/components/cosmic/icons";
import { PILLARS, pillarVar } from "@/lib/pillars";
import { fmtYear, fmtWords } from "@/lib/format";

/**
 * Mental Model:
 *   Sophia's Mind made browsable. The whole corpus, grouped by the four
 *   pillars, each collapsible, with a search box and per-pillar filters. When
 *   Sophia cites documents in an answer, the panel lights those rows, expands
 *   their pillars, and scrolls the first into view with a brief flash — so you
 *   can see exactly where her words came from. Clicking a document opens it.
 */
export default function MindPanel({
  corpus,
  citedPaths,
  open,
  onOpenDoc,
}: {
  corpus: CorpusDocOut[];
  citedPaths: string[];
  open: boolean;
  onOpenDoc: (doc: CorpusDocOut) => void;
}) {
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const docRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const byPath = useMemo(() => {
    const map = new Map<string, CorpusDocOut>();
    for (const d of corpus) map.set(d.path, d);
    return map;
  }, [corpus]);

  const citedIds = useMemo(() => {
    const ids = new Set<string>();
    for (const path of citedPaths) {
      const d = byPath.get(path);
      if (d) ids.add(d.id);
    }
    return ids;
  }, [citedPaths, byPath]);

  const totalWords = useMemo(
    () => corpus.reduce((sum, d) => sum + (d.words || 0), 0),
    [corpus],
  );

  // Pillars holding a cited document are always shown, overriding a manual
  // collapse — derived, so no state needs to change when citations arrive.
  const citedPillars = useMemo(() => {
    const set = new Set<string>();
    for (const d of corpus) if (citedIds.has(d.id)) set.add(d.pillar);
    return set;
  }, [corpus, citedIds]);

  // When citations change, scroll the first cited row into view and flash it.
  // Pure DOM work — no React state, so no cascading renders.
  useEffect(() => {
    if (citedIds.size === 0) return;
    const firstId = [...citedIds][0];
    const el = docRefs.current.get(firstId);
    const scroll = scrollRef.current;
    if (!el || !scroll) return;
    const top = el.offsetTop - scroll.clientHeight / 2 + el.clientHeight / 2;
    scroll.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    el.classList.add("flash");
    const timer = setTimeout(() => el.classList.remove("flash"), 1600);
    return () => clearTimeout(timer);
  }, [citedIds]);

  function matches(d: CorpusDocOut): boolean {
    if (activeFilter && d.pillar !== activeFilter) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      (d.title || "").toLowerCase().includes(q) ||
      (d.author || "").toLowerCase().includes(q)
    );
  }

  function toggleCollapse(pillar: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(pillar)) next.delete(pillar);
      else next.add(pillar);
      return next;
    });
  }

  const visible = corpus.filter(matches);

  return (
    <GlassPanel as="aside" id="mind" className={`mind${open ? " open" : ""}`}>
      <div className="mind-head">
        <h2>Sophia&apos;s Mind</h2>
        <p className="mind-stat">
          <b>{corpus.length}</b> sources ·{" "}
          <b>{totalWords >= 1000 ? `${Math.round(totalWords / 1000)}K` : totalWords}</b> words · 4 pillars
        </p>
        <div className="pillar-filters">
          {PILLARS.map((p) => (
            <button
              key={p.id}
              type="button"
              className={`pfilter${activeFilter === p.id ? " on" : ""}`}
              style={pillarVar(p.id)}
              onClick={() => setActiveFilter((cur) => (cur === p.id ? null : p.id))}
            >
              <span className="dot" />
              {p.label}
            </button>
          ))}
        </div>
        <div className="panel-search">
          <SearchIcon />
          <input
            type="search"
            placeholder="Search the corpus"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search the corpus"
          />
        </div>
      </div>

      <div className="mind-scroll" ref={scrollRef}>
        {visible.length === 0 ? (
          <div className="mind-empty">No documents match.</div>
        ) : (
          PILLARS.map((p) => {
            if (activeFilter && activeFilter !== p.id) return null;
            const docs = visible.filter((d) => d.pillar === p.id);
            if (docs.length === 0) return null;
            const isCollapsed = collapsed.has(p.id) && !citedPillars.has(p.id);
            return (
              <div
                key={p.id}
                className={`pillar-sec${isCollapsed ? " collapsed" : ""}`}
                style={pillarVar(p.id)}
              >
                <button type="button" className="pillar-h" onClick={() => toggleCollapse(p.id)}>
                  <span className="glyph" />
                  <span className="pl">{p.label}</span>
                  <span className="cnt">{docs.length}</span>
                  <ChevronIcon className="chev" />
                </button>
                <div className="doc-list">
                  {docs.map((d) => {
                    const year = fmtYear(d.year);
                    const classes = ["doc", citedIds.has(d.id) ? "cited" : ""]
                      .filter(Boolean)
                      .join(" ");
                    return (
                      <button
                        key={d.id}
                        type="button"
                        className={classes}
                        style={pillarVar(p.id)}
                        ref={(el) => {
                          if (el) docRefs.current.set(d.id, el);
                          else docRefs.current.delete(d.id);
                        }}
                        onClick={() => onOpenDoc(d)}
                      >
                        <span className="dt">{d.title}</span>
                        <span className="dm">
                          <span className="dauth">{d.author}</span>
                          {year ? <span>· {year}</span> : null}
                          <span>· {fmtWords(d.words)}w</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </GlassPanel>
  );
}
