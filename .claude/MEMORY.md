# SophiaAI — Project Memory

Durable facts that survive across sessions. Anything derivable from the repo
(file paths, test names, git history, code structure) lives in CLAUDE.md,
the code itself, or `git log` — not here. This file holds the WHY, not the WHAT.

---

## Who & What

**User:** Cosmos De La Cruz — final-year student at Tokio School
(Programación Python, Proyecto Final). Building SophiaAI as the technical
anchor of "Spiritual Tech" — a bridge between the Divine and Technology.

**School requirements (must satisfy all five):**
1. Database (sophia_memory SQLite)
2. OOP (SQLAlchemy models + service classes)
3. Framework (FastAPI)
4. Login (JWT)
5. Documentation (cosmos_log.md as the living dev log)

A ~10-minute defense video is required after submission.

---

## Architecture Decisions & Rationale

**LLM = Groq API, not local.**
Free tier (Llama 3.1 / Gemma). No GPU needed. One swap-point file
(`sophia/llm/groq_client.py`) so the LLM provider is replaceable in
one commit if Groq disappears.

**Embeddings = sentence-transformers/all-MiniLM-L6-v2 (384 dims).**
Small (90 MB), fast on CPU, free, good enough for a 137-file corpus.
"You do not need a Ferrari to drive to the corner store."

**Vector store = FAISS IndexFlatIP on L2-normalized vectors.**
Flat = exact search. 1,422 vectors is trivial size — no approximate
index needed. IP after normalization = cosine similarity, the standard
metric for sentence embeddings.

**Retrieval = class, not function.**
Loading FAISS + the SentenceTransformer is a ~2-second cost on CPU.
Pay it once at FastAPI startup, not per user message. State lives on
the instance.

**Chunk order is sacred.**
The list index in `chunks_index.json['rag_chunks']` IS the FAISS
internal id. Never sort, filter, or reorder the chunks list at load
time. The 1:1 mapping must be preserved or the retriever silently
returns wrong passages.

**Web search = DuckDuckGo (no key).**
No API key, no quota, no signup. Right tool for an open-source
educational project.

**Front-end = Jinja2 + vanilla JS. No React.**
"Every layer of complexity you add is a layer you must defend,
maintain, and explain in the video." School project, not startup MVP.

**JWT not server-side sessions.**
Stateless. Simpler deploy. Satisfies the school requirement cleanly.

---

## Code Conventions

**Philosophy:** ZenCode PRO + CEO of Water in every file.
- Single-responsibility functions, explicit naming, no clever tricks.
- Bulletproof error handling — one bad file must never kill a pipeline.
  Wrap parsers in `try/except`, log a warning, continue.
- "Mental Model" docstrings on every public function and class
  (see `scripts/build_faiss_index.py` and `sophia/rag/retriever.py`
  for the canonical style).
- Author line at the top of each module:
  `Author: Cosmos De La Cruz — SophiaAI Phase N`.

**Script vs library code:**
- Scripts under `scripts/` may `sys.exit(1)` on fatal startup errors.
- Library code under `sophia/` MUST raise instead — never `sys.exit`.

**Style for written text and essays:**
- Plain English. No italic formatting. Headers and text only.
- World-class writing — substance over decoration.

**Imports:** `from __future__ import annotations` at the top of every
module under `sophia/`.

**Logging:** shared format across the project —
`"%(asctime)s | %(levelname)-8s | %(message)s"`, datefmt `"%H:%M:%S"`.

---

## Process & Workflow

**Per phase:**
1. Write a plan at `docs/superpowers/plans/phase-N-name.md` BEFORE coding,
   using the `superpowers:writing-plans` skill conventions
   (checkboxes, exact commands, expected output, self-review section).
2. Branch `feat/phase-N-name`, work there.
3. TDD: failing tests first, then implementation, then green.
4. Two commits per phase typically:
   - `feat(phaseN): add <thing> with unit tests`
   - `feat(phaseN): <verify or wire-up step>`
5. Merge to master with `--no-ff` so phase boundaries show in
   `git log --graph`.
6. Append a Phase N entry to `cosmos_log.md`: what was built, artifacts,
   why decisions were made, lessons learned, next step.

**Caveman mode:** active by default at session start (full intensity).
Code, commits, security text stay normal English. Conversation may drop
articles and filler.

**Spanish OK** in conversation. Code, commits, docstrings, and the
cosmos_log stay in English.

---

## Critical Gotchas

**sentence-transformers 5.x renamed methods.**
`get_sentence_embedding_dimension` → `get_embedding_dimension`.
The old name still works but emits a `FutureWarning`. Prefer the new
name; fall back to the old one for backward compatibility.

**transformers 5.9.0 is a major version.**
Watch for 4.x → 5.x API drift when adding any HuggingFace pipeline code.

**FAISS requires float32 + C-contiguous arrays.**
Cast `np.float64` → `np.float32` and call `np.ascontiguousarray` when
loading external `.npy` files.

**FAISS returns -1 ids as padding** when `top_k > index.ntotal`.
Always filter `< 0` ids out of search results.

**Windows line endings.**
Git warns `LF will be replaced by CRLF` on every add — harmless,
no action needed.

**venv activation on Windows:**
`SophiaAI-venv\Scripts\Activate.ps1` in PowerShell.

---

## What Goes Where (anti-duplication rule)

| Information | Home |
|---|---|
| Architecture decisions + WHY | This file |
| User profile + school requirements | This file |
| Code conventions + process rules | This file |
| Known gotchas + version-specific quirks | This file |
| Repository layout, tech stack list | `CLAUDE.md` |
| Full phase roadmap | `developing_plan.md` |
| Per-phase narrative + lessons + artifacts | `cosmos_log.md` |
| Live "where I am right now" handoff | `.remember/remember.md` + `.remember/now.md` |
| Implementation details, file structure | the code itself |
| Phase status, who-changed-what | `git log --oneline --graph` |

**Rule:** before writing here, ask "could the reader derive this from
the repo in under one minute?" If yes, do not write it here.

---

## Phase Status (one line)

Phases 0-6 complete. Phase 7 (DuckDuckGo web search) is the next slot.
Full status table lives in `cosmos_log.md` and `git log --graph`.

---

## Next Phase Preview — Phase 7 (Web Search Tool)

**Goal:** `sophia/tools/web_search.py` with function `web_search()`.

**Shape:**
- Uses `duckduckgo-search` (version 8.x): `DDGS().text(query, max_results)`.
- Returns `list[SearchResult]` dataclass with fields: title, url, snippet.
- Wraps network calls in try/except — internet is unreliable, app must
  not crash on a network blip.
- No API key needed. No signup. No quota.

**Why DuckDuckGo:** No API key, no quota, no signup. For an open-source
educational project this is the path of least friction.

**Dependencies:** `duckduckgo-search` (already in requirements.txt).
