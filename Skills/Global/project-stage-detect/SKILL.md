---
name: project-stage-detect
description: "Analyze an existing software project and classify whether SHIELD should run zero build, improve repo, solve issue, or assigned-task flow."
argument-hint: "[optional: role filter]"
user-invocable: true
allowed-tools: Read, Glob, Grep
---

# Project Stage Detect

Use this skill when a session needs to understand where a project is before planning work.

This is not a full architecture review.

It is a fast stage and gap scan.

## Workflow

### 1. Scan Minimal Project Signals

Check for:

- repo docs: `README.md`, `docs/`, `CHANGELOG.md`
- app entrypoints: `src/`, `app/`, `services/`, `packages/`, `lib/`
- test entrypoints: `tests/`, `test/`, `e2e/`, `playwright.config.*`
- package files: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `.csproj`
- SHIELD artifacts: `ONBOARDING.md`, `DASHBOARD.md`, `manifest.yaml`, `ROLE_SKILL_MATRIX.md`, `.hub/`, `runtime/reports/`
- issue context: failing logs, open task, handoff, verification report

Do not scan the whole repo if the task already names the relevant files.

### 2. Classify Stage

| Stage | Indicators |
|---|---|
| `new idea` | no repo or only rough notes |
| `repo intake` | code exists, goal still vague |
| `planned improvement` | goal and target area exist, tasks not yet decomposed |
| `assigned task` | task.yaml or handoff exists |
| `active execution` | `.hub/active/` has current task state |
| `verification/retry` | verification report, failed test, or handoff exists |
| `maintenance` | change is small, bounded, and mostly regression-safe |

### 3. Recommend Role Path

| Stage | Recommended path |
|---|---|
| `new idea` | Product -> CTO -> task slices |
| `repo intake` | Product -> CTO -> first improvement task |
| `planned improvement` | CTO or Producer -> worker role |
| `assigned task` | assigned worker role |
| `active execution` | current owner session or handoff target |
| `verification/retry` | QA -> owning worker role |
| `maintenance` | owning worker role -> QA |

### 4. Produce Stage Report

Return:

```markdown
# Project Stage Report

## Stage
[stage]

## Evidence
[files/artifacts checked]

## Current SHIELD Artifacts
[dashboard, active task, handoff, reports, task contract]

## Gaps
[only gaps that affect next action]

## Recommended Next Role
[role]

## Next Step
[smallest useful action]
```

### 5. Guardrails

- Prefer structured SHIELD artifacts over chat memory.
- If raw intent is vague, route to Product first.
- If technical boundary is unclear, route to CTO.
- If verification failed, route to QA or the owning worker role with a handoff.
- Do not write files unless the user explicitly asks.
