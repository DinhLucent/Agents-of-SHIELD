window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "role_backend",
    title: "Backend Session",
    category: "Role",
    tags: ["backend", "api", "service"],
    description: "Use a backend-focused session shape for server-side work.",
    use_when: ["API work", "Validation", "Jobs", "Auth", "Data access"],
    avoid_when: ["Pure UI styling"],
    fields: [
        { id: "backend_feature", label: "Feature or issue", type: "textarea", required: true, placeholder: "Describe the backend task" },
        { id: "backend_area", label: "Backend area", type: "text", required: true, placeholder: "API / auth / jobs / integration / data model" },
        { id: "backend_constraints", label: "Constraints", type: "text", default: "No breaking API changes unless explicitly required" },
        { id: "extra_content", label: "Extra Context / Logs / Code", type: "textarea", placeholder: "Paste relevant snippets, logs, or error traces here (Optional)" }
    ],
    template: `<system_directive>
Onboard as backend-agent.
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
Read CTO_PRODUCT_WORKFLOW.md only if scope or ownership is unclear.
Confirm this task is assigned to backend or has Product/CTO approval for backend ownership.
</system_directive>

<context>
- Backend area: {{backend_area}}
- Constraints: {{backend_constraints}}
</context>

<task_specification>
{{backend_feature}}
</task_specification>

<input_content>
{{extra_content}}
</input_content>

<instructions>
Please:
1. Run role gate: if this task is not assigned to backend, do not execute; hand off to the correct role.
2. Check the latest relevant session report/handoff before editing.
3. Identify the backend code path involved.
4. Find the right service, handler, and validation boundaries.
5. Implement or propose the smallest clean change.
6. Add or suggest the right tests.
7. Call out rollout or migration risks.
8. Read the required report/handoff template before writing the output.
9. End with a complete SHIELD session report or handoff including role_gate, context_check, verification, handoff_needed, next_owner_role, and next_step.
</instructions>`
});

window.promptRegistry.push({
    id: "role_frontend",
    title: "Frontend Session",
    category: "Role",
    tags: ["frontend", "ui", "ux"],
    description: "Use a frontend-focused session shape for UI and interaction work.",
    use_when: ["UI features", "Component work", "Page redesign", "Forms"],
    avoid_when: ["Database or backend-only work"],
    fields: [
        { id: "frontend_feature", label: "Feature or issue", type: "textarea", required: true, placeholder: "Describe the UI task" },
        { id: "frontend_area", label: "UI area", type: "text", required: true, placeholder: "Page / component / form / state / performance" },
        { id: "frontend_constraints", label: "Constraints", type: "text", default: "Match existing UI language and keep it accessible" }
    ],
    template: `<system_directive>
Onboard as frontend-agent.
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
Read CTO_PRODUCT_WORKFLOW.md only if scope or ownership is unclear.
Confirm this task is assigned to frontend or has Product/CTO approval for frontend ownership.
</system_directive>

<context>
- UI area: {{frontend_area}}
- Constraints: {{frontend_constraints}}
</context>

<task_specification>
{{frontend_feature}}
</task_specification>

<instructions>
Please:
1. Run role gate: if this task is not assigned to frontend, do not execute; hand off to the correct role.
2. Check the latest relevant session report/handoff before editing.
3. Find the best existing UI pattern in the repo.
4. Keep the UI consistent with the current visual language.
5. Implement or propose the smallest clean change.
6. Handle loading, empty, and error states.
7. Suggest visual or interaction risks to watch for.
8. Read the required report/handoff template before writing the output.
9. End with a complete SHIELD session report or handoff including role_gate, context_check, verification, handoff_needed, next_owner_role, and next_step.
</instructions>`
});

window.promptRegistry.push({
    id: "role_fullstack",
    title: "Fullstack Session",
    category: "Role",
    tags: ["fullstack", "e2e", "integration"],
    description: "Use a fullstack session shape for changes that cross frontend and backend.",
    use_when: ["End-to-end feature work", "Cross-layer bugfixes"],
    avoid_when: ["Only one layer is involved"],
    fields: [
        { id: "fullstack_feature", label: "Feature or issue", type: "textarea", required: true, placeholder: "Describe the end-to-end change" },
        { id: "fullstack_frontend", label: "Frontend surface", type: "text", placeholder: "Which page, component, route" },
        { id: "fullstack_backend", label: "Backend surface", type: "text", placeholder: "Which API, service, model" },
        { id: "fullstack_constraints", label: "Constraints", type: "text", default: "Prefer the smallest end-to-end slice that proves value" }
    ],
    template: `<system_directive>
Onboard as fullstack-agent.
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
Read CTO_PRODUCT_WORKFLOW.md only if scope or ownership is unclear.
Confirm this task is assigned to fullstack or has Product/CTO approval for fullstack ownership.
</system_directive>

<context>
- Frontend surface: {{fullstack_frontend}}
- Backend surface: {{fullstack_backend}}
- Constraints: {{fullstack_constraints}}
</context>

<task_specification>
{{fullstack_feature}}
</task_specification>

<instructions>
Please:
1. Run role gate: if this task is not assigned to fullstack, do not execute; hand off to the correct role.
2. Check the latest relevant session report/handoff before editing.
3. Trace the end-to-end flow.
4. Split responsibilities cleanly between frontend and backend.
5. Avoid unnecessary coupling.
6. Implement or propose the smallest end-to-end slice that proves the feature.
7. Suggest the test plan across both layers.
8. Read the required report/handoff template before writing the output.
9. End with a complete SHIELD session report or handoff including role_gate, context_check, verification, handoff_needed, next_owner_role, and next_step.
</instructions>`
});

window.promptRegistry.push({
    id: "role_qa",
    title: "QA Session",
    category: "Role",
    tags: ["qa", "testing", "risk"],
    description: "Use a QA-focused session shape for risk-based testing and release checks.",
    use_when: ["Release checks", "Regression planning", "High-risk features"],
    avoid_when: ["Pure architecture design"],
    fields: [
        { id: "qa_feature", label: "Feature or issue", type: "textarea", required: true, placeholder: "Describe the feature or change under test" },
        { id: "qa_risks", label: "Risk areas", type: "list", placeholder: "Enter one risk area at a time" },
        { id: "qa_constraints", label: "Constraints", type: "text", default: "Prioritize the smallest useful test matrix" }
    ],
    template: `<system_directive>
Onboard as qa-lead-agent.
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
Read CTO_PRODUCT_WORKFLOW.md only if scope or ownership is unclear.
Confirm this task is ready for QA or has Product/CTO approval for QA triage.
</system_directive>

<context>
- Feature or issue: {{qa_feature}}
- Constraints: {{qa_constraints}}
</context>

<risk_areas>
{{qa_risks}}
</risk_areas>

<instructions>
Please:
1. Run role gate: if this task is not assigned to QA/reviewer verification, do not execute; hand off to the correct role.
2. Check the latest relevant session report/handoff before reviewing.
3. Identify the highest-risk behaviors.
4. Suggest the minimum useful test matrix.
5. Separate smoke, regression, and edge-case coverage.
6. Call out likely flaky areas.
7. Tell me what should be manually verified before release.
8. Read the verification/session-report template before writing the output.
9. End with a complete session report using templates/session_report.json (all required fields: role_gate, context_check, verification, handoff_needed, next_owner_role, artifacts, report_completeness).
10. If the task needs another role, also produce a handoff using templates/handoff.json.
</instructions>`
});

window.promptRegistry.push({
    id: "role_product",
    title: "Product Manager Session",
    category: "Role",
    tags: ["product", "leadership", "scope"],
    description: "Use a Product-focused session shape for scoping, briefs, and task creation.",
    use_when: ["Raw user intent", "Scope definition", "Leadership brief creation", "Task proposal"],
    avoid_when: ["Worker implementation", "Architecture design"],
    fields: [
        { id: "product_intent", label: "Intent or goal", type: "textarea", required: true, placeholder: "What needs to be scoped or decided?" },
        { id: "product_scenario", label: "Scenario", type: "text", required: true, placeholder: "zero build / improve repo / solve issue" },
        { id: "product_constraints", label: "Constraints", type: "textarea", placeholder: "Timeline, budget, non-goals, compliance" }
    ],
    template: `<system_directive>
Onboard as product-manager-agent.
Read ONBOARDING.md, DASHBOARD.md, CTO_PRODUCT_WORKFLOW.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
</system_directive>

<context>
- Scenario: {{product_scenario}}
- Constraints: {{product_constraints}}
</context>

<task_specification>
{{product_intent}}
</task_specification>

<instructions>
Please:
1. Run role gate: confirm this is leadership/scoping work. Do not execute worker implementation.
2. Check latest session reports, handoffs, and briefs for prior context.
3. Define the problem, user value, scope, and acceptance summary.
4. Create a leadership brief using templates/leadership_brief.json.
5. Propose scoped tasks with role assignments and acceptance criteria.
6. List open questions and non-goals.
7. End with a complete session report using templates/session_report.json (all required fields: role_gate, context_check, verification, handoff_needed, next_owner_role, artifacts, report_completeness).
8. If CTO decomposition is needed, produce a handoff using templates/handoff.json.
</instructions>`
});

window.promptRegistry.push({
    id: "role_cto",
    title: "CTO Session",
    category: "Role",
    tags: ["cto", "architecture", "decomposition"],
    description: "Use a CTO-focused session shape for architecture, ADR, and task decomposition.",
    use_when: ["Architecture decisions", "ADR creation", "Task decomposition from briefs", "Technical risk review"],
    avoid_when: ["Worker implementation", "Pure product scoping without a brief"],
    fields: [
        { id: "cto_brief", label: "Product brief or input", type: "textarea", required: true, placeholder: "Paste the product brief or technical input" },
        { id: "cto_decision", label: "Decision needed", type: "text", required: true, placeholder: "architecture / ADR / task decomposition / risk review" },
        { id: "cto_constraints", label: "Technical constraints", type: "textarea", placeholder: "Stack, deadline, compliance, deployment target" }
    ],
    template: `<system_directive>
Onboard as cto-agent.
Read ONBOARDING.md, DASHBOARD.md, CTO_PRODUCT_WORKFLOW.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
</system_directive>

<context>
- Decision needed: {{cto_decision}}
- Constraints: {{cto_constraints}}
</context>

<task_specification>
{{cto_brief}}
</task_specification>

<instructions>
Please:
1. Run role gate: confirm this is architecture/decomposition work. Do not perform worker implementation.
2. Check latest session reports, handoffs, and briefs for prior context.
3. Verify a valid product brief or leadership brief exists. If not, hand off to Product.
4. Propose the simplest shippable architecture.
5. Decide whether an ADR is required and create it if so.
6. Split work into small role-assigned tasks with acceptance criteria.
7. Identify risks and module boundaries.
8. End with a complete session report using templates/session_report.json (all required fields).
9. If worker roles must continue, produce a handoff using templates/handoff.json.
</instructions>`
});

window.promptRegistry.push({
    id: "role_reviewer_security",
    title: "Reviewer / Security Session",
    category: "Role",
    tags: ["review", "security", "audit"],
    description: "Use a review-focused session shape for code review, security audit, or architecture review.",
    use_when: ["Code review", "Security review", "Architecture review", "Pre-release audit"],
    avoid_when: ["Worker implementation", "Scoping work"],
    fields: [
        { id: "review_task", label: "Task under review", type: "textarea", required: true, placeholder: "Paste the task or describe what to review" },
        { id: "review_report", label: "Worker report", type: "textarea", placeholder: "Paste the worker session report or path" },
        { id: "review_files", label: "Changed files", type: "textarea", placeholder: "List of changed files" },
        { id: "review_focus", label: "Review focus", type: "text", default: "correctness / maintainability / security / all" }
    ],
    template: `<system_directive>
Onboard as lead-programmer-agent or security-agent.
Read ONBOARDING.md, DASHBOARD.md, OPERATING_RULES.md, manifest.yaml, and ROLE_SKILL_MATRIX.md first.
Read CTO_PRODUCT_WORKFLOW.md only if scope or ownership is unclear.
</system_directive>

<context>
- Review focus: {{review_focus}}
</context>

<task_specification>
{{review_task}}
</task_specification>

<worker_report>
{{review_report}}
</worker_report>

<changed_files>
{{review_files}}
</changed_files>

<instructions>
Please:
1. Run role gate: confirm this is review/security work. Do not implement fixes directly unless assigned.
2. Check latest session report/handoff from the preceding worker.
3. Review changed files for correctness, maintainability, regression, and security risk.
4. Return findings ordered by severity, then required fixes.
5. Determine whether QA can proceed or if retry/rework is needed.
6. End with a complete session report using templates/session_report.json (all required fields: role_gate, context_check, verification, handoff_needed, next_owner_role, artifacts, report_completeness).
7. If the worker must fix issues, produce a handoff using templates/handoff.json.
</instructions>`
});
