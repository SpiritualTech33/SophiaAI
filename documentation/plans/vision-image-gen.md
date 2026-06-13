# Plan: Image Understanding (Vision) + Image Generation for Sophia

## Context

SophiaAI is text-only today: `OpenRouterClient.chat`/`chat_stream` send
`{"role": ..., "content": "<string>"}` messages to `google/gemma-4-31b-it:free`.
The file-tool (`sophia/files/`) already lets users attach txt/md/pdf/docx —
`extract_text` caches plain text into `UserFile.extracted_text`, and the
orchestrator injects that text into the system prompt.

Goal: extend Sophia with two new senses, each via a free provider, following
the existing "one-swap-point" tool pattern (pure functions, isolated module,
mapped errors → HTTP status):

1. **Image understanding (vision):** user attaches an image → Sophia sees it.
   Provider: same OpenRouter model already configured
   (`OPENROUTER_MODEL`, `google/gemma-4-31b-it:free` — multimodal, accepts
   image input). No model switch — multimodal content arrays go to the
   existing `DEFAULT_MODEL`.
2. **Image generation:** user asks for a picture → Sophia returns one.
   Provider: Pollinations.ai (`https://image.pollinations.ai/prompt/{prompt}`,
   free, no API key).

Scope: full stack (backend modules/routes + DB plumbing + frontend UI). No
agent tool-calling loop exists yet (M1 still pending) — this ships as direct
chat/UI wiring now, in a shape that becomes a tool later without rework (pure
functions, isolated modules).

## Backend

### 1. `sophia/vision/` (new module, mirrors `sophia/files/`)

- `sophia/vision/__init__.py` — exports
- `sophia/vision/encoder.py`:
  - `MAX_IMAGE_SIZE_BYTES` constant (10 MB, matches file ceiling)
  - `ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}`
  - `UnsupportedImageTypeError`, `ImageTooLargeError` (mirror `sophia/files` error names)
  - `encode_image_content(data: bytes, mime_type: str) -> dict` — pure function,
    validates mime + size, returns OpenAI-format content part:
    `{"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}`
  - Mental Model docstring per `scripts/build_faiss_index.py` style.

### 2. `sophia/image_gen/` (new module)

- `sophia/image_gen/__init__.py` — exports
- `sophia/image_gen/generator.py`:
  - `ImageGenerationError` (single exception type, mirrors `SophiaLLMError`)
  - `generate_image(prompt: str) -> bytes` — `httpx.get` to
    `https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}`,
    returns PNG bytes, raises `ImageGenerationError` on failure.

### 3. Config

- No config changes needed. `sophia/llm/openrouter_client.py` `chat`/`chat_stream`
  already accept arbitrary `messages`/`model=DEFAULT_MODEL`; multimodal
  `content` arrays (text + `image_url` parts) pass through to
  `google/gemma-4-31b-it:free` as-is — no client or env changes.

### 4. `sophia/db/service.py`

- Add `get_user_files(session, file_ids, user_id) -> list[UserFile]` — owner-scoped
  fetch of full records (need `mime_type` + `stored_path`, not just text).

### 5. `sophia/app/routers/files.py`

- `upload_file`: if `file.content_type` starts with `image/`, skip
  `extract_text` (would raise `UnsupportedFileTypeError`) — validate via
  `sophia.vision.encoder` (mime + size), store bytes as today, `extracted_text=""`.
- New `GET /api/files/{file_id}/raw` — owner-scoped, 404 if missing/not owned,
  streams bytes with `media_type=record.mime_type`. Needed by frontend to
  display both user-uploaded image previews and Sophia-generated images.

### 6. `sophia/app/routers/images.py` (new router)

- `POST /api/images/generate` — body `{prompt: str}`, auth required.
  Calls `generate_image(prompt)`, stores result as `UserFile`
  (mime_type="image/png", original_filename=f"{prompt[:40]}.png",
  conversation_id=None), returns `{id, filename, mime, url}` (url =
  `/api/files/{id}/raw`). `ImageGenerationError` → 502.
- Register router in `sophia/app/main.py` alongside existing routers.

### 7. `sophia/core/orchestrator.py`

- `ask`/`ask_stream`: given `attached_file_ids`, split into text files
  (existing path, `_format_attachments`) and image files (mime startswith
  `image/`, via `encode_image_content`).
- If any image attachments: build user message as multimodal content array
  `[{"type": "text", "text": query}, *image_content_parts]`. Otherwise
  unchanged (string content). `DEFAULT_MODEL` handles both.
- `sophia/app/routers/chat.py`: replace `get_files_text(...)` call with
  `get_user_files(...)`, pass full records into `ask()`/`ask_stream()`.

## Frontend (`web/`)

### 1. `web/components/chat/Composer.tsx`

- Extend file-picker `accept` to include `image/jpeg,image/png,image/webp,image/gif`
  alongside existing `.txt,.md,.pdf,.docx`.
- Image attachments render as a thumbnail chip (`<img src="/api/files/{id}/raw">`)
  instead of a filename chip.
- New "Generate Image" button next to the paperclip → opens a small inline
  prompt input → `POST /api/images/generate` (new BFF route) → on success,
  appends a Sophia message containing the returned image.

### 2. New BFF routes (mirror existing `web/app/api/files/...` proxy pattern)

- `web/app/api/images/generate/route.ts` — proxies to backend
  `POST /api/images/generate`, forwards JWT cookie.
- `web/app/api/files/[id]/raw/route.ts` — proxies to backend
  `GET /api/files/{id}/raw`, streams image bytes through with correct
  content-type.

### 3. Chat message rendering

- Sophia-generated image messages: store content as a small markdown-ish
  sentinel, e.g. `![generated](file:{id})`. Message-rendering component
  detects this pattern and renders `<img src="/api/files/{id}/raw">` instead
  of plain text. Plain text messages render unchanged.

## Verification

- Backend pytest (TDD, red/green per CLAUDE.md):
  - `sophia/vision/encoder.py`: valid/invalid mime, oversize, correct base64 data-URI
  - `sophia/image_gen/generator.py`: mocked httpx success + failure → `ImageGenerationError`
  - orchestrator: image attachment → multimodal message shape; text-only path unchanged
  - `files.py` router: image upload succeeds (no `extract_text` call), `/api/files/{id}/raw` serves bytes, 404 for non-owner
  - `images.py` router: `/api/images/generate` happy path (201 + file id) and provider-error path (502)
- E2E manual (real OpenRouter call):
  - Upload a photo, ask "what's in this image?" — verify grounded answer
  - Click "Generate Image", enter a prompt — verify PNG returns and renders inline in chat
- Frontend: `npm run dev`, manual browser pass for both flows
- Update `documentation/plans/SaaS-implementations.md` and `CLAUDE.md`
  Architecture section (vision/image-gen move from "out of scope" to ✅) after
  merge, per repo convention.
