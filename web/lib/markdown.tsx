import { Fragment, type ReactNode } from "react";

/**
 * Mental Model:
 *   Sophia speaks plain markdown. We render a small, safe subset of it into
 *   React nodes — never into HTML strings. Because React escapes all text by
 *   default, model and corpus content cannot inject markup; the only elements
 *   in the output are the ones we create from our own whitelist. This is the
 *   React equivalent of the safe renderers in chat.js and mind.js.
 *
 *   Two renderers:
 *     - renderAnswer(): line-based, for streaming chat answers (headings 1–3,
 *       lists, paragraphs). Line-based so a half-streamed answer still renders.
 *     - renderProse(): block-based, for the document reader (adds blockquotes
 *       and horizontal rules, strips frontmatter + the leading "# Title").
 *
 *   Both share renderInline() for **bold**, *italic*, and `code`.
 */

const INLINE_RE = /(\*\*([^*]+)\*\*|\*([^*\n]+)\*|`([^`]+)`)/;

/** Parse a single line of already-safe text into inline-marked React nodes. */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const out: ReactNode[] = [];
  let rest = text;
  let i = 0;
  let match: RegExpExecArray | null;

  while ((match = INLINE_RE.exec(rest))) {
    if (match.index > 0) {
      out.push(<Fragment key={`${keyPrefix}-t${i}`}>{rest.slice(0, match.index)}</Fragment>);
    }
    if (match[2] !== undefined) {
      out.push(<strong key={`${keyPrefix}-b${i}`}>{match[2]}</strong>);
    } else if (match[3] !== undefined) {
      out.push(<em key={`${keyPrefix}-i${i}`}>{match[3]}</em>);
    } else if (match[4] !== undefined) {
      out.push(<code key={`${keyPrefix}-c${i}`}>{match[4]}</code>);
    }
    rest = rest.slice(match.index + match[0].length);
    i += 1;
  }
  if (rest) out.push(<Fragment key={`${keyPrefix}-t${i}`}>{rest}</Fragment>);
  return out;
}

function Heading({ level, text, k }: { level: number; text: string; k: string }) {
  const children = renderInline(text, k);
  if (level === 1) return <h1 key={k}>{children}</h1>;
  if (level === 2) return <h2 key={k}>{children}</h2>;
  return <h3 key={k}>{children}</h3>;
}

/** Streaming chat answers: line-based headings, lists, and paragraphs. */
export function renderAnswer(text: string): ReactNode[] {
  const lines = text.split("\n");
  const out: ReactNode[] = [];
  let list: ReactNode[] | null = null;
  let listType: "ul" | "ol" | null = null;
  let key = 0;

  const closeList = () => {
    if (list && listType) {
      const items = list;
      out.push(listType === "ul" ? <ul key={`l${key}`}>{items}</ul> : <ol key={`l${key}`}>{items}</ol>);
      key += 1;
      list = null;
      listType = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const ordered = line.match(/^\d+\.\s+(.*)$/);

    if (heading) {
      closeList();
      out.push(<Heading key={`h${key}`} level={heading[1].length} text={heading[2]} k={`h${key}`} />);
      key += 1;
    } else if (bullet) {
      if (listType !== "ul") {
        closeList();
        list = [];
        listType = "ul";
      }
      list!.push(<li key={`li${key}`}>{renderInline(bullet[1], `li${key}`)}</li>);
      key += 1;
    } else if (ordered) {
      if (listType !== "ol") {
        closeList();
        list = [];
        listType = "ol";
      }
      list!.push(<li key={`li${key}`}>{renderInline(ordered[1], `li${key}`)}</li>);
      key += 1;
    } else if (line.trim() === "") {
      closeList();
    } else {
      closeList();
      out.push(<p key={`p${key}`}>{renderInline(line, `p${key}`)}</p>);
      key += 1;
    }
  }
  closeList();
  return out;
}

/** Document reader: block-based prose with quotes and rules. */
export function renderProse(raw: string): ReactNode[] {
  let body = raw.replace(/^﻿/, "");
  // drop a YAML frontmatter block
  const fm = body.match(/^---\n[\s\S]*?\n---\n?/);
  if (fm) body = body.slice(fm[0].length);
  // drop the leading "# Title" (already shown in the reader header)
  body = body.replace(/^\s*#\s+.*\n?/, "");

  const blocks = body.split(/\n{2,}/);
  const out: ReactNode[] = [];
  let key = 0;

  for (const rawBlock of blocks) {
    const t = rawBlock.trim();
    if (!t) continue;
    const k = `bk${key}`;

    if (/^###\s+/.test(t)) {
      out.push(<h3 key={k}>{renderInline(t.replace(/^###\s+/, ""), k)}</h3>);
    } else if (/^##\s+/.test(t)) {
      out.push(<h2 key={k}>{renderInline(t.replace(/^##\s+/, ""), k)}</h2>);
    } else if (/^#\s+/.test(t)) {
      out.push(<h2 key={k}>{renderInline(t.replace(/^#\s+/, ""), k)}</h2>);
    } else if (/^-{3,}$/.test(t)) {
      out.push(<hr key={k} />);
    } else if (/^>\s?/.test(t)) {
      out.push(<blockquote key={k}>{renderInline(t.replace(/^>\s?/gm, "").trim(), k)}</blockquote>);
    } else if (/^[-*]\s+/.test(t)) {
      out.push(<ul key={k}>{listItems(t, /^[-*]\s+/, k)}</ul>);
    } else if (/^\d+\.\s+/.test(t)) {
      out.push(<ol key={k}>{listItems(t, /^\d+\.\s+/, k)}</ol>);
    } else {
      out.push(<p key={k}>{renderInline(t.replace(/\n/g, " "), k)}</p>);
    }
    key += 1;
  }
  return out;
}

function listItems(text: string, marker: RegExp, keyPrefix: string): ReactNode[] {
  const items: ReactNode[] = [];
  let i = 0;
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    items.push(<li key={`${keyPrefix}-li${i}`}>{renderInline(line.replace(marker, ""), `${keyPrefix}-li${i}`)}</li>);
    i += 1;
  }
  return items;
}
