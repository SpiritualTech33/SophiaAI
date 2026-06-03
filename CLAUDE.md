# CLAUDE.md — SophiaAI

Durable facts that survive across sessions. Holds the WHY, not the WHAT.
Anything derivable from the repo (file paths, test names, git history, code
structure) lives in the code, `git log`, or the graph — not here.

## What We Are Building

SophiaAI: a wisdom-grounded **agent**. Same soul (a hand-curated corpus of
wisdom literature), new hands (tools she calls herself). A Groq-hosted LLM is
given a set of tools — RAG over sophia_engine, web search, and a growing set
of action tools — and decides itself which to call, looping until the task is
done. Wrapped in a FastAPI app with JWT login and persistent conversation
memory. The technical anchor of Spiritual Tech — a bridge between the Divine
and Technology.

The school phase shipped a chatbot. This phase is the pivot: **chatbot →
agent.** The corpus stays the source of truth; what changes is that Sophia can
now *act*, not only answer.

**User:** Cosmos De La Cruz — final-year student, Tokio School
(Programación Python, Proyecto Final). School phase complete; now building
beyond the assignment.

## Architecture

Markers: ✅ live today · 🚧 in progress · 🎯 north-star vision (not built yet).

- ✅ **RAG:** query → embed → FAISS vector search over sophia_engine chunks →
  top-k passages → inject into LLM prompt → grounded answer.
- ✅ **Web search:** query DuckDuckGo and fold results into the answer.
- ✅ **LLM:** Groq free tier. Not local — API calls.
- ✅ **Web app:** FastAPI + Jinja2 + SQLite (sophia_memory DB) + JWT login.
- ✅ **Routing (today):** a deterministic confidence-router in the orchestrator
  picks corpus-only / hybrid / web modes. This is the brain *now*.
- 🎯 **Agency (north star):** replace the router with an **LLM tool-calling
  loop** — Sophia is handed tools and decides herself which to call and when,
  iterating until done. The router demotes from "the brain" to one strategy.
- 🎯 **Action tools:** file read/write (read what the user gives her, generate
  files back) and voice mode (STT in / TTS out). RAG + web become two tools
  among several, behind one uniform tool interface.

## North Star (directional, not yet decided in code)

The destination, written so future sessions know where this is heading. None
of this is built — do not reference these as existing modules.

- **Agency:** confidence-router → LLM tool-calling loop. The curated corpus
  stays privileged grounding; tools extend reach, they don't replace the soul.
- **Capabilities in scope:** tool-calling loop · file read/write · voice mode.
  Explicitly *out* of current scope: image generation, image understanding.
- **Stack:** evolve FastAPI into an **API-first** backend (clean JSON +
  streaming endpoints); the frontend decouples into a separate modern client
  that consumes the API. Jinja2 server-rendering is the starting point, not the
  destination.
- **Discipline preserved:** keep one-swap-point boundaries (LLM provider, each
  tool) so any piece is replaceable in one commit. New tools plug into a single
  uniform interface, not scattered call sites.

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
- **Front-end = Jinja2 + vanilla JS, no React (school phase).** Every layer of
  complexity was a layer to defend in the defense video. Post-school north star
  reverses this: API-first backend + decoupled modern client. The Jinja2 app is
  the starting point, not the final shape — see North Star.
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

**School phase complete.** Working chatbot shipped: RAG + web search, streaming
chat, JWT auth, conversation memory, cosmic three-panel UI (Jinja2), DB under
Alembic. The five Tokio School requirements are met. Full history:
`cosmos_log.md` + `git log --graph`.

**Now: chatbot → agent.** New direction is set at the vision level (see
*What We Are Building* and *North Star*); the detailed implementation roadmap is
not written yet. First real engineering steps still TBD — likely the
tool-calling loop and a uniform tool interface, since file I/O and voice both
depend on it. Do not treat north-star capabilities as existing.

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
