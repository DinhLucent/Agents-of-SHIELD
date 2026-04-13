window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "test_plan",
    title: "Lập Test Plan cho Bug Fix",
    category: "Test",
    tags: ["QA", "testing", "bug-fix"],
    description: "Thiết kế bộ test case bảo vệ code sau khi sửa bug.",
    use_when: ["Đã fix xong, muốn verifiy", "Trước khi viết test code"],
    fields: [
        { id: "bug_desc", label: "Mô tả bug", type: "textarea", required: true },
        { id: "behavior", label: "Hành vi đúng", type: "text" }
    ],
    template: `<system_directive>
Tôi muốn lập test plan để xác minh lỗi đã được fix triệt để.
</system_directive>

<input_content>
- Bug Description: {{bug_desc}}
- Expected Behavior: {{behavior}}
</input_content>

<instructions>
Hãy đề xuất test plan:
1. Test case nào tái hiện được bug cũ (Reproduce)?
2. Test case nào xác nhận behavior mới là đúng (Verification)?
3. Các case biên (Edge cases) cần lưu ý?
4. Nên viết unit, integration, hay e2e cho phần này?
5. Cần chuẩn bị test data tối thiểu như thế nào?
</instructions>`
});

window.promptRegistry.push({
    id: "test_coverage",
    title: "Đánh giá Coverage vùng sửa",
    category: "Test",
    tags: ["quality", "blind-spots"],
    description: "Kiểm tra xem vùng code quan trọng đã có đủ test chưa.",
    use_when: ["Refactor code cũ", "Viết code quan trọng"],
    fields: [
        { id: "file_path", label: "File/Module/Function", type: "text", required: true }
    ],
    template: `<system_directive>
Tôi muốn đánh giá coverage cho vùng code cụ thể.
</system_directive>

<input_content>
- Target: {{file_path}}
</input_content>

<instructions>
Hãy giúp tôi:
1. Xác định các behavior quan trọng nhất trong vùng này cần được bảo vệ.
2. Chỉ ra các case (luồng chạy) quan trọng mà có thể đang thiếu test.
3. Chỉ ra các case biên tiềm ẩn nguy cơ.
4. Đề xuất danh sách test ưu tiên cao nhất cần bổ sung.
</instructions>`
});
