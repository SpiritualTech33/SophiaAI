# Plan — File Read & Generate for SophiaAI

## Context

Today SophiaAI only answers from her corpus + web. The user wants two new
capabilities in the chat UI:

1. **Upload** files (txt, md, PDF, docx) so **Sophia can read them** and use
   their content when answering.
2. **Download** files **Sophia generates** — any of her answers exported as
   txt, md, PDF, or docx.

Confirmed scope decisions:
- **Read path:** parse uploaded file → raw text → inject into the prompt with a
  size cap (no per-file embedding/RAG for v1). Reuses existing prompt assembly.
- **Download = Sophia-generated:** export a Sophia answer to the chosen format.
  No re-download of uploads in v1.
- **Input formats:** txt/md, PDF, docx. (Legacy binary `.doc` skipped.)
- **Output formats:** txt/md, PDF, docx.

This lands as a **tool-shaped module** (`sophia/files/`) behind a single
interface, so when the agent phase (LLM tool-calling loop) arrives, Sophia can
call `read_file` / `generate_file` herself with zero rewrite. v1 wires them
deterministically (attach + export button); the agent reuses the same functions.

## Architecture Decisions

- **One-swap-point module `sophia/files/`** — parsing and generation live behind
  two pure functions (`extract_text`, `render_file`). Matches the codebase's
  "each tool behind one interface" rule (CLAUDE.md). The router and the future
  agent loop both call these; no logic scattered in endpoints.
- **Inject, don't embed (v1).** Uploaded text is injected into
  `_build_system_prompt` alongside corpus passages, truncated to a char cap.
  Simple, ships now, good for small/medium docs. Embedding big files into an
  ephemeral FAISS index is a documented future upgrade, not v1.
- **Persist uploads, render exports on the fly.** Store the raw upload on disk
  per-user + cache its extracted text in the DB (parse once). Generated files
  are streamed straight to the browser — no need to persist them.
- **Pure-Python generation, no system deps.** `fpdf2` for PDF and `python-docx`
  for docx avoid WeasyPrint/wkhtmltopdf native-binary pain on Windows.

## Backend Changes

### 1. Dependencies — `requirements.txt`
Add `pypdf` (PDF read), `python-docx` (docx read + write), `fpdf2` (PDF write).
`python-multipart` is already installed.

### 2. New module `sophia/files/` (the tool boundary)
- `sophia/files/parsers.py`
  - `extract_text(data: bytes, mime: str, filename: str) -> str` — dispatch by
    type: txt/md decode as UTF-8; PDF via `pypdf`; docx via `python-docx`.
    Each branch wrapped in `try/except` → on failure raise a clear
    `FileParseError` (library code raises, never `sys.exit` — CLAUDE.md).
  - Allowlist of accepted extensions/mimes + a `MAX_UPLOAD_BYTES` guard.
- `sophia/files/generators.py`
  - `render_file(content: str, fmt: Literal["txt","md","pdf","docx"]) -> tuple[bytes, str]`
    returns (bytes, mime). txt/md = encode; pdf = `fpdf2` paragraphs; docx =
    `python-docx` paragraphs. Markdown is written as-is (light formatting); a
    richer md→styled-PDF pass is a noted future improvement.
- "Mental Model" docstrings on both, per house style.

### 3. DB — `sophia/db/models.py` + Alembic
- New `UserFile` model: `id`, `user_id` (FK), `conversation_id` (FK, nullable),
  `original_filename`, `stored_path`, `mime_type`, `extracted_text` (Text),
  `size_bytes`, `created_at`. Relationship + cascade like `Conversation`.
- Alembic migration for the new table. **Gotcha (CLAUDE.md):** app reads
  `DATABASE_URL`, Alembic reads `SOPHIA_DB_URL` — set the right env when running
  `alembic upgrade head`.

### 4. Service layer — `sophia/db/service.py`
- `create_user_file(...)`, `get_user_file(session, file_id, user_id)` (ownership
  enforced — returns None / raises if not owner), `get_files_text(session, ids,
  user_id)` for chat injection. Same style as existing `add_message` etc.

### 5. New router `sophia/app/routers/files.py`
- `POST /api/files/upload` (multipart, `get_authenticated_user`):
  validate size + extension/mime → save raw bytes to
  `data/user_uploads/{user_id}/{uuid}{ext}` (never trust client filename for the
  path) → `extract_text(...)` → persist `UserFile` → return
  `{id, filename, mime, chars}`.
- `POST /api/files/generate` (JSON, auth): body `{content, format}` →
  `render_file(...)` → `StreamingResponse`/`Response` with
  `Content-Disposition: attachment; filename=...` and the right media type.
- Register the router in `sophia/app/main.py` (alongside auth/chat/corpus).

### 6. Wire reading into chat — `schemas.py`, `routers/chat.py`, `core/orchestrator.py`
- Extend `ChatRequest` with `attached_file_ids: list[int] = []`
  (`sophia/app/schemas.py`).
- In `chat.py` (both `/api/chat` and `/api/chat/stream`): fetch the files'
  `extracted_text` via the service (ownership-checked) and pass to the
  orchestrator.
- `core/orchestrator.py`: `ask` / `ask_stream` take an optional
  `attachments: list[str]`; `_build_system_prompt` (orchestrator.py:186) injects
  them as a clearly-labelled "User-provided documents" block **before** corpus
  passages, truncated to a char cap with a "[truncated]" marker.

### 7. Tests — `tests/test_app_files.py` (+ orchestrator test)
- Upload each format → 200 + text extracted; reject oversize / bad type.
- Download ownership: user B cannot read user A's file.
- `/api/files/generate` returns correct bytes + `Content-Disposition` per format.
- Orchestrator injects attachment text into the system prompt (unit test).
- Follow `tests/conftest.py` fixtures (`test_app`, `client`,
  `register_and_get_token`, `MockSophia`).

### Security notes
- Enforce extension **and** mime allowlist + `MAX_UPLOAD_BYTES` before parsing.
- Store under a generated UUID name; never build the path from the client
  filename (path-traversal safe).
- Every download/read checks `user_id` ownership.

## Frontend Changes (`web/`)

### 1. Types — `web/lib/types.ts`
Add `UploadedFile = { id: number; filename: string; mime: string; chars: number }`,
extend `ChatRequest` with `attached_file_ids: number[]`, add
`ExportFormat = "txt" | "md" | "pdf" | "docx"`.

### 2. BFF route handlers
- `web/app/api/files/upload/route.ts` → forward multipart to backend
  `POST /api/files/upload`. **Note:** `forward()` (lib/backend.ts) must pass the
  raw `FormData`/body through **without** forcing a JSON `Content-Type` (let
  fetch set the multipart boundary). Add a multipart-aware path or a small
  variant; keep the JWT-from-cookie attach.
- `web/app/api/files/generate/route.ts` → forward JSON to backend, relay the
  binary response (preserve `Content-Disposition` + content-type).

### 3. Upload UI — `web/components/chat/Composer.tsx`
- Add a paperclip icon button next to the send button (reuse `.btn-send` /
  `.btn-ghost` styling). Hidden `<input type="file" multiple accept=".txt,.md,
  .pdf,.docx">`.
- On select → `clientFetch("/api/files/upload", FormData)` → show attached files
  as chips above the textarea (filename + remove ✕).

### 4. Send wiring — `web/components/chat/ChatWorkspace.tsx`
- Hold `attachedFiles` state; include their ids as `attached_file_ids` in the
  `send()` body (ChatWorkspace.tsx:75); clear after the message is sent.

### 5. Download UI — `web/components/chat/MessageBubble.tsx`
- On Sophia messages, add a "Download" control → small menu (md / txt / pdf /
  docx) → `POST /api/files/generate {content: message.content, format}` → read
  blob → trigger browser download (anchor + `URL.createObjectURL`).

### 6. Styling + icons
- `web/app/globals.css`: styles for the attach button, file chips, download menu
  (use existing tokens — `--azure`, `--surface`, `--radius`, `.btn-ghost`).
- Add `paperclip` + `download` SVGs to `web/components/cosmic/icons.tsx`.

## Critical Files

| Area | Files |
|---|---|
| New tool module | `sophia/files/parsers.py`, `sophia/files/generators.py` |
| Router | `sophia/app/routers/files.py` (new), `sophia/app/main.py` |
| DB | `sophia/db/models.py`, `sophia/db/service.py`, new Alembic migration |
| Chat wiring | `sophia/app/schemas.py`, `sophia/app/routers/chat.py`, `sophia/core/orchestrator.py` |
| Deps | `requirements.txt` |
| Tests | `tests/test_app_files.py` |
| FE BFF | `web/app/api/files/upload/route.ts`, `web/app/api/files/generate/route.ts`, `web/lib/backend.ts` |
| FE UI | `web/components/chat/Composer.tsx`, `ChatWorkspace.tsx`, `MessageBubble.tsx`, `web/components/cosmic/icons.tsx`, `web/app/globals.css`, `web/lib/types.ts` |

## Verification

1. **Deps:** `pip install -r requirements.txt` (in `SophiaAI-venv`).
2. **Migration:** `$env:SOPHIA_DB_URL=...; alembic upgrade head` → `user_files`
   table exists.
3. **Backend tests:** `pytest tests/test_app_files.py -v` green; full suite
   (185+) still green.
4. **Manual E2E** (PowerShell, backend + `cd web; npm run dev`):
   - Upload a PDF, a docx, a txt → chips appear in the composer.
   - Ask "summarize the file I uploaded" → answer references real file content.
   - On Sophia's answer, click Download → md / txt / pdf / docx each download and
     open correctly.
   - Ownership: a second account cannot fetch the first account's file id.
5. **Direct API check:** `curl -F file=@sample.pdf` to `/api/files/upload` with a
   Bearer token returns extracted `chars`; `POST /api/files/generate` returns a
   valid file with `Content-Disposition`.

## Out of Scope (v1)
- Per-file embedding/RAG over large uploads (inject-with-cap only).
- Legacy binary `.doc`, scanned-PDF OCR, images.
- Re-downloading uploaded originals.
- Sophia autonomously deciding to emit a file (arrives with the agent loop;
  these same functions are what it will call).