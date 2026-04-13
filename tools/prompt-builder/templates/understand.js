window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "understand_architecture",
    title: "Vẽ bản đồ kiến trúc",
    category: "Understand",
    tags: ["architecture", "mapping", "mental-model"],
    description: "Xác định các module lõi, entrypoints và luồng dữ liệu của hệ thống.",
    use_when: ["Muốn hiểu framework đang dùng", "Cần vẽ diagram", "Xác định core vs glue code"],
    avoid_when: ["Đã hiểu rõ hệ thống", "Sửa bug nhỏ"],
    fields: [
        { id: "system_context", label: "Hệ thống / Repo", type: "text", required: true, placeholder: "Tên repo hoặc domain công việc" },
        { id: "core_goal", label: "Mục tiêu cốt lõi", type: "text", required: true, placeholder: "Hệ thống này dùng để làm gì?" },
        { id: "current_confusion", label: "Phần đang gây rối nhất", type: "textarea", placeholder: "Ví dụ: Phần state machine của orchestrator" },
        { id: "constraints", label: "Giới hạn (Constraints)", type: "text", default: "Giữ nguyên kiến trúc hiện tại" }
    ],
    template: `<system_directive>
Tôi muốn lập bản đồ kiến trúc hiện tại của repo này.
</system_directive>

<system_context>
- Dự án: {{system_context}}
- Mục tiêu: {{core_goal}}
- Giới hạn: {{constraints}}
- Phần gây rối: {{current_confusion}}
</system_context>

<instructions>
Hãy làm theo thứ tự:
1. Xác định entrypoints chính.
2. Xác định các module lõi.
3. Vẽ luồng dữ liệu và luồng control flow.
4. Chỉ ra state machine / orchestrator / adapters nằm ở đâu.
5. Nêu module nào đóng vai trò "core kernel".
6. Nêu module nào chỉ là glue code.

<expected_output>
- Kiến trúc theo từng khối chức năng.
- Trách nhiệm của từng khối.
- File/Function chính cho mỗi khối.
</expected_output>
</instructions>`
});

window.promptRegistry.push({
    id: "understand_onboarding",
    title: "Onboarding Thực Chiến",
    category: "Understand",
    tags: ["newcomer", "onboarding", "quick-start"],
    description: "Dùng cho người mới tham gia dự án cần nắm bắt logic nhanh nhất.",
    use_when: ["Bắt đầu task đầu tiên", "Cần biết file nào quan trọng"],
    avoid_when: ["Chỉ ghé ngang qua sửa typo"],
    fields: [
        { id: "system_context", label: "Tên Repo", type: "text", required: true },
        { id: "feature_focus", label: "Feature tôi sắp làm", type: "text" }
    ],
    template: `<system_directive>
Tôi sắp tham gia tiếp tục phát triển repo {{system_context}}.
Hãy giúp tôi onboarding kỹ thuật theo hướng thực chiến.
</system_directive>

<context>
- Feature focus: {{feature_focus}}
</context>

<instructions>
Việc cần làm:
1. Repo này giải bài toán cốt lõi gì?
2. Entry points chính nằm ở đâu?
3. Luồng chạy end-to-end đi qua những file nào?
4. Module nào là lõi, module nào là phụ trợ?
5. Nếu tôi muốn sửa feature {{feature_focus}}, tôi nên đọc file nào trước?
6. Nếu tôi muốn debug issue production, tôi nên bắt đầu từ đâu?

<expected_output_format>
- Một bản mental model ngắn gọn của hệ thống.
- Danh sách file quan trọng nhất.
- Thứ tự đọc code đề xuất cho người mới.
</expected_output_format>
</instructions>`
});
