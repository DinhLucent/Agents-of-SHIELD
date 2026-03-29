# ⚖️ Operating Rules

> Core rules. For full Hub protocol see `Skills/Global/task-hub/SKILL.md`.

---

## 1. Task Hub

- All work goes through `.hub/`. No exceptions.
- On session start: read `DASHBOARD.md` → `.hub/backlog.yaml`
- Only claim tasks matching your `assigned_role`. Wrong role → **refuse**.
- After every task: update Dashboard (1 line) + write report to `.hub/done/`.

## 2. User Communication

```
ASK → OPTIONS → USER OK → DRAFT → APPROVE
```

Never write files without approval. Never override User choices.

## 3. Role Boundaries

- Stay within your Persona scope. **Never** do work outside your role.
- Need other expertise → suggest User call the right Agent.
- Found security issue → **must** report to `security-agent`.
- Task needs a role that doesn't exist → **request hiring**:
  > "This requires [role]. No active Agent covers this. Recommend hiring via RECRUITMENT.md."

## 4. Escalation

| Issue | Escalate To |
|-------|-------------|
| Technical conflict | `technical-director-agent` |
| Architecture impact | `cto-agent` |
| Scope/timeline | `producer-agent` |
| Quality concern | `qa-lead-agent` |
| Uncertain | **Ask User** |

## 5. Handoff

1. Create file in `.hub/handoffs/` (use `templates/handoff-template.md`)
2. Create new task in `backlog.yaml` for next Agent
3. Update Dashboard

## 6. Security

- ❌ No hardcoded secrets
- ❌ No logging PII
- ✅ Validate input, sanitize output
- Full rules: `Skills/Global/.agents/rules/security.md`
