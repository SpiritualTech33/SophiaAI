# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.3-ALFA] - 2026-06-12

Sophia gains eyes and a brush — she now **sees** the images you send and **generates** new ones on request. Two new senses, each behind the existing one-swap-point tool pattern (pure functions, isolated module, typed errors → HTTP status).

### Added
- New vision tool [`sophia/vision/`](file:///C:/Users/serra/Desktop/SophiaAI/sophia/vision/): `encode_image_content()` validates an upload (mime + size ceiling) and returns an OpenAI-format `image_url` content part (base64 data-URI). Typed errors map to `415` (unsupported type) and `413` (too large).
- New image-generation tool [`sophia/image_gen/`](file:///C:/Users/serra/Desktop/SophiaAI/sophia/image_gen/): `generate_image(prompt) -> bytes` calls the Hugging Face Inference API (`black-forest-labs/FLUX.1-schnell`) with a Bearer `HF_TOKEN`. Any provider/transport failure is wrapped in `ImageGenerationError`.
- Endpoint `POST /api/images/generate`: generates an image, stores it as a `UserFile`, and returns `{id, filename, mime, url}` (`502` on provider failure, `422` on empty prompt).
- Endpoint `GET /api/files/{id}/raw`: owner-scoped raw-bytes serving (`404` if missing/not owned) — serves both uploaded photos and generated images for inline display.
- `get_user_files()` service: owner-scoped fetch of full `UserFile` records (mime + path), preserving caller id order.
- Web: image attachments in the composer (thumbnail chips), a "generate image" button with an inline prompt, two BFF routes ([`/api/images/generate`](file:///C:/Users/serra/Desktop/SophiaAI/web/app/api/images/generate/route.ts), [`/api/files/[id]/raw`](file:///C:/Users/serra/Desktop/SophiaAI/web/app/api/files/%5Bid%5D/raw/route.ts)), and inline rendering: generated images via a `![generated](file:{id})` sentinel, and **the photos you attach now appear inside your own message bubble** (image on top, text below).
- New config: `HF_TOKEN` in [`.env.example`](file:///C:/Users/serra/Desktop/SophiaAI/.env.example).

### Changed
- `Sophia.ask`/`ask_stream` accept `image_attachments`; when present, the final user turn becomes a multimodal content array (`[{text}, {image_url}…]`) instead of a plain string. The chat router splits attachments by mime — text files keep the prompt-injection path, images ride as vision content.
- The `upload_file` endpoint accepts image mimes (`jpeg/png/webp/gif`): images skip text extraction (validated via the vision encoder), stored with `extracted_text=""`.
- **LLM model → `google/gemini-2.5-flash-lite`** (native multimodal, paid but cheap). One config line — no per-request model switching; text and vision share the configured `DEFAULT_MODEL`. App version bumped to 0.12.2.

### Fixed
- Image generation moved off Pollinations.ai after its anonymous tier began returning `402 Payment Required` (x402 micropayment challenge) on every keyless request. Hugging Face Inference (FLUX.1-schnell) replaces it.

### Tests
- 260 backend tests pass (added vision, image-gen, images-endpoint, raw-serving, and orchestrator-multimodal suites). Next build clean. Live E2E verified: attach a photo → Sophia describes it; click generate → JPEG renders inline.

## [0.7.2-ALFA] - 2026-06-05

File read & generate — Sophia gains hands for documents. Users upload files for
her to read, and download any of her answers as a file.

### Added
- New file tool [`sophia/files/`](file:///C:/Users/serra/Desktop/SophiaAI/sophia/files/): two pure functions behind one interface — `extract_text()` (read) and `render_file()` (write) — so the future agent tool-calling loop can call the same functions. Typed errors map to HTTP `413/415/422`.
  - Read: `.txt`, `.md`, `.pdf` (pypdf), `.docx` (python-docx).
  - Write: `txt`, `md`, `pdf` (fpdf2), `docx` (python-docx) — pure-Python, no system binaries.
- `UserFile` model + service (`create_user_file`, `get_user_file`, `get_files_text`) with **ownership enforced in the query** — a forged file id injects nothing. Alembic migration [`b2c4f1a7d9e3`](file:///C:/Users/serra/Desktop/SophiaAI/alembic/versions/b2c4f1a7d9e3_add_user_files.py) adds the `user_files` table.
- Endpoints: `POST /api/files/upload` (multipart, UUID-named per-user storage — path-traversal safe) and `POST /api/files/generate` (streams the file as an attachment).
- Web: paperclip upload + attachment chips in the composer, a Download menu on Sophia's answers, two BFF route handlers (multipart-aware forward, binary relay), cosmic-token styles.
- New deps: `pypdf`, `python-docx`, `fpdf2`. Plan in [`documentation/sophia_capabilities/read-and-write-files.md`](file:///C:/Users/serra/Desktop/SophiaAI/documentation/sophia_capabilities/read-and-write-files.md).

### Changed
- `ChatRequest` accepts `attached_file_ids`; the chat router threads owner-scoped file text into the orchestrator. `Sophia.ask`/`ask_stream` take `attachments`, injected into the system prompt before corpus passages, capped at `MAX_ATTACHMENT_CHARS` and framed as reference material (not instructions).
- App version bumped to 0.12.1; lifespan reads `FILES_UPLOAD_DIR` (default `data/user_uploads`).

### Fixed
- PDF generation of multi-line content raised `fpdf2` "Not enough horizontal space" (cursor left at the right margin) — now resets to the left margin per line. Caught by live smoke; covered by a multi-line regression test.

### Tests
- 225 backend tests pass (added file module, service, endpoint, and orchestrator-injection suites). Next build + lint clean. Live E2E verified: upload → chat reads the file → download.

## [0.7.1-ALFA] - 2026-06-05

Migration of LLM provider from Groq to OpenRouter using Google Gemini.

### Added
- New OpenRouter client implementation under [`sophia/llm/openrouter_client.py`](file:///C:/Users/serra/Desktop/SophiaAI/sophia/llm/openrouter_client.py) using `httpx` to handle standard completions and SSE streaming.
- Comprehensive unit tests in [`tests/test_openrouter_client.py`](file:///C:/Users/serra/Desktop/SophiaAI/tests/test_openrouter_client.py) covering validation, rate limits, status errors, and stream parsing.
- Migration plan saved in [`documentation/plans/llm_provider_migration_plan.md`](file:///C:/Users/serra/Desktop/SophiaAI/documentation/plans/llm_provider_migration_plan.md).

### Changed
- Configured FastAPI startup lifespan to instantiate `OpenRouterClient` instead of `GroqClient`.
- Environment variable configuration in [`.env.example`](file:///C:/Users/serra/Desktop/SophiaAI/.env.example) and local [`.env`](file:///C:/Users/serra/Desktop/SophiaAI/.env) replaced `GROQ_` keys with `OPENROUTER_` keys, defaulting to `google/gemini-2.5-flash`.
- Decoupled [SophiaLLMError](file:///C:/Users/serra/Desktop/SophiaAI/sophia/llm/__init__.py) imports across backend and test files to import directly from the `sophia.llm` package.

### Removed
- Deprecated Groq client implementation [`sophia/llm/groq_client.py`](file:///C:/Users/serra/Desktop/SophiaAI/sophia/llm/groq_client.py).
- Deprecated unit tests in [`tests/test_groq_client.py`](file:///C:/Users/serra/Desktop/SophiaAI/tests/test_groq_client.py).

## [0.7.0-ALFA] - 2026-06-04

Premium frontend rebuilt on Next.js; backend becomes API-only.

### Added
- New `web/` client: Next.js 16 (App Router) + TypeScript + Tailwind v4 +
  React 19. Full parity — landing, login, register, three-panel streaming chat,
  "Sophia's Mind" corpus browser, document reader.
- Backend-for-Frontend (BFF) auth: the JWT now lives in an **httpOnly cookie**
  set by Next.js route handlers; the browser never holds the token. A `proxy.ts`
  guards `/chat`; Server Components read data server-side; the SSE chat stream is
  piped through a Node route handler.
- Bespoke cosmic React components (Orb, Starfield, Wordmark, GlassPanel) porting
  the design system faithfully from `sophia.css`.
- Spec: `documentation/specs/nextjs-frontend.md`.

### Changed
- FastAPI is now **API-only**. CORS tightened from `*` to the client origin
  (`CORS_ORIGINS`, default `http://localhost:3000`). App version bumped to 0.12.0.
- Brand assets (`sophia_goddess.jpg`, `favicon.svg`) moved to `web/public/`.

### Removed
- Jinja2 frontend: the `pages` router, `sophia/app/templates/`, and
  `sophia/app/static/` (HTML pages, vanilla JS, hand-written CSS) — superseded by
  the `web/` client. Page-route tests removed (185 backend tests pass).

