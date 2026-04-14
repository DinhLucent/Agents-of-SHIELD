# STATUS

Last updated: 2026-04-14

## Current State

The V2 execution kernel is operational for normal serial use.

The product direction is now role-first:

`User -> Product + CTO -> Tasks -> Worker sessions -> QA/Reviewer -> Dashboard`

What is working:

- `compile -> plan -> run` works as the worker execution flow.
- The runtime loop is real: execute -> verify -> retry/complete.
- Task state is persisted through the execution state machine.
- Runtime metrics are written per run.
- Runtime post-task writeback now creates session reports and quick reports.
- Session reports now include required role gate, context check, verification, handoff decision, next owner, and completeness self-check fields.
- Hard-fail handoffs use the structured collaboration contract.
- `python run_orchestrator.py audit` runs the serial execution + collaboration baseline.
- `python run_orchestrator.py dashboard` prints the CEO/operator view from `.hub/` and `runtime/reports/`.
- `python run_orchestrator.py system-test --iterations 1` runs a fresh sandbox loop for zero-build, improve, and fix/retry scenarios.
- Collaboration docs now define Product/CTO intake, role sessions, reports, handoffs, and decision logs.
- `OPERATING_RULES.md` is the shared protocol every session must follow.
- `ROLE_SKILL_MATRIX.md` defines the role curriculum so each session knows its persona, skills, scenario, and expected output.
- Audit fixtures are runnable and verified serially:
  - `tests/fixtures/audit/happy_path.yaml`
  - `tests/fixtures/audit/retry_scenario.yaml`
  - `tests/fixtures/audit/hard_fail.yaml`
- `.skills_pool` is optional and only included when requested:
  - `python run_orchestrator.py compile --include-pool`

## Recommended Usage

For raw user intent:

1. Open `product-manager-agent`.
2. Create or update a `leadership_brief`.
3. Involve `cto-agent` if architecture or task decomposition matters.
4. Create scoped tasks.
5. Open worker sessions by assigned role.

For executable tasks:

```bash
python run_orchestrator.py compile
python run_orchestrator.py plan path/to/task.yaml
python run_orchestrator.py run path/to/task.yaml
python run_orchestrator.py dashboard
python run_orchestrator.py audit
python run_orchestrator.py system-test --iterations 1
```

For system re-validation after docs/template-only changes, use `audit`.

For system re-validation after orchestration, classifier, router, execution, retry, or collaboration-flow changes, use `system-test`.

## Audit Status

The current audit baseline is:

- happy path completes in one attempt
- retry scenario passes on retry
- hard-fail scenario exhausts retries and writes a handoff

This means the control plane is currently healthy for serial runs and review.

The current sandbox baseline also verifies:

- zero-build website task routes to `frontend` + `solo`
- improve website task routes to `frontend` + `solo`
- fix issue task fails once, retries once, then completes
- generated reports appear in `.hub/done/`, session reports, quick reports, and system test reports

## Known Limitations

- The executor is command-driven. Tasks still need `metadata.execution` to do useful work.
- Dashboard rendering is CLI-based; it reads `.hub/`, session reports, and system test reports, but there is not yet a polished web/TUI board.
- Dashboard snapshot writes use temp-file replace; this is safer for concurrent runs, but not a full cross-process lock.
- `manifest.yaml` still mixes runtime concerns and skill catalog concerns.

## Backlog

- `P2`: Split `manifest.yaml` into `runtime_manifest` and `skill_catalog` after a separate design review.
- `P3`: Clean up encoding in `_agent/workflows/report-writing.md`.

## Document Authority

Use one canonical source per concern:

| Concern | Source |
|---|---|
| Shared session process | [OPERATING_RULES.md](OPERATING_RULES.md) |
| New-session boot order | [ONBOARDING.md](ONBOARDING.md) |
| Role curriculum and skills | [ROLE_SKILL_MATRIX.md](ROLE_SKILL_MATRIX.md) |
| Copy-paste prompts | [PROMPT_PACK.md](PROMPT_PACK.md) |
| Product + CTO leadership flow | [CTO_PRODUCT_WORKFLOW.md](CTO_PRODUCT_WORKFLOW.md) |
| Current status and backlog | [STATUS.md](STATUS.md) |
| CEO/operator view | [DASHBOARD.md](DASHBOARD.md) and `python run_orchestrator.py dashboard` |
| System validation | [SYSTEM_AUDIT.md](SYSTEM_AUDIT.md) and `python run_orchestrator.py system-test --iterations 1` |

Do not add a new process file unless an existing canonical source cannot be extended safely.
