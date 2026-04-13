# CHEATSHEET

Open this when you do not know what to do next.

This is a quick guide, not the canonical process.

If anything here conflicts with `OPERATING_RULES.md`, follow `OPERATING_RULES.md`.

## Default SHIELD Flow

```text
User -> Product + CTO -> Task -> Worker -> QA/Reviewer -> Product + CTO -> Dashboard
```

Workers should not start from vague user intent.

Product and CTO turn intent into tasks first.

## First 60 Seconds

1. Open `DASHBOARD.md`.
2. Read `ONBOARDING.md`.
3. Identify your role.
4. Identify the scenario:
   - `zero build`
   - `improve repo`
   - `solve issue`
   - `assigned task`
5. Read only the relevant task/report/handoff.
6. Work.
7. End with report or handoff.

## Which Session To Open

| Situation | Open this role first |
|---|---|
| Idea from zero | `product-manager-agent`, then `cto-agent` |
| Improve a cloned repo | `product-manager-agent`, then `cto-agent` if architecture impact exists |
| Fix a bug or issue | `qa-lead-agent` for impact triage, then worker role |
| Architecture concern | `cto-agent` |
| Backend/API/data change | `backend-agent` after task exists |
| UI/component/page change | `frontend-agent` after task exists |
| Cross-layer feature | `fullstack-agent` after task exists |
| Verify or release check | `qa-lead-agent` |
| Security concern | `security-agent` |

If unsure, open `product-manager-agent`.

## Copy-Paste Session Start

```text
Onboard into this repo as [role].
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, CTO_PRODUCT_WORKFLOW.md when leadership context is needed, manifest.yaml, and ROLE_SKILL_MATRIX.md.
Use manifest.yaml plus ROLE_SKILL_MATRIX.md to confirm my role/persona/skills.

Scenario: [zero build / improve repo / solve issue / assigned task]
Task or intent: [paste]

Stay inside my role.
End with a session report or handoff.
```

## Zero Build

Use `PROMPT_PACK.md` scenario 1.

Short version: Product brief first, CTO decomposition second, worker tasks third, QA last.

## Improve Existing Repo

Use `PROMPT_PACK.md` scenario 2.

Short version: Product frames value, CTO maps impact when needed, workers handle scoped tasks, QA/reviewer verifies.

## Solve Issue

Use `PROMPT_PACK.md` scenario 3.

Short version: clarify impact/repro, assign a focused fix task, verify the original issue and nearby regression risk.

## Runtime Commands

Use these when a task is already structured and executable.

```bash
python run_orchestrator.py compile
python run_orchestrator.py plan path/to/task.yaml
python run_orchestrator.py run path/to/task.yaml
python run_orchestrator.py dashboard
python run_orchestrator.py audit
python run_orchestrator.py system-test --iterations 1
```

`plan` checks routing and packet shape.

`run` executes, verifies, retries, and finalizes.

`dashboard` shows the current CEO/operator view from `.hub/` and `runtime/reports/`.

`audit` checks compile, collaboration templates, plan, happy path, retry path, and hard-fail handoff.

`system-test` creates a fresh sandbox and runs zero-build, improve, and fix/retry scenarios.

## Artifacts To Read

| Need | Read |
|---|---|
| Overall status | `DASHBOARD.md` |
| Live CEO/operator view | `python run_orchestrator.py dashboard` |
| How sessions work | `ONBOARDING.md` |
| Shared process for every session | `OPERATING_RULES.md` |
| Role curriculum | `ROLE_SKILL_MATRIX.md` |
| Leadership flow | `CTO_PRODUCT_WORKFLOW.md` |
| Executed task output | `.hub/done/` |
| Active task state | `.hub/active/` |
| Transfer context | `.hub/handoffs/` |
| Detailed session reports | `runtime/reports/session_reports/` |
| Quick session reports | `runtime/reports/quick_reports/` |
| Runtime packets | `runtime/state/task_packets/` |
| Verification | `runtime/state/verification_reports/` |
| Sandbox validation reports | `runtime/reports/system_tests/` |

## Never Skip

- Role resolution
- Role gate: session role must match task `assigned_role`
- Shared protocol in `OPERATING_RULES.md`
- Task ownership check
- Latest relevant report/handoff check
- Acceptance criteria
- Required output template
- Verification
- Session report or handoff with `handoff_needed`, `next_owner_role`, and `next_step`

## One-Line Reminder

```text
Role first. Task second. Work third. Report last.
```
