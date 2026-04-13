---
name: onboard
description: "Onboard a SHIELD role session into the current project. Loads the correct system docs, role persona, task context, and task-specific skills without scanning the whole repo."
argument-hint: "[role] [scenario]"
user-invocable: true
allowed-tools: Read, Glob, Grep
---

# SHIELD Role Onboarding

Use this skill when a new AI session joins the project.

The goal is not to read everything.

The goal is:

```text
Role -> Task -> Minimal context -> Work -> Report or Handoff
```

## Workflow

### 1. Resolve Role

If the user provides a role, use it.

Examples:

- `product-manager-agent`
- `cto-agent`
- `backend-agent`
- `frontend-agent`
- `fullstack-agent`
- `qa-lead-agent`
- `lead-programmer-agent`
- `security-agent`

If no role is provided, infer conservatively:

| Situation | Default role |
|---|---|
| Raw idea or unclear intent | `product-manager-agent` |
| Architecture or system direction | `cto-agent` |
| Existing task with assigned role | assigned role |
| Implementation task | `backend-agent`, `frontend-agent`, or `fullstack-agent` |
| Verification or reproduction | `qa-lead-agent` |
| Review correctness | `lead-programmer-agent` |
| Security-sensitive task | `security-agent` |

If still unclear, start as `product-manager-agent`.

### 2. Read Boot Docs

Read these in order:

1. `ONBOARDING.md`
2. `DASHBOARD.md`
3. `COLLABORATION_MODEL.md`
4. `CTO_PRODUCT_WORKFLOW.md`
5. `OPERATING_RULES.md`
6. `manifest.yaml`
7. `ROLE_SKILL_MATRIX.md`

Do not read raw chat history if SHIELD artifacts exist.

### 3. Load Role Curriculum

From `manifest.yaml` and `ROLE_SKILL_MATRIX.md`, identify:

- agent id
- task role key
- persona path
- core skills
- task-specific skills
- expected output artifact

From `OPERATING_RULES.md`, identify:

- required sync checks
- claim conditions
- verification expectations
- report or handoff rule
- required template for the expected output

Read the persona file.

Read only skills needed for the current task.

Do not load every role skill by default.

### 4. Locate Current Work

Use the smallest available source of truth:

- assigned `task.yaml`
- `leadership_brief`
- `.hub/active/`
- `.hub/handoffs/`
- `runtime/reports/session_reports/`
- `DASHBOARD.md`

Prefer structured artifacts over full repo scans.

### 5. Produce Onboarding Summary

Return this summary before working:

```markdown
# Session Onboarding: [role]

## Role
[agent id and task role key]

## Scenario
[zero build / improve repo / solve issue / assigned task]

## Loaded Context
[docs, persona, task, handoff, specific skills]

## Current Task
[task id, objective, acceptance criteria, owner session]

## Boundaries
[what this session should not do]

## Expected Output
[session_report / handoff / leadership_brief / verification_report / decision_log]

## Required Template
[template path to read before writing]

## Next Action
[the smallest safe next step]
```

### 6. End Correctly

Every onboarded session must end with one of:

- `session_report`
- `handoff`
- `leadership_brief`
- `verification_report`
- `decision_log`, only when a durable decision was made

No silent exits.

## Guardrails

- Workers do not start from vague intent.
- Product and CTO turn vague intent into tasks.
- QA and reviewers verify and challenge.
- If role curriculum is missing, stop and ask for a role-system audit.
