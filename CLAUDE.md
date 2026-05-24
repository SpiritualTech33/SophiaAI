# CLAUDE.md — SophiaAI Session Context

## What We Are Building

SophiaAI is an AI assistant grounded in a hand-curated corpus of wisdom literature. A base LLM downloaded from HuggingFace, connected to two capabilities: a RAG pipeline that uses sophia_engine as source of truth, and a web search tool for when the answer lives beyond the corpus. Wrapped in a FastAPI web app with user login and persistent conversation memory. This is the technical anchor of Spiritual Tech — a bridge between the Divine and Technology.


## Architecture

RAG pipeline: user query -> embed query -> FAISS vector search over sophia_engine chunks -> retrieve top-k passages -> inject into LLM prompt -> answer grounded in the corpus.

Web search: when the corpus is insufficient, Sophia queries DuckDuckGo, retrieves results, and incorporates them into her answer.

LLM inference: Groq free tier (Llama 3 or Gemma). Not local — API calls to Groq.

Web app: FastAPI + Jinja2 templates + SQLite (sophia_memory DB) + JWT login.


## Project State

Ready to start Phase 8 - Sophia Orchestrator




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
