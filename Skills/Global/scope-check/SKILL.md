---
name: scope-check
description: "Check whether a SHIELD task, feature, sprint, or issue fix is drifting beyond the approved scope."
argument-hint: "[task-id, feature, sprint, or issue]"
user-invocable: true
allowed-tools: Read, Glob, Grep
---

# Scope Check

Use this skill when a session may be doing more than the task asked for.

The goal is to protect focus:

```text
approved intent -> scoped task -> bounded execution -> report or handoff
```

## Workflow

### 1. Find The Approved Scope

Read the smallest relevant artifact:

- assigned `task.yaml`
- `leadership_brief`
- `CTO_PRODUCT_WORKFLOW.md` task breakdown
- `.hub/active/<task>.json`
- `.hub/handoffs/<task>.json`
- `runtime/reports/session_reports/<task>.json`
- issue text or PR summary, if SHIELD artifacts do not exist yet

Do not treat vague chat as approved scope if a structured task exists.

### 2. Compare Against Current Work

Check:

- changed files
- newly introduced modules
- tests added or skipped
- acceptance criteria touched
- extra behavior added
- new dependencies or config changes
- any architecture decision made without a decision log

### 3. Classify Scope Drift

| Verdict | Meaning |
|---|---|
| `on track` | Work matches task and acceptance criteria |
| `minor drift` | Small adjacent changes, low risk, should be reported |
| `needs approval` | Adds new behavior, dependency, schema, API, or architecture decision |
| `out of scope` | Work solves a different problem or expands the task materially |

### 4. Output

Return:

```markdown
# Scope Check: [task or feature]

## Verdict
[on track / minor drift / needs approval / out of scope]

## Approved Scope
[summary]

## Current Work
[summary]

## Drift
[what changed beyond scope, if any]

## Recommendation
[continue / report drift / create handoff / ask Product or CTO]
```

### 5. Guardrails

- Product owns value and scope.
- CTO owns technical direction and architecture boundaries.
- Worker roles should not silently expand scope.
- If scope changed, write it into the session report or handoff.
