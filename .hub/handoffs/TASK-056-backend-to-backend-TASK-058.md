# Handoff: backend-agent -> backend-agent
## Task: TASK-058 - LIS Integration API: ACK handler + order state update

## Completed (TASK-056)
- LIS Core now has an `orders` table with lifecycle enum values:
  - `created`
  - `queued_for_gateway`
  - `synced_to_gateway`
  - `sync_failed`
  - `result_received`
  - `approved`
- `POST /api/orders` is implemented and returns a persisted order with:
  - generated `accession_number`
  - generated `specimen_id`
  - patient snapshot fields
  - `requested_tests`
  - initial `status=created`
- `OrderService.trigger_gateway_push(session, order_id)` transitions the order from `created` to `queued_for_gateway`.
- Verified against local PostgreSQL 16:
  - `alembic upgrade head` applied revision `20260401_03`
  - order creation works through FastAPI
  - queue transition works through the service layer

## What TASK-058 must do
1. Add `POST /api/integration/orders/ack`.
2. Validate incoming ACK payloads against the frozen contract source if/when the shared package is restored; otherwise align strictly to backlog fields.
3. Transition order status from:
   - `accepted_new` or `accepted_existing` -> `synced_to_gateway`
   - `rejected` -> `sync_failed`
4. Keep the transition logic inside the existing order service/state machine.
5. Add unit tests for accepted and rejected ACK paths plus idempotency expectations.

## Context / Warnings
- `TASK-058` is still dependency-blocked on `TASK-057` because the Mirth channel path must exist before ACK flow is fully exercised.
- The `packages/shared` contract package referenced by TASK-053 is not present in the current workspace, so contract imports cannot yet be consumed directly from disk.
- Order lifecycle values were inferred from backlog/handoff state because the frozen Sprint 6 spec document was also missing from the workspace.
