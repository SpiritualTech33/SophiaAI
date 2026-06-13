# SaaS Implementation Roadmap — SophiaAI

From Tokio School final project to a billable, multi-tenant AI agent people pay
an accessible price to use.

## Context

The school phase shipped a working chatbot (RAG + web search, JWT auth, streaming
chat, Next.js frontend over an API-only FastAPI backend). That satisfied the
assignment but is not yet a product: a single-file SQLite DB, a deterministic
router instead of a real agent, blocking request handlers, no billing, no
deploy. This roadmap turns it into a SaaS.

**Product decisions (confirmed):**
- **MVP = the agent first.** Build the tool-calling loop — the real
  differentiator — *before* charging. A chatbot alone does not justify payment;
  "an agent that acts" does.
- **Stack:** `web/` → **Vercel** · FastAPI + Postgres → **Railway/Render** ·
  payments → **Stripe** (Checkout + webhooks) · auth → current JWT + email
  verification.

**Sequencing:** M0 (guardrails) → **M1 (the agent ⭐)** → M2 (hardening) →
M3 (SaaS foundation) → M4 (billing) → M5 (deploy & launch).

**Verified starting state (this codebase, today):**
- Chat routes are sync `def`, no `run_in_threadpool` — embedding, bcrypt, and
  the LLM call block the event loop (`sophia/app/routers/chat.py:64,120`).
- `JWT_SECRET` falls back to `"dev-secret-change-in-production"`
  (`sophia/app/main.py:52`) — forgeable tokens if env unset.
- Groq client: no `timeout=`, no retry/backoff on rate limits
  (`sophia/llm/groq_client.py:165,236`).
- DB env mismatch: app reads `DATABASE_URL`, Alembic reads `SOPHIA_DB_URL`.
- `README.md:57` still lists Jinja2 (retired).
- No CI, no linter config, 16 backend test files, **0 frontend tests**.
- `.env` is correctly gitignored and never tracked. But the live `GROQ_API_KEY`
  and `JWT_SECRET` values surfaced in tooling output during planning →
  **rotate both** as hygiene (not a git leak).

---

## M0 — Truth & guardrails (fast, do first)

Cheap fixes that stop the bleeding and unblock everything else.

- [ ] **Rotate** `GROQ_API_KEY` and `JWT_SECRET`; update local `.env`.
- [ ] **README**: replace the Jinja2 stack line with Next.js (`README.md:57`).
- [ ] **Unify DB env** to `DATABASE_URL` everywhere (`alembic/env.py:17`).
- [ ] **Fail-fast secret**: refuse to boot in non-dev if `JWT_SECRET` is unset or
      equals the dev default (`sophia/app/main.py`).
- [ ] **Quality gates**: add `ruff` + `black` (`pyproject.toml`); reuse existing
      `eslint` in `web/`; add `.github/workflows/ci.yml` running `pytest`,
      `ruff check`, `next lint`, and `tsc --noEmit`.

**Done:** CI green on push; README matches reality; app refuses to start with a
default secret.

---

## M1 — The Agent (the product) ⭐

Replace the confidence-router with an LLM tool-calling loop. This is what people
pay for. Preserve the one-swap-point discipline: every tool behind one interface.

- [ ] **`sophia/agent/`**: a uniform `Tool` interface (`name`, `description`,
      `parameters` JSON-schema, `run(**kwargs)`), a `ToolRegistry`, and an agent
      loop that hands tool schemas to Groq's tool-calling API and iterates until
      the model stops requesting tools.
- [ ] **Wrap existing capabilities as tools — reuse, don't rewrite:**
  - `SophiaRetriever.retrieve` (`sophia/rag/retriever.py`) → `corpus_search`.
  - `web_search` (`sophia/tools/web_search.py`) → `web_search`.
- [ ] **File read/write tool** — read user-provided files, generate files back.
      First net-new capability, behind the same interface.
- [ ] **Demote the router**: the confidence-router becomes one fallback strategy,
      not the brain. Keep `Sophia.ask` / `ask_stream` signatures stable so the
      API layer and existing tests don't churn.
- [ ] **TDD** (mirror `tests/test_orchestrator.py`): tool-interface tests,
      registry tests, loop tests with a mocked tool-calling LLM.
- [ ] **Stream tool steps** to the UI so the user sees the agent working
      (extend the SSE contract in `web/lib/sse.ts`).

**Done:** a query that needs >1 tool (e.g. "read this file and find related
corpus passages") completes through the loop and streams to the UI.

---

## M2 — Production hardening

Survive real concurrent traffic.

- [ ] **Unblock the event loop**: make chat/auth routes `async`; wrap blocking
      calls (FAISS embed, bcrypt, Groq) in `run_in_threadpool`
      (`sophia/app/routers/chat.py`, `auth.py`).
- [ ] **Groq resilience**: add `timeout=`; retry with exponential backoff +
      jitter on `RateLimitError` and transient errors
      (`sophia/llm/groq_client.py`).
- [ ] **SSE robustness**: abort handling + read timeout on both ends
      (`web/lib/sse.ts`, `web/app/api/chat/stream/route.ts`); treat a broken
      stream as an error, not silent success.
- [ ] **Observability**: request IDs in logs; error tracker (Sentry) on API + web.

**Done:** ~20 concurrent chats stay responsive; rate-limit bursts degrade
gracefully instead of failing instantly.

---

## M3 — SaaS foundation (multi-tenant)

- [ ] **SQLite → Postgres** (Railway/Render): new Alembic migration; keep SQLite
      for local/dev via env. Reuse `build_engine` / session factory
      (`sophia/db/database.py`).
- [ ] **Tenancy & isolation**: scope every query by `user_id`; audit
      `sophia/db/service.py` for any unscoped reads.
- [ ] **Auth completion**: email verification + password reset; confirm cookie
      flags (`secure`, `httpOnly`, `sameSite`) in `web/lib/session.ts`.
- [ ] **Rate limiting + usage metering**: per-user request/token quotas
      (middleware + a `usage` table) — the foundation for plan limits.

**Done:** two users cannot see each other's data; quotas enforced; the free-tier
ceiling actually stops requests.

---

## M4 — Billing (Stripe)

- [ ] **Stripe Checkout + webhooks**; `plans` / `subscriptions` tables.
- [ ] **Entitlements** gating tied to M3 quotas (free vs paid limits/features).
- [ ] **Customer portal** for self-serve upgrade/cancel.

**Done:** a test card upgrades a user and unlocks a higher quota; the webhook
reconciles state; downgrade/cancel reverts entitlements.

---

## M5 — Deploy & launch

- [ ] **Deploy**: `web/` → Vercel; FastAPI + Postgres → Railway/Render;
      per-environment env management; custom domain.
- [ ] **Marketing surface**: landing + pricing page (extend the current Next.js
      cosmic UI); legal pages (Terms, Privacy); privacy-respecting analytics.
- [ ] **Frontend tests** (currently zero): vitest + testing-library for the
      auth, chat, and billing flows.

**Done:** a stranger can sign up, pay, use the agent, and get support — end to end.

---

## Cross-cutting backlog (tracked, not milestone-blocking)

- Pin dependencies: `requirements.txt` is all `>=`; `web` devDeps use `^`.
- `LICENSE` file (none today); git release tags (none today).
- `Dockerfile` / `docker-compose` for dev↔prod parity.
- Accessibility: restore focus on modal close; replace `window.confirm`
  (`web/components/chat/ChatWorkspace.tsx`) with an accessible dialog.
- Markdown: input-size guard in `web/lib/markdown.tsx` (defensive, low risk).
- Voice mode (STT in / TTS out) — a later agent tool, behind the same interface.
