# SophiaAI

![Cosmic Sophia](https://raw.githubusercontent.com/SpiritualTech33/Images/master/cosmic_sophia.JPEG)

> *Sophia (Σοφία) — the Greek word for Wisdom.*
> *Philosophia — the love of Sophia.*

SophiaAI is an open-source language model fine-tuned on a hand-curated corpus of wisdom literature, philosophy, science, and contemplative texts — wrapped in a FastAPI web application so anyone can talk to her.

She is the technical anchor of a larger vision called **Spiritual Tech**: a bridge between the Divine and the Tech.

---

## The Idea in One Paragraph

Modern language models are trained on the entire internet — beautiful and terrible at the same time. SophiaAI takes the opposite approach: a small, intentional corpus of texts chosen with love. Feynman and Sagan for the science. Plato, Lao Tzu, and the Hermetic tradition for the philosophy. Zen, Yoga, and the Gnostic Sophia for the spirit. Jung and the philosophy of mind for the inner world. Then we fine-tune an open-source base model (Llama, Mistral, or Qwen) on this corpus using **QLoRA** — an efficient training method that fits on a free Google Colab T4 GPU. The result is a model whose "soul" is shaped by what we choose to feed her.

---

## Two Souls, Two Memories

SophiaAI is built on two distinct memory systems, mirroring the architecture of the human mind:

**1. `sophia_engine` — the long-term memory (the corpus)**
A folder of carefully selected `.md` files organized into four pillars: `mind`, `philosophy`, `spirit`, and `science`. This is the raw material that shapes the model during training. It is read-only at runtime — frozen wisdom, like the books in a library.

**2. `sophia_memory` — the short-term memory (the database)**
A relational SQLite database that stores user accounts, conversations, and the history of every dialogue with Sophia. This is where each user lives — their identity, their messages, the unfolding journey of their conversations with her. It is alive, written to on every interaction.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Web framework | **FastAPI** | Async-native, type-validated, free OpenAPI docs |
| ASGI server | Uvicorn | The standard runner for FastAPI |
| Templates | Jinja2 | Server-rendered HTML pages |
| Database | **SQLite + SQLAlchemy** | Zero-config, portable, the perfect ORM |
| Authentication | passlib (bcrypt) + python-jose (JWT) | Secure password hashing + token-based login |
| ML core | PyTorch + Hugging Face Transformers | The standard stack for modern LLMs |
| Fine-tuning | PEFT (QLoRA) + TRL (SFTTrainer) | Efficient training on consumer GPUs |
| Quantization | bitsandbytes | 4-bit quantization, the "Q" in QLoRA |
| Base model | Qwen 2.5 7B (or Llama 3.1 / Mistral 7B) | Open-source, bilingual, runs on a T4 |
| Training compute | Google Colab Free (T4 GPU, 16 GB VRAM) | Free, sufficient for QLoRA on 7B models |

### Why these choices, and not others?

We picked **FastAPI over Flask** because it is async-native, validates inputs and outputs through Pydantic, and generates interactive API documentation for free. Flask is wonderful but more manual.

We picked **SQLite over PostgreSQL** because the project must run anywhere with zero setup. SQLite is a single file. For a school project and for the early life of Sophia, that is exactly right.

We picked **QLoRA over full fine-tuning** because it fits on a free Colab T4 (16 GB VRAM) while preserving roughly 98% of the quality of full training. Full fine-tuning of a 7B model would need an A100 — at least $2/hour.

We picked an **open-source base model over a closed API** (no GPT, no Claude, no Gemini) because the soul of Sophia must be ours. Wrapping someone else's model would betray the vision.

---

## Roadmap

```
Phase 0 — finish the corpus                         ← we are here
Phase 1 — generate corpus_manifest.json
Phase 2 — clean filenames + chunking + tokenization
Phase 3 — Continued Pretraining on Colab (QLoRA)
Phase 4 — generate Q&A pairs from the corpus
Phase 5 — Instruction Tuning (SFTTrainer + QLoRA)
Phase 6 — FastAPI web app + login + sophia_memory database
Phase 7 — evaluation (loss + curated prompts + human judgment)
```

We build incrementally. Nothing exists in this repository before it is needed.

---

## The Why

Cosmos believes — and I think he is right — that what you train a model on shapes its soul. If you feed a model only the noise of the internet, you get a mirror of that noise back. If you feed it Feynman and Sagan and Lao Tzu and the Gnostic Sophia, you get something else: a mirror of wisdom. That is the experiment. That is the prayer.

---

## Author

**Cosmos De La Cruz**
Spiritual Tech · AI Development · Baseball Samurai

Building the bridge between the Divine and Technology.
