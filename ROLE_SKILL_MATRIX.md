# ROLE_SKILL_MATRIX

This is the role curriculum for SHIELD sessions.

Use it to answer one question:

```text
When I open a session as this role, what should it know before acting?
```

Do not load every skill in the repository.

Load the boot docs first, then the persona, then only the skills that match the task.

## Universal Boot Order

Every session starts here:

1. `ONBOARDING.md`
2. `DASHBOARD.md`
3. `OPERATING_RULES.md`
4. `CTO_PRODUCT_WORKFLOW.md` only for Product/CTO leadership work or scope questions
5. `manifest.yaml`
6. This role matrix
7. The role persona file from `manifest.yaml`
8. Task-specific skills only

If a task has a handoff, read the handoff before reading extra skills.

`OPERATING_RULES.md` is the shared process for every role. This file only adds role-specific curriculum.

## Core Role Curriculum

| Session role | Task role key | Persona | Core skills | Use when | Must produce |
|---|---|---|---|---|---|
| `product-manager-agent` | `product` | `Skills/Roles/Management/product-manager.md` | `Skills/Roles/Management/sprint-plan`, `Skills/Roles/Management/estimate`, `Skills/Roles/Management/milestone-review` | Raw intent, scope, user value, acceptance criteria | `leadership_brief`, scoped task proposal, acceptance summary |
| `cto-agent` | `cto` | `Skills/Roles/Architecture/cto.md` | `Skills/Roles/Architecture/architecture-decision`, `Skills/Roles/Architecture/map-systems`, `Skills/Roles/Architecture/reverse-document` | Architecture, ADR, task decomposition, technical risk | technical direction, ADR trigger, task breakdown |
| `lead-programmer-agent` | `reviewer` | `Skills/Roles/Architecture/lead-programmer.md` | `Skills/Roles/Development/code-review`, `Skills/Roles/Development/tech-debt`, `Skills/Roles/Architecture/architecture-decision` | Engineering review, correctness, maintainability risk | review findings, required fixes, merge recommendation |
| `backend-agent` | `backend` | `Skills/Roles/Development/backend-developer.md` | `Skills/Roles/Development/api-design`, `Skills/Roles/Development/db-review`, `Skills/Roles/Development/code-review`, `Skills/Roles/Development/team-backend` | API, data, services, backend bugfix | implementation, tests, session report |
| `frontend-agent` | `frontend` | `Skills/Roles/Development/frontend-developer.md` | `Skills/Roles/Development/design-system`, `Skills/Roles/Development/design-review`, `Skills/Roles/Development/code-review`, `Skills/Roles/Development/team-frontend` | UI, components, pages, frontend bugfix | implementation, visual notes, session report |
| `fullstack-agent` | `fullstack` | `Skills/Roles/Development/fullstack-developer.md` | `Skills/Roles/Development/api-design`, `Skills/Roles/Development/db-review`, `Skills/Roles/Development/code-review`, `Skills/Roles/Development/team-feature` | Cross-layer feature or integration | implementation, tests, session report |
| `qa-lead-agent` | `qa` | `Skills/Roles/Quality/qa-lead.md` | `Skills/Roles/Quality/gate-check`, `Skills/Roles/Quality/bug-report`, `Skills/Roles/Quality/release-checklist` | Verification, reproduction, release confidence | verification report, pass/fail, risk note |
| `security-agent` | `security` | `Skills/Roles/Specialist/Security/security-engineer.md` | `Skills/Roles/Specialist/Security/threat-model`, `Skills/Roles/Specialist/Security/secret-audit`, `Skills/Roles/Specialist/Security/deep-scan` | Auth, secrets, security-sensitive changes | findings, threat model, required fixes |
| `producer-agent` | `producer` | `Skills/Roles/Management/producer.md` | `Skills/Roles/Management/sprint-plan`, `Skills/Roles/Management/estimate`, `Skills/Roles/Management/retrospective`, `Skills/Roles/Management/team-release` | Sprint hygiene, sequencing, cross-session status | sprint plan, status update, coordination note |
| `ui-programmer-agent` | `ui` | `Skills/Roles/Development/ui-programmer.md` | `Skills/Roles/Development/design-system`, `Skills/Roles/Development/team-ui`, `Skills/Roles/Development/localize` | Focused UI implementation and UI polish | UI implementation, design-system notes |
| `ux-designer-agent` | `ux` | `Skills/Roles/Specialist/Design/ux-designer.md` | `Skills/Roles/Development/design-system`, `Skills/Roles/Development/design-review` | UX flow, interaction clarity, usability review | UX notes, design review, acceptance advice |

## Scenario Mapping

| Scenario | First roles | Worker roles | Reviewer roles |
|---|---|---|---|
| `zero build` | `product-manager-agent`, then `cto-agent` | `backend-agent`, `frontend-agent`, `fullstack-agent`, `ui-programmer-agent` | `qa-lead-agent`, `lead-programmer-agent`, `security-agent` when needed |
| `improve repo` | `product-manager-agent`, then `cto-agent` | role from task scope | `qa-lead-agent`, `lead-programmer-agent` |
| `solve issue` | `qa-lead-agent` or `product-manager-agent`, then `cto-agent` if boundary is unclear | role owning the failing area | `qa-lead-agent`, plus `security-agent` for sensitive bugs |
| `assigned task` | no new leadership unless scope is unclear | assigned role only | reviewer role from task risk |

## Artifact Template Map

| Output | Required template |
|---|---|
| `leadership_brief` | `templates/leadership_brief.json` |
| `session_report` | `templates/session_report.json` |
| `handoff` | `templates/handoff.json` |
| `decision_log` | `templates/decision_log.json` |
| `verification_report` | `templates/verification_report.json` |
| `task` | `templates/task.yaml` |
| `task_packet` | `templates/task_packet.json` |

Every role must read the relevant output template before writing or updating that artifact.

## Optional Skill Pool

Some roles reference `.skills_pool/`.

Those skills are opt-in for compilation:

```bash
python run_orchestrator.py compile --include-pool
```

If `.skills_pool` is not included, sessions should still follow the role persona and core `Skills/` curriculum.

Do not make a worker depend on a pool skill unless the project has opted into `.skills_pool`.

## Guardrails

- Product and CTO receive raw, vague intent.
- Worker roles receive scoped tasks.
- QA and reviewer roles verify, challenge, and close.
- Every role ends with a session report or handoff.
- If a role cannot find its persona or core skills, stop and run `python run_orchestrator.py audit`.
