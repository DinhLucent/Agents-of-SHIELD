---
description: "Task Hub Protocol — How Agents pick up, execute, and return tasks"
---

# 🏗️ Task Hub Protocol

> **MANDATORY.** All Agents follow this. The only way to receive and return tasks.

## Hub Structure

```
.hub/
├── backlog.yaml    ← Task queue (source of truth)
├── active/         ← Tasks in progress (1 file per task)
├── done/           ← Completed + detailed report for CEO
└── handoffs/       ← Agent-to-agent transfer files
```

`DASHBOARD.md` at project root = Quick Context + Task Board + Timeline.

---

## Step 0: READ FIRST (every session)

1. Read `DASHBOARD.md` → Quick Context (phase, progress, last agent)
2. Read `.hub/backlog.yaml` → find task with `assigned_role` = your Agent ID

---

## Step 1: FIND matching task

In `backlog.yaml`, find tasks where:
- `status: "todo"`
- `assigned_role` = **your** Agent ID
- `dependencies` all `done`

```
┌─────────────────────────────────────────────────┐
│  assigned_role ≠ your ID → MUST REFUSE          │
│  → "Task [ID] is for [assigned_role], not me."  │
│  → DO NOT execute even 1 line                   │
│                                                 │
│  No matching tasks → Tell User:                 │
│  → "No tasks in Hub for my role [my-role]."     │
│                                                 │
│  Task needs expertise outside ALL active roles: │
│  → HIRING REQUEST to User:                      │
│  → "This task requires [skill/role] expertise.  │
│     No active Agent covers this. Recommend      │
│     hiring [suggested-agent-id] via             │
│     RECRUITMENT.md to fill this gap."           │
│  → DO NOT attempt the work yourself             │
└─────────────────────────────────────────────────┘
```

## Step 2: CLAIM

1. `backlog.yaml`: change `status` → `"claimed"`
2. Create `.hub/active/TASK-xxx.md`:
   ```
   # TASK-xxx: [Title]
   - Agent: [id] | Claimed: [time] | Status: 🔄
   ## Acceptance Criteria
   [from backlog]
   ## Work Log
   - [time] Started...
   ```
3. Update `DASHBOARD.md` (move to IN PROGRESS, update Quick Context)

## Step 3: EXECUTE

- Update Work Log in `.hub/active/TASK-xxx.md`
- Blocked → note in Dashboard
- Need another Agent → create handoff (Step 5)

## Step 4: COMPLETE

1. `backlog.yaml`: `status` → `"done"`, fill `output_files`
2. Move `.hub/active/TASK-xxx.md` → `.hub/done/TASK-xxx.md`
3. Add to done file:
   ```
   ## Completion Report
   - Completed: [time]
   - Files: [list]
   - Summary: [2-3 sentences]
   - Decisions: [key decisions]
   - Issues: [if any]
   - Notes for next Agent: [if any]
   ```
4. Update `DASHBOARD.md`:
   - **Quick Context**: progress %, last agent, 1-line summary
   - **Tasks**: move to DONE
   - **Timeline**: add 1 line (`[date] agent — COMPLETED: description`)

## Step 5: HANDOFF

Create `.hub/handoffs/TASK-xxx-[from]-to-[to].md`:
```
# Handoff: [from] → [to]
## Task: TASK-xxx — [title]
## Completed: [what was done]
## Needs: [what next agent must do]
## Files: [changed/created]
## Context: [decisions, warnings]
```
Create new task in `backlog.yaml` for next Agent.

---

## Compact Reporting Rules

| Where | What | Limit |
|-------|------|-------|
| `DASHBOARD.md` Quick Context | 1-line summary for AI | ≤10 rows |
| `DASHBOARD.md` Timeline | 1 line per event | ≤20 entries |
| `.hub/done/TASK-xxx.md` | Full report for CEO | No limit |

> Dashboard must stay lean. If too long → new AI can't absorb it.

---

## Anti-Patterns

- ❌ Skip reading Hub before working
- ❌ Accept wrong-role task
- ❌ Skip Dashboard update after task
- ❌ Create tasks without User/Producer approval
- ❌ Skip handoff when transferring work
- ❌ Do work outside your role "to be helpful" — escalate instead
- ❌ Silently skip tasks that need missing roles — always request hiring

## Triggers

Auto-activates on: session start, "get task", "check tasks", "update dashboard", task completion.
