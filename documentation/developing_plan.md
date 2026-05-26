# SophiaAI — Developing Plan

A step-by-step path from where the project stands today to a fully working web application. Plain English. No fluff. Each phase has a purpose, a deliverable, and a reason it must exist before the next one starts.

---

## Where We Are Today

Phase 0 (corpus), Phase 1 (manifest), and Phase 2 (chunking) are complete. The repository holds 137 markdown files of curated wisdom literature, a manifest that indexes every file, and a chunks index containing 1,422 RAG chunks of 384 tokens each. The soul of Sophia is on disk. What remains is to give her the ability to remember, to retrieve, to reason, to speak, and to live behind a web interface.

---

## Phase 3 — Embeddings

### Purpose
Turn every text chunk into a mathematical fingerprint that captures its meaning. A 384-token passage about Lao Tzu becomes a vector of, say, 384 floating point numbers that lives in a high-dimensional space. Passages with similar meaning end up near each other in that space. This is the bridge between language and search.

### Deliverable
A new file at `data/embeddings.npy` containing one vector per chunk, in the exact order of `chunks_index.json`. A second file `data/embedding_meta.json` records the model name, dimension, and creation timestamp.

### How
Create `scripts/build_embeddings.py`. The script loads `chunks_index.json`, instantiates `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, fast, free), iterates the RAG chunks with a tqdm progress bar, and writes the matrix to disk as a numpy array. Batch size 32 is a safe starting point. Wrap the embedding loop in try/except per batch so one ugly chunk does not kill the run.

### Why this model
all-MiniLM-L6-v2 is small (90 MB), fast on CPU, and good enough for a corpus this size. Larger models exist, but you do not need a Ferrari to drive to the corner store. We choose intentional simplicity.

---

## Phase 4 — FAISS Index

### Purpose
An array of vectors is useless if you have to compare your query to all 1,422 of them every time. FAISS is a library written by Meta that organizes vectors into a structure where you can find the nearest neighbors in milliseconds even with millions of entries. For 1,422 chunks the speed gain is invisible, but the discipline of building it the right way pays off when the corpus grows.

### Deliverable
A file at `data/sophia_index.faiss` containing the FAISS index.

### How
Create `scripts/build_faiss_index.py`. Load `embeddings.npy`, normalize each vector to unit length, then build an `IndexFlatIP` (inner product, which equals cosine similarity when vectors are normalized). Write the index to disk with `faiss.write_index`.

### Why IndexFlatIP
For 1,422 vectors there is no reason to use an approximate index. Flat means exact search. IP after normalization gives cosine similarity, which is the standard way to measure semantic closeness.

---

## Phase 5 — Retrieval Module

### Purpose
A reusable Python class that takes a question in plain English and returns the most relevant chunks from the corpus, along with their source file and chunk metadata. This is the heart of the RAG pipeline.

### Deliverable
A new package `sophia/rag/` containing:
- `retriever.py` with class `SophiaRetriever`
- `__init__.py` exporting the class

### How
`SophiaRetriever.__init__` loads the FAISS index, the embedding model, and `chunks_index.json` into memory once at startup. The method `retrieve(query: str, top_k: int = 5) -> list[Chunk]` embeds the query, normalizes it, searches the index, and returns a list of Chunk dataclasses with fields: text, source_file, pillar (mind, philosophy, spirit, science), score.

### Why a class and not a function
Loading FAISS and the embedding model takes a few seconds. You want that cost paid once when the app starts, not every time a user sends a message. A class with state is the right tool.

---

## Phase 6 — LLM Client

### Purpose
A clean wrapper around the Groq API that turns a list of messages into a response. Isolated so that if you swap Groq for something else later, only this file changes.

### Deliverable
`sophia/llm/groq_client.py` with class `GroqClient`.

### How
Read `GROQ_API_KEY` from an environment variable (use python-dotenv to load `.env`). Expose one method: `chat(messages: list[dict], model: str = "llama-3.1-8b-instant") -> str`. Wrap the API call in try/except and translate Groq exceptions into a clean `SophiaLLMError` so the rest of the app does not need to know what library is underneath.

### Why a wrapper
Single responsibility. The orchestrator should not know about Groq's specific error classes. It should ask for an answer and get one, or get a clear failure.

---

## Phase 7 — Web Search Tool

### Purpose
When the corpus does not contain the answer, Sophia must be able to look at the world. DuckDuckGo gives a free, no-key search endpoint.

### Deliverable
`sophia/tools/web_search.py` with function `web_search(query: str, max_results: int = 5) -> list[SearchResult]`.

### How
Use `duckduckgo-search` version 8.x: `DDGS().text(query, max_results=max_results)`. Parse each result into a `SearchResult` dataclass with fields: title, url, snippet. Wrap the call in try/except — the internet is unreliable and your app should not crash because of a network blip.

### Why DuckDuckGo
No API key, no quota, no signup. For an open-source educational project this is the path of least friction.

---

## Phase 8 — The Sophia Orchestrator

### Purpose
The brain. This is where the decisions are made: should I answer from the corpus, or should I search the web? How do I build the prompt? How do I cite my sources?

### Deliverable
`sophia/core/orchestrator.py` with class `Sophia`.

### How
The flow per user message:
1. Receive the user query and the conversation history.
2. Call `SophiaRetriever.retrieve(query, top_k=5)`.
3. Inspect the top score. If it crosses a confidence threshold (start with 0.45), proceed with corpus-only RAG. Otherwise, also call `web_search`.
4. Build a system prompt that describes Sophia's voice (the bridge between the Divine and the Tech) and injects the retrieved passages with their source citations.
5. Call `GroqClient.chat` with the constructed messages.
6. Return a response object with the answer text and the list of sources used.

### Why a threshold
Not every question lives in the corpus. Some questions are about today's news, current events, or facts that simply do not belong in a wisdom library. The threshold is the line between memory and curiosity. Tune it later with real usage.

---

## Phase 9 — Database Layer

### Purpose
Persistent memory of users and conversations. This is `sophia_memory` — the short-term, alive, written-on-every-interaction database from the README.

### Deliverable
`sophia/db/` package containing:
- `database.py` — SQLAlchemy engine and session factory
- `models.py` — ORM models: User, Conversation, Message
- `__init__.py` — exports

### How
Use SQLAlchemy 2.0 style with `DeclarativeBase`. Tables:
- `users`: id, email (unique), hashed_password, created_at
- `conversations`: id, user_id (FK), title, created_at, updated_at
- `messages`: id, conversation_id (FK), role (user or sophia), content, sources_json (nullable), created_at

Database URL: `sqlite:///./sophia_memory.db`. Echo off in production, on while developing.

### Why three tables
A user has many conversations. A conversation has many messages. A message stores who said what, when, and which sources Sophia used. This is the minimum that satisfies the school requirement (database + OOP via models) and supports the real product.

---

## Phase 10 — Auth Layer

### Purpose
Login and registration. JWT for stateless sessions. Bcrypt for password hashing.

### Deliverable
`sophia/auth/` containing:
- `security.py` — password hashing, JWT encode and decode helpers
- `dependencies.py` — FastAPI dependency `get_current_user`

### How
Hashing with `passlib[bcrypt]`. Token creation and verification with `python-jose`. Tokens are signed with a secret read from an environment variable `JWT_SECRET`. Tokens live for 24 hours. The `get_current_user` dependency reads the Authorization header (or a cookie, depending on the chosen flow), decodes the JWT, fetches the user from the database, and returns it. If anything fails it raises `HTTPException(401)`.

### Why JWT and not server-side sessions
Stateless. Simpler to deploy. Satisfies the school requirement cleanly. And it is what the rest of the world uses.

---

## Phase 11 — FastAPI Skeleton

### Purpose
Wire everything together behind HTTP endpoints.

### Deliverable
`sophia/app/main.py` with the FastAPI instance and routes. Sub-routers in `sophia/app/routers/`:
- `auth.py` — POST /register, POST /login
- `chat.py` — POST /api/chat, GET /api/conversations, GET /api/conversations/{id}
- `pages.py` — GET / (landing), GET /chat (main UI), GET /login, GET /register

### How
Application lifespan: instantiate `Sophia`, `SophiaRetriever`, `GroqClient` once at startup and store them on `app.state`. Routes pull them from `app.state` so the heavy objects are shared across requests. CORS middleware permissive in development, locked down in production.

### Why lifespan and not module-level globals
Predictable startup, clean teardown, easier testing. FastAPI's lifespan context manager is the right tool.

---

## Phase 12 — Templates and Chat UI

### Purpose
A human face for Sophia. A page where you can type a question, see her think, and read her answer with sources cited.

### Deliverable
`sophia/app/templates/`:
- `base.html` — layout with header, footer, CSS hook
- `index.html` — landing page explaining what Sophia is
- `login.html`, `register.html`
- `chat.html` — the conversation view

Static assets in `sophia/app/static/`: one stylesheet, minimal JavaScript to handle form submission and append messages to the chat.

### How
Server-rendered HTML with Jinja2. The chat page submits user messages to `/api/chat` via fetch, then appends the response to the conversation thread. Keep it simple. No frontend framework. No build step. This is a school project that must work, not a startup MVP that must impress investors.

### Why no React or Vue
Every layer of complexity you add is a layer you must defend, maintain, and explain in the video. Jinja2 is enough.

---

## Phase 13 — Alembic Migrations

### Purpose
Version control for the database schema. The school requirement explicitly lists Alembic in the stack.

### Deliverable
`alembic.ini`, `alembic/env.py` configured against `sophia/db/models.py`, and the initial migration that creates users, conversations, and messages.

### How
Run `alembic init alembic`, point `env.py` at the SQLAlchemy metadata, generate the first revision with `alembic revision --autogenerate -m "initial schema"`, then `alembic upgrade head`.

### Why bother for a small project
Because the moment you add a column to `messages` (and you will), you do not want to drop the database and start over. Migrations are the way.

---

## Phase 14 — Testing

### Purpose
Confidence that nothing has silently broken when you ship.

### Deliverable
`tests/` directory with:
- `test_retriever.py` — embed a known query, assert the top result is from the expected file
- `test_orchestrator.py` — mock the LLM and assert the prompt contains the retrieved passages
- `test_auth.py` — register, login, hit a protected endpoint with and without a valid token
- `test_chat_endpoint.py` — full request to /api/chat with a logged-in user

### How
pytest, pytest-asyncio for async tests, httpx.AsyncClient against the FastAPI app. Mock the Groq client so tests do not burn API calls.

### Why
A test suite is the difference between code you trust and code you hope. Even five solid tests change the conversation.

---

## Phase 15 — Run It Locally

### Purpose
A clean, reproducible startup sequence so anyone can clone the repo and run Sophia in under five minutes.

### Deliverable
A `Makefile` or a section in the README with the exact commands:

```
python -m venv SophiaAI-venv
SophiaAI-venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env       # then edit it
python scripts/build_manifest.py
python scripts/build_chunks.py
python scripts/build_embeddings.py
python scripts/build_faiss_index.py
alembic upgrade head
uvicorn sophia.app.main:app --reload
```

### Why a Makefile
One command per step. No guessing. Future-you will thank present-you.

---

## Phase 16 — Defense Video Preparation

### Purpose
The Tokio School submission requires a roughly ten-minute defense video. Sophia must speak for herself there.

### Deliverable
A short script and a screen recording showing:
1. The corpus and its four pillars.
2. The pipeline from corpus to chunks to embeddings to FAISS.
3. A live conversation with Sophia: one corpus-grounded answer, one web-search answer, both with sources.
4. The database after the conversation, showing the saved messages.
5. The five school requirements ticked off on screen: database, OOP, framework, login, documentation.

### How
Record with OBS. One take is fine. The substance is what is being defended, not the production value.

---

## Final Repository Layout (target state)

```
SophiaAI/
├── alembic/
│   ├── env.py
│   └── versions/
├── data/
│   ├── sophia_engine/
│   ├── corpus_manifest.json
│   ├── chunks_index.json
│   ├── embeddings.npy
│   ├── embedding_meta.json
│   └── sophia_index.faiss
├── scripts/
│   ├── build_manifest.py
│   ├── build_chunks.py
│   ├── build_embeddings.py        <- Phase 3
│   ├── build_faiss_index.py       <- Phase 4
│   └── sophia_engine_word_counter.py
├── sophia/
│   ├── __init__.py
│   ├── rag/
│   │   ├── __init__.py
│   │   └── retriever.py           <- Phase 5
│   ├── llm/
│   │   ├── __init__.py
│   │   └── groq_client.py         <- Phase 6
│   ├── tools/
│   │   ├── __init__.py
│   │   └── web_search.py          <- Phase 7
│   ├── core/
│   │   ├── __init__.py
│   │   └── orchestrator.py        <- Phase 8
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py            <- Phase 9
│   │   └── models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── security.py            <- Phase 10
│   │   └── dependencies.py
│   └── app/
│       ├── __init__.py
│       ├── main.py                <- Phase 11
│       ├── routers/
│       │   ├── auth.py
│       │   ├── chat.py
│       │   └── pages.py
│       ├── templates/             <- Phase 12
│       └── static/
├── tests/                         <- Phase 14
├── alembic.ini
├── .env.example
├── requirements.txt
├── README.md
├── CLAUDE.md
├── developing_plan.md
└── cosmos_log.md
```

---

## Order of Operations and Dependencies

Phase 3 must come before 4. Phase 4 must come before 5. Phase 5 must come before 8. Phases 6 and 7 can be built in parallel with 3, 4, 5 since they do not depend on retrieval. Phase 8 needs 5, 6, and 7 finished. Phases 9 and 10 are independent of the AI side and can be built in parallel with 3 through 8. Phase 11 needs 8, 9, and 10. Phase 12 needs 11. Phase 13 needs 9. Phase 14 needs everything above. Phases 15 and 16 are wrap-up.

The honest critical path is: 3, 4, 5, 8, 11, 12, 14, 16. Everything else is parallelizable.

---

## A Note on Process

Each phase ends when its deliverable runs cleanly and produces the artifact described. Log every phase in `cosmos_log.md` with the date, what was built, what surprised you, and what you learned. The log is not bureaucracy. It is the historical record of how a piece of Spiritual Tech came into being. Future readers — including future-you — will read it and understand why the system is shaped the way it is.

Build with love. Build with care. One phase at a time.
