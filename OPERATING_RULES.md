# Operating Rules

Rules for running SHIELD as a multi-session AI team.

This is the shared protocol for every session.

Role-specific prompts and skills must follow this file first.

## Document Authority

Use one canonical source per concern:

| Concern | Canonical source |
|---|---|
| Shared session process | `OPERATING_RULES.md` |
| New-session boot order | `ONBOARDING.md` |
| Role curriculum and skills | `ROLE_SKILL_MATRIX.md` |
| Copy-paste prompts | `PROMPT_PACK.md` |
| Product + CTO leadership workflow | `CTO_PRODUCT_WORKFLOW.md` |
| Current status and backlog | `STATUS.md` |
| CEO/operator view | `DASHBOARD.md` and `python run_orchestrator.py dashboard` |
| System validation | `SYSTEM_AUDIT.md` and `python run_orchestrator.py system-test --iterations 1` |

Other files may summarize these rules, but they should not define a competing workflow.

## 0. Universal Session Protocol

Every session follows the same sequence:

```text
Boot -> Sync -> Claim -> Work -> Verify -> Report or Handoff -> Dashboard
```

Before acting, confirm:

- scenario: `zero build`, `improve repo`, `solve issue`, or `assigned task`
- session role id, for example `backend-agent`
- task role key, for example `backend`
- current task id or leadership brief id
- owner session, if present
- latest relevant report or handoff
- acceptance criteria
- expected output artifact and template

If any of these are unclear, stop and resolve them before working.

## 1. Leadership First

Raw user intent goes to Product and CTO first.

Worker sessions should receive tasks, not vague ambitions.

Default chain:

```text
User -> Product + CTO -> Task -> Worker -> QA/Reviewer -> Product + CTO
```

## 2. Role Boundaries

- Stay inside your assigned role.
- Do not work on a task assigned to another role.
- If the task needs another role, create a handoff.
- If architecture changes, escalate to `cto-agent`.
- If scope or priority changes, escalate to `product-manager-agent` or `producer-agent`.
- If quality or release risk appears, escalate to `qa-lead-agent`.
- If security risk appears, escalate to `security-agent`.

Runtime note:

- `task.yaml.assigned_role` uses short role keys like `backend`, `frontend`, `qa`
- session prompts use agent ids like `backend-agent`, `frontend-agent`, `qa-lead-agent`
- map them explicitly before claiming work

Role Gate:

Before doing work, a session must answer:

- What is my `session_role`?
- What is the task `assigned_role`?
- Do they match?
- If not, which role should receive the handoff?

If `session_role` does not match `assigned_role`, do not execute the task.

Create a handoff or ask Product/CTO/Producer to reassign it.

## 3. One Task, One Owner

Every active task should have one active owner session.

Required fields:

- `task_id`
- `owner_role`
- `owner_session`
- `status`
- `next_step`

Do not let two sessions silently edit the same task.

## 4. Artifacts Over Chat

Chat is temporary.

Artifacts are the source of truth.

Important artifacts:

- `templates/leadership_brief.json`
- `templates/task.yaml`
- `templates/session_report.json`
- `templates/handoff.json`
- `templates/decision_log.json`
- `DASHBOARD.md`

Read the relevant template before writing the artifact.

Template map:

| Situation | Artifact | Template |
|---|---|---|
| Product/CTO intake or task decomposition | `leadership_brief` | `templates/leadership_brief.json` |
| Executable task | `task` | `templates/task.yaml` |
| Worker or reviewer progress | `session_report` | `templates/session_report.json` |
| Role transfer, blocker, or continuation | `handoff` | `templates/handoff.json` |
| Durable architecture or process decision | `decision_log` | `templates/decision_log.json` |
| Verification result | `verification_report` | `templates/verification_report.json` |
| Runtime context packet | `task_packet` | `templates/task_packet.json` |

## 5. Session Exit Rule

Before stopping, every session must leave:

- a session report, or
- a handoff, or
- a clear blocker report

No silent exits.

Minimum exit data:

- role gate result
- context check result
- what changed
- what was verified
- what is blocked
- whether handoff is needed
- next owner role
- who owns the next step
- which artifact was updated

Report Completeness Gate:

A session report is incomplete unless it has:

- `task_id`
- `session_id`
- `role`
- `role_gate`
- `context_check`
- `status`
- `summary`
- `changed_files`
- `verification`
- `blockers`
- `handoff_needed`
- `next_owner_role`
- `next_step`
- `artifacts`

## 6. Minimal Context

Read only what you need:

1. dashboard
2. onboarding
3. relevant task
4. latest relevant report or handoff
5. related files

Do not scan the whole repo unless the task requires architecture review.

## 7. Handoff Rules

Use a handoff when:

- another role must continue
- a blocker exists
- verification failed and the next attempt needs targeted context
- the task owner changes
- scope or architecture needs leadership decision

A handoff must include:

- handoff gate result
- from role/session
- to role
- reason
- completed work
- required context
- related files
- evidence
- open questions
- recommended next step

## 8. Security

- No hardcoded secrets.
- No logging PII.
- Validate input.
- Sanitize output.
- Treat auth, payments, security, migrations, and data deletion as high-risk.

## 9. Git Workflow

- One task = one branch when doing implementation work.
- Do not mix unrelated changes.
- Run relevant checks before marking work complete.
- Do not mark a task done if there are unreported changes.
- Record commit/branch/PR status in the session report when applicable.

## 10. Runtime Commands

Use runtime commands only after a task exists.

```bash
python run_orchestrator.py compile
python run_orchestrator.py plan path/to/task.yaml
python run_orchestrator.py run path/to/task.yaml
python run_orchestrator.py audit
```

`run` is a worker execution engine.

It is not a replacement for Product/CTO intake.

`audit` should be run after workflow, contract, hook, or runtime changes.

## 11. Keep It Simple

Do not add process for its own sake.

The minimum useful system is:

```text
leadership brief -> task -> execution -> verification -> report/handoff -> dashboard
```

## 12. No Duplicate Process

- Do not create a new workflow document if an existing canonical file can be updated.
- Do not repeat full process steps in multiple docs; summarize and link back to the canonical source.
- Do not add templates with overlapping purpose.
- Do not add a new status/report artifact unless `.hub/`, `runtime/reports/`, or existing templates cannot represent it.
- If two rules conflict, `OPERATING_RULES.md` wins for session process.
