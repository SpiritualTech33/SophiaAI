# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [ALFA] - 2026-06-04

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

