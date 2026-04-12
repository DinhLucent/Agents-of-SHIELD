---
description: Plan the next sprint — define tasks, assign roles, and set acceptance criteria.
---

# Sprint Planning Workflow (V2)

> Under V2, tasks are defined as `task.yaml` files and processed by the orchestrator.
> The legacy `.hub/backlog.yaml` is no longer used.

1. Review current project state via `DASHBOARD.md` and recent `runtime/` reports.
2. Identify the next set of work items based on project goals.
3. For each task, create a `task.yaml` following the schema at `templates/task.yaml`:
   - `assigned_role`: Must match a role defined in `manifest.yaml`
   - `status`: `queued` for new tasks
   - `acceptance_criteria`: Specific, verifiable conditions
   - `inputs.related_paths`: Files the task will likely touch
4. Group tasks into logical sprints (5-10 tasks per sprint).
5. Present the plan to the user for approval before persisting.
6. Run tasks via: `python run_orchestrator.py run <task.yaml>`
