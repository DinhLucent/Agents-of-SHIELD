window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "handoff_note",
    title: "Viết Handoff Note (Bàn giao)",
    category: "Handoff",
    tags: ["handoff", "knowledge-transfer"],
    description: "Viết note bàn giao cực kỳ chuyên nghiệp cho đồng nghiệp.",
    use_when: ["Xong task", "Đi nghỉ phép", "Chuyển dự án"],
    fields: [
        { id: "work_done", label: "Việc đã xong", type: "textarea", required: true },
        { id: "pending", label: "Việc đang dở", type: "textarea" },
        { id: "risks", label: "Rủi ro cần chú ý", type: "text" }
    ],
    template: `<system_directive>
Tôi muốn viết handoff note cho người tiếp quản công việc này.
</system_directive>

<input_content>
<completed>
{{work_done}}
</completed>
<pending>
{{pending}}
</pending>
<risks>
{{risks}}
</risks>
</input_content>

<instructions>
Hãy viết cho tôi một bản handoff note chuyên nghiệp gồm:
1. Tóm tắt hiện trạng hệ thống.
2. Danh sách Checkpoint công việc.
3. Các file/module quan trọng cần lưu tâm.
4. Bước tiếp theo được khuyến nghị.
</instructions>`
});

window.promptRegistry.push({
    id: "handoff_task",
    title: "Viết Implementation Task",
    category: "Handoff",
    tags: ["delegation", "task-split", "agent-task"],
    description: "Chia nhỏ PRD thành các task code cụ thể.",
    use_when: ["Giao việc cho sub-agent", "Tạo Ticket Jira/Issue"],
    fields: [
        { id: "context", label: "Bối cảnh nhiệm vụ", type: "textarea", required: true },
        { id: "criteria", label: "Acceptance Criteria", type: "textarea", required: true }
    ],
    template: `<system_directive>
Tôi muốn biến vấn đề này thành một task rõ ràng để giao cho người khác (hoặc sub-agent).
</system_directive>

<input_content>
<problem_statement>
{{context}}
</problem_statement>
<acceptance_criteria>
{{criteria}}
</acceptance_criteria>
</input_content>

<instructions>
Hãy viết implementation task spec gồm:
1. Context & Problem Statement.
2. Goal & Scope.
3. Expected code changes.
4. Risks & Edge cases.
5. Suggested files to inspect.
</instructions>`
});
