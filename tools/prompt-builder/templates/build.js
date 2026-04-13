window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "build_add_component",
    title: "Add UI Component",
    category: "Build",
    tags: ["ui", "component", "frontend"],
    description: "Add a new UI component that fits the current codebase and design system.",
    use_when: ["New component", "UI addition", "Need existing pattern match"],
    avoid_when: ["Pure architecture discussion"],
    fields: [
        { id: "component_stack", label: "Stack", type: "text", required: true, placeholder: "React / Vue / Next.js / plain HTML" },
        { id: "component_name", label: "Component name", type: "text", required: true, placeholder: "Component or feature name" },
        { id: "component_goal", label: "What it should do", type: "textarea", required: true, placeholder: "Describe behavior and purpose" },
        { id: "component_constraints", label: "Constraints", type: "text", default: "Match existing style and keep implementation minimal" }
    ],
    template: `<system_directive>
I want to add a new UI component.
</system_directive>

<context>
- Stack: {{component_stack}}
- Component: {{component_name}}
- Constraints: {{component_constraints}}
</context>

<goal>
{{component_goal}}
</goal>

<instructions>
1. Find the best existing pattern in the repo.
2. Tell me which files to inspect first.
3. Implement the smallest clean version that fits the current codebase.
4. Add or update tests if appropriate.
5. Explain any styling or state-management decisions briefly.

<shield_notice>
If this is a SHIELD-managed repo, wrap this prompt with SHIELD Session Boot first (role gate, context check, and session report/handoff at close).
</shield_notice>
</instructions>`
});

window.promptRegistry.push({
    id: "build_add_endpoint",
    title: "Add API Endpoint",
    category: "Build",
    tags: ["api", "backend", "endpoint"],
    description: "Add a new API endpoint in the current style of the repository.",
    use_when: ["New API route", "Need handler + validation + tests"],
    avoid_when: ["Only frontend work"],
    fields: [
        { id: "api_framework", label: "Framework", type: "text", required: true, placeholder: "FastAPI / Express / Django / Rails" },
        { id: "api_route", label: "Method and path", type: "text", required: true, placeholder: "POST /api/items" },
        { id: "api_input", label: "Input", type: "textarea", required: true, placeholder: "Body, params, auth, validation" },
        { id: "api_output", label: "Output", type: "textarea", required: true, placeholder: "Response shape" },
        { id: "api_constraints", label: "Constraints", type: "text", default: "No breaking changes and validate input" }
    ],
    template: `<system_directive>
I want to add a new API endpoint.
</system_directive>

<context>
- Framework: {{api_framework}}
- Endpoint: {{api_route}}
- Constraints: {{api_constraints}}
</context>

<input_specs>
{{api_input}}
</input_specs>

<output_specs>
{{api_output}}
</output_specs>

<instructions>
1. Find similar endpoints in the repo.
2. Identify the handler, service, and validation layers involved.
3. Implement the endpoint in the repo's existing style.
4. Add or update tests.
5. Call out migration, auth, or rollout concerns.

<shield_notice>
If this is a SHIELD-managed repo, wrap this prompt with SHIELD Session Boot first (role gate, context check, and session report/handoff at close).
</shield_notice>
</instructions>`
});

window.promptRegistry.push({
    id: "build_fix_issue",
    title: "Fix Issue",
    category: "Build",
    tags: ["bugfix", "issue", "patch"],
    description: "Fix a real issue quickly and correctly with a focused prompt.",
    use_when: ["Bug", "Regression", "Failing check", "Broken workflow"],
    avoid_when: ["Broad redesign or roadmap work"],
    fields: [
        { id: "issue_desc", label: "Issue", type: "textarea", required: true, placeholder: "Describe the real issue" },
        { id: "issue_impact", label: "Impact", type: "text", placeholder: "Who or what is affected" },
        { id: "issue_repro", label: "Reproduction", type: "textarea", placeholder: "How to reproduce" },
        { id: "issue_logs", label: "Logs or evidence", type: "textarea", placeholder: "Paste logs, traces, or observations" },
        { id: "issue_constraints", label: "Constraints", type: "text", default: "Prefer the smallest safe fix" }
    ],
    template: `<system_directive>
I want to fix a real issue quickly and correctly.
</system_directive>

<context>
- Issue: {{issue_desc}}
- Impact: {{issue_impact}}
- Constraints: {{issue_constraints}}
</context>

<input_content>
<reproduction>
{{issue_repro}}
</reproduction>
<logs>
{{issue_logs}}
</logs>
</input_content>

<instructions>
1. Trace the code path.
2. Give likely root causes in probability order.
3. Identify the smallest safe fix.
4. Tell me what test should lock the fix in.
5. Call out any rollback or deployment considerations.

<shield_notice>
If this is a SHIELD-managed repo, wrap this prompt with SHIELD Session Boot first (role gate, context check, and session report/handoff at close).
</shield_notice>
</instructions>`
});
