---
name: start
description: "Start a SHIELD workflow by detecting whether the user needs zero build, improve repo, solve issue, or assigned-task execution."
argument-hint: "[optional: intent]"
user-invocable: true
allowed-tools: Read, Glob, Grep
---

# SHIELD Start

Use this skill when the user says they want to begin applying SHIELD, but has not yet chosen the right workflow.

Do not assume they need code immediately.

First route the situation.

## Workflow

### 1. Detect Project State

Silently check for:

- `README.md`
- `ONBOARDING.md`
- `DASHBOARD.md`
- `manifest.yaml`
- `ROLE_SKILL_MATRIX.md`
- `templates/task.yaml`
- `.hub/active/`
- `.hub/handoffs/`
- `runtime/reports/session_reports/`
- source directories such as `src/`, `app/`, `services/`, `packages/`, `lib/`
- test directories such as `tests/`, `test/`, `e2e/`

Use this only to tailor the recommendation.

### 2. Classify The User Intent

Choose one:

| Situation | Workflow | First role |
|---|---|---|
| User wants to create something from zero | `zero build` | `product-manager-agent` |
| User cloned or has an existing repo to improve | `improve repo` | `product-manager-agent` |
| User has a concrete bug, issue, failing test, or incident | `solve issue` | `qa-lead-agent` or `product-manager-agent` |
| User has a structured task already | `assigned task` | assigned role |

If the intent is vague, default to `improve repo` for existing code and `zero build` for empty projects.

### 3. Recommend The Next Session

Give the user the next session prompt.

For raw intent:

```text
Onboard into this repo as product-manager-agent.
Read ONBOARDING.md, DASHBOARD.md, COLLABORATION_MODEL.md, CTO_PRODUCT_WORKFLOW.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md.
Scenario: [zero build / improve repo / solve issue]
Intent: [paste the user goal]
End with a leadership brief or clear next step.
```

For implementation:

```text
Onboard into this repo as [assigned-role-agent].
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, ROLE_SKILL_MATRIX.md, and the assigned task/handoff.
Stay inside the task scope.
End with a session report or handoff.
```

### 4. Do Not Skip Leadership

Workers should not receive vague goals like:

```text
Improve this repo however you think.
```

Instead Product/CTO should produce:

- scope
- acceptance criteria
- task breakdown
- role assignment
- verification expectation

### 5. Output Format

Return:

```markdown
# SHIELD Start Recommendation

## Detected Workflow
[zero build / improve repo / solve issue / assigned task]

## First Session
[role]

## Why
[short reason]

## Copy-Paste Prompt
[prompt]

## Next Artifact
[leadership_brief / task.yaml / session_report / handoff]
```

## Guardrail

Keep it simple.

The start skill routes work. It does not redesign the system.
