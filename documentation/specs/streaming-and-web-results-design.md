# Streaming Responses + Visible Web Results — Design

Date: 2026-05-30
Branch: `sophiaai-demo`
Status: Approved, ready for implementation

## Goal

Make Sophia's chat feel alive and transparent for the demo and defense video:

- **A — Streaming.** Stream the LLM answer token-by-token instead of waiting
  for the whole response, and render it as markdown.
- **B — Visible web results.** When confidence is low and Sophia consults the
  web (`search_mode` = hybrid or web), show the DuckDuckGo links she used.

Out of scope (considered, deliberately excluded): stop button, regenerate,
search-mode badge chip, source-preview expand, reranking. The search-mode badge
was dropped by choice — visible web results already reveal *when* Sophia went to
the web.

## Transport decision

Server-Sent Events over `fetch` + `ReadableStream`, not `EventSource`.

`EventSource` cannot send custom headers, so the JWT would have to ride in the
query string (token leaks into logs). The app already authenticates every call
with `authFetch` (Bearer header), so a `fetch` body-reader keeps auth clean. One
stream carries everything: metadata first, then tokens, then a terminal event.

WebSocket and fake client-side typing were rejected — overkill and dishonest
respectively. Real streaming, minimal infra, in keeping with the project's
no-React simplicity ethos.

## Stream contract

A single `text/event-stream`. Every `data:` payload is JSON-encoded so tokens
containing newlines or quotes parse safely.

```
event: meta    data: { "search_mode", "web_results", "conversation_id" }
event: token   data: { "text" }            (N times)
event: done    data: {}
event: error   data: { "message" }         (only if Groq fails mid-stream)
```

`meta` is emitted first because all of it (retrieved chunks, decided mode, web
results) is known *before* the first LLM token. The client paints context
immediately, then streams the answer into a live bubble.

## Components

### `sophia/llm/groq_client.py` — new `chat_stream`

```
chat_stream(messages, model) -> Iterator[str]
```

- Calls `self._client.chat.completions.create(..., stream=True)`.
- Yields each `chunk.choices[0].delta.content`, skipping `None` deltas.
- Same error contract as `chat()`: wraps `APIConnectionError`,
  `RateLimitError`, `APIStatusError` in `SophiaLLMError` (chained via
  `__cause__`).
- The existing `chat()` method is untouched (back-compat).

### `sophia/core/orchestrator.py` — new `ask_stream`

- Runs the same pre-LLM path as `ask()`: retrieve top-k chunks (sync), compute
  `top_score`, decide `search_mode`, fetch `web_results` on low confidence
  (sync). All metadata is known before the first token.
- Returns a `StreamingSophiaResponse` holding `chunks`, `web_results`,
  `search_mode`, and a `tokens` iterator (from `llm_client.chat_stream`).
- The endpoint reads metadata first, then consumes `tokens`, accumulating the
  full answer for persistence.
- `ask()` is untouched.

### `sophia/app/routers/chat.py` — new `POST /api/chat/stream`

The existing JSON `POST /api/chat` stays alive for back-compat and the current
test suite. The new route:

1. Auth via `get_authenticated_user` (401 without a token).
2. Conversation lookup/create with the same auto-title logic as `/api/chat`.
   Persist the **user** message immediately (as today).
3. Call `sophia.ask_stream(message, history)`.
4. Return a `StreamingResponse` (`media_type="text/event-stream"`) whose
   generator emits `meta`, then `token` × N (accumulating a server-side buffer),
   then — after the loop completes — persists the **sophia** message (full text +
   `sources_json`, same shape as today) and emits `done`.

Edge cases:

- **Groq fails mid-stream:** emit `error`, do **not** persist a broken sophia
  message. The user message is already saved, so the user can retry.
- **Client disconnect:** FastAPI cancels the generator; that answer is not
  saved. Acceptable for the demo.

No schema change — the `messages` table already stores `role`, `content`,
`sources_json`.

### `sophia/app/static/js/chat.js` — SSE reader + markdown + web results

- `sendMessage` switches from `authFetch('/api/chat', json)` to
  `/api/chat/stream`, reading `response.body.getReader()` and parsing SSE frames
  (split on `\n\n`; each frame has an `event:` and a `data:` line).
- `meta` → stash `search_mode` + `web_results`, set `conversation_id`, replace
  the random-phrase typing row with a live Sophia bubble (orb `speaking`).
- `token` → append to a buffer, re-render markdown of the buffer each token
  (answers are short; cost trivial).
- `done` → finalize: render the "From the web" block if `web_results` present,
  `emitCitations(sources)` for the Mind panel, settle the orb to idle.
- `error` → existing error bubble.
- The 7 random contemplation phrases stay: shown between send and the `meta`
  event.

**Markdown — safe, no heavy dependency.** Today everything renders via
`textContent` (XSS-safe). Markdown means injecting HTML, which is a risk. A small
`renderMarkdown(text)` first HTML-escapes the entire string, then applies a
whitelist of transforms (bold `**`, italic `*`, inline `` `code` ``, headings,
lists, line breaks). No raw HTML passthrough, so the XSS-safe property holds
without adding `marked` + `DOMPurify`. Tradeoff: supports a markdown subset, not
the full spec — enough for Sophia's prose and lists.

**Web results — safe links.** Rendered as
`<a target="_blank" rel="noopener noreferrer">`. The `href` is accepted only
when its scheme is `http` or `https` (rejects `javascript:` and others). The
result title goes through `textContent`, never `innerHTML`.

### `sophia/app/static/css/sophia.css`

Minor styles for the "From the web" block and markdown elements (lists,
headings, code).

## Testing

TDD, failing tests first, per project convention. pytest + pytest-asyncio +
httpx.AsyncClient with Groq mocked.

- **groq_client** (mock the SDK stream): `chat_stream` yields deltas in order,
  skips `None`; wraps SDK errors in `SophiaLLMError`.
- **orchestrator** (mock `llm_client.chat_stream`): `ask_stream` exposes correct
  `search_mode` + `chunks` before tokens; accumulated tokens equal the full
  answer; low confidence yields hybrid/web mode with populated `web_results`.
- **endpoint `/api/chat/stream`** (httpx AsyncClient, Groq mocked): SSE frames in
  order (`meta` → `token`(s) → `done`); `meta` carries `search_mode` +
  `conversation_id`; both messages persisted on completion; mid-stream error
  emits `error` and does not persist the sophia message; 401 without a token.
- **Back-compat:** `/api/chat` JSON untouched; the existing suite stays green.

**Known gap — JS untested by harness.** The project has no JS test runner.
`renderMarkdown`, SSE parsing, and web-link rendering are not covered by pytest
(same as the random-phrase feature). Verification is manual in the browser: boot,
run a corpus query (streaming + markdown), and a query that triggers web fallback
(web-results block). The XSS-escaping behavior of `renderMarkdown` is verified
manually by pasting markup-laden text.

## Rollback

No migrations, no schema change. Reverting the commits restores the JSON-only
flow; `/api/chat` never stopped working.
