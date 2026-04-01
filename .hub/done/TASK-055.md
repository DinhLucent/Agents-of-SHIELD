# TASK-055: Master Data: TestCatalog + ReferenceRangeRule schema & seeder
- Agent: backend-agent | Claimed: 2026-04-01T14:54:02.8321586+07:00 | Status: DONE

## Acceptance Criteria
- [x] TestCatalog and ReferenceRangeRule tables created via Alembic
- [x] Seed script loads sample data (GLU, AST, ALT, etc.)
- [x] Read-only API: `GET /api/meta/tests`, `GET /api/meta/reference-ranges`
- [x] Unit tests for seeder and meta endpoints

## Work Log
- [2026-04-01T14:54:02.8321586+07:00] Confirmed TASK-055 is the next unlocked backend task after TASK-054 completion.
- [2026-04-01T14:54:02.8321586+07:00] Loaded TASK-054 handoff and current LIS Core scaffold to plan the first domain tables, seed flow, and meta API.
- [2026-04-01T15:04:28.5031921+07:00] Added SQLAlchemy models for `TestCatalog` and `ReferenceRangeRule`, registered metadata with Alembic, and created migration `20260401_02`.
- [2026-04-01T15:04:28.5031921+07:00] Added CSV-backed master data seed flow, CLI entrypoint, paginated meta endpoints, and unit tests for the seeder plus read-only API.
- [2026-04-01T15:04:28.5031921+07:00] Verified live PostgreSQL migration and seed execution, then exercised `/api/meta/tests` and `/api/meta/reference-ranges?test_code=GLU` through the FastAPI app using the configured PostgreSQL DSN.

## Completion Report
- Completed: 2026-04-01T15:04:28.5031921+07:00
- Files:
  - `packages/lis-core/alembic/env.py`
  - `packages/lis-core/alembic/versions/20260401_02_master_data_catalog.py`
  - `packages/lis-core/data/master_data/test_catalog.csv`
  - `packages/lis-core/data/master_data/reference_ranges.csv`
  - `packages/lis-core/src/lis_core/app.py`
  - `packages/lis-core/src/lis_core/cli/seed_master_data.py`
  - `packages/lis-core/src/lis_core/db/session.py`
  - `packages/lis-core/src/lis_core/models/test_catalog.py`
  - `packages/lis-core/src/lis_core/models/reference_range_rule.py`
  - `packages/lis-core/src/lis_core/routers/meta.py`
  - `packages/lis-core/src/lis_core/schemas/master_data.py`
  - `packages/lis-core/src/lis_core/services/master_data_seed.py`
  - `packages/lis-core/src/lis_core/services/meta.py`
  - `packages/lis-core/tests/test_master_data_seed.py`
  - `packages/lis-core/tests/test_meta.py`
- Summary: LIS Core now exposes seeded laboratory master data through read-only metadata APIs. The schema is under Alembic control, seed data is idempotent on repeated runs, and the task is verified both with local unit tests and against the live PostgreSQL 16 instance.
- Decisions: Used CSV seed files for easy diffing and direct CLI ingestion. Kept the meta endpoints paginated and filterable by `test_code` so downstream resolver work can reuse the same query path in later tasks.
- Issues: Verification still uses the shared `postgres` database user from local setup. A dedicated least-privilege runtime role remains a separate hardening step.
- Verification:
  - `python -m pytest -q --basetemp D:\MyProject\LabInfoSys\packages\lis-core\.codex-tmp\pytest -p no:cacheprovider` -> `7 passed`
  - `alembic -c alembic.ini upgrade head` against PostgreSQL 16 -> success
  - `python -m lis_core.cli.seed_master_data` -> `Seeded 5 tests and 8 reference ranges.`
  - `GET /api/meta/tests` via ASGI transport with PostgreSQL-backed dependency -> `200`, `total=5`
  - `GET /api/meta/reference-ranges?test_code=GLU` via ASGI transport -> `200`, `total=1`
- Notes for next Agent: TASK-056 can build order creation directly on this seeded catalog base. Reuse the existing DB session dependency and keep order state transitions aligned with the frozen Sprint 6 spec.
