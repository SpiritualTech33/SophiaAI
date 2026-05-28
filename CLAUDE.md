# CLAUDE.md — SophiaAI

Durable facts that survive across sessions. Holds the WHY, not the WHAT.
Anything derivable from the repo (file paths, test names, git history, code
structure) lives in the code, `git log`, or the graph — not here.

## What We Are Building

SophiaAI: an AI assistant grounded in a hand-curated corpus of wisdom
literature. A Groq-hosted LLM connected to two capabilities — a RAG pipeline
that uses sophia_engine as source of truth, and a web search tool for answers
beyond the corpus. Wrapped in a FastAPI web app with JWT login and persistent
conversation memory. The technical anchor of Spiritual Tech — a bridge between
the Divine and Technology.

**User:** Cosmos De La Cruz — final-year student, Tokio School
(Programación Python, Proyecto Final).

## Architecture

- **RAG:** query → embed → FAISS vector search over sophia_engine chunks →
  top-k passages → inject into LLM prompt → grounded answer.
- **Web search:** when corpus confidence is low, query DuckDuckGo and fold
  results into the answer.
- **LLM:** Groq free tier (Llama 3 / Gemma). Not local — API calls.
- **Web app:** FastAPI + Jinja2 + SQLite (sophia_memory DB) + JWT login.

## Tech Stack

- Embeddings: sentence-transformers (all-MiniLM-L6-v2, 384 dims)
- Vector store: FAISS (faiss-cpu)
- LLM: Groq API (groq client)
- Web search: duckduckgo-search (DDGS().text(), v8.x API)
- Web: FastAPI + Uvicorn + Jinja2
- DB: SQLAlchemy + SQLite + Alembic
- Auth: passlib (bcrypt<4.1) + python-jose (JWT)
- transformers 5.9.0 (major version — watch 4.x→5.x API drift)

## Architecture Decisions & Rationale

- **LLM = Groq, not local.** Free tier, no GPU. One swap-point file
  (`sophia/llm/groq_client.py`) so the provider is replaceable in one commit.
- **Embeddings = all-MiniLM-L6-v2 (384 dims).** Small, fast on CPU, free,
  good enough for the corpus. No Ferrari to drive to the corner store.
- **FAISS IndexFlatIP on L2-normalized vectors.** Flat = exact search; ~1,422
  vectors is trivial size. IP after normalization = cosine similarity.
- **Retrieval = class, not function.** Loading FAISS + SentenceTransformer is
  a ~2s cost — pay it once at FastAPI startup, not per message.
- **Chunk order is sacred.** The list index in `chunks_index.json['rag_chunks']`
  IS the FAISS internal id. Never sort/filter/reorder the chunks list at load —
  the 1:1 mapping must hold or the retriever silently returns wrong passages.
- **Web search = DuckDuckGo.** No key, no quota, no signup.
- **Front-end = Jinja2 + vanilla JS, no React.** Every layer of complexity is a
  layer to defend, maintain, and explain in the defense video.
- **JWT, not server-side sessions.** Stateless, simpler deploy, clean school fit.

## Code Conventions

- SOLID + ZenCode PRO + CEO of Water in every file. Single-responsibility
  functions, explicit naming, no clever tricks.
- Bulletproof error handling — one bad file must never kill a pipeline. Wrap
  parsers in `try/except`, log a warning, continue.
- "Mental Model" docstrings on every public function/class. Canonical style:
  `scripts/build_faiss_index.py`, `sophia/rag/retriever.py`.
- Script vs library: scripts under `scripts/` may `sys.exit(1)` on fatal
  startup errors; library code under `sophia/` MUST raise, never `sys.exit`.
- `from __future__ import annotations` at the top of every `sophia/` module.
- Logging format: `"%(asctime)s | %(levelname)-8s | %(message)s"`, datefmt
  `"%H:%M:%S"`.
- Written text/essays: plain English, no italics, headers + text only.

## Process & Workflow

Per phase:
1. Write a plan at `documentation/plans/phase-N-name.md` BEFORE coding
   (`superpowers:writing-plans` conventions: checkboxes, exact commands,
   expected output, self-review).
2. Branch `feat/phase-N-name`.
3. TDD: failing tests first, then implementation, then green.
4. Typically two commits: `feat(phaseN): add <thing> with unit tests`, then
   `feat(phaseN): <verify or wire-up>`.
5. Merge to master with `--no-ff` so phase boundaries show in `git log --graph`.
6. Append a Phase N entry to `cosmos_log.md`.

- **Caveman mode:** active by default (full). Code/commits/security stay normal
  English; conversation may drop articles and filler.
- **Spanish OK** in conversation. Code, commits, docstrings, cosmos_log = English.

## Critical Gotchas

- **sentence-transformers 5.x renamed methods.**
  `get_sentence_embedding_dimension` → `get_embedding_dimension`. Old name
  still works but emits `FutureWarning`. Prefer new, fall back to old.
- **transformers 5.9.0 is a major version.** Watch 4.x→5.x API drift.
- **FAISS needs float32 + C-contiguous.** Cast `np.float64`→`np.float32` and
  `np.ascontiguousarray` when loading external `.npy`.
- **FAISS returns -1 ids as padding** when `top_k > index.ntotal`. Filter `< 0`.
- **Windows line endings.** Git warns `LF will be replaced by CRLF` — harmless.
- **venv activation:** `SophiaAI-venv\Scripts\Activate.ps1` (PowerShell).

## Querying the Codebase — graphify

`graphify-out/` holds a persistent knowledge graph of the code + docs (scope:
everything except `data/`). Use it to answer architecture questions without
re-reading files.

- `graphify-out/graph.json` — the graph (nodes, edges, communities). Source of truth.
- `graphify-out/GRAPH_REPORT.md` — god nodes, communities, surprising links, audit.
- `graphify-out/graph.html` — interactive viz, open in a browser.

Query commands (read the graph, do not re-scan the repo):
- `/graphify query "how does auth work"` — BFS, broad context.
- `/graphify query "..." --dfs` — trace one path.
- `/graphify path "Sophia" "Database"` — shortest path between two concepts.
- `/graphify explain "SophiaRetriever"` — one node + its connections.

Keeping it fresh (manual): after adding/changing code or docs, run
`/graphify . --update` — diffs against the saved manifest, re-extracts only
changed files, prunes deleted ones. Code-only changes skip the LLM (AST only).

## Project Status

Phases 0-12 complete. Phase 13 (Alembic Migrations) is next. Web UI live
(Jinja2, cosmic design system, working chat with conversation memory).
Refinement/polish pending. Full table: `cosmos_log.md` + `git log --graph`.

**Phase 13 — Alembic Migrations.** Version control for the DB schema; last
stack piece the school requirement names. `alembic init alembic`, point env.py
at `sophia/db/models.py` metadata, autogenerate initial migration (users,
conversations, messages), `alembic upgrade head`. Depends on Phase 9.

## School Context

Final project for Tokio School. Must satisfy five requirements, all met:
database (sophia_memory SQLite), OOP (SQLAlchemy models + service classes),
framework (FastAPI), login (JWT), documentation (cosmos_log.md). A ~10-minute
defense video is required after submission.

## What Goes Where (anti-duplication)

| Information | Home |
|---|---|
| Architecture decisions + WHY, conventions, gotchas, user profile | this file |
| Codebase structure / "what connects to what" | `graphify-out/` (query it) |
| Full phase roadmap | `developing_plan.md` |
| Per-phase narrative + lessons | `cosmos_log.md` |
| Live "where I am now" handoff | `.remember/now.md`, `.remember/remember.md` |
| Implementation details, file structure | the code itself |
| Phase status, who-changed-what | `git log --oneline --graph` |

**Rule:** before writing here, ask "could the reader derive this from the repo
(or the graph) in under a minute?" If yes, don't write it here.
