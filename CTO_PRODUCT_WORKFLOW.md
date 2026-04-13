# CTO + Product Workflow

Practical operating model for running SHIELD like a disciplined AI team instead of a long single-session chat.

This file defines the leadership lane only. Shared session rules still live in `OPERATING_RULES.md`.

## Why The Old Model Felt Easier To Control

The old `MyTeam` style was easier to operate for a reason.

It had five strong control properties:

1. one clear intake point
2. strong role boundaries
3. a visible task hub
4. fast dashboard context for new sessions
5. short reports plus detailed handoff when needed

That made the system feel manageable.

The current SHIELD runtime is stronger technically, but it drifted toward execution-first orchestration.

That made it better at running tasks, but weaker at preserving leadership structure.

The right move is not to go backward.

The right move is to combine:

- the old control model
- the current execution kernel

## The Distilled Model

The best operating model is:

`User/CEO -> Product + CTO -> plan/ADR/sprint/tasks -> worker sessions -> QA/reviewer -> Product + CTO -> dashboard`

This keeps strategy separate from execution.

## Role Responsibilities

### User / CEO

The human provides intent, constraints, and final decisions.

The human should not need to manually coordinate every specialist session.

### Product

Product owns:

- problem framing
- scope clarity
- user value
- priority
- acceptance framing
- sprint sequencing with the user

Product answers:

- what problem are we solving
- what is in scope now
- what does success look like

### CTO

CTO owns:

- technical direction
- architecture impact
- system boundaries
- design decisions
- ADRs
- implementation decomposition

CTO answers:

- how should this be built
- what are the major technical risks
- what must stay stable

### Producer / PM

Producer or PM can exist as a lighter operations role.

It owns:

- task board hygiene
- sequencing
- sprint progress
- coordination follow-through

If the team is small, Product can absorb this function.

### Worker Sessions

Examples:

- backend
- frontend
- fullstack
- devops
- data

Workers should not reinterpret the whole project.

They should receive:

- one primary task
- the latest relevant context
- acceptance criteria
- role boundary

### QA / Reviewer / Security

These roles verify work and protect quality.

They should not become the place where project strategy is invented.

## Golden Rule

No specialist session should start from raw user intent.

Every meaningful request should first pass through Product and CTO.

That is the center of control.

## Required Artifact Chain

To make this work, SHIELD should preserve a small but complete artifact chain.

### Leadership Artifacts

- `leadership_brief`
- `request_brief`
- `plan`
- `ADR` when architecture changes
- `sprint` or backlog update
- `task`

### Execution Artifacts

- `task_packet`
- `execution_result`
- `verification_report`

### Collaboration Artifacts

- `session_report`
- `handoff`
- `decision_log`
- `dashboard_snapshot`

If these artifacts are healthy, multi-session work stays coherent.

For small projects, `leadership_brief` can combine request brief, product scope, CTO technical direction, sprint focus, and proposed tasks in one file.

Only split it into separate plan, ADR, and sprint documents when the work is large enough to justify that ceremony.

## Practical Flow

### Stage 1: Intake

The user speaks to Product or CTO.

Expected output:

- clarified request
- initial scope
- risks or unknowns

### Stage 2: Strategy

Product and CTO refine the request together.

Expected output:

- plan
- ADR if needed
- sprint or backlog changes
- explicit tasks

### Stage 3: Execution

Workers receive tasks, not broad ambitions.

Expected output:

- code changes
- tests
- session report
- handoff if needed

### Stage 4: Verification

QA, reviewer, or security verifies the work.

Expected output:

- verification report
- pass/fail
- required fixes or signoff

### Stage 5: Leadership Closure

Product and CTO review outcomes.

Expected output:

- task closure
- decision update if needed
- dashboard update
- next sprint or next task recommendation

## What Must Change In Current SHIELD

The current SHIELD system already has the runtime engine we need.

The missing part is leadership structure and collaboration writeback.

### Keep as-is or mostly as-is

- `compile`
- task packet builder
- runtime planner
- agent executor
- verifier runners
- retry loop
- task state machine

### Reposition in the operating model

- `run_orchestrator.py plan`
  This should be understood as worker-task packaging, not project leadership planning.

- `run_orchestrator.py run`
  This should remain the worker execution engine, not the front door for every raw request.

### Upgrade next

- `control_plane/hooks/post_task.py`
  Upgrade from compact status payload to true `session_report` generation.

- `control_plane/hooks/on_handoff.py`
  Expand from minimal transfer JSON into a stronger handoff contract with reason, open questions, and recommended next step.

- `control_plane/execution/task_state_machine.py`
  Extend task ownership tracking so the system clearly records who owns a task and where it sits in the collaboration flow.

- dashboard snapshot generation
  Rebuild around collaboration artifacts, not only runtime state.

## Integration Strategy

This should be done in phases, not as a big-bang rewrite.

## Phase 1: Restore Leadership Control

Goal:

- make Product and CTO the official intake path again

Work:

- write leadership workflow
- define how Product and CTO split responsibility
- define what a valid task must inherit from leadership artifacts

### Gate

No new feature request should go directly to backend or frontend by default.

## Phase 2: Freeze Collaboration Contracts

Goal:

- stop collaboration from being implicit

Work:

- freeze `session_report`
- freeze `handoff`
- freeze `decision_log`

### Gate

Every session must have a durable writeback artifact.

## Phase 3: Connect Runtime To Collaboration

Goal:

- make the system generate these artifacts automatically

Work:

- post-task creates session report
- handoff hook creates structured handoff
- verification can propose next owner or escalation
- task state reflects owner and phase clearly

### Gate

A fresh session can resume work from artifacts instead of chat.

## Phase 4: Dashboard Recenter

Goal:

- make project state visible to both humans and incoming AI sessions

Work:

- show active owner
- show blocked tasks
- show recent reports
- show recent handoffs
- show sprint focus and leadership decisions

### Gate

The dashboard is enough to orient a new session in minutes.

## Phase 5: Collaboration Audit

Goal:

- prove the whole loop works

Work:

- run one leadership-to-worker-to-QA happy path
- run one failure and handoff path
- verify all artifacts are produced cleanly

### Gate

No human needs to manually reconstruct context from old chat.

## The "Pro Max" Version Without Unnecessary Complexity

The polished version of SHIELD should be:

- leadership-first
- execution-strong
- artifact-driven
- easy to audit
- easy for the human to supervise

It should not be:

- a giant agent theater
- a memory blob
- a chat-first maze
- a system where every role can do everything

## Concrete Next Implementation Moves

These are the highest-leverage next changes:

1. use `templates/leadership_brief.json` for Product + CTO intake
2. freeze `session_report`, `handoff`, and `decision_log` templates
3. make `post_task` write a real session report
4. enrich `on_handoff` with structured continuation guidance
5. update dashboard snapshot to summarize collaboration state, not only execution state

## Final Principle

The old system was easier to control because leadership, execution, and reporting were separated.

The new system should preserve that separation while using the current SHIELD kernel for actual execution quality.

That is the synthesis worth building.
