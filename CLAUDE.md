# CLAUDE.md — SophiaAI

Durable facts that survive across sessions. Holds the WHY, not the WHAT.
Anything derivable from the repo (file paths, test names, git history, code
structure) lives in the code, `git log`, or the graph — not here.

## What We Are Building

**SophiaAI is becoming a SaaS product: a billable, wisdom-grounded AI agent
people pay an accessible price to use.** Same soul (a hand-curated corpus of
wisdom literature), new hands (tools she calls herself) — and now a business
around it (tiers, billing, multi-tenant accounts). The technical anchor of
Spiritual Tech: a bridge between the Divine and Technology.

Three phases, in order:
1. **School phase — complete.** Shipped a chatbot: RAG + web search, streaming
   chat, JWT auth, conversation memory. The five Tokio School requirements met.
2. **Agent phase — current.** Pivot chatbot → agent: an LLM tool-calling loop
   replaces the router, so Sophia *acts*, not only answers. This is the product
   worth charging for.
3. **SaaS phase — current, in parallel.** Hardening, Postgres/multi-tenancy,
   Stripe billing, deploy. Roadmap: `documentation/plans/SaaS-implementations.md`.

**User:** Cosmos De La Cruz — building SophiaAI from school project into an
indie SaaS. Spanish OK in conversation.

## Architecture

Markers: ✅ live today · 🎯 north-star (not built yet — don't reference as existing).

- ✅ **RAG:** query → embed → FAISS vector search over sophia_engine chunks →
  top-k passages → inject into prompt → grounded answer.
- ✅ **Web search:** DuckDuckGo, folded into the answer.
- ✅ **File tool (`sophia/files/`):** `extract_text` reads uploads (txt/md/pdf/
  docx) → injected into the prompt; `render_file` writes downloads (txt/md/pdf/
  docx). Two pure functions behind one interface — wired deterministically now
  (upload button + download menu), the same functions the agent loop will call.
- ✅ **LLM:** OpenRouter API (`google/gemini-2.5-flash`). Not local — API calls.
- ✅ **Backend:** API-only FastAPI (JSON + SSE) + SQLite (sophia_memory) + JWT.
- ✅ **Frontend:** decoupled Next.js client in `web/` (App Router, TS, Tailwind
  v4, React 19). Backend-for-Frontend auth: route handlers hold the JWT in an
  httpOnly cookie. Jinja2 retired.
- ✅ **Routing (today):** a deterministic confidence-router in the orchestrator
  picks corpus-only / hybrid / web. The brain *now*.
- 🎯 **Agency (the pivot):** replace the router with an **LLM tool-calling
  loop** — Sophia is handed tools (RAG, web, file I/O, later voice) behind one
  uniform interface and decides which to call, looping until done. The router
  demotes to one fallback strategy. Out of scope: image gen/understanding.

## Tech Stack

- Embeddings: sentence-transformers (all-MiniLM-L6-v2, 384 dims)
- Vector store: FAISS (faiss-cpu), IndexFlatIP on L2-normalized vectors
- LLM: OpenRouter API (httpx client), model `google/gemini-2.5-flash`
- Web search: duckduckgo-search (DDGS().text(), v8.x API)
- File I/O: pypdf + python-docx (read), fpdf2 + python-docx (write) — pure-Python
- Backend: FastAPI + Uvicorn (API-only: JSON + SSE)
- Frontend: Next.js 16 + TypeScript + Tailwind v4 + React 19 (`web/`)
- DB: SQLAlchemy + SQLite + Alembic (→ Postgres in SaaS phase)
- Auth: passlib (bcrypt<4.1) + python-jose (JWT)
- transformers 5.9.0 (major version — watch 4.x→5.x API drift)

## Architecture Decisions & Rationale

- **LLM = OpenRouter, not local.** No GPU; one API key reaches many providers.
  One swap-point file (`sophia/llm/openrouter_client.py`) → provider/model
  replaceable in one commit (set `OPENROUTER_MODEL`).
- **Embeddings = all-MiniLM-L6-v2 (384 dims).** Small, fast on CPU, free, good
  enough. No Ferrari to drive to the corner store.
- **FAISS IndexFlatIP on L2-normalized vectors.** Flat = exact search; ~1,422
  vectors is trivial. IP after normalization = cosine similarity.
- **Retrieval = class, not function.** Loading FAISS + SentenceTransformer is a
  ~2s cost — pay it once at FastAPI startup, not per message.
- **Chunk order is sacred.** The list index in `chunks_index.json['rag_chunks']`
  IS the FAISS internal id. Never sort/filter/reorder the chunks list at load —
  the 1:1 mapping must hold or the retriever silently returns wrong passages.
- **BFF auth.** Next.js route handlers hold the JWT in an httpOnly cookie; the
  SSE stream is piped through a Node route handler. JWT (not server sessions) =
  stateless, simpler deploy.
- **One-swap-point boundaries.** LLM provider and each tool live behind a single
  interface so any piece is replaceable in one commit. New tools plug into the
  uniform tool interface, not scattered call sites. **Preserve this** — it's
  what makes the agent pivot and SaaS swaps cheap.

## Code Conventions

- SOLID + ZenCode PRO + CEO of Water. Single-responsibility functions, explicit
  naming, no clever tricks.
- Bulletproof error handling — one bad file never kills a pipeline. Wrap parsers
  in `try/except`, log a warning, continue.
- "Mental Model" docstrings on every public function/class. Canonical style:
  `scripts/build_faiss_index.py`, `sophia/rag/retriever.py`.
- Scripts under `scripts/` may `sys.exit(1)` on fatal startup; library code
  under `sophia/` MUST raise, never `sys.exit`.
- `from __future__ import annotations` atop every `sophia/` module.
- Logging: `"%(asctime)s | %(levelname)-8s | %(message)s"`, datefmt `"%H:%M:%S"`.
- Per phase: plan in `documentation/plans/` first → branch → TDD (red/green) →
  merge `--no-ff` → append to `cosmos_log.md`. Code/commits/docstrings = English.

## Critical Gotchas

- **sentence-transformers 5.x renamed methods.**
  `get_sentence_embedding_dimension` → `get_embedding_dimension`. Old name still
  works but emits `FutureWarning`. Prefer new, fall back to old.
- **transformers 5.9.0 is a major version.** Watch 4.x→5.x API drift.
- **FAISS needs float32 + C-contiguous.** Cast `np.float64`→`np.float32` and
  `np.ascontiguousarray` when loading external `.npy`.
- **FAISS returns -1 ids as padding** when `top_k > index.ntotal`. Filter `< 0`.
- **DB env name mismatch (fix in SaaS M0):** app reads `DATABASE_URL`
  (`sophia/app/main.py`), Alembic reads `SOPHIA_DB_URL` (`alembic/env.py`).
- **Windows line endings.** Git warns `LF will be replaced by CRLF` — harmless.
- **venv activation:** `SophiaAI-venv\Scripts\Activate.ps1` (PowerShell). Run
  shell commands via PowerShell on this Windows box.

## Memory & Context (where durable state lives)

- **`.remember/`** — live session handoff: `now.md` (current buffer),
  `recent.md` (7d), `archive.md` (old), `core-memories.md`, `today-*.md`.
  Read at session start; the canonical "where am I now."
- **`graphify-out/`** — persistent knowledge graph of code + docs (scope:
  everything except `data/`). `graph.json` (source of truth), `GRAPH_REPORT.md`
  (god nodes, communities, audit), `graph.html` (viz). Query it instead of
  re-reading files: `/graphify query "how does auth work"`,
  `/graphify path "Sophia" "Database"`, `/graphify explain "SophiaRetriever"`.
  Refresh after changes: `/graphify . --update` (diffs the manifest, re-extracts
  only changed files; code-only changes skip the LLM).
- **`documentation/plans/`** — phase/feature plans, incl.
  `SaaS-implementations.md` (the road from here to a billable product).

## What Goes Where (anti-duplication)

| Information | Home |
|---|---|
| Architecture decisions + WHY, conventions, gotchas, user profile | this file |
| Codebase structure / "what connects to what" | `graphify-out/` (query it) |
| Full SaaS roadmap | `documentation/plans/SaaS-implementations.md` |
| Per-phase narrative + lessons | `cosmos_log.md` |
| Live "where I am now" handoff | `.remember/now.md` |
| Implementation details, file structure | the code itself |
| Phase status, who-changed-what | `git log --oneline --graph` |

**Rule:** before writing here, ask "could the reader derive this from the repo
(or the graph) in under a minute?" If yes, don't write it here.

## School Context (complete — superseded by SaaS phase)

Tokio School final project, five requirements all met: database (sophia_memory
SQLite), OOP (SQLAlchemy models + service classes), framework (FastAPI), login
(JWT), documentation (cosmos_log.md). Defense video pending. History:
`cosmos_log.md` + `git log --graph`.
