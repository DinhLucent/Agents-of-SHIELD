# SYSTEM_AUDIT

Use this document when you change the control plane itself, not just an individual task.

This file defines validation and regression checks only.

It should not introduce a competing session workflow; use `OPERATING_RULES.md` for live process.

This repository already verifies single tasks through:

- `compile`
- `plan`
- `run`
- verifier checks
- retry packets
- metrics

That is not enough to prove the system still works after control-plane changes.

It is also not enough after collaboration-flow changes.

SHIELD now has two health layers:

- execution health: can it run and verify tasks
- collaboration health: can many role sessions coordinate without losing context

This document defines the manual re-validation workflow for the whole runtime.

## Purpose

Run a repeatable system audit after changing any of these areas:

- classifier
- router
- retriever
- packet builder
- execution planner
- agent executor
- verifier runners
- retry hook
- task state machine
- runtime metrics
- frozen contracts
- compile layer
- onboarding docs
- prompt pack
- role skill matrix
- Product/CTO workflow
- session report or handoff contracts
- shared session protocol in `OPERATING_RULES.md`

Goal:

- catch regressions early
- avoid re-thinking the whole architecture after every change
- keep the control plane deterministic and debuggable
- keep multi-session collaboration coherent

## Audit Levels

### Level 1: Quick Recheck

Use this after:

- doc updates that affect usage
- metric changes
- summary or report changes
- small hook changes
- low-risk packet formatting changes

Run serially:

```bash
python run_orchestrator.py compile
python run_orchestrator.py plan templates/task.yaml
python run_orchestrator.py run tests/fixtures/audit/happy_path.yaml
```

Check:

- compile succeeds
- packet is generated
- metrics file is generated
- verification passes for the happy-path task
- no import error occurs
- `ONBOARDING.md`, `PROMPT_PACK.md`, and `DASHBOARD.md` do not contradict the Product/CTO-first workflow
- `OPERATING_RULES.md` still contains the universal session protocol and template map
- core role personas and skill paths still exist

### Level 2: Runtime Regression

Use this after:

- orchestrator changes
- verifier changes
- retry changes
- execution planner changes
- executor changes
- state machine changes

Run serially:

```bash
python run_orchestrator.py compile
python run_orchestrator.py run tests/fixtures/audit/happy_path.yaml
python run_orchestrator.py run tests/fixtures/audit/retry_scenario.yaml
python run_orchestrator.py run tests/fixtures/audit/hard_fail.yaml
```

Check:

- happy path completes in one attempt
- failure path generates a retry packet with targeted context
- hard-fail path ends in terminal failure and writes a handoff
- paired mode changes runtime behavior
- metrics capture execution attempts and verifier status
- `.hub/done/` and `.hub/handoffs/` outputs are correct
- session report and handoff contracts still match the docs

### Level 3: Full System Revalidation

Use this after:

- contract changes
- compile-layer changes
- retriever changes
- module index changes
- role or routing model changes
- cleanup of legacy files
- onboarding or prompt-pack restructuring
- collaboration contract changes

Run:

1. Remove generated artifacts.
2. Rebuild compiled knowledge from scratch.
3. Re-run the runtime regression suite.
4. Inspect compiled and runtime outputs for stale artifacts.

Suggested serial sequence:

```bash
make clean
python run_orchestrator.py compile
python run_orchestrator.py plan templates/task.yaml
python run_orchestrator.py run tests/fixtures/audit/happy_path.yaml
python run_orchestrator.py run tests/fixtures/audit/retry_scenario.yaml
python run_orchestrator.py run tests/fixtures/audit/hard_fail.yaml
```

Check:

- compile output is rebuilt cleanly
- no stale compiled fragments remain
- packet stays minimal for small tasks
- retry packet only adds targeted context
- state transitions remain valid
- metrics remain present per run
- generated artifacts match current contracts
- Product/CTO-first docs still route raw intent before worker execution
- `ROLE_SKILL_MATRIX.md` still matches `manifest.yaml` for core role IDs
- every session output type points to a real template

### Level 4: Collaboration Revalidation

Use this after:

- role workflow changes
- role curriculum changes
- shared session protocol changes
- onboarding changes
- prompt pack changes
- dashboard guidance changes
- collaboration artifact changes

Manual scenario:

1. Open a Product session prompt from `PROMPT_PACK.md`.
2. Create or inspect a `leadership_brief`.
3. Route the result to CTO for technical decomposition.
4. Convert one task into `templates/task.yaml` shape.
5. Confirm the worker role appears in `ROLE_SKILL_MATRIX.md`.
6. Run `plan` on that task.
7. Simulate a worker session report using `templates/session_report.json`.
8. Simulate a QA or reviewer handoff using `templates/handoff.json`.
9. Confirm `DASHBOARD.md` still gives a new session enough context without reading chat.

Check:

- raw intent does not go directly to worker roles
- Product owns problem/scope/acceptance
- CTO owns technical direction/ADR/task decomposition
- worker prompts require assigned tasks
- role prompts load only the persona and task-specific skills
- every session ends with report or handoff
- dashboard stays short and points to artifacts

## Required Scenarios

The system audit is not complete unless these scenarios pass.

### Scenario A: Happy Path

Task type:

- small
- one module
- explicit file
- clear acceptance criteria

Must prove:

- classifier is reasonable
- routing is reasonable
- packet is small
- execution succeeds
- verification passes
- retry count is zero

### Scenario B: Retry Path

Task type:

- intentionally fails the first attempt
- succeeds on retry
- ideally auth or helper related

Must prove:

- verification report is written
- `next_context_needs` is meaningful
- retry packet adds targeted fragments
- second attempt is better than the first

### Scenario C: Hard Fail Path

Task type:

- intentionally cannot recover within retry budget

Must prove:

- task reaches terminal failure
- escalation handoff is written
- metrics capture failure
- state history is complete

### Scenario D: Collaboration Path

Task type:

- raw user intent
- requires Product/CTO decomposition
- then one worker task and one QA check

Must prove:

- leadership brief is created before worker execution
- task has an assigned role and acceptance criteria
- worker session prompt stays in role
- session report captures changed files, result, blockers, and next step
- QA or reviewer can continue from artifacts without reading chat history

## Required Metrics

Every audited run must produce metrics containing at least:

- `packet_size`
- `loaded_file_count`
- `retry_count`
- `verifier_status`
- `execution_mode`

Useful secondary metrics:

- `execution_attempts`
- `last_changed_file_count`
- `last_command_count`

## Artifacts To Inspect

For each audited task, inspect:

- `runtime/state/task_packets/<TASK>.json`
- `runtime/state/task_packets/<TASK>.retry-1.json` when retry happens
- `runtime/state/agent_runs/<TASK>.attempt-N.execution.json`
- `runtime/state/verification_reports/<TASK>.verification.json`
- `runtime/reports/metrics/<TASK>.metrics.json`
- `runtime/reports/<TASK>.summary.json`
- `.hub/done/<TASK>.json`
- `.hub/handoffs/<TASK>-*.json` when escalation happens

## Change Impact Matrix

Use this table to decide the minimum audit level.

| Change Area | Minimum Audit |
|---|---|
| README, CHEATSHEET, non-runtime docs | Quick Recheck |
| ONBOARDING, PROMPT_PACK, DASHBOARD, OPERATING_RULES | Collaboration Revalidation |
| Metrics logger, summaries, post-task hooks | Quick Recheck |
| Orchestrator flow | Runtime Regression |
| Executor or runtime planner | Runtime Regression |
| Verifier or retry hook | Runtime Regression |
| State machine | Runtime Regression |
| Contracts or templates | Full System Revalidation |
| Session report, handoff, decision log, leadership brief contracts | Full System Revalidation + Collaboration Revalidation |
| Compile layer | Full System Revalidation |
| Retriever or module index | Full System Revalidation |
| Legacy cleanup affecting active manifests or docs | Full System Revalidation |

## Pass Criteria

The audit passes only when all of these are true:

- compile succeeds
- no import error occurs
- happy path completes
- retry path adds targeted context
- hard-fail path escalates cleanly
- metrics exist for every audited run
- session reports include role gate, context check, verification, handoff decision, next owner, and completeness gate
- handoffs include handoff gate, required context, evidence, and recommended next step
- small task packets remain small
- no stale compiled or runtime artifacts confuse the results

## Failure Criteria

Treat the audit as failed if any of these happen:

- compile succeeds but stale fragments survive from deleted docs or modules
- packet grows unexpectedly for a small task
- retry packet adds broad or irrelevant context
- state transitions are missing or inconsistent
- metrics are missing required fields
- runtime behavior does not change between `solo` and `paired`
- docs instruct users to follow a legacy workflow that conflicts with the V2 runtime

## Automated Commands

Use the serial audit command for template, docs, and baseline runtime checks:

```bash
python run_orchestrator.py audit
```

Use the sandbox system test after changing orchestration, classifier, router, execution, retry, or collaboration flow:

```bash
python run_orchestrator.py system-test --iterations 1
```

`system-test` copies SHIELD into a fresh sandbox and runs:

- zero-build simple website
- improve simple website
- solve-issue retry flow

Use the manual steps in this document when you need deeper inspection than the command output provides.
