window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "debug_runtime",
    title: "Debug lỗi Runtime",
    category: "Debug",
    tags: ["bug", "crash", "runtime", "stack-trace"],
    description: "Dùng để fix lỗi crash, exception hoặc hành vi sai khi chạy.",
    use_when: ["Có stack trace", "Có hiện tượng tái hiện được"],
    avoid_when: ["Lỗi compile", "Chưa rõ kiến trúc"],
    fields: [
        { id: "symptom", label: "Hiện tượng (Symptom)", type: "textarea", required: true },
        { id: "expected", label: "Hành vi đúng (Expected)", type: "text", required: true },
        { id: "repro", label: "Cách tái hiện", type: "textarea" },
        { id: "log", label: "Log / Stack Trace", type: "textarea" },
        { id: "area", label: "Vùng nghi ngờ", type: "text" },
        { id: "strategy", label: "Chiến thuật fix", type: "select", options: ["Patch nhỏ (ưu tiên)", "Refactor & Fix", "Rewrite đoạn lỗi"], default: "Patch nhỏ (ưu tiên)" }
    ],
    template: `<system_directive>
Tôi muốn debug một lỗi runtime cụ thể.
</system_directive>

<context>
- Hiện tượng: {{symptom}}
- Hành vi kỳ vọng: {{expected}}
- Phạm vi nghi ngờ: {{area}}
- Chiến thuật ưu tiên: {{strategy}}
</context>

<input_content>
<reproduction>
{{repro}}
</reproduction>
<logs>
{{log}}
</logs>
</input_content>

<instructions>
1. Xác định luồng code liên quan trực tiếp.
2. Nêu 3-5 giả thuyết lỗi theo xác suất.
3. Chỉ ra file/function cần đọc trước.
4. Đề xuất patch nhỏ nhất hợp lý.
5. Nêu rủi ro regression và test cần thêm.
</instructions>`
});

window.promptRegistry.push({
    id: "debug_flaky",
    title: "Xử lý Flaky Test",
    category: "Debug",
    tags: ["testing", "flaky", "nondeterminism"],
    description: "Điều tra test thỉnh thoảng fail mà không rõ nguyên nhân.",
    use_when: ["Test fail ngẫu nhiên", "Fail trên CI nhưng pass local"],
    avoid_when: ["Fail 100% (đó là bug thật)"],
    fields: [
        { id: "test_name", label: "Tên Test", type: "text", required: true },
        { id: "fail_rate", label: "Tần suất fail", type: "text", default: "2/10 lần" },
        { id: "fail_type", label: "Dấu hiệu", type: "select", options: ["Timeout", "Race Condition", "Data Dependency", "Randomness"], required: true }
    ],
    template: `<system_directive>
Tôi muốn điều tra flaky test {{test_name}}.
</system_directive>

<context>
- Tần suất fail: {{fail_rate}}
- Dấu hiệu: {{fail_type}}
</context>

<instructions>
1. Nêu các nguyên nhân flaky có khả năng nhất cho case này.
2. Tìm điểm nondeterminism trong code/test.
3. Chỉ ra chỗ đang phụ thuộc time / order / shared state / network.
4. Đề xuất cách sửa để test ổn định.
5. Đề xuất cách tái hiện flaky (nếu có).
</instructions>`
});
