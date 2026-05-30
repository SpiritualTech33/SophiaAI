# SophiaAI

![Cosmic Sophia](https://raw.githubusercontent.com/SpiritualTech33/Images/master/cosmic_sophia.JPEG)

> *Sophia (Σοφία) — the Greek word for Wisdom.*
> *Philosophia — the love of Sophia.*

SophiaAI is an open-source AI assistant grounded in a hand-curated corpus of wisdom literature, philosophy, science, and contemplative texts — wrapped in a FastAPI web application so anyone can talk to her.

She is the technical anchor of a larger vision called **Spiritual Tech**: a bridge between the Divine and the Tech.

---

## The Idea in One Paragraph

Modern language models are trained on the entire internet — beautiful and terrible at the same time. SophiaAI takes the opposite approach: a small, intentional corpus of texts chosen with love. Feynman and Sagan for the science. Plato, Lao Tzu, and the Hermetic tradition for the philosophy. Zen, Yoga, and the Gnostic Sophia for the spirit. Jung and the philosophy of mind for the inner world. An open-source base model is connected to this corpus through a RAG pipeline — so when you ask Sophia something, she retrieves the exact passages that are relevant and builds her answer on top of them, citing real sources rather than improvising from training memory. When the answer lives beyond the corpus, she reaches out through a web search tool and brings the truth back. The soul is the corpus. The RAG pipeline is the memory. The web search is the curiosity.

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
| LLM inference | Groq free tier (Llama 3 / Gemma) |
| Web search | DuckDuckGo Search API |
| Model loading | Hugging Face Transformers + Hub |

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

Run the test suite (171 tests) with `pytest -q`.

---

## The Why

I think that what you ground a model in shapes its soul. If you feed a model only the noise of the internet, you get a mirror of that noise back. If you ground it in Feynman and Sagan and Lao Tzu and the Gnostic Sophia, you get something else: a mirror of wisdom. And, something else, i really belive that technology and spirit are not opposites, they are complements That is the experiment. That is the prayer.

---

## Author

**Cosmos De La Cruz**
Spiritual Tech · AI Development · Baseball Samurai

Building the bridge between the Divine and Technology.
