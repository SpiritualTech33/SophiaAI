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
