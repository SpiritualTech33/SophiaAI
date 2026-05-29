# Handoff

## State
Phases 0-12 done (web UI live, 144 tests pass). Phase 13 (Alembic) plan written
at `documentation/plans/phase13-alembic-migrations.md` — 8 tasks, TDD, ready to
execute. No code written yet for Phase 13. Branch: master.

## Next
1. Execute the Phase 13 plan (subagent-driven recommended). Start: add `alembic`
   to requirements.txt, `alembic init alembic`, wire env.py to `Base.metadata`.
2. Phase 14 (Testing) after.

## Context
- Dev `sophia_memory.db` already has the 3 tables → autogenerate against an empty
  throwaway DB (`SOPHIA_DB_URL=sqlite:///./_alembic_tmp.db`) or migration is empty.
  Reconcile real DB with `alembic stamp head`, not upgrade.
- `render_as_batch=True` in env.py — SQLite needs it for future ALTERs.
- Use PowerShell tool, not Bash (Bash hung in Phase 12).
- `Base.metadata` from `sophia/db/models.py`; URL env var `SOPHIA_DB_URL`.
