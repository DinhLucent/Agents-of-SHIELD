# TASK-056: Order & Specimen schema + Order Entry API
- Agent: backend-agent | Claimed: 2026-04-01T15:04:28.5031921+07:00 | Status: DONE

## Acceptance Criteria
- [x] Order table with status enum matching Spec Section 3
- [x] `POST /api/orders` creates order, generates barcode, status=`created`
- [x] Order transitions to `queued_for_gateway` after Mirth push triggered
- [x] Unit tests for creation and state transitions

## Work Log
- [2026-04-01T15:04:28.5031921+07:00] Claimed TASK-056 immediately after closing TASK-055 because its dependency chain was clear.
- [2026-04-01T15:17:53.5018137+07:00] Implemented the `orders` persistence model, lifecycle enum, Alembic revision `20260401_03`, and request/response schemas for order entry.
- [2026-04-01T15:17:53.5018137+07:00] Added `POST /api/orders` plus `OrderService.trigger_gateway_push()` so the order starts in `created` and can transition to `queued_for_gateway` when outbound sync is triggered.
- [2026-04-01T15:17:53.5018137+07:00] Verified the new flow with unit tests and the live PostgreSQL 16 instance by creating an order through FastAPI and then transitioning it to `queued_for_gateway`.

## Completion Report
- Completed: 2026-04-01T15:17:53.5018137+07:00
- Files:
  - `packages/lis-core/alembic/env.py`
  - `packages/lis-core/alembic/versions/20260401_03_order_entry.py`
  - `packages/lis-core/src/lis_core/app.py`
  - `packages/lis-core/src/lis_core/models/order.py`
  - `packages/lis-core/src/lis_core/routers/orders.py`
  - `packages/lis-core/src/lis_core/schemas/order.py`
  - `packages/lis-core/src/lis_core/services/orders.py`
  - `packages/lis-core/tests/test_orders.py`
- Summary: LIS Core now has the first order-entry slice: a persisted order table with a concrete status lifecycle, auto-generated accession/barcode fields, and a `POST /api/orders` API that stores patient snapshot data and requested test codes. The queue transition hook is isolated in the service layer so later ACK/integration work can reuse the same state machine.
- Decisions: Stored requested test codes as JSON on the order record to keep the thin slice simple while preserving the set of requested assays for downstream sync tasks. Used a service-level `trigger_gateway_push()` transition instead of baking Mirth behavior into the creation endpoint so TASK-057/TASK-058 can attach the real integration step cleanly.
- Issues: The frozen Sprint 6 spec file and `packages/shared` contract package referenced by TASK-053 handoffs were not present on disk during implementation. The order lifecycle enum was therefore reconstructed from the active backlog and handoff notes: `created`, `queued_for_gateway`, `synced_to_gateway`, `sync_failed`, `result_received`, `approved`.
- Verification:
  - `python -m pytest -q --basetemp D:\MyProject\LabInfoSys\packages\lis-core\.codex-tmp\pytest -p no:cacheprovider` -> `9 passed`
  - `alembic -c alembic.ini upgrade head` against PostgreSQL 16 -> success
  - `POST /api/orders` via ASGI transport with PostgreSQL-backed dependency -> `201`, `status=created`
  - `OrderService.trigger_gateway_push(order_id)` against PostgreSQL-backed session -> `queued_for_gateway`
- Notes for next Agent: TASK-058 should reuse `OrderStatus` and `OrderService` instead of creating a parallel state machine. The next status transitions expected by the backlog are `accepted_new|accepted_existing -> synced_to_gateway` and `rejected -> sync_failed`.
