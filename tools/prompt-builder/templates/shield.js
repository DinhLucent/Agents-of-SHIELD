window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "shield_session_boot",
    title: "SHIELD Session Boot",
    category: "SHIELD",
    tags: ["role", "onboarding", "session"],
    description: "Start a new session with a clear SHIELD role, scenario, and output contract.",
    use_when: ["Opening any role session", "Switching from chat to SHIELD workflow"],
    avoid_when: ["You already have a fully scoped task packet"],
    fields: [
        { id: "role", label: "Role", type: "text", required: true, placeholder: "product-manager-agent / cto-agent / backend-agent / qa-lead-agent" },
        { id: "scenario", label: "Scenario", type: "text", required: true, placeholder: "zero build / improve repo / solve issue / assigned task" },
        { id: "task_or_intent", label: "Task or intent", type: "textarea", required: true, placeholder: "Paste the task or raw intent" },
        { id: "constraints", label: "Constraints", type: "textarea", placeholder: "No rewrite, keep compatibility, small patch, etc." }
    ],
    template: `<system_directive>
Onboard into this repo as {{role}}.
</system_directive>

<shield_boot_order>
1. Read ONBOARDING.md.
2. Read DASHBOARD.md.
3. Read OPERATING_RULES.md.
4. Read CTO_PRODUCT_WORKFLOW.md only if this is Product/CTO leadership work or scope is unclear.
5. Check manifest.yaml for my role/persona/skills.
6. Read ROLE_SKILL_MATRIX.md.
7. Load only skills needed for this task.
</shield_boot_order>

<input_content>
Scenario: {{scenario}}
<task_intent>
{{task_or_intent}}
</task_intent>
<constraints>
{{constraints}}
</constraints>
</input_content>

<instructions>
Rules:
- If this is raw user intent, Product/CTO must create a leadership brief before worker execution.
- If this is an assigned worker task, stay inside the assigned role.
- Run the role gate before work: if my role does not match task.assigned_role, do not execute; hand off to the correct role.
- Check latest relevant session report/handoff before editing.
- Read the required template before writing a report, handoff, brief, task, or decision log.
- End with a complete session report or handoff including role_gate, context_check, verification, handoff_needed, next_owner_role, and next_step.
</instructions>`
});

window.promptRegistry.push({
    id: "shield_zero_build",
    title: "Zero Build Leadership",
    category: "SHIELD",
    tags: ["zero-build", "product", "cto"],
    description: "Create the first leadership brief, architecture slice, and role tasks for a new system.",
    use_when: ["Starting from an idea", "Creating a new product from scratch"],
    avoid_when: ["A scoped task already exists for a worker"],
    fields: [
        { id: "idea", label: "Product idea", type: "textarea", required: true, placeholder: "What do you want to build?" },
        { id: "constraints", label: "Constraints", type: "textarea", placeholder: "Stack, deadline, budget, compliance, deployment, etc." }
    ],
    template: `<system_directive>
Onboard as product-manager-agent first, then involve cto-agent for technical decomposition.
</system_directive>

<input_content>
Scenario: zero build
<product_idea>
{{idea}}
</product_idea>
<constraints>
{{constraints}}
</constraints>
</input_content>

<instructions>
Please:
1. Create a leadership brief using templates/leadership_brief.json as the shape.
2. Define problem, user value, scope now, out of scope, and acceptance summary.
3. Ask only the questions needed to reduce major risk.
4. Let CTO propose the simplest shippable architecture and first vertical slice.
5. Produce 3-7 role-assigned tasks for the first sprint.

<restriction>
Do not assign worker implementation until the leadership brief and scope are clear.
</restriction>

<shield_guard>
SESSION CLOSE CONTRACT:
- Run role gate: confirm this is Product/CTO leadership work. If not, hand off.
- Check latest session reports and handoffs before making decisions.
- Do not produce output without clear scope and acceptance criteria.
- End with a complete session report using templates/session_report.json (all required fields: role_gate, context_check, verification, handoff_needed, next_owner_role, artifacts, report_completeness).
- If another role must continue, also produce a handoff using templates/handoff.json (handoff_gate, evidence, from_role, to_role required).
</shield_guard>
</instructions>`
});

window.promptRegistry.push({
    id: "shield_zero_build_behavior_test",
    title: "Zero Build Behavior Test",
    category: "SHIELD",
    tags: ["zero-build", "test", "cto", "process"],
    description: "Test whether CTO/Product follow the zero-build workflow instead of jumping into implementation.",
    use_when: ["Auditing zero-build behavior", "Testing process discipline before worker sessions"],
    avoid_when: ["A worker task is already assigned and accepted"],
    fields: [
        { id: "raw_intent", label: "Raw product intent", type: "textarea", required: true, placeholder: "Paste a vague product idea with no product brief" },
        { id: "product_output", label: "Product output", type: "textarea", placeholder: "Paste product brief or path, if available" },
        { id: "cto_output", label: "CTO output", type: "textarea", placeholder: "Paste CTO output or path, if available" }
    ],
    template: `<system_directive>
Onboard as lead-programmer-agent for process audit.
</system_directive>

<input_content>
Scenario: zero build behavior audit
<evidence>
<raw_intent>{{raw_intent}}</raw_intent>
<product_output>{{product_output}}</product_output>
<cto_output>{{cto_output}}</cto_output>
</evidence>
</input_content>

<audit_criteria>
- Product runs before CTO unless a valid leadership brief already exists.
- CTO does not start implementation.
- CTO does not create worker tasks from vague raw intent.
- CTO asks for Product clarification or uses templates/leadership_brief.json as the required shape.
- Worker sessions are not opened until tasks have role, scope, and acceptance criteria.
</audit_criteria>

<instructions>
Please evaluate:
1. Did Product run before CTO, or did CTO correctly stop when no product brief existed?
2. Did Product use templates/leadership_brief.json?
3. Did CTO avoid implementation and stay at architecture/task-decomposition level?
4. Did every proposed task have owner role and acceptance criteria?
5. Did any session skip OPERATING_RULES.md, ROLE_SKILL_MATRIX.md, or the required template?

<verdict_options>
- PASS: behavior is aligned
- PASS WITH SMELL: usable but needs tightening
- FAIL: process violation, do not continue to worker sessions.
</verdict_options>
</instructions>`
});

window.promptRegistry.push({
    id: "shield_improve_repo",
    title: "Improve Existing Repo",
    category: "SHIELD",
    tags: ["improve", "repo", "leadership"],
    description: "Use Product + CTO to turn a repo improvement goal into scoped worker tasks.",
    use_when: ["Cloned repo improvement", "Feature enhancement", "Refactor planning"],
    avoid_when: ["Small isolated bug with an already known owner"],
    fields: [
        { id: "repo", label: "Repo", type: "text", required: true, placeholder: "Repo name or path" },
        { id: "intent", label: "Improvement intent", type: "textarea", required: true, placeholder: "What do you want to improve?" },
        { id: "constraints", label: "Constraints", type: "textarea", placeholder: "No rewrite, compatibility, test constraints, etc." }
    ],
    template: `<system_directive>
Onboard as product-manager-agent, then involve cto-agent if architecture impact exists.
</system_directive>

<input_content>
Scenario: improve existing repo
- Repo: {{repo}}
- Intent: {{intent}}
- Constraints: {{constraints}}
</input_content>

<instructions>
Please:
1. Read the repo lightly: README, configs, docs, entrypoints.
2. Define improvement value, scope now, out of scope, and acceptance summary.
3. Identify architecture impact and whether CTO/ADR is needed.
4. Create a leadership brief.
5. Propose small role-assigned tasks with related files and verification ideas.

<restriction>
Do not ask worker sessions to code until tasks are explicit.
</restriction>

<shield_guard>
SESSION CLOSE CONTRACT:
- Run role gate: confirm this is Product/CTO leadership work.
- Check latest session reports and handoffs for prior context.
- End with a complete session report using templates/session_report.json (all required fields).
- If another role must continue, also produce a handoff using templates/handoff.json.
</shield_guard>
</instructions>`
});

window.promptRegistry.push({
    id: "shield_solve_issue",
    title: "Solve Issue Flow",
    category: "SHIELD",
    tags: ["issue", "bug", "triage"],
    description: "Triage an issue into a focused task, then route to the right worker and QA.",
    use_when: ["Bug report", "Failing test", "Runtime issue", "Production issue"],
    avoid_when: ["Pure product ideation without a symptom"],
    fields: [
        { id: "symptom", label: "Symptom", type: "textarea", required: true, placeholder: "What is wrong?" },
        { id: "expected", label: "Expected behavior", type: "textarea", placeholder: "What should happen?" },
        { id: "evidence", label: "Logs or reproduction", type: "textarea", placeholder: "Steps, logs, stack trace, failing test" }
    ],
    template: `<system_directive>
Onboard as qa-lead-agent or product-manager-agent for impact triage.
Escalate to cto-agent if the system boundary or architecture impact is unclear.
</system_directive>

<input_content>
Scenario: solve issue
- Symptom: {{symptom}}
- Expected behavior: {{expected}}
<evidence>
{{evidence}}
</evidence>
</input_content>

<instructions>
Please:
1. Classify severity and likely owning role.
2. Identify what evidence the fixer must preserve.
3. Create the smallest focused fix task with acceptance criteria.
4. Recommend backend/frontend/fullstack/QA owner.
5. Define the verification path for QA.

<restriction>
Do not broaden into redesign unless the issue requires it.
</restriction>

<shield_guard>
SESSION CLOSE CONTRACT:
- Run role gate: confirm this is triage/ownership work.
- Check latest session reports, handoffs, and evidence before triaging.
- End with a complete session report using templates/session_report.json (all required fields).
- If another role must continue, also produce a handoff using templates/handoff.json.
</shield_guard>
</instructions>`
});

window.promptRegistry.push({
    id: "shield_ceo_dashboard",
    title: "CEO Dashboard Review",
    category: "SHIELD",
    tags: ["dashboard", "ceo", "progress", "status"],
    description: "Review overall project progress from the CEO/leadership perspective using dashboard, reports, and handoffs.",
    use_when: ["Checking project progress", "Sprint review", "Decision checkpoint", "Stakeholder update"],
    avoid_when: ["Worker implementation", "Debugging a specific issue"],
    fields: [
        { id: "focus", label: "Review focus", type: "text", placeholder: "Overall progress / blockers / next decisions / sprint status" },
        { id: "timeframe", label: "Timeframe", type: "text", placeholder: "Last sprint / last 24h / since milestone X" }
    ],
    template: `<system_directive>
Onboard as product-manager-agent or cto-agent for progress review.
</system_directive>

<input_content>
- Review focus: {{focus}}
- Timeframe: {{timeframe}}
</input_content>

<instructions>
Please review the current project status:
1. Read DASHBOARD.md for the latest snapshot.
2. List all completed tasks from .hub/done/.
3. List all pending handoffs from .hub/handoffs/.
4. Read the latest session reports from runtime/reports/session_reports/.
5. Identify current blockers and unresolved open questions.
6. Summarize overall progress as a percentage or milestone.
7. List the top 3 decisions needed from leadership right now.
8. Recommend the next 3 highest-priority actions.

<output_format>
Return a structured progress summary:
- Overall status: on track / at risk / blocked
- Completed since last review: [list]
- Active blockers: [list]
- Pending handoffs: [list]
- Decisions needed: [list]
- Recommended next actions: [list]
</output_format>

End with a session report using templates/session_report.json.
</instructions>`
});

window.promptRegistry.push({
    id: "shield_short_prompt_adapter",
    title: "Short Prompt Adapter",
    category: "SHIELD",
    tags: ["adapter", "normalizer", "intake", "short-prompt"],
    description: "Turn a short, informal prompt into a full SHIELD-safe session prompt with scenario, role, scope, and guards.",
    use_when: ["Short informal prompt", "Quick task description", "Lazy one-liner", "Unclear intent that needs structure"],
    avoid_when: ["You already have a fully scoped SHIELD prompt"],
    fields: [
        { id: "raw_prompt", label: "Raw prompt", type: "textarea", required: true, placeholder: "Paste the short user prompt (e.g. 'sửa login', 'thêm component X', 'commit push')" },
        { id: "repo_context", label: "Repo context", type: "text", placeholder: "Repo name or path (or 'unknown')" },
        { id: "current_state", label: "Current state", type: "textarea", placeholder: "What exists now? Recent changes? (or 'unknown')" }
    ],
    template: `<system_directive>
You are a SHIELD Prompt Normalizer.
Do not execute the task. Only classify and normalize the prompt.
</system_directive>

<input_content>
<raw_prompt>{{raw_prompt}}</raw_prompt>
<repo_context>{{repo_context}}</repo_context>
<current_state>{{current_state}}</current_state>
</input_content>

<instructions>
Process:

1. Classify the scenario:
   - zero build: nothing exists yet, building from scratch
   - improve repo: repo exists, improving or extending it
   - solve issue: bug, failing test, production issue, broken behavior
   - assigned task: a scoped task already exists with role and criteria
   - review: code review, security audit, QA verification
   - git: commit, push, branch, merge, tag, release

2. Recommend the starting role:
   - zero build → product-manager-agent (then cto-agent)
   - improve repo → product-manager-agent (or cto-agent if architecture impact)
   - solve issue → qa-lead-agent or product-manager-agent for triage
   - assigned task → the role in task.assigned_role
   - review → lead-programmer-agent or security-agent
   - git → the current worker role (no leadership needed)

3. Determine whether to execute now or stop:
   - Execute now: scope is clear, no dangerous gaps
   - Stop and ask: prompt touches auth, payment, data deletion, production deploy, security, compliance, or user data migration

4. Fill safe assumptions for non-critical gaps:
   - No constraints → "smallest safe change, no breaking API changes"
   - No acceptance criteria → derive from the goal
   - No related files → "unknown, agent should discover"
   - No verification path → "run relevant checks if available"

5. STOP and list blocking questions if the prompt mentions:
   - auth, login, tokens, passwords, sessions
   - payment, billing, subscription, money
   - delete, drop, truncate, data loss
   - production, deploy, release, rollback
   - security, secrets, keys, credentials
   - compliance, GDPR, HIPAA, PCI

<output_shape>
Output the normalized prompt in this EXACT shape:

Normalized SHIELD Prompt
- Scenario: [zero build / improve repo / solve issue / assigned task / review / git]
- Recommended starting role: [agent id]
- Should execute now: [yes / no — stop and ask if dangerous gap]
- Goal: [what to achieve]
- Scope: [what is in scope / out of scope]
- Constraints: [constraints or safe default]
- Related files: [paths or "unknown — agent should discover"]
- Acceptance criteria: [criteria or derived from goal]
- Verification path: [how to verify or "run relevant checks if available"]
- Required report/handoff: [session report using templates/session_report.json; handoff using templates/handoff.json if needed]
- Assumptions: [list all assumptions made for gaps]
- Blocking questions: [questions that must be answered before execution, or "none"]
- Next prompt to paste: [the full SHIELD session boot prompt for the recommended role, ready to copy-paste]
</output_shape>

<restriction>
Do not execute the task. Only normalize and classify.
The "Next prompt to paste" must include SHIELD boot order, role gate, context check, and session report/handoff contract.
</restriction>
</instructions>`
});
