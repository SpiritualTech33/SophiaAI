# Recent

```

# Recent

## 2026-05-28
Phase 12 complete: cosmic chat UI. Jinja2 templates (base/index/login/register/chat), sophia.css design system, pure CSS/SVG orb avatar, starfield, vanilla JS (cosmos/auth/chat, JWT in localStorage + authFetch). Hybrid avatar (goddess hero image + orb), deep-cosmic palette, Cinzel+Inter. Fixed latent Phase 8 bug: orchestrator maps DB role "sophia"->LLM "assistant" (Groq 400 broke 2nd message). configure_assets() shared with test harness. Goddess image shipped as JPG (no WebP encoder, avoided Pillow dep). 144 tests pass, E2E multi-turn verified live. Phase 13 (Alembic) next; UI refinement pending.

## 2026-05-27
Phase 11 complete: FastAPI skeleton (3 routers, 6 endpoints, Pydantic/DI/lifespan). 142 tests (26 new). Merged to master; Phase 10-11 implementation documented. Phase 12 (UI+Templates) queued with Sophia avatar.

## 2026-05-26
Phase 9 complete: sophia/db/ package (database.py, models.py, service.py). 3 ORM tables (users, conversations, messages) with cascade deletes, 6 CRUD service functions. 27 new tests, 103 total (102 pass, 1 skip). Subagent-driven execution. Merged to master. Phase 10 Auth Layer next.

## 2026-05-25
Phase 8 complete: Sophia orchestrator (core/orchestrator.py). Decision flow: corpus-only vs hybrid vs web-only based on confidence threshold. 17 tests, 76 total. Merged to master. Phase 7 also committed (web_search wrapper).