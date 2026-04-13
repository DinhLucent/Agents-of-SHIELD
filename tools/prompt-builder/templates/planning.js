window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "planning_improve_repo",
    title: "Improve Existing Repo",
    category: "Planning",
    tags: ["cto", "improve", "roadmap", "strategy"],
    description: "Build a deliberate improvement plan for an existing repository.",
    use_when: ["Inherited repo", "Want direction, not random cleanup", "Need phased technical improvement"],
    avoid_when: ["Only fixing one isolated bug"],
    fields: [
        { id: "repo_goal", label: "Repo / System Goal", type: "text", required: true, placeholder: "What this repo does" },
        { id: "repo_strengths", label: "Current strengths", type: "textarea", placeholder: "What is already working well" },
        { id: "repo_pains", label: "Pain points", type: "textarea", required: true, placeholder: "What feels slow, fragile, messy, or expensive" },
        { id: "repo_direction", label: "Desired direction", type: "text", required: true, placeholder: "Faster delivery / cleaner architecture / better onboarding / ..." },
        { id: "repo_constraints", label: "Constraints", type: "text", default: "No rewrite unless clearly justified" }
    ],
    template: `<system_directive>
I want a CTO-style improvement plan for this repository.
</system_directive>

<input_content>
- Repo or system: {{repo_goal}}
- Desired direction: {{repo_direction}}
- Constraints: {{repo_constraints}}
</input_content>

<strengths>
{{repo_strengths}}
</strengths>

<pain_points>
{{repo_pains}}
</pain_points>

<instructions>
Please:
1. Assess the current system honestly.
2. Separate core strengths from technical debt.
3. Identify the highest-leverage improvement areas.
4. Split the plan into quick wins, medium refactors, and major redesigns.
5. Tell me what should not be touched yet.
6. Give me a realistic execution order.
</instructions>`
});

window.promptRegistry.push({
    id: "planning_sprint",
    title: "Sprint Planning",
    category: "Planning",
    tags: ["sprint", "planning", "execution"],
    description: "Turn current priorities into a realistic sprint plan.",
    use_when: ["Sprint planning", "Need practical work breakdown", "Need sequencing and acceptance criteria"],
    avoid_when: ["Long-term architecture roadmap only"],
    fields: [
        { id: "sprint_length", label: "Sprint length", type: "text", required: true, placeholder: "1 week / 2 weeks / custom" },
        { id: "team_shape", label: "Team shape", type: "text", required: true, placeholder: "Backend + frontend + QA" },
        { id: "priorities", label: "Current priorities", type: "list", required: true, placeholder: "Type a priority and press Enter" },
        { id: "sprint_constraints", label: "Constraints", type: "text", default: "Keep tasks small and independently testable" }
    ],
    template: `<system_directive>
I want to turn current priorities into a realistic sprint plan.
</system_directive>

<input_content>
- Sprint length: {{sprint_length}}
- Team shape: {{team_shape}}
- Constraints: {{sprint_constraints}}
</input_content>

<priorities>
{{priorities}}
</priorities>

<instructions>
Please:
1. Group the work into a coherent sprint.
2. Separate must-do from nice-to-have.
3. Identify dependencies and sequencing.
4. Suggest task granularity that is easy to assign.
5. Add clear acceptance criteria for each work item.
6. Call out the main sprint risks.
</instructions>`
});

window.promptRegistry.push({
    id: "planning_adr",
    title: "Write ADR",
    category: "Planning",
    tags: ["adr", "decision", "architecture"],
    description: "Write an architecture decision record for a real technical choice.",
    use_when: ["Choosing between approaches", "Need a documented technical decision"],
    avoid_when: ["Already decided and no record is needed"],
    fields: [
        { id: "decision", label: "Decision", type: "text", required: true, placeholder: "What is being decided" },
        { id: "decision_context", label: "Context", type: "textarea", required: true, placeholder: "Current state and why this matters" },
        { id: "options", label: "Options considered", type: "list", required: true, placeholder: "Option A, Option B, ..." },
        { id: "decision_constraints", label: "Constraints", type: "text", default: "Optimize for long-term maintainability and safe rollout" }
    ],
    template: `<system_directive>
I want to write an ADR for this technical decision.
</system_directive>

<decision_context>
Decision Idea: {{decision}}
Context Detail: {{decision_context}}
</decision_context>

<options>
{{options}}
</options>

<constraints>
{{decision_constraints}}
</constraints>

<instructions>
Please write a professional ADR including:
1. Title
2. Status
3. Context
4. Decision
5. Alternatives considered
6. Consequences
7. Risks
8. Follow-up actions
</instructions>`
});

window.promptRegistry.push({
    id: "planning_build_from_zero",
    title: "Build From Zero",
    category: "Planning",
    tags: ["greenfield", "mvp", "architecture"],
    description: "Plan a new technical system from zero without overbuilding version 1.",
    use_when: ["New project", "Need MVP architecture", "Want phased implementation"],
    avoid_when: ["Existing repo with only small changes needed"],
    fields: [
        { id: "greenfield_goal", label: "What to build", type: "textarea", required: true, placeholder: "Describe the product or system" },
        { id: "greenfield_users", label: "Users", type: "text", required: true, placeholder: "Who it is for" },
        { id: "greenfield_constraints", label: "Constraints", type: "text", default: "Prefer simple MVP over broad platform scope" }
    ],
    template: `<system_directive>
I want to create a new technical system from zero.
</system_directive>

<input_content>
Goal: {{greenfield_goal}}
Users: {{greenfield_users}}
Constraints: {{greenfield_constraints}}
</input_content>

<instructions>
Please:
1. Clarify the core scope.
2. Separate MVP from later expansion.
3. Propose the simplest credible architecture.
4. Suggest module boundaries and contracts.
5. Give me a phased implementation plan.
6. Tell me the biggest mistakes to avoid in version 1.
</instructions>`
});
