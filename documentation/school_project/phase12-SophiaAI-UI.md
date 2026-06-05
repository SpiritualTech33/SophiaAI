# Phase 12 — Templates and Chat UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Front-end design follows the `ui-ux-pro-max` skill (Immersive / Spatial-UI pattern) and the `frontend-design` skill for craft.

**Goal:** Give Sophia a human face. Replace the placeholder HTML stubs in `sophia/app/routers/pages.py` with real Jinja2 templates and a working chat UI. The chat page is a "portal to cosmic intelligence" — a living, metaphysical interface where a user types a question, watches Sophia contemplate, and reads her answer with sources cited. Satisfies the user-facing experience and is the centerpiece of the defense video. No frontend framework, no build step.

**Aesthetic (decided with Cosmos, 2026-05-28):**
- **Avatar — hybrid.** Landing hero = the marble goddess image (IMG_1795). Chat avatar = a **pure CSS/SVG cosmic orb** (no image) next to each Sophia message and as the centerpiece. Brand mark = "SOPHIA" in Cinzel.
- **Palette — deep cosmic (black-hole).** Near-black indigo void, violet + cyan + magenta nebula accents, starfield. See tokens below.
- **Liveness — living portal.** Animated starfield background, orb avatar reacts to idle / thinking / speaking states, "Sophia is contemplating…" typing indicator, messages fade-and-rise in, glow pulse on send. **Every animation gated behind `prefers-reduced-motion`.**
- **Scope — chat-first.** `chat.html` gets the full cosmic portal treatment. `index.html`, `login.html`, `register.html` are themed but simple (shared design system, less motion).
- **Type.** Cinzel (engraved Roman caps) for the SOPHIA wordmark and headings; Inter for body.

**Tech Stack:** Jinja2 >= 3.1 (already in `requirements.txt`), FastAPI `StaticFiles`, vanilla JS (ES modules, `fetch`), CSS custom properties. No npm, no bundler, no CDN JS framework. Google Fonts via `<link>` with `display=swap`.

**Architecture note:** Auth returns a JWT in the JSON response body (`TokenResponse.access_token`), and protected endpoints read it via `OAuth2PasswordBearer` from the `Authorization: Bearer <token>` header (confirmed in `sophia/app/dependencies.py:36`). Therefore the front end stores the token in `localStorage` and attaches it to every `fetch` to `/api/*`. There is no cookie/session flow. Page routes (`/`, `/chat`, `/login`, `/register`) are public HTML shells; the JS inside them enforces auth client-side (redirect to `/login` if no token) and the API enforces it server-side (401).

---

## API Contract (read-only — do not change in this phase)

| Method | Path | Auth | Body / Returns |
|--------|------|------|----------------|
| POST | `/auth/register` | none | `{email, password}` → `201 {access_token, token_type}` (409 if email taken) |
| POST | `/auth/login` | none | `{email, password}` → `200 {access_token, token_type}` (401 on bad creds) |
| POST | `/api/chat` | Bearer | `{message, conversation_id?}` → `{answer, sources[], conversation_id, search_mode}` |
| GET | `/api/conversations` | Bearer | → `[{id, title, created_at, updated_at}]` |
| GET | `/api/conversations/{id}` | Bearer | → `{id, title, messages:[{id, role, content, sources_json, created_at}]}` |

`source` shape: `{text, source_file, pillar, score}`. `role` is `"user"` or `"sophia"`. `search_mode` is a string (e.g. corpus-only / hybrid / web-only) — render as a small badge on Sophia's answers. `sources_json` in conversation detail is a JSON **string** (parse it client-side).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `sophia/app/templates/base.html` | Shared layout: `<head>`, fonts, CSS link, starfield mount, header/footer blocks, `{% block content %}`, `{% block scripts %}` |
| Create | `sophia/app/templates/index.html` | Landing: goddess hero image, SOPHIA wordmark, one-line manifesto, CTAs to login/register |
| Create | `sophia/app/templates/login.html` | Login form (email, password) → POST /auth/login |
| Create | `sophia/app/templates/register.html` | Register form (email, password) → POST /auth/register |
| Create | `sophia/app/templates/chat.html` | The portal: conversation thread, composer, orb avatar, sources, conversation sidebar |
| Create | `sophia/app/static/css/sophia.css` | Full design system: tokens, layout, components, orb, animations, reduced-motion |
| Create | `sophia/app/static/js/cosmos.js` | Shared helpers: token storage, `authFetch`, redirect guard, starfield init |
| Create | `sophia/app/static/js/auth.js` | Login + register form handling (used by login.html, register.html) |
| Create | `sophia/app/static/js/chat.js` | Chat: send message, render messages, orb states, conversation list, sources |
| Create | `sophia/app/static/img/sophia_goddess.webp` | Goddess hero — converted from `c:\Users\serra\Downloads\IMG_1795.JPEG` |
| Create | `sophia/app/static/img/favicon.svg` | Small cosmic orb favicon (SVG) |
| Modify | `sophia/app/routers/pages.py` | Replace inline-HTML stubs with `Jinja2Templates` rendering |
| Modify | `sophia/app/main.py` | Mount `StaticFiles` at `/static`, create `Jinja2Templates`, store on `app.state` |
| Modify | `tests/test_app_pages.py` | Update assertions for the new rendered templates |

**No new Python dependencies.** Jinja2 is already in `requirements.txt:13`.

---

## Design System — Single Source of Truth

Put these in `:root` of `sophia.css`. Every component reads from tokens; **no raw hex inside components** (ui-ux rule `color-semantic`).

```css
:root {
  /* Cosmic palette (deep / black-hole) */
  --void:        #07061a;   /* page background base */
  --void-2:      #0c0a24;   /* gradient stop */
  --surface:     #12102e;   /* panels, composer */
  --surface-2:   #1a1840;   /* user message bubble, raised cards */
  --violet:      #7c5cff;   /* primary accent / Sophia glow */
  --cyan:        #3ad0ff;   /* secondary accent / links */
  --magenta:     #ff6ec7;   /* tertiary accent / highlights */
  --gold:        #c9a227;   /* sacred accent, used sparingly */
  --text:        #e8e6ff;   /* primary text on void */
  --text-dim:    #a7a3d6;   /* secondary text (>=3:1) */
  --danger:      #ff5d6c;   /* form errors */
  --ok:          #5ce6a3;   /* success */
  --border:      #2a2752;   /* dividers, input borders */

  /* Type */
  --font-brand:  'Cinzel', Georgia, serif;
  --font-head:   'Cinzel', Georgia, serif;
  --font-body:   'Inter', system-ui, -apple-system, sans-serif;

  /* Scale (4/8 rhythm) */
  --space-1: 4px; --space-2: 8px; --space-3: 16px;
  --space-4: 24px; --space-5: 32px; --space-6: 48px;
  --radius:   14px;
  --radius-lg: 22px;

  /* Motion */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 180ms;
  --dur:      280ms;

  /* Glass (Spatial-UI). Used on panels; keep blur modest for perf. */
  --glass-bg:   rgba(18, 16, 46, 0.55);
  --glass-blur: 14px;
  --glass-brd:  rgba(124, 92, 255, 0.25);
}
```

**Contrast guards (ui-ux `color-accessible-pairs`):** `--text` on `--void` and on `--surface` must clear 4.5:1; `--text-dim` must clear 3:1. The skill flagged Spatial-UI for "contrast risk" — verify both before delivery. Never put body text directly on a busy nebula region; always on a `--surface`/glass panel.

**Fonts:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
```

**Icons:** inline SVG only (send arrow, logout, new chat, source/book, web-globe for web-search mode). No emoji (ui-ux `no-emoji-icons`).

---

## The Cosmic Orb (pure CSS/SVG, no image)

The orb is Sophia's avatar: a small one (~36px) beside each of her messages, and a large one (~160px) as the chat hero/empty-state centerpiece. Built from stacked radial gradients + a conic-gradient accretion ring.

**Structure** (single element + pseudo-elements, scalable via `font-size`/`--orb-size`):
```html
<span class="orb" data-state="idle" aria-hidden="true"></span>
```
- Core: `radial-gradient` dark center → violet → transparent (the "event horizon").
- Accretion ring: `::before` conic-gradient(violet → cyan → magenta → violet), masked to a ring, slow `rotate` animation.
- Glow halo: `::after` soft blurred radial bloom.

**States** (set via `data-state`, driven by `chat.js`):
| State | Meaning | Motion |
|-------|---------|--------|
| `idle` | waiting | ring rotates slowly (~24s), gentle breathe |
| `thinking` | request in flight | ring accelerates (~6s), halo pulses |
| `speaking` | answer streaming/appended | brief outward pulse, then settle to idle |

All orb motion lives inside `@media (prefers-reduced-motion: no-preference)`. Under reduced-motion the orb is a static gradient (still beautiful, no spin).

---

## Tasks

### Task 1: Wire Jinja2 + StaticFiles into the app

**Files:** Modify `sophia/app/main.py`, `sophia/app/routers/pages.py`.

- [ ] **Step 1 — main.py:** In `create_app()`, after routers are included, compute template/static dirs relative to the package and mount them:
  ```python
  from pathlib import Path
  from fastapi.staticfiles import StaticFiles
  from fastapi.templating import Jinja2Templates

  _APP_DIR = Path(__file__).resolve().parent
  application.mount("/static", StaticFiles(directory=_APP_DIR / "static"), name="static")
  application.state.templates = Jinja2Templates(directory=str(_APP_DIR / "templates"))
  ```
  Keep the `from __future__ import annotations` and existing structure. Add a "Mental Model" note to the docstring that templates/static are now served from `sophia/app/`.

- [ ] **Step 2 — pages.py:** Replace every inline `HTMLResponse(...)` with template rendering. Each route takes `request: Request` and returns `request.app.state.templates.TemplateResponse(request, "name.html", {...})`. Pass nothing secret — these are public shells. Keep four routes: `/`→index.html, `/chat`→chat.html, `/login`→login.html, `/register`→register.html. Update the module docstring (no longer "placeholder stubs").

- [ ] **Step 3 — verify boot:** `uvicorn sophia.app.main:app --reload` starts without error; `GET /` returns the rendered landing (200). **Expected:** no `TemplateNotFound`, `/static/...` resolves.

> Build the templates (Tasks 3–6) before this passes end-to-end. It's fine to create empty template files first so the app boots, then fill them.

---

### Task 2: base.html + design-system CSS + shared JS

**Files:** Create `templates/base.html`, `static/css/sophia.css`, `static/js/cosmos.js`, `static/img/favicon.svg`.

- [ ] **Step 1 — base.html:** A single layout all pages extend.
  - `<head>`: `<meta charset>`, `<meta name="viewport" content="width=device-width, initial-scale=1">` (never disable zoom — ui-ux `viewport-meta`), title block, favicon, font `<link>`s, `<link rel="stylesheet" href="/static/css/sophia.css">`.
  - `<body>`: a `<canvas id="starfield" aria-hidden="true">` fixed behind everything; a header with the **SOPHIA** Cinzel wordmark linking to `/`; `{% block content %}`; a quiet footer ("A bridge between the Divine and Technology"); `<script type="module" src="/static/js/cosmos.js"></script>` then `{% block scripts %}`.
  - Blocks: `{% block title %}`, `{% block content %}`, `{% block scripts %}`.

- [ ] **Step 2 — sophia.css:** Implement the full design system above: tokens in `:root`, base/reset, body gradient background (`--void` → `--void-2`), typography (Cinzel headings, Inter body, base 16px, line-height 1.5), glass panel utility, buttons (primary = violet glow, secondary = ghost), inputs, the `.orb` component + states, message bubbles, sources, badges, header/footer. End the file with a `@media (prefers-reduced-motion: reduce)` block that disables/zeroes every animation. Mobile-first; breakpoints at 768 / 1024. No horizontal scroll. Touch targets ≥44px.

- [ ] **Step 3 — cosmos.js (shared, ES module):** Export small helpers:
  - `getToken()` / `setToken(t)` / `clearToken()` — `localStorage` key `sophia_token`.
  - `authFetch(url, opts)` — wraps `fetch`, injects `Authorization: Bearer ${getToken()}`, and on `401` clears token + redirects to `/login`.
  - `requireAuth()` — if no token, `location.replace('/login')`. (chat.html calls this.)
  - `initStarfield()` — draws drifting stars on `#starfield` via `requestAnimationFrame`; **guard with `matchMedia('(prefers-reduced-motion: reduce)')`** — if reduced motion, paint a static star field once and stop. Throttle to be cheap (cap star count by viewport area; pause on `visibilitychange`).
  - On DOM ready, call `initStarfield()`.

- [ ] **Step 4 — favicon.svg:** tiny self-contained SVG orb (dark core + violet ring). No external refs.

---

### Task 3: index.html (landing — themed, simple)

**Files:** Create `templates/index.html`. Asset: convert goddess image (Task 7).

- [ ] Extend base.html. Hero section:
  - Left/center: **SOPHIA** in Cinzel (large), a one-line manifesto ("Wisdom, grounded. A bridge between the Divine and Technology."), two CTAs — primary "Enter the Portal" → `/register`, secondary "Sign in" → `/login`.
  - Goddess image: `<img src="/static/img/sophia_goddess.webp" alt="Sophia, marble goddess of wisdom, holding a glowing atom over a galaxy" width=... height=... loading="eager">` with explicit dimensions (ui-ux `image-dimension`, avoid CLS). A soft violet glow behind her via CSS; she sits on the starfield.
  - One CTA is the single primary action on the page (ui-ux `primary-action`).
- [ ] If a token already exists in localStorage, offer a "Continue to chat" link (small JS in `{% block scripts %}`), but do not force-redirect (landing is public).
- [ ] Responsive: image stacks above text on mobile; readable measure (≤70 chars) for the manifesto.

---

### Task 4: login.html + register.html (themed, simple)

**Files:** Create `templates/login.html`, `templates/register.html`, `static/js/auth.js`.

- [ ] **Forms:** A centered glass "portal gate" card. Each input has a **visible `<label>`** (not placeholder-only — ui-ux `input-labels`), `type="email"` / `type="password"` (correct mobile keyboard), `autocomplete` (`email`, `current-password` / `new-password`), required indicator, and a password show/hide toggle (ui-ux `password-toggle`). A submit button that disables + shows a spinner during the request (`loading-buttons`). An inline error region with `role="alert"` (`aria-live`) below the form for 401/409 messages with a clear recovery path (`error-clarity`). Register links to login and vice-versa.
- [ ] **auth.js (ES module):**
  - On submit: `preventDefault`, disable button, POST JSON to `/auth/login` or `/auth/register`.
  - On success: `setToken(data.access_token)` then `location.replace('/chat')`.
  - On failure: re-enable button, show the API `detail` message in the error region (e.g. "Invalid email or password", "Email already registered"). Auto-focus the offending field.
  - Read which endpoint to hit from a `data-mode` attribute on the `<form>` (`login` / `register`) so one module serves both pages.
- [ ] Wire each template's `{% block scripts %}` to load `auth.js`.

---

### Task 5: chat.html — the cosmic portal (full treatment)

**Files:** Create `templates/chat.html`. (JS in Task 6.)

- [ ] **Layout (desktop ≥1024):** two columns inside a max-width container.
  - **Sidebar (left):** SOPHIA mark, a "＋ New conversation" button (inline SVG, not emoji), and a scrollable conversation list (titles, newest first). A "Sign out" action **visually separated at the bottom** (ui-ux `destructive-nav-separation`) → clears token, redirects to `/`.
  - **Main (right):** the conversation thread (scrollable) + a fixed composer at the bottom.
- [ ] **Mobile (<1024):** sidebar collapses behind a menu toggle; thread is full-width; composer pinned to bottom with safe-area padding. No nested scroll traps (ui-ux `scroll-behavior`).
- [ ] **Empty state:** large cosmic **orb** centered with a line like "Ask Sophia anything." plus 3 example prompts as tappable chips (ui-ux `empty-states`). The orb sits in `idle`.
- [ ] **Message thread markup:** Sophia messages render with a small `.orb` avatar + a glass bubble; below the answer, a collapsible "Sources" disclosure listing each source (pillar tag, source_file, score), and a small `search_mode` badge (corpus / hybrid / web — book icon vs globe icon). User messages render as a right-aligned `--surface-2` bubble, no avatar. Long text wraps (no truncation — `truncation-strategy`).
- [ ] **Composer:** a `<textarea>` (auto-grow, Enter to send, Shift+Enter for newline), and a send button (inline SVG arrow, ≥44px, disabled while a request is in flight). A "Sophia is contemplating…" typing indicator row (with the orb in `thinking`) shown between send and response.
- [ ] **Scripts block:** load `chat.js`.

---

### Task 6: chat.js — behavior, states, rendering

**Files:** Create `static/js/chat.js` (ES module, imports from `cosmos.js`).

- [ ] **On load:** `requireAuth()`. Fetch `GET /api/conversations`, render the sidebar list. Track `currentConversationId = null` (null = a fresh conversation; the first send creates one server-side and returns its id).
- [ ] **Render helpers:** `appendUserMessage(text)`, `appendSophiaMessage({answer, sources, search_mode})`. Build DOM with `document.createElement` and `textContent` (no `innerHTML` with server/user strings — **XSS guard**; parse markdown only if explicitly added later). Messages fade-and-rise in via a CSS class (gated by reduced-motion). Auto-scroll to newest.
- [ ] **Send flow:**
  1. Read textarea, ignore empty/whitespace. Clear + disable composer.
  2. `appendUserMessage`, show typing indicator, set hero/avatar orb → `thinking`.
  3. `authFetch('/api/chat', {method:'POST', body: JSON.stringify({message, conversation_id: currentConversationId})})`.
  4. On success: hide typing indicator, orb → `speaking` (then settle to `idle`), `appendSophiaMessage(...)`, set `currentConversationId = data.conversation_id`. If the sidebar had no entry for it, refresh the conversation list (or optimistically prepend).
  5. On error/timeout: hide indicator, orb → `idle`, show an inline retryable error bubble (ui-ux `timeout-feedback`, `error-recovery`). Re-enable composer.
- [ ] **Load a past conversation:** clicking a sidebar item → `GET /api/conversations/{id}`, clear thread, render each message (parse `sources_json` string for Sophia messages), set `currentConversationId`, highlight the active item (ui-ux `nav-state-active`), preserve nothing else.
- [ ] **New conversation:** reset thread to empty state, `currentConversationId = null`.
- [ ] **Sign out:** `clearToken()` → `location.replace('/')`.
- [ ] **Accessibility:** typing indicator uses `aria-live="polite"`; composer textarea has a label; send button has `aria-label`; focus returns to the textarea after each send.

---

### Task 7: Goddess hero asset

**Files:** Create `static/img/sophia_goddess.webp`.

- [ ] Copy + convert `c:\Users\serra\Downloads\IMG_1795.JPEG` → WebP, optimized for web (target ≤300 KB, max ~1200px on the long edge). Use Pillow (already pulled in transitively) or any local tool. Keep the original aspect ratio; record the pixel `width`/`height` to hard-code in `index.html` (CLS guard). Confirm the file loads at `/static/img/sophia_goddess.webp`.

> If WebP conversion isn't trivially available, fall back to a compressed `.jpg` — but prefer WebP (ui-ux `image-optimization`).

---

### Task 8: Update page tests

**Files:** Modify `tests/test_app_pages.py`.

- [ ] The four existing tests assert substrings ("SophiaAI", "Chat", "Login", "Register"). After templating, update them to assert the rendered templates return 200 and contain stable markers — e.g. landing contains `SOPHIA` and a link to `/register`; `/chat` contains the composer/orb marker; `/login` and `/register` contain their form `data-mode`. Avoid asserting on volatile copy. **Do not** add JS/browser tests (out of scope; verified manually).
- [ ] Existing `conftest.py` `client` fixture should still work since the app now mounts static/templates at startup. If `Jinja2Templates`/`StaticFiles` need the dirs to exist at import/boot, ensure the template files exist before running tests.
- [ ] **Run:** `pytest tests/test_app_pages.py -v` → 4 passing. Then full `pytest -q` → all 142 prior tests still green (no regressions in auth/chat/schemas).

---

## Manual Verification (the part automated tests can't cover)

The UI is the deliverable; per CLAUDE.md and `superpowers:verification-before-completion`, **drive it in a browser before claiming done.**

- [ ] `uvicorn sophia.app.main:app --reload`, open `http://127.0.0.1:8000/`.
- [ ] Landing renders: goddess image loads, SOPHIA wordmark in Cinzel, starfield drifting, CTAs work.
- [ ] Register a new user → lands on `/chat` authenticated. Reload `/chat` → stays (token persists). Open `/chat` in a fresh private window with no token → redirects to `/login`.
- [ ] Send a corpus question ("What does Lao Tzu say about water?") → orb goes thinking → answer appears with sources + a corpus/hybrid badge. Send a current-events question → web-search badge.
- [ ] New conversation, then switch back to the first via the sidebar → full history reloads with sources.
- [ ] Sign out → back to `/`, token cleared, `/chat` now redirects to `/login`.
- [ ] **Responsive:** test at 375px and 1440px — no horizontal scroll, composer reachable, sidebar collapses on mobile.
- [ ] **Reduced motion:** enable OS "reduce motion" → starfield static, orb static, messages appear without slide; everything still usable.
- [ ] **Contrast:** spot-check `--text`/`--text-dim` on `--void` and on glass panels meet 4.5:1 / 3:1.

---

## Self-Review Checklist (before merge)

**Craft (ui-ux-pro-max Pre-Delivery):**
- [ ] No emoji as icons — all icons are inline SVG.
- [ ] One primary CTA per page; destructive actions (sign out) visually separated.
- [ ] Visible labels on all inputs; errors near the field with `role="alert"`; loading state on submit.
- [ ] `prefers-reduced-motion` respected everywhere (starfield, orb, message entrance).
- [ ] Focus states visible; tab order matches visual order; touch targets ≥44px.
- [ ] Images have alt text + explicit dimensions; goddess image is WebP, lazy where below fold.
- [ ] No raw hex in components — only design tokens. Light text never on bare nebula.

**Security / correctness:**
- [ ] All user/server strings rendered via `textContent` — no `innerHTML` injection path (XSS).
- [ ] `authFetch` attaches the Bearer token and handles 401 by clearing + redirecting.
- [ ] No secrets in templates or JS; token only in `localStorage`.

**Project conventions (CLAUDE.md):**
- [ ] `from __future__ import annotations` on the two modified Python files.
- [ ] Library code raises, never `sys.exit`. Page routes degrade gracefully.
- [ ] "Mental Model" docstrings on modified Python functions; plain-English comments only where the WHY is non-obvious.
- [ ] Shared logging format untouched.

---

## Out of Scope (later phases)

- Streaming token-by-token responses (current API returns the full answer).
- Markdown rendering inside answers (plan renders plain text; revisit if needed).
- Conversation rename/delete UI (API has no endpoints for it yet).
- Alembic migrations (Phase 13), broader test suite (Phase 14), Makefile/run docs (Phase 15).

---

## Suggested Commits (per project workflow)

Branch: `feat/phase-12-templates-chat-ui`.
1. `feat(phase12): wire Jinja2 + StaticFiles, base layout and design system`
2. `feat(phase12): landing, login, register pages with auth JS`
3. `feat(phase12): cosmic chat portal — orb avatar, sources, conversation sidebar`
4. `feat(phase12): goddess hero asset + update page tests`

Merge to master with `--no-ff`. Append a Phase 12 entry to `cosmos_log.md` (what was built, the aesthetic decisions and why, lessons, next step = Phase 13 Alembic).