# SHIELD Session Onboarding

Read this first when opening any new AI session.

This file defines boot order only. For shared process rules, use `OPERATING_RULES.md`.

The goal is simple:

```text
Role -> Task -> Minimal context -> Work -> Report or Handoff
```

Do not start from raw chat history if SHIELD artifacts exist.

## 1. Resolve Your Role

If the user explicitly gives a role, use it.

Examples:

- `Onboard as product-manager-agent`
- `Onboard as cto-agent`
- `Onboard as backend-agent`
- `Onboard as frontend-agent`
- `Onboard as qa-lead-agent`

If no role is given, infer the safest role:

| Situation | Default role |
|---|---|
| Raw idea, new feature, unclear request | `product-manager-agent` |
| Architecture, ADR, system direction | `cto-agent` |
| Existing task with `assigned_role` | that assigned role |
| Build or code implementation | `backend-agent`, `frontend-agent`, or `fullstack-agent` based on task |
| Verify, test, release confidence | `qa-lead-agent` |
| Review correctness or risk | `lead-programmer-agent` or `security-agent` |

If still unsure, start as `product-manager-agent` and ask for clarification.

Role naming note:

- session agent ids usually look like `backend-agent`, `frontend-agent`, `qa-lead-agent`
- runtime task role keys usually look like `backend`, `frontend`, `qa`

When reading `assigned_role` in `task.yaml`, map it to the closest session agent id.

Examples:

| Task `assigned_role` | Session agent |
|---|---|
| `backend` | `backend-agent` |
| `frontend` | `frontend-agent` |
| `fullstack` | `fullstack-agent` |
| `qa` | `qa-lead-agent` |
| `cto` | `cto-agent` |
| `producer` | `producer-agent` |
| `security` | `security-agent` |

## 2. Load System Context

Read in this order:

1. `DASHBOARD.md`
2. `runtime/cache/indexes/project_snapshot_index.json` (quick summary of tasks, handoffs, reports — no full file scan needed)
3. `OPERATING_RULES.md`
4. `CTO_PRODUCT_WORKFLOW.md` only when the task needs Product/CTO leadership context
5. `manifest.yaml`
6. `ROLE_SKILL_MATRIX.md`
7. your persona file from `manifest.yaml`, if present
8. only the skills relevant to the current task

Do not read every skill upfront.

Load skills on demand.

The matrix is the role curriculum. It tells each session which persona and core skills are required for that role.

## 3. Pick The Right Workflow

Use one of these paths.

| Scenario | Leadership path | Worker path |
|---|---|---|
| Zero build | Product frames product goal, CTO frames architecture, then tasks are created | Workers build only after leadership brief is approved |
| Improve existing repo | Product defines improvement value, CTO maps impact, then tasks are created | Workers implement scoped tasks and report back |
| Solve issue | Product clarifies impact, CTO or QA triages root cause, then a fix task is created | Worker fixes, QA verifies, leadership closes |

## 4. Claim Work Safely

Before doing work, confirm:

- task id
- assigned role
- mapped session agent id
- role gate result: mapped session role must match assigned role
- owner session
- acceptance criteria
- related files
- latest relevant session report or handoff
- task is not already done unless this is an explicit retry/new task
- expected output

Read the template for the expected output before writing it.

Do not work on a task assigned to another role unless Product or CTO reassigns it.

If the role gate fails, stop and write a handoff to the correct role.

## 5. During Work

Keep scope tight.

Rules:

- one session, one primary task
- do not redesign unless the task asks for it
- read only context that helps the task
- if blocked, write the blocker clearly
- if another role is needed, create a handoff

## 6. Before Stopping

Every session must leave one of these:

- `session_report`
- `handoff`
- `decision_log`, only if a durable decision was made

Minimum report:

```text
Task:
Role:
Role gate:
Context checked:
Summary:
Changed files:
Verification:
Blockers:
Handoff needed:
Next owner role:
Next step:
```

No silent exits.

## 7. What Each Role Produces

| Role | Main output |
|---|---|
| Product | `leadership_brief`, scope, acceptance summary, priority |
| CTO | technical direction, ADR trigger, task decomposition |
| Producer / PM | sprint, task sequencing, status hygiene |
| Backend / Frontend / Fullstack | implementation, tests, session report |
| QA | verification report, risk notes, pass/fail |
| Reviewer / Security | findings, risks, required fixes |

## 8. Golden Rule

Workers do not start from vague user intent.

Leadership turns intent into tasks first.

Then workers execute.
