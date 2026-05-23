# CLAUDE.md — SophiaAI Session Context

## What We Are Building

SophiaAI is an AI assistant grounded in a hand-curated corpus of wisdom literature. A base LLM downloaded from HuggingFace, connected to two capabilities: a RAG pipeline that uses sophia_engine as source of truth, and a web search tool for when the answer lives beyond the corpus. Wrapped in a FastAPI web app with user login and persistent conversation memory. This is the technical anchor of Spiritual Tech — a bridge between the Divine and Technology.


## Architecture

RAG pipeline: user query -> embed query -> FAISS vector search over sophia_engine chunks -> retrieve top-k passages -> inject into LLM prompt -> answer grounded in the corpus.

Web search: when the corpus is insufficient, Sophia queries DuckDuckGo, retrieves results, and incorporates them into her answer.

LLM inference: Groq free tier (Llama 3 or Gemma). Not local — API calls to Groq.

Web app: FastAPI + Jinja2 templates + SQLite (sophia_memory DB) + JWT login.


## Project State

Ready to start phase 6 - LLM client

## Repository Layout

```
SophiaAI/
├── data/
│   ├── sophia_engine/                    <- 137 .md files, the corpus, source of truth
│   │   ├── mind/                         <- 45 files — consciousness, psychology, cognition
│   │   ├── philosophy/                   <- 33 files — philosophy corpus
│   │   ├── science/                      <- 22 files — science corpus
│   │   └── spirit/                       <- 37 files — spirituality corpus
│   ├── corpus_manifest.json              <- Phase 1 output
│   ├── chunks_index.json                 <- Phase 2 output, 1422 RAG chunks
│   ├── embedding_meta.json               <- Phase 3 output, embedding metadata
│   ├── embeddings.npy                    <- Phase 3 output, 1422 vectors at 384 dims (gitignored)
│   ├── faiss_index_meta.json             <- Phase 4 output, FAISS index metadata
│   └── sophia_index.faiss                <- Phase 4 output, IndexFlatIP (gitignored)
├── docs/
│   └── superpowers/
│       └── plans/
│           ├── phase3-embeddings.md
│           ├── phase4-FAISS-Index.md
│           └── phase5-retrieval-module.md
├── scripts/
│   ├── build_manifest.py                 <- Phase 1 script
│   ├── build_chunks.py                   <- Phase 2 script
│   ├── build_embeddings.py               <- Phase 3 script
│   ├── build_faiss_index.py              <- Phase 4 script
│   └── sophia_engine_word_counter.py
├── sophia/                               <- application package (real code lives here)
│   ├── __init__.py
│   └── rag/                              <- Phase 5 package
│       ├── __init__.py                   <- exports: SophiaRetriever, Chunk
│       └── retriever.py                  <- SophiaRetriever class + Chunk dataclass
├── tests/
│   ├── test_build_embeddings.py          <- 7 tests, all pass
│   ├── test_build_faiss_index.py         <- 9 tests, all pass
│   └── test_sophia_retriever.py          <- 13 tests (12 mocked + 1 integration), all pass
├── SophiaAI-venv/                        <- local venv, activate: SophiaAI-venv\Scripts\Activate.ps1
├── .claude/                              <- project-local Claude config + MEMORY.md (gitignored)
├── .remember/                            <- session handoff buffer (gitignored)
├── .env                                  <- secrets (GROQ_API_KEY etc.)
├── .env.example
├── .gitignore
├── cosmos_log.md                         <- living development log
├── developing_plan.md                    <- full phase roadmap
├── requirements.txt
├── setup.sh
├── README.md
└── CLAUDE.md
```

## Tech Stack

- Embeddings: sentence-transformers (all-MiniLM-L6-v2 or similar)
- Vector store: FAISS (faiss-cpu)
- LLM inference: Groq API (groq Python client)
- Web search: duckduckgo-search (DDGS().text() — version 8.x API)
- Web framework: FastAPI + Uvicorn + Jinja2
- Database: SQLAlchemy + SQLite + Alembic
- Auth: passlib (bcrypt) + python-jose (JWT)
- transformers version: 5.9.0 (major version — watch for API changes vs 4.x)

## Code Conventions

All code follows zencode-pro principles: single-responsibility functions, explicit naming, bulletproof error handling, no clever tricks. One bad file must never kill a pipeline — wrap parsers in try/except, log a warning, continue.

All text and essays are written in plain English. No italic formatting. Headers and text only. Word-class writing.

## School Context

This is a final project for Tokio School (Programacion Python — Proyecto Final). Must satisfy five requirements: database (sophia_memory SQLite), OOP (SQLAlchemy models + service classes), framework (FastAPI), login (JWT), and documentation (cosmos_log.md). A defense video (~10 min) is required after submission.
