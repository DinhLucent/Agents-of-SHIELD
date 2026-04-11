# Joining an Existing Project

> **Understand → Compress → Validate → Develop. No skipping.**

---

## Phase 1 — UNDERSTAND

Run `understand-anything` or equivalent deep-scan on the codebase.

**Must answer:**

- Tech stack? (lang, framework, DB, infra)
- Architecture? (monolith / microservices / event-driven)
- Entry points? (main files, API routes, CLI)
- Data flow? (input → process → output → storage)
- External deps? (APIs, 3rd-party services, shared DBs)
- Deploy pipeline? (CI/CD, staging, prod)
- Test coverage? (unit, integration, e2e)
- Known debt? (README, issues, TODOs)

**Also read:** `README.md`, `CHANGELOG.md`, `docs/`, recent PRs, open issues.

**Run locally:** Clone → Install → Build → Run → Execute tests.

> ⚠️ Cannot run locally = first red flag to fix.

---

## Phase 2 — COMPRESS

Distill everything into **1 token-efficient context file** at project root.

**File:** `PROJECT_CONTEXT.md` (or `CLAUDE.md` / `AGENTS.md`)

```
# Project: [name]
## Stack: [one-liner]
## Architecture: [pattern + mermaid if needed]
## Modules: [name: purpose — one line each]
## Data Flow: [input → process → output]
## Rules: [MUST do / MUST NOT do]
## Current State: [sprint focus]
## Known Issues: [top 3]
```

**Compression rules:**

| Rule | Why |
|------|-----|
| Every line = information | No filler prose |
| Headers + tables + bullets | No long paragraphs |
| Actionable | Every item → specific action |
| Layered | L1: 30s overview. L2: 5min detail |
| Living doc | Update as project evolves |
| English only | ~2x fewer tokens than Vietnamese |

**Optional extras:** `ARCHITECTURE.md` for complex systems, directory-level `.context.md` for large modules.

---

## Phase 3 — VALIDATE

> Wrong understanding here = wrong code all sprint.

1. **Review** — Present understanding to team lead. Ask: "What did I miss?"
2. **Warm-up task** — Pick 1 small bug/low-risk task to verify:
   - Local setup works
   - Can navigate codebase
   - Dev workflow (branch → PR → review) is clear
3. **Checkpoint** — Only proceed when: context reviewed, warm-up done, no blocking questions.

---

## Phase 4 — DEVELOP

Follow team workflows: `ONBOARDING.md` → `OPERATING_RULES.md` → `GIT_WORKFLOW.md` → Task Hub.

**Per task:** Claim → Read context → Plan → Implement → Test → PR → Update context if changed → Handoff.

**Keep context alive:** New discovery → update context file. Architecture change → update diagram. New debt → log it.

---

## Anti-Patterns

| ❌ Wrong | ✅ Right |
|----------|----------|
| Jump into code immediately | Understand → Compress → Validate → Develop |
| Read every file in project | Read context → deep-dive only when needed |
| Assume you understand | Verify with warm-up task |
| One-time context, then forget | Living document, update continuously |
| Copy conventions from old project | Learn THIS project's conventions |
| Write docs in non-English | English = fewer tokens, better agent recall |
