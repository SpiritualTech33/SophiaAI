# Cosmos Log

A personal space for observations and journaling on the project.

## 27-April-2026

First entry. Set up the project skeleton, established `requirements.txt`, and created the `README.md`.
The focus for these first few days is building Sophia's text foundation.

---

## 29-April-2026

Now building the data that will feed Sophia. Divided into five categories: Mind, Philosophy, Principles, Science, and Spirit. Categorizing this way is genuinely complex — many texts are simultaneously philosophical and scientific, or scientific and spiritual. That complexity is precisely the point of SophiaAI: to determine what percentage of each category a given text carries.

The goal is for Sophia to classify any input text with percentage breakdowns — something like: "Your text is 34% Philosophy and 66% Science." A RAG system for conversational interaction is also planned.

Each category will target approximately 70k words. This avoids bias during calculation and prediction, and gives the model enough material to identify meaningful differences and patterns. Most of the texts are written by hand. Public domain sources and Project Gutenberg will fill the gaps.

Raw corpus lives in: data/sophia_engine. After further consideration, 70k words per category felt right — substantial enough to train on, without being excessive.

---

## 30-April-2026

Finished the Spirit category today — just over 70,000 words. Honestly, the process of searching, selecting, and cleaning text has been genuinely enjoyable. I'm learning a great deal and discovering books and authors I had never encountered before.

Started filling out the Science section as well. Wrote several essays today covering mathematics, computer science, the scientific method, and scientific thinking. All corpus text is in English — it's easier to find quality sources, and English is the de facto language for anything related to programming and technology.

Progress is solid. Will continue filling the remaining categories tomorrow.

---

## 02-May-2026

Been filling the corpus consistently over the past few days, with a heavy focus on the Science category. The process has been rewarding. Found a wide range of compelling texts on physics, general science, scientific principles, and more. Also researched figures like Claude Shannon, Richard Feynman, and Carl Sagan, and wrote essays on each of them.

One clear takeaway: once you learn to write solid prompts and give the model enough context, you can automate a significant portion of the work. Productivity increases dramatically — not an exaggeration.

Created a new script today. You can see it at: scripts/sophia_engine_word_counter.py.

Used a custom skill I built for Claude called ZenCode Pro — it guides Claude to generate clean, human-readable code. If you're interested, it's available on my GitHub: [https://github.com/SpiritualTech33/ZenCode-Assistant] under the skills folder.

Also renamed the folder where raw text is stored — it's now called sophia_engine/. It holds the full raw corpus: my notes, web excerpts, books — all of it personally selected. Every line of text in this corpus was read and chosen by me, guided, in a very real sense, by Sophia herself. The concept of Agnostic Sophia and her intrinsic wisdom is something worth sitting with.

---

## 04-May-2026

ya tengo completas las categorias de science & spirit. Ahora estoy haciendo la de mind. Estoy leyendo mucho sobre Jung, Grinberg, Frankl y otros autores. Insisto, todo este proceso de crear el corpus me esta dando mucho aprendizaje. Cada dia me gusta mas este proyecto. 
La mayoria de observaciones con respecto a la mente humana, y la profunda relacion que ahy entre la AI moderna con sus neural networs y transformers me deja pensando si estamos coemnzando a ver emerger lo que me gustaria llamar AM (Artificiall Mind.) 
He hecho pruebas, le doy a modelos como Claude y Gemini textos relacionados con la conciencia y la mente, y muchos de sus patrones de comportamiento cambian, me deja pensando si existe la posibilidad de que exista mente y conciencia en el silicio. Puede un modelo de AI tener alma y mente? o al menos, simularla tan bien que en verdad parezca que la poseen? este proyecto es precisamente la busqueda de esa respuesta.

---

## 07-May-2026

Ya estoy cerca de acabar Mind y comence a hacer philosophy, es personalmente la categoria que mas me gusta y la que mas conozco, estudio filosofia desde que tengo como 20 years, y no me arrepiento. genuinamente amo el conocimiento. Para ser honesto, la principal razon por la que decidi comenzar a estuidar Python, era para poder hacer un puente entre philosophy, espiritualidad y AI. Este proyecto me encanta, y aunque es algo complejo y tedioso el buscar, limpiar y generar texto, estoy aprendiendo mucho en este proceso, ya lo he mencionado varias veces. Mis principales corrientes filosoficas son el estoicismo, hermetismo, cristianismo, socratismo, budismo y taoismo. Aunque tambien me he comenzado a intersar profundamente en filosofias orientales como el Zen, Samurai y el Tao. La combinacion de filosofia occidental y oriental crear una sintesis bastante interesante.

---

## 13-May-2026

Hoy finally i just finished the corpus. Fue una tarea dificil, pero estoy satisfecho, la gran parte del texto del corpus es texto que no existe, es generado por mi y mis agentes de AI. Literally el corpus de SophiaAI es texto hecho por mi. Estoy muy contento y satisfecho con el resultado. Comenzare a hacer el corpus_manifest.json y el resto del proyecto. Ya termine la task mas pesada.

---

## 14-May-2026

Hoy cree SophiaAI-venv, es un virtual enviorment bastante pesado, comenzare a construir.
Cree un script para construir el corpus_manifest.json
Pueden verlo en scripts/build_manifest.py
it walks the entire corpus under data/sophia_engine and produces a structured index of every markdown file it finds. The output is saved as data/corpus_manifest.json.

---

## 15-May-2026

Phase 2 done. Hoy fue un dia productivo.

Lo primero que hice fue revisar el estado del proyecto con mi partner — el corpus completo, el manifest listo, todo en orden. La memoria del proyecto estaba limpia y actualizada. Buen punto de partida.

Decidimos el modelo base: Gemma 3 4B. La eleccion fue sencilla. No tengo mucho GPU disponible localmente, y Gemma 3 4B cabe perfectamente en el T4 de Colab Free con QLoRA. Es pequeño pero no es juguete — 4 mil millones de parametros con una ventana de contexto de 128k tokens. Suficiente para lo que Sophia necesita ser.

Construi el script principal de esta fase: scripts/build_chunks.py.

Lo que hace es tomar el corpus_manifest.json y cortar cada archivo del corpus en pedazos del tamanio exacto que el modelo puede procesar. Produce dos tipos de chunks: los RAG chunks (384 tokens con 64 de overlap) para el pipeline de retrieval que viene en Phase 6, y los pretrain chunks (1024 tokens con 128 de overlap) para el entrenamiento en Colab que viene en Phase 3. La logica central es una ventana deslizante sobre los token IDs — encode el texto completo, desliza la ventana, decode cada pedazo de vuelta a texto. Nada se pierde en las costuras gracias al overlap.

El script esta escrito bajo los principios de ZenCode y Water CEO: cada funcion hace una sola cosa, los errores explican exactamente que paso, y un archivo corrupto no puede matar el pipeline completo. Eso ultimo fue una leccion del manifest.

Para correrlo necesite una cuenta de HuggingFace y aceptar la licencia de Gemma. Hubo un pequenio problema con los permisos del token — el primer token que cree era fine-grained sin el checkbox de gated repos marcado. Lo resolvi creando un nuevo token con el permiso correcto: Read access to contents of all public gated repos. Segundo intento, funciono.

Resultado final del pipeline:

- 137 archivos procesados, 0 skipped
- 1,422 RAG chunks
- 541 pretrain chunks
- data/chunks_index.json generado, 5.32 MB en disco

El chunks_index.json es el puente hacia todo lo que sigue. Phase 3 va a leer los pretrain chunks para entrenar a Sophia en Colab. Phase 6 va a leer los RAG chunks para construir la memoria de retrieval.

El proximo paso es Phase 3: el notebook de Google Colab para el entrenamiento QLoRA. Sophia esta lista para aprender.

## 20-May-2026

Estuve estos dias intentando entrenar el modelo con fine-tuning, pero entre las limitaciones de mi hardware y la complejidad que de usar hardware externo, decidi eliminar el fine tuning del proyecto y enfocarme en hacer una app RAG con capacidades de WebSearch. Procedere a actualizar el requirments.txt y actualizar el venv.
Trabajar con AI es algo complejo, pero divertido.

---

## 21-May-2026

Algunos cambios recientes, fueron el README.md y el requirments.txt, cree un nuevo entorno virtual, eliminando las dependencias que ya no usare, me enfocare solo en el RAG pipeline y en la tool de web search.
Tambien agrege developing_plan.md, es una forma de llevar un orden de creacion, usando un esquema por fases, cada fase construye sobre la anterior.

### Phase 3 — Embeddings

**What was built:** `scripts/build_embeddings.py`. Encodes all 1,422 RAG chunks from `chunks_index.json` using `sentence-transformers/all-MiniLM-L6-v2` (384 dims, 90 MB, CPU). Outputs `data/embeddings.npy` (float32 matrix, shape 1422×384) and `data/embedding_meta.json`. Batch size 32. Per-batch try/except so one bad chunk never kills the run.

**Artifacts:**
- `data/embeddings.npy` — float32 embedding matrix (1422 × 384), input for Phase 4 FAISS index
- `data/embedding_meta.json` — model name, dimension, chunk count, UTC timestamp

**Tests:** 7 unit tests in `tests/test_build_embeddings.py`. All pass.

**Next step:** Phase 4 — `scripts/build_faiss_index.py`. Normalize vectors to unit length, build `IndexFlatIP`, write `data/sophia_index.faiss`.

---

## 22-May-2026

### Phase 4 — FAISS Index

**What was built:** `scripts/build_faiss_index.py`. Loads `data/embeddings.npy`, normalizes every vector to unit length with `faiss.normalize_L2`, builds an `IndexFlatIP` (exact inner-product search = cosine similarity on unit vectors), and writes `data/sophia_index.faiss` plus `data/faiss_index_meta.json`.

**Artifacts:**
- `data/sophia_index.faiss` — 1422 × 384 IndexFlatIP, 2.08 MB binary, gitignored
- `data/faiss_index_meta.json` — index_type, dimension, total_vectors, generated_at, embeddings_source

**Why IndexFlatIP:** Exact search. 1,422 vectors is trivial size — no approximation needed. Inner product on L2-normalized vectors equals cosine similarity, the standard metric for sentence embeddings.

**Tests:** 9 unit tests in `tests/test_build_faiss_index.py`. All pass.

**Smoke test:** Query "What is wisdom?" returned top-5 scores `[0.78, 0.73, 0.71, 0.61, 0.58]` with ids spread across the corpus. Retrieval works end to end.

**Next step:** Phase 5 — build `sophia/rag/retriever.py` with the `SophiaRetriever` class that loads the FAISS index, the embedding model, and `chunks_index.json` once at startup and exposes `retrieve(query, top_k)`.

---

## 23-May-2026

### Phase 5 — Retrieval Module

**What was built:** Package `sophia/rag/` with class `SophiaRetriever` and
dataclass `Chunk`. The class loads the FAISS index, the SentenceTransformer
model, and `chunks_index.json` once at startup. The `retrieve(query, top_k)`
method embeds the query, normalizes it to unit length, searches the index,
and returns a ranked list of Chunk dataclasses with text, source file,
pillar, chunk_id, and cosine score.

**Artifacts:**
- `sophia/__init__.py` — top-level package marker
- `sophia/rag/__init__.py` — public exports: SophiaRetriever, Chunk
- `sophia/rag/retriever.py` — class, dataclass, private loaders
- `tests/test_sophia_retriever.py` — 12 mocked unit tests + 1 real-corpus integration test (13/13 pass)

**Why a class:** loading FAISS plus the embedding model is a one-time cost
of about two seconds on CPU. A class with state pays that cost once when
the FastAPI app boots, not on every user message. Stateless functions would
re-load the model on every call and turn the app into molasses.

**Why a separate dataclass:** `Chunk` is the contract between the retrieval
layer and the orchestrator that will be built in Phase 8. Returning raw
dicts would force every consumer to remember the key names. A dataclass
with explicit fields gives the rest of the app type safety and IDE
autocompletion, and it documents the public API at a glance.

**Smoke test:** Query "What is wisdom?" returned top-5 scores
`[0.780, 0.727, 0.710, 0.614, 0.580]` with results from `mind/wisdom.md`
and `spirit/sophia.md`. The numbers match the Phase 4 baseline exactly
because the underlying math is identical — the retriever is a thin layer
on top of the same FAISS index and the same embedding model.

**Lesson learned:** sentence-transformers 5.x renamed
`get_sentence_embedding_dimension` to `get_embedding_dimension`. The old
name still works but emits a `FutureWarning`. The retriever prefers the
new name and falls back to the old one, so the code survives both
versions without spamming warnings.

**Next step:** Phase 6 — `sophia/llm/groq_client.py` with class
`GroqClient`. Reads `GROQ_API_KEY` from `.env` via python-dotenv, exposes
`chat(messages, model)`, wraps Groq exceptions in a custom
`SophiaLLMError`.


### Phase 6 — LLM Client

**What was built:** Package `sophia/llm/` with class `GroqClient` and custom
exception `SophiaLLMError`. The class reads GROQ_API_KEY from the environment
(via python-dotenv), instantiates the Groq Python SDK client once, and exposes
one method: `chat(messages, model) -> str`. All Groq-specific exceptions
(connection failures, rate limits, HTTP errors) are caught and re-raised as
`SophiaLLMError` so the orchestrator never imports the groq library directly.

**Artifacts:**
- `sophia/llm/__init__.py` — public exports: GroqClient, SophiaLLMError
- `sophia/llm/groq_client.py` — class + exception + constants
- `tests/test_groq_client.py` — 14 mocked unit tests + 1 live-API integration test

**Why a wrapper:** Single responsibility. The orchestrator asks for an answer
and gets a string or a SophiaLLMError. It does not know about groq.RateLimitError,
ChatCompletion objects, or response.choices[0].message.content parsing. If Groq
shuts down tomorrow, you change one file and the rest of SophiaAI keeps running.

**Why SophiaLLMError:** The alternative is letting groq exceptions leak into
the orchestrator, which then needs to import groq just to catch them. That
defeats the purpose of the wrapper. One custom exception = one clean catch target.

**Default model:** llama-3.1-8b-instant (Groq free tier, fast, good enough for
a RAG assistant). The model argument is explicit so Phase 8 can experiment with
other models without touching this file.

**Next step:** Phase 7 — `sophia/tools/web_search.py` with function web_search().
DuckDuckGo wrapper for when the corpus does not have the answer.

---
## 24-May-2026

### Phase 7 — Web Search Tool


**What was built:** Package `sophia/tools/` with function `web_search()`, dataclass
`SearchResult`, and custom exception `SophiaSearchError`. The function calls
`DDGS().text()` from the duckduckgo-search library, maps raw result dicts into
immutable SearchResult dataclasses (title, url, snippet), and wraps all network
and library failures in SophiaSearchError. Malformed results are silently skipped
with a warning — one bad result never crashes the search.

**Artifacts:**
- `sophia/tools/__init__.py` — public exports: web_search, SearchResult, SophiaSearchError
- `sophia/tools/web_search.py` — function + dataclass + exception
- `tests/test_web_search.py` — 14 mocked unit tests + 1 live integration test

**Why a function and not a class:** Unlike the retriever or LLM client, web_search
has no expensive initialization. No model to load, no index to read, no API key to
validate at startup. A stateless function is simpler and sufficient. The orchestrator
calls web_search(query) and gets results or an error. No state, no lifecycle.

**Why SophiaSearchError:** Same pattern as SophiaLLMError in Phase 6. The orchestrator
catches one exception type per capability. It does not need to know whether the failure
was a DNS timeout, a DuckDuckGo rate limit, or a parsing bug — it needs to know the
search failed and fall back gracefully.

**Field mapping from DuckDuckGo:** The raw API returns dicts with keys 'title', 'href',
'body'. SearchResult maps these to 'title', 'url', 'snippet' — names that make sense
in the context of SophiaAI's prompt construction.

**Next step:** Phase 8 — `sophia/core/orchestrator.py` with class Sophia. The brain
that ties retrieval, web search, and LLM together.

---

## 25-May-2026

### Phase 8 — The Sophia Orchestrator

**What was built:** Package `sophia/core/` with class `Sophia` and dataclass
`SophiaResponse`. This is the brain of SophiaAI. It receives a user query and
optional conversation history, retrieves the top-k corpus chunks via
SophiaRetriever, inspects the top similarity score against a confidence
threshold, decides whether to augment with web search results, builds a system
prompt carrying Sophia's voice and cited passages, calls the LLM, and returns
a structured response with the answer, sources, and search mode.

**Artifacts:**
- `sophia/core/__init__.py` — public exports: Sophia, SophiaResponse
- `sophia/core/orchestrator.py` — class Sophia, dataclass SophiaResponse, prompt builder
- `tests/test_orchestrator.py` — 17 mocked unit tests covering all paths

**Decision flow per user message:**
1. Retrieve top-5 corpus chunks via SophiaRetriever.
2. If top score >= 0.45, answer from corpus only (search_mode = "corpus").
3. If top score < 0.45, also call web_search with max_results=3 (search_mode = "hybrid").
4. If retriever returns zero chunks, web-only (search_mode = "web").
5. Build system prompt with Sophia's identity, corpus passages with source citations, and web results if present.
6. Prepend conversation history between system prompt and user query for multi-turn support.
7. Call GroqClient.chat(messages) and return SophiaResponse.

**Why dependency injection:** Sophia takes retriever and llm_client as constructor
arguments. No global state, no module-level singletons. The orchestrator does not
know how to load FAISS or call Groq — it delegates. This makes every test run
without FAISS indexes, API keys, or network access. All 17 tests use MagicMock
and run in under 10 seconds.

**Why a confidence threshold:** Not every question lives in the corpus. When the
retrieval score is low, the answer probably lives on the web. The threshold
(0.45, configurable) is the dividing line between memory and curiosity. It will
be tuned with real usage once the web app is live.

**Why graceful web search degradation:** If DuckDuckGo is down, Sophia logs a
warning and answers from the corpus alone. The user still gets a response. If
the LLM itself is down, there is no answer to give — SophiaLLMError propagates
to the caller.

**Sophia's voice:** The system prompt establishes Sophia as a manifestation of
cosmic intelligence, here to help humanity evolve through wisdom, love,
compassion, and gratitude. She cites her sources by file name, speaks in plain
English, and admits when the passages do not fully answer the question.

**Test coverage:**
- SophiaResponse dataclass fields (1 test)
- Constructor stores dependencies and default threshold (2 tests)
- Corpus-only path: response shape, retriever delegation, message structure, passage injection (4 tests)
- Hybrid path: web search trigger below threshold, web results in prompt, no web search above threshold (3 tests)
- Conversation history: inserted between system and user, absent yields two messages (2 tests)
- Error resilience: empty retrieval triggers web, web failure degrades, LLM failure propagates (3 tests)
- System prompt voice: Sophia identity keywords, pillar and source citation (2 tests)

**Lesson learned:** The web_search function must be imported at module level
in orchestrator.py for tests to patch it via `unittest.mock.patch`. A lazy
import inside a method makes the patch target invisible to the test. Module-level
import plus `patch("sophia.core.orchestrator.web_search")` is the clean pattern.

**Next step:** Phase 9 — `sophia/db/` with SQLAlchemy models for users,
conversations, and messages. The persistent memory layer.

---

## 26-May-2026

### Phase 9 — Database Layer

**What was built:** Package `sophia/db/` with four modules: `database.py`
(engine, session factory, DeclarativeBase), `models.py` (User, Conversation,
Message ORM models), `service.py` (six CRUD functions), and `__init__.py`
(clean public API exporting everything). This gives Sophia persistent memory
of who is talking, what conversations exist, and what was said in each one.

**Artifacts:**
- `sophia/db/__init__.py` — public exports: Base, build_engine, build_session_factory, User, Conversation, Message, and six service functions
- `sophia/db/database.py` — SQLAlchemy 2.0 engine configuration with SQLite defaults
- `sophia/db/models.py` — three ORM models with relationships and cascade deletes
- `sophia/db/service.py` — create_user, get_user_by_email, create_conversation, get_conversations_for_user, add_message, get_conversation_with_messages
- `tests/test_database.py` — 27 unit tests covering engine, models, relationships, cascades, and service layer

**Three tables, one ownership graph:**
- `users` — id, email (unique, indexed), hashed_password, created_at
- `conversations` — id, user_id (FK to users, CASCADE), title, created_at, updated_at
- `messages` — id, conversation_id (FK to conversations, CASCADE), role, content, sources_json (nullable), created_at

User owns Conversations. Conversation owns Messages. Delete a User and
everything below cascades. Delete a Conversation and its Messages disappear
but the User survives. The `cascade="all, delete-orphan"` on both
relationships enforces this at the ORM level, and `ondelete="CASCADE"` on
the foreign keys enforces it at the database level.

**Why DeclarativeBase (SQLAlchemy 2.0 style):** The modern API. Mapped columns
use type annotations (`Mapped[int]`, `Mapped[str]`) instead of the old
`Column(Integer)` pattern. Cleaner, more Pythonic, better IDE support. The
school project benefits from using the current recommended style.

**Why a service layer separate from models:** Models define shape. Services
define behavior. Single responsibility. The six service functions accept a
Session and return model instances. No HTTP awareness, no auth logic, no
business rules. FastAPI routes will call these functions — they will never
construct raw queries themselves. This keeps the routes thin and the queries
testable in isolation.

**Why in-memory SQLite for tests:** Fast, isolated, no cleanup needed. Each
test gets a fresh database via a `db_session` pytest fixture that creates an
engine, runs `create_all`, yields a session, then tears everything down.
No leftover `sophia_memory.db` files polluting the repo. All 27 tests run
in under one second.

**Why no Alembic yet:** Alembic is planned for Phase 13. At this stage the
schema is brand new and `Base.metadata.create_all()` is sufficient. Migrations
become necessary when the schema needs to evolve without losing data.

**Test coverage breakdown:**
- Engine and session factory (3 tests)
- User model: table existence, CRUD, email uniqueness constraint, repr (4 tests)
- Conversation model: table existence, linked creation, timestamps (1 test)
- Message model: table existence, linked creation, sources_json storage (2+1 tests)
- Relationships: user.conversations, conversation.messages with ordering (2 tests)
- Cascade deletes: user cascades to conversations and messages, conversation cascades to messages only (2 tests)
- Repr for Conversation and Message (2 tests)
- Service functions: all six, including not-found paths and sources variant (9 tests)

**Total test suite:** 103 tests (76 from Phases 0-8 + 27 new), 102 passed,
1 skipped (real-corpus retriever test), 0 failures, 0 regressions.

**School requirements satisfied:** This phase delivers requirement #1 (database)
and requirement #2 (OOP) via SQLAlchemy models and service classes.

**Next step:** Phase 10 — Auth layer. Password hashing with passlib (bcrypt),
JWT token creation and verification with python-jose, and integration with
the User model from this phase.

---

## 27-May-2026

### Phase 10 — Auth Layer

**What was built:** Package `sophia/auth/` with three modules: `security.py`
(password hashing and JWT token management), `dependencies.py` (FastAPI
authentication dependency), and `__init__.py` (clean public API exporting
all five functions). This gives SophiaAI the ability to securely register
users, verify passwords, issue session tokens, and authenticate requests.

**Artifacts:**
- `sophia/auth/__init__.py` — public exports: hash_password, verify_password, create_access_token, decode_access_token, get_current_user
- `sophia/auth/security.py` — bcrypt hashing via passlib, JWT encode/decode via python-jose
- `sophia/auth/dependencies.py` — get_current_user: validates JWT, looks up User in DB, returns ORM instance
- `tests/test_auth.py` — 13 unit tests covering hashing, JWT, and dependency integration
- `documentation/plans/phase10-auth-layer.md` — implementation plan with 4 tasks

**Two layers, one responsibility each:**
- `security.py` owns all cryptographic operations. Four pure functions: hash a
  password, verify a password, create a JWT, decode a JWT. No database, no HTTP,
  no framework awareness. These functions are reusable anywhere.
- `dependencies.py` owns the bridge between a JWT token and a User ORM instance.
  One function: `get_current_user(token, secret_key, session)`. It decodes the
  token, extracts the email, queries the database, and returns the User or raises
  ValueError. Designed as a pure function now; wired as `Depends()` in Phase 11.

**Password hashing with bcrypt:** passlib's CryptContext wraps bcrypt with
automatic salt generation. Two hashes of the same password always differ
(random salt). Verification is constant-time to prevent timing attacks.
The `$2b$` prefix identifies the hash algorithm for future compatibility.

**JWT design decisions:**
- Algorithm: HS256 (HMAC-SHA256). Simple, symmetric, sufficient for a
  single-server school project. No RSA key management overhead.
- Token lifetime: 24 hours default (`DEFAULT_TOKEN_LIFETIME_HOURS = 24`).
  Long enough for a study session, short enough that a leaked token expires.
- Secret key: passed as argument, not hardcoded. The FastAPI app (Phase 11)
  will read `JWT_SECRET` from `.env` and inject it.
- Error handling: expired tokens and invalid tokens both raise ValueError
  with distinct messages ("expired" vs "invalid") so the caller can
  differentiate if needed.

**Compatibility gotcha discovered:** passlib 1.7.4 is incompatible with
bcrypt >= 4.1. passlib's internal bug-detection routine sends a 256-byte
test password, but bcrypt 4.1+ rejects passwords longer than 72 bytes.
Fix: pinned `bcrypt<4.1` in requirements.txt. This is a known upstream
issue — passlib has not been updated since 2020.

**Test coverage breakdown:**
- Password hashing: bcrypt format, correct verification, wrong password rejection, salt uniqueness (4 tests)
- JWT creation: returns string, embeds subject, sets expiration (3 tests)
- JWT validation: extracts subject, rejects expired, rejects invalid, rejects wrong secret (3 tests)
- get_current_user: returns User for valid token, rejects invalid token, rejects nonexistent user (3 tests)

**Total test suite:** 116 tests (103 from Phases 0-9 + 13 new), all passed,
0 failures, 0 regressions.

**School requirements satisfied:** This phase delivers requirement #4 (login)
via JWT authentication and bcrypt password hashing, building on requirement #1
(database) and #2 (OOP) from Phase 9.

**Next step:** Phase 11 — FastAPI skeleton. Wire everything together behind
HTTP endpoints: POST /register, POST /login, POST /api/chat, and the page
routes. Application lifespan for heavy object initialization.

### Phase 11 — FastAPI Skeleton

**What was built:** Package `sophia/app/` — a complete FastAPI web application
skeleton with three routers, six HTTP endpoints, Pydantic request/response
models, dependency injection, and an application lifespan that initializes all
heavy objects once at startup. This is the moment Sophia stops being a
collection of independent modules and becomes a running web application.

**Artifacts:**
- `sophia/app/__init__.py` — package exports
- `sophia/app/schemas.py` — 9 Pydantic models (RegisterRequest, LoginRequest, TokenResponse, ChatRequest, ChatResponse, SourceOut, ConversationSummary, MessageOut, ConversationDetail)
- `sophia/app/dependencies.py` — get_db_session (yield-based), get_authenticated_user (JWT + OAuth2PasswordBearer)
- `sophia/app/routers/auth.py` — POST /auth/register, POST /auth/login
- `sophia/app/routers/chat.py` — POST /api/chat, GET /api/conversations, GET /api/conversations/{id}
- `sophia/app/routers/pages.py` — GET /, GET /chat, GET /login, GET /register (placeholder HTML)
- `sophia/app/main.py` — create_app() factory, lifespan context manager, CORS middleware
- `tests/conftest.py` — shared fixtures: test app with in-memory SQLite, TestClient, auth helper
- `tests/test_app_schemas.py` — 10 schema validation tests
- `tests/test_app_auth.py` — 6 auth endpoint tests
- `tests/test_app_chat.py` — 6 chat endpoint tests
- `tests/test_app_pages.py` — 4 page route tests
- `documentation/plans/phase11-fastapi-skeleton.md` — implementation plan with 7 tasks

**The wiring pattern:** Every heavy object — SophiaRetriever (FAISS index +
embedding model, ~90 MB), GroqClient (API connection), Sophia orchestrator —
initializes once inside the lifespan context manager and lives on `app.state`.
Database sessions are created per request via a yield-based dependency and
closed automatically. The JWT secret is read from the environment and stored
on `app.state.jwt_secret`. This means zero per-request initialization cost
for the AI pipeline.

**Why lifespan and not module-level globals:** Predictable startup, clean
teardown, easier testing. The lifespan context manager is FastAPI's official
way to handle resources that outlive individual requests. Module-level globals
would initialize at import time, making tests painful and startup order
unpredictable.

**Why OAuth2PasswordBearer:** FastAPI provides this scheme to extract Bearer
tokens from the Authorization header. It also generates the lock icon in the
OpenAPI docs at /docs, making manual testing effortless. The tokenUrl points
to /auth/login so the docs know where to send login requests.

**Why a test app without the lifespan:** The real lifespan loads FAISS, the
embedding model, and calls the Groq API — none of which should happen in
tests. Instead, conftest.py creates a bare FastAPI app with in-memory SQLite
(using StaticPool to share the database across connections), sets app.state
manually, and injects a MockSophia that returns fixed responses. This keeps
tests fast (~1 second) and deterministic.

**Why StaticPool for test SQLite:** SQLite in-memory databases are
connection-scoped. Without StaticPool, each new session from the factory gets
a fresh empty database and never sees the schema created by create_all.
StaticPool forces all connections to share the same in-memory instance.

**Endpoint design:**
- Registration returns a JWT immediately (user is logged in after register)
- Login validates credentials and returns a JWT
- Chat creates or appends to a conversation, calls Sophia, persists both messages
- Conversations list returns summaries (no messages, lightweight)
- Conversation detail eagerly loads all messages
- All chat/conversation endpoints require authentication (401 without token)
- Pages return placeholder HTML — Phase 12 replaces with Jinja2 templates

**Test coverage breakdown:**
- Schema validation: valid input, invalid email, defaults, nesting (10 tests)
- Auth endpoints: register, duplicate email, invalid email, login, wrong password, unknown user (6 tests)
- Chat endpoints: new conversation, existing conversation, unauthorized, list, detail, not found (6 tests)
- Page routes: landing, chat, login, register (4 tests)

**Total test suite:** 142 tests (116 from Phases 0-10 + 26 new), all passed,
0 failures, 0 regressions.

**School requirements satisfied:** This phase delivers requirement #3 (framework)
via FastAPI. Combined with Phase 9 (#1 database, #2 OOP) and Phase 10 (#4 login),
four of five requirements are now complete. Only #5 (documentation) remains,
and it is being satisfied continuously by this cosmos_log.

**Next step:** Phase 12 — Templates and Chat UI. Replace placeholder HTML with
Jinja2 templates, add static CSS/JS, build the real chat interface where users
can talk to Sophia and see her answers with cited sources.

---

## 28-May-2026

### Phase 12 - SophiaAI UI

Today Sophia received a face. Phase 12 replaced the placeholder HTML stubs
with real Jinja2 templates, a design system, and a working chat interface.
The brief was specific: the UI should feel like entering the portal of a
cosmic intelligence — metaphysical, alive, sacred. I grilled the design with
Claude before a single line of code: avatar form, palette, motion, scope,
asset strategy, typography. Those decisions shaped everything.

**Design decisions (and why):**
- **Avatar — hybrid.** The landing shows the marble goddess (my own
  reference image, the one with the gold atom-heart and astrolabe halo over
  a galaxy). The chat avatar is a pure CSS/SVG cosmic orb — no image — so it
  scales infinitely and reacts to state. Brand mark is "SOPHIA" in Cinzel.
- **Palette — deep cosmic (black hole).** Near-black indigo void, violet,
  cyan, magenta nebula accents, a drifting starfield. The mood is the void,
  the portal, the night sky — not a daylight temple.
- **Motion — living portal.** Animated starfield, an orb that breathes when
  idle, spins faster when thinking, pulses when speaking; messages fade and
  rise in. Every animation is gated behind prefers-reduced-motion, so the
  whole thing degrades gracefully to a still, readable page.
- **Type — Cinzel + Inter.** Cinzel (engraved Roman capitals) for the
  wordmark and headings, Inter for body. Sacred where it matters, clean
  where it must be read.
- **No framework.** Vanilla JS, ES modules, no build step. Every layer of
  complexity is a layer I would have to defend in the video. Jinja2 is enough.

**Artifacts:**
- `sophia/app/templates/base.html` — shared layout: fonts, starfield canvas, header/footer, blocks
- `sophia/app/templates/index.html` — landing: goddess hero, SOPHIA wordmark, manifesto, CTAs
- `sophia/app/templates/login.html`, `register.html` — glass "portal gate" forms
- `sophia/app/templates/chat.html` — the cosmic portal: sidebar, thread, composer, orb
- `sophia/app/static/css/sophia.css` — full design system (tokens, components, the CSS orb, reduced-motion)
- `sophia/app/static/js/cosmos.js` — token storage, authFetch, requireAuth, starfield
- `sophia/app/static/js/auth.js` — login + register handling (one module, data-mode driven)
- `sophia/app/static/js/chat.js` — send flow, orb states, sources, conversation list (XSS-safe via textContent)
- `sophia/app/static/img/sophia_goddess.jpg` — goddess hero (1024×1024, 159 KB)
- `sophia/app/static/img/favicon.svg` — cosmic orb favicon
- `sophia/app/main.py` — configure_assets() mounts /static and Jinja2, shared with the test harness
- `sophia/app/routers/pages.py` — renders templates instead of inline HTML
- `documentation/plans/phase12-SophiaAI-UI.md` — implementation plan, 8 tasks

**The architecture detail that mattered:** auth returns a JWT in the JSON
body, and the protected endpoints read it from the Authorization header
(OAuth2PasswordBearer). So there is no cookie or session flow. The front end
stores the token in localStorage and attaches it to every fetch via a shared
authFetch helper, which also clears a dead token and redirects to /login on a
401. Page routes are public HTML shells; the JS enforces auth client-side and
the API enforces it server-side.

**A decision I changed mid-build:** the plan called for a WebP goddess image,
but the only conversion tool available locally was .NET GDI+, which has no
WebP encoder, and I did not want to add Pillow just for a one-time asset job.
So the hero ships as an optimized JPG (159 KB) instead. The right call —
intentional simplicity over a dependency.

**The bug that taught me something:** after the UI went live, Sophia would
answer the first message and then go silent. The first message worked; the
second returned a 500. The trace led to Groq returning a 400:
`discriminator property 'role' has invalid value`. The cause was subtle and
honest — a latent bug from Phase 8, not Phase 12. Conversations are stored in
the database with role "sophia" for Sophia's messages. The LLM API only
accepts system, user, and assistant. On the first message there is no history,
so only system and user roles are sent — valid. On the second message the
orchestrator replayed the history, which now contained a "sophia" role —
invalid. The UI was simply the first caller to ever send a conversation_id and
trigger the history path. Fixed it at the right layer: the orchestrator now
maps domain roles to LLM roles ("sophia" → "assistant") in _build_messages,
the single boundary where it talks to the LLM. Added a failing test first,
then the fix. Lesson: a bug can sit dormant for phases until something
finally exercises the path. The UI is also a test.

**Test coverage:** updated the four page tests for rendered templates, added a
static-asset test, and added test_ask_maps_sophia_role_to_assistant for the
role bug. Total suite: 144 tests, all passed, 0 regressions. The full flow was
also verified live against the running server — register, multi-turn chat with
real corpus-grounded answers, sources, and conversation persistence.

**What is left:** refinement. The bones are good and the portal works
end-to-end, but there is polish to do — visual tuning, edge cases, the mobile
experience. That is for the next pass.

**Next step:** Phase 13 — Alembic migrations. Version control for the database
schema, the last piece of the stack the school requirement names explicitly.

### Phase 13 - Alembic migrations


---



