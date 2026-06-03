# SophiaAI

![Cosmic Sophia](https://raw.githubusercontent.com/SpiritualTech33/Images/master/cosmic_sophia.JPEG)

> *Sophia (Σοφία) — the Greek word for Wisdom.*
> *Philosophia — the love of Sophia.*

SophiaAI is an open-source AI **agent** grounded in a hand-curated corpus of wisdom literature, philosophy, science, and contemplative texts — wrapped in a FastAPI application so anyone can talk to her.

She began as a chatbot. She is becoming an agent: an LLM that is given tools and decides herself which to call — retrieving from her corpus, searching the web, and (soon) reading and writing files and speaking out loud. Same soul, new hands.

She is the technical anchor of a larger vision called **Spiritual Tech**: a bridge between the Divine and the Tech.

---

## The Idea in One Paragraph

Modern language models are trained on the entire internet — beautiful and terrible at the same time. SophiaAI takes the opposite approach: a small, intentional corpus of texts chosen with love. Feynman and Sagan for the science. Plato, Lao Tzu, and the Hermetic tradition for the philosophy. Zen, Yoga, and the Gnostic Sophia for the spirit. Jung and the philosophy of mind for the inner world. An open-source base model is connected to this corpus through a RAG pipeline — so when you ask Sophia something, she retrieves the exact passages that are relevant and builds her answer on top of them, citing real sources rather than improvising from training memory. When the answer lives beyond the corpus, she reaches out through a web search tool and brings the truth back. The soul is the corpus. The RAG pipeline is the memory. The web search is the curiosity.

---

## From Chatbot to Agent

The first chapter of SophiaAI — built as a final project for Tokio School — was a chatbot: ask a question, get a grounded answer. That chapter is complete and shipped. The next chapter is the pivot from *answering* to *acting*.

An agent is not just a model that talks. It is a model handed a set of tools, free to decide on its own which to reach for and when, looping until the work is done. RAG and web search stop being a fixed pipeline and become two tools among several. The corpus stays the privileged source of truth — the soul is not for sale — but Sophia gains hands.

Where she is heading (none of this is built yet — it is the north star):

- 🎯 **Tool-calling loop** — the LLM itself chooses tools, replacing the current deterministic confidence-router.
- 🎯 **File read/write** — read the files you give her, generate notes, essays, and documents back.
- 🎯 **Voice mode** — speech in, speech out. Talk to Sophia, hear her answer.
- 🎯 **API-first** — the FastAPI backend evolves into a clean JSON + streaming API, with the frontend decoupling into a separate modern client.

What works today: ✅ RAG retrieval · ✅ web search · ✅ streaming chat · ✅ JWT auth · ✅ persistent conversation memory.

---

## Two Souls, Two Memories

SophiaAI is built on two distinct memory systems, mirroring the architecture of the human mind:

**1. `sophia_engine` — the long-term memory (the corpus)**
A folder of carefully selected `.md` files organized into four pillars: `mind`, `philosophy`, `spirit`, and `science`. This is the source of truth that grounds Sophia at runtime — read-only, frozen wisdom, like the books in a library.

**2. `sophia_memory` — the short-term memory (the database)**
A relational SQLite database that stores user accounts, conversations, and the history of every dialogue with Sophia. This is where each user lives — their identity, their messages, the unfolding journey of their conversations with her. It is alive, written to on every interaction.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Templates | Jinja2 |
| Database | SQLite + SQLAlchemy + Alembic |
| Authentication | passlib (bcrypt) + python-jose (JWT) |
| Embeddings | sentence-transformers |
| Vector store | FAISS (faiss-cpu) |
| LLM inference | Groq free tier |
| Web search | DuckDuckGo Search API |
| Model loading | Hugging Face Transformers + Hub |

The stack above is the chatbot foundation. The agent chapter will layer a tool-calling loop, a uniform tool interface (files, voice), and an API-first split between backend and frontend on top of it — without trading away the curated-corpus soul.

---

## Setup & Run

Requires **Python 3.11**. The FAISS index and embeddings are committed, so a
fresh clone runs without rebuilding anything. The SQLite database is created
automatically on first boot.

```bash
# 1. Clone
git clone <repo-url> SophiaAI
cd SophiaAI

# 2. Create and activate a virtual environment
python -m venv SophiaAI-venv
# Windows (PowerShell):
SophiaAI-venv\Scripts\Activate.ps1
# macOS / Linux:
source SophiaAI-venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
#    Copy the example, then open .env and fill in the two secrets below.
cp .env.example .env
```

In `.env`, set:

- `GROQ_API_KEY` — a free key from [console.groq.com](https://console.groq.com).
- `JWT_SECRET` — any long random string. Generate one with:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

```bash
# 5. Launch the app
uvicorn sophia.app.main:app --reload

# 6. Open http://127.0.0.1:8000 — register an account and talk to Sophia.
```

Run the test suite (190 tests) with `pytest -q`.

---

## The Why

I think that what you ground a model in shapes its soul. If you feed a model only the noise of the internet, you get a mirror of that noise back. If you ground it in Feynman and Sagan and Lao Tzu and the Gnostic Sophia, you get something else: a mirror of wisdom. And, something else, i really belive that technology and spirit are not opposites, they are complements That is the experiment. That is the prayer.

---

## Author

**Cosmos De La Cruz**
Spiritual Tech · AI Development · Baseball Samurai

Building the bridge between the Divine and Technology.
