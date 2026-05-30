/* =========================================================================
   mind.js — "Sophia's Mind" panel: browse and read the corpus.

   Responsibilities:
     - load the corpus metadata (GET /api/corpus)
     - render the 137 documents grouped by the four pillars, with search
       and per-pillar filters
     - open a document in a reader overlay (GET /api/corpus/{id}), rendering
       its markdown safely
     - react to the chat: highlight the documents cited in Sophia's last
       answer, and open a document when a source chip is clicked

   Coordination with chat.js happens through window CustomEvents:
     - "sophia:cite" { paths: [...] }  -> highlight those documents
     - "sophia:open" { path }          -> open that document in the reader

   Security: every piece of document text is placed via textContent, never
   innerHTML. Markdown is rendered into real DOM nodes, so corpus content
   cannot inject markup.
   ========================================================================= */

import { authFetch, requireAuth } from "/static/js/cosmos.js";

const PILLARS = [
  { id: "mind", label: "Mind" },
  { id: "philosophy", label: "Philosophy" },
  { id: "science", label: "Science" },
  { id: "spirit", label: "Spirit" },
];

if (requireAuth()) {
  initMind();
}

function initMind() {
  const scroll = document.getElementById("mind-scroll");
  const statEl = document.getElementById("mind-stat");
  const filtersEl = document.getElementById("pillar-filters");
  const searchEl = document.getElementById("corpus-search");
  const backdrop = document.getElementById("reader-backdrop");
  const mind = document.getElementById("mind");
  const mindToggle = document.getElementById("mind-toggle");

  let docs = [];                 // all CorpusDocOut
  const byPath = new Map();      // path -> doc
  let activeFilter = null;       // pillar id or null
  let query = "";
  let cited = new Set();         // doc ids cited by the last answer
  const collapsed = new Set();   // collapsed pillar ids
  const docNodes = new Map();    // doc id -> button element (for scroll/flash)

  /* ------------------------------ Loading ------------------------------ */

  async function loadCorpus() {
    try {
      const res = await authFetch("/api/corpus");
      if (!res.ok) {
        statEl.textContent = "Could not reach the corpus.";
        return;
      }
      docs = await res.json();
      for (const d of docs) byPath.set(d.path, d);
      // Share path -> {title, pillar} so chat.js can label its source chips.
      window.__corpusByPath = byPath;
      renderStat();
      renderFilters();
      render();
    } catch (_) {
      statEl.textContent = "Could not reach the corpus.";
    }
  }

  function renderStat() {
    const words = docs.reduce((sum, d) => sum + (d.words || 0), 0);
    statEl.textContent = "";
    const a = document.createElement("b");
    a.textContent = String(docs.length);
    const b = document.createElement("b");
    b.textContent = words >= 1000 ? (words / 1000).toFixed(0) + "K" : String(words);
    statEl.append(a, " sources · ", b, " words · 4 pillars");
  }

  function renderFilters() {
    filtersEl.innerHTML = "";
    for (const p of PILLARS) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pfilter" + (activeFilter === p.id ? " on" : "");
      btn.style.setProperty("--p", `var(--pillar-${p.id})`);
      const dot = document.createElement("span");
      dot.className = "dot";
      btn.append(dot, p.label);
      btn.addEventListener("click", () => {
        activeFilter = activeFilter === p.id ? null : p.id;
        renderFilters();
        render();
      });
      filtersEl.appendChild(btn);
    }
  }

  /* ----------------------------- Rendering ----------------------------- */

  function matches(d) {
    if (activeFilter && d.pillar !== activeFilter) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      (d.title || "").toLowerCase().includes(q) ||
      (d.author || "").toLowerCase().includes(q)
    );
  }

  function fmtYear(y) {
    if (y === null || y === undefined) return "";
    return y < 0 ? `${Math.abs(y)} BCE` : String(y);
  }
  function fmtWords(w) {
    return w >= 1000 ? (w / 1000).toFixed(w >= 10000 ? 0 : 1) + "K" : String(w);
  }

  function render() {
    scroll.innerHTML = "";
    docNodes.clear();

    const visible = docs.filter(matches);
    if (visible.length === 0) {
      const empty = document.createElement("div");
      empty.className = "mind-empty";
      empty.textContent = "No documents match.";
      scroll.appendChild(empty);
      return;
    }

    for (const p of PILLARS) {
      if (activeFilter && activeFilter !== p.id) continue;
      const pillarDocs = visible.filter((d) => d.pillar === p.id);
      if (pillarDocs.length === 0) continue;

      const sec = document.createElement("div");
      sec.className = "pillar-sec" + (collapsed.has(p.id) ? " collapsed" : "");
      sec.style.setProperty("--p", `var(--pillar-${p.id})`);

      const head = document.createElement("button");
      head.type = "button";
      head.className = "pillar-h";
      const glyph = document.createElement("span");
      glyph.className = "glyph";
      const pl = document.createElement("span");
      pl.className = "pl";
      pl.textContent = p.label;
      const cnt = document.createElement("span");
      cnt.className = "cnt";
      cnt.textContent = String(pillarDocs.length);
      const chev = svgIcon("M9 6l6 6-6 6", "chev");
      head.append(glyph, pl, cnt, chev);
      head.addEventListener("click", () => {
        if (collapsed.has(p.id)) collapsed.delete(p.id);
        else collapsed.add(p.id);
        render();
      });

      const list = document.createElement("div");
      list.className = "doc-list";
      for (const d of pillarDocs) list.appendChild(docButton(d, p.id));

      sec.append(head, list);
      scroll.appendChild(sec);
    }
  }

  function docButton(d, pillarId) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "doc" + (cited.has(d.id) ? " cited" : "");
    btn.style.setProperty("--p", `var(--pillar-${pillarId})`);

    const title = document.createElement("span");
    title.className = "dt";
    title.textContent = d.title;

    const meta = document.createElement("span");
    meta.className = "dm";
    const auth = document.createElement("span");
    auth.className = "dauth";
    auth.textContent = d.author;
    meta.append(auth);
    const year = fmtYear(d.year);
    if (year) { meta.append(" · ", year); }
    meta.append(` · ${fmtWords(d.words)}w`);

    btn.append(title, meta);
    btn.addEventListener("click", () => openReader(d.id));
    docNodes.set(d.id, btn);
    return btn;
  }

  /* ------------------------------ Highlight ---------------------------- */

  function highlight(paths) {
    cited = new Set();
    for (const path of paths) {
      const d = byPath.get(path);
      if (d) cited.add(d.id);
    }
    // auto-expand pillars that contain a cited doc
    for (const id of cited) {
      const d = docs.find((x) => x.id === id);
      if (d) collapsed.delete(d.pillar);
    }
    render();

    // scroll the first cited doc into view and flash it
    const firstId = [...cited][0];
    if (firstId && docNodes.has(firstId)) {
      const el = docNodes.get(firstId);
      el.classList.add("flash");
      const top = el.offsetTop - scroll.clientHeight / 2 + el.clientHeight / 2;
      scroll.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
      setTimeout(() => el.classList.remove("flash"), 1600);
    }
  }

  /* ------------------------------ Reader ------------------------------- */

  async function openReader(docId) {
    const doc = docs.find((d) => d.id === docId);
    if (!doc) return;

    backdrop.innerHTML = "";
    backdrop.hidden = false;

    const article = document.createElement("article");
    article.className = "reader";
    article.style.setProperty("--p", `var(--pillar-${doc.pillar})`);
    article.addEventListener("click", (e) => e.stopPropagation());

    // header
    const top = document.createElement("header");
    top.className = "reader-top";
    const metaWrap = document.createElement("div");

    const pill = document.createElement("div");
    pill.className = "reader-pill";
    const dot = document.createElement("span");
    dot.className = "dot";
    pill.append(dot, doc.pillar);

    const h1 = document.createElement("h1");
    h1.className = "r-title";
    h1.textContent = doc.title;

    const metaLine = document.createElement("div");
    metaLine.className = "reader-meta";
    const author = document.createElement("b");
    author.textContent = doc.author;
    metaLine.append(author);
    const yr = fmtYear(doc.year);
    if (yr) metaLine.append("· " + yr);
    metaLine.append(`· ${Number(doc.words).toLocaleString()} words`);

    metaWrap.append(pill, h1, metaLine);

    const close = document.createElement("button");
    close.className = "reader-close";
    close.setAttribute("aria-label", "Close reader");
    close.append(svgIcon(["M18 6L6 18", "M6 6l12 12"]));
    close.addEventListener("click", closeReader);

    top.append(metaWrap, close);

    // body (loading first)
    const body = document.createElement("div");
    body.className = "reader-body";
    const loading = document.createElement("div");
    loading.className = "reader-loading";
    const orb = document.createElement("span");
    orb.className = "orb";
    orb.dataset.state = "thinking";
    loading.append(orb, "Retrieving from Sophia's engine…");
    body.appendChild(loading);

    article.append(top, body);
    backdrop.appendChild(article);

    try {
      const res = await authFetch(`/api/corpus/${docId}`);
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      body.innerHTML = "";
      const prose = document.createElement("div");
      prose.className = "reader-prose";
      renderMarkdown(data.text, prose);
      body.appendChild(prose);
      body.scrollTop = 0;
    } catch (_) {
      body.innerHTML = "";
      const err = document.createElement("div");
      err.className = "reader-error";
      err.textContent = "Full text isn't available right now.";
      body.appendChild(err);
    }
  }

  function closeReader() {
    backdrop.hidden = true;
    backdrop.innerHTML = "";
  }

  backdrop.addEventListener("click", closeReader);
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !backdrop.hidden) closeReader();
  });

  /* --------------------------- Markdown render ------------------------- */
  /* A small, safe markdown renderer. Block-level: headings, lists, quotes,
     hr, paragraphs. Inline: **bold**, *italic*, `code`. Everything lands as
     DOM text nodes — no HTML strings, so corpus content can't inject markup. */

  function renderMarkdown(raw, container) {
    let body = raw.replace(/^﻿/, "");
    // drop a YAML frontmatter block
    const fm = body.match(/^---\n[\s\S]*?\n---\n?/);
    if (fm) body = body.slice(fm[0].length);
    // drop the leading "# Title" (already shown in the header)
    body = body.replace(/^\s*#\s+.*\n?/, "");

    const blocks = body.split(/\n{2,}/);
    for (const rawBlock of blocks) {
      const t = rawBlock.trim();
      if (!t) continue;

      if (/^###\s+/.test(t)) {
        container.appendChild(inlineInto("h3", t.replace(/^###\s+/, "")));
      } else if (/^##\s+/.test(t)) {
        container.appendChild(inlineInto("h2", t.replace(/^##\s+/, "")));
      } else if (/^#\s+/.test(t)) {
        container.appendChild(inlineInto("h2", t.replace(/^#\s+/, "")));
      } else if (/^-{3,}$/.test(t)) {
        container.appendChild(document.createElement("hr"));
      } else if (/^>\s?/.test(t)) {
        container.appendChild(inlineInto("blockquote", t.replace(/^>\s?/gm, "").trim()));
      } else if (/^[-*]\s+/.test(t)) {
        container.appendChild(listFrom(t, "ul", /^[-*]\s+/));
      } else if (/^\d+\.\s+/.test(t)) {
        container.appendChild(listFrom(t, "ol", /^\d+\.\s+/));
      } else {
        container.appendChild(inlineInto("p", t.replace(/\n/g, " ")));
      }
    }
  }

  function listFrom(text, tag, marker) {
    const el = document.createElement(tag);
    for (const line of text.split("\n")) {
      if (!line.trim()) continue;
      const li = document.createElement("li");
      applyInline(li, line.replace(marker, ""));
      el.appendChild(li);
    }
    return el;
  }

  function inlineInto(tag, text) {
    const el = document.createElement(tag);
    applyInline(el, text);
    return el;
  }

  function applyInline(el, text) {
    const re = /(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)/;
    let rest = text;
    let m;
    while ((m = re.exec(rest))) {
      if (m.index > 0) el.appendChild(document.createTextNode(rest.slice(0, m.index)));
      if (m[2] !== undefined) {
        const strong = document.createElement("strong");
        strong.textContent = m[2];
        el.appendChild(strong);
      } else if (m[3] !== undefined) {
        const em = document.createElement("em");
        em.textContent = m[3];
        el.appendChild(em);
      } else if (m[4] !== undefined) {
        const code = document.createElement("code");
        code.textContent = m[4];
        el.appendChild(code);
      }
      rest = rest.slice(m.index + m[0].length);
    }
    if (rest) el.appendChild(document.createTextNode(rest));
  }

  /* ------------------------------ Helpers ------------------------------ */

  function svgIcon(d, className) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "15");
    svg.setAttribute("height", "15");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    if (className) svg.setAttribute("class", className);
    for (const path of Array.isArray(d) ? d : [d]) {
      const p = document.createElementNS(ns, "path");
      p.setAttribute("d", path);
      svg.appendChild(p);
    }
    return svg;
  }

  /* ------------------------------ Events ------------------------------- */

  window.addEventListener("sophia:cite", (e) => {
    highlight((e.detail && e.detail.paths) || []);
  });
  window.addEventListener("sophia:open", (e) => {
    const path = e.detail && e.detail.path;
    const d = path && byPath.get(path);
    if (d) openReader(d.id);
  });

  searchEl.addEventListener("input", () => {
    query = searchEl.value.trim();
    render();
  });

  if (mindToggle) {
    mindToggle.addEventListener("click", () => {
      const open = mind.classList.toggle("open");
      mindToggle.setAttribute("aria-expanded", String(open));
    });
  }

  /* ------------------------------- Boot -------------------------------- */
  loadCorpus();
}
