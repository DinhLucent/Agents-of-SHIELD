# DASHBOARD

Quick context for SHIELD sessions.

Keep this file short. Detailed history belongs in reports and handoffs.

## Project Snapshot

| Key | Value |
|---|---|
| Project | Agents-of-SHIELD |
| Operating model | Product + CTO first, workers by assigned task |
| Current phase | Collaboration workflow + sandbox validation |
| Primary workflow | `User -> Product + CTO -> Task -> Worker -> QA/Reviewer -> Dashboard` |
| Last updated | 2026-04-14 |

## CEO / Operator Check

Use this for the live artifact view:

```bash
python run_orchestrator.py dashboard
```

Source of truth:

- `.hub/active/`
- `.hub/done/`
- `.hub/handoffs/`
- `runtime/reports/session_reports/`
- `runtime/reports/quick_reports/`
- `runtime/reports/system_tests/`

## Current Focus

- Restore leadership-first intake.
- Make role sessions start from onboarding and task artifacts.
- Keep the execution kernel stable.
- Add collaboration writeback through session reports, handoffs, and decisions.
- Keep sandbox system tests passing for zero-build, improve, and fix/retry flows.

## Active Roles

| Role | Use for |
|---|---|
| `product-manager-agent` | problem framing, scope, priority, acceptance |
| `cto-agent` | architecture, ADR, technical decomposition |
| `producer-agent` | sprint sequencing and task hygiene |
| `backend-agent` | backend/API/data tasks |
| `frontend-agent` | UI/component/page tasks |
| `fullstack-agent` | cross-layer tasks |
| `qa-lead-agent` | verification, release confidence, bug triage |
| `security-agent` | security review and risk escalation |

## Open Work

| Item | Owner | Status |
|---|---|---|
| Collaboration contracts | Product + CTO | drafted |
| Runtime writeback for session reports | Runtime | working |
| Handoff contract integration | Runtime | working |
| Dashboard derived from artifacts | Runtime | working via CLI |
| Sandbox system-test loop | Runtime | working |

## Recent Decisions

- Keep current execution kernel.
- Restore the old `MyTeam` control rhythm.
- Use `leadership_brief` before worker execution when user intent is raw.
- Use structured JSON artifacts first, markdown summaries second.

## Session Boot Reminder

```text
Read ONBOARDING.md -> confirm role -> read task/report/handoff -> work -> write report/handoff
```
