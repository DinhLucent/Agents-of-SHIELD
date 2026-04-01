# Handoff: backend-agent -> backend-agent
## Task: TASK-056 - Order & Specimen schema + Order Entry API

## Completed (TASK-055)
- `TestCatalog` and `ReferenceRangeRule` are implemented in LIS Core and migrated through Alembic revision `20260401_02`.
- Seed data now lives in `packages/lis-core/data/master_data/` and can be loaded with `python -m lis_core.cli.seed_master_data`.
- Read-only metadata APIs are available:
  - `GET /api/meta/tests`
  - `GET /api/meta/reference-ranges`
- Verification passed on the real local PostgreSQL 16 instance:
  - migration applied
  - seed data loaded
  - `/api/meta/tests` returned `total=5`
  - `/api/meta/reference-ranges?test_code=GLU` returned `total=1`

## What TASK-056 must do
1. Add the first order/specimen persistence model and matching Alembic revision.
2. Define the order status enum to match the Sprint 6 spec lifecycle.
3. Build `POST /api/orders` with accession/barcode generation and persisted patient snapshot fields.
4. Implement the transition hook to `queued_for_gateway` when the outbound push is triggered.
5. Add unit tests for creation and state transitions.

## Context / Warnings
- Keep using the shared contracts from TASK-053 instead of cloning payload models inside LIS Core.
- Local PostgreSQL verification currently uses the existing `postgres` DSN. No dedicated `lis_core_app` role exists yet.
- Master data endpoints are already available if order validation needs to reference catalog codes in later steps.
