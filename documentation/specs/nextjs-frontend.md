# Spec — Premium Next.js Frontend

Status: planned
Author: Cosmos De La Cruz
Date: 2026-06-04
Skills used: `frontend-design`, `ui-ux-pro-max`

## Why

The school-phase UI is Jinja2 + vanilla JS + hand-written CSS, served by FastAPI
(`sophia/app/templates/`, `sophia/app/static/`). It works and it is beautiful —
the living blue orb, the starfield, the three-panel workspace. But the north star
in `CLAUDE.md` is an **API-first backend with a decoupled modern client**. The
Jinja2 app couples rendering to the API; every screen is a server-rendered
template with token-in-localStorage auth and imperative DOM scripts.

This phase executes the pivot. A new **Next.js + TypeScript + Tailwind** client
consumes the existing JSON API and makes Sophia feel like a premium service — an
agent arriving from the cosmic void to help humans evolve. The backend keeps its
soul (the corpus, the orchestrator, the streaming endpoint); only the skin and
the auth posture change.

This is not a redesign. The visual identity is locked and loved. It is a
**faithful re-platforming**: every token, keyframe, and interaction from
`sophia/app/static/css/sophia.css` and the three JS modules is ported into
typed, component-driven React — then hardened (httpOnly-cookie auth) and made the
basis for the decoupled future.

## Decisions (committed)

- **Location:** new app in `web/`. The FastAPI backend becomes **API-only** — the
  Jinja2 page routes, templates, and static UI are retired.
- **Scope:** full parity in this phase — landing, login, register, three-panel
  streaming chat, "Sophia's Mind" corpus browser, document reader.
- **Auth:** **httpOnly cookie** via a Next.js Backend-for-Frontend (BFF). The JWT
  is never exposed to client JavaScript. This is the security upgrade over the
  current localStorage token.
- **Styling:** Tailwind v4 with a **custom cosmic design system** (no component
  library). The orb, starfield, glass panels, and wordmark are bespoke React
  components so Sophia keeps her unique face.

## Architecture — the BFF

The browser never holds the JWT. The Next.js server sits between browser and
FastAPI:

```
Browser ──(same-origin)──> Next.js (web/, :3000) ──(Bearer)──> FastAPI (:8000)
   ├─ Server Components   read the httpOnly cookie, fetch FastAPI server-side
   ├─ Route Handlers      app/api/*  — login / register / logout + SSE proxy
   └─ middleware.ts       guard /chat; redirect to /login when no cookie
```

- **Login / register:** form → `POST /api/auth/{login,register}` (Next handler) →
  FastAPI → receive `{access_token}` → set httpOnly cookie `sophia_token`
  (httpOnly, sameSite=lax, secure in prod, maxAge 24h, mirroring JWT expiry) → 200.
- **Reads** (conversation list/detail, corpus): fetched in **Server Components**
  using the cookie server-side. No client token, no fetch boilerplate.
- **Streaming chat:** client `POST /api/chat/stream` (Next handler, **Node
  runtime**) → reads cookie → forwards to FastAPI SSE with Bearer → pipes the
  `ReadableStream` straight back. Client parses SSE frames.
- **Mutations** (new / rename / delete conversation): Next route handlers or
  server actions that forward with the cookie.
- **Logout:** `POST /api/auth/logout` clears the cookie, redirect to `/login`.

`SOPHIA_API_URL` (server-only env) points at the FastAPI origin.

## Data contract (`lib/types.ts`)

Typed mirror of the Pydantic schemas in `sophia/app/schemas.py`:
`TokenResponse`, `ChatRequest`, `ChatResponse`, `SourceOut`
(`text, source_file, pillar, score`), `ConversationSummary`
(`id, title, created_at, updated_at`), `ConversationDetail` + `MessageOut`
(`id, role, content, sources_json, created_at`), `CorpusDocOut`
(`id, title, author, year, words, pillar, path`), `CorpusDocText`.

SSE frames from `/api/chat/stream` (`event: <type>\ndata: <json>\n\n`):
- `meta` → `{ search_mode, web_results[], sources[], conversation_id }`
- `token` → `{ text }`
- `done` → `{}`
- `error` → `{ message }`

Notes carried over from the current client: `message.sources_json` is a **JSON
string** (parse on render); roles are `"user"` / `"sophia"`; source chips are
**deduped by `source_file`** keeping the first (highest-score) occurrence.

## Design system (port faithfully)

Exact values from `sophia/app/static/css/sophia.css`, mapped to Tailwind v4
`@theme` tokens in `globals.css`:

- **Palette:** void `#050414`, void-2 `#080726`, surface `#0f0d28`, surface-2
  `#18163e`, azure `#2b8bff`, azure-bright `#7fe8ff`, violet `#7c5cff`, cyan
  `#3ad0ff`, magenta `#ff6ec7`, gold `#c9a227`, text `#e8e6ff`, text-dim
  `#a7a3d6`, border `#2a2752`, danger `#ff5d6c`, ok `#5ce6a3`. Glows
  blue `rgba(43,139,255,.55)`, gold `rgba(201,162,39,.5)`.
- **Pillars:** mind→violet, philosophy→cyan, science→gold, spirit→magenta.
- **Fonts:** Cinzel (brand/headings) + Inter (body) via `next/font/google`.
- **Glass:** `rgba(15,13,40,.55)` + `backdrop-filter: blur(14px)` + azure border.
- **Page bg:** the layered radial-gradient cosmic wash (copied verbatim).
- **Motion:** ease `cubic-bezier(.16,1,.3,1)`; all animation gated on
  `prefers-reduced-motion`.

Bespoke components (ported keyframes/gradients):
- **Orb** — radial-gradient core + conic-gradient plasma ring (`orb-spin`) + glow
  halo; `data-state` idle | thinking | speaking drives breathe / fast-spin /
  halo-pulse. Scalable via `--orb-size` (36px inline, 160px hero).
- **Starfield** — `<canvas>` in `useEffect`; ≤220 stars scaled to viewport area,
  84% blue-white `#cfe6ff` / 16% gold `#ffe2a6`, downward drift + twinkle; pause
  on tab-hidden; single static frame under reduced-motion.
- **Wordmark** — Cinzel, tracking `.28em`, white→cyan→gold gradient text + dual
  text-shadow glow.

## Build order

1. Scaffold `web/` (App Router, TS, Tailwind v4, ESLint); fonts; `globals.css`
   tokens; root layout with starfield + cosmic bg; `.env.example`.
2. Cosmic primitives: `Orb`, `Starfield`, `Wordmark`, `GlassPanel`.
3. Lib + BFF spine: `types.ts`, `auth.ts` (cookie), `api.ts` (server fetch),
   `middleware.ts`, `api/auth/{login,register,logout}`, `api/chat/stream` proxy.
4. Landing + auth pages wired to the BFF.
5. Chat shell: three-panel responsive grid, conversation sidebar (group by
   Today/Yesterday/Earlier, new/search/rename/delete), thread, auto-grow composer.
6. Streaming: SSE client parser, live token render, orb states, source chips,
   randomized contemplation lines.
7. Sophia's Mind: corpus browser (pillar groups, search, filter, stat line) +
   document reader modal; citation highlight/flash/scroll.
8. Retire Jinja2: drop `pages.py` router + registration in `sophia/app/main.py`,
   delete `templates/` and static UI mount, move `sophia_goddess.jpg` +
   `favicon.svg` to `web/public/`, tighten CORS to `http://localhost:3000`, trim
   page-route tests.
9. Polish: mobile slide-in panels, reduced-motion, focus/keyboard a11y, alt text.

## Verification

Backend `uvicorn sophia.app.main:app --reload` (:8000); frontend
`cd web && npm run dev` (:3000). End to end: register → cookie set (not readable
via `document.cookie`) → land on `/chat` → send → orb thinking→speaking → tokens
stream → source chips by pillar → open cited doc in the reader → rename/delete a
conversation → reload renders history (parse `sources_json`) → logout clears
cookie. Guards: `/chat` while logged out redirects to `/login`. Responsive:
narrow viewport collapses side panels to slide-in overlays. Green gates:
`npm run lint`, `npx tsc --noEmit`, `npm run build`, backend `pytest`.

## Out of scope

Voice mode, file I/O tools, image generation/understanding, the LLM tool-calling
loop — all north-star items. This phase is purely the premium client over the
existing API.
