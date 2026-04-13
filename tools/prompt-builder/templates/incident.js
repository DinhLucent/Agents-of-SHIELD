window.promptRegistry = window.promptRegistry || [];

window.promptRegistry.push({
    id: "incident_mgmt",
    title: "Xử lý Incident Production",
    category: "Incident",
    tags: ["incident", "hotfix", "ops"],
    description: "Dành cho xử lý sự cố đang xảy ra trên live.",
    use_when: ["Downtime", "Data corruption", "Lỗi diện rộng"],
    fields: [
        { id: "symptoms", label: "Triệu chứng", type: "textarea", required: true },
        { id: "impact", label: "Mức độ ảnh hưởng", type: "text", placeholder: "Số lượng user, task bị lỗi..." },
        { id: "recent_changes", label: "Thay đổi gần đây", type: "text", placeholder: "Deploy/Config change..." }
    ],
    template: `<system_directive>
Tôi đang xử lý một incident nghiêm trọng.
</system_directive>

<input_content>
- Triệu chứng: {{symptoms}}
- Mức độ ảnh hưởng: {{impact}}
- Thay đổi gần đây: {{recent_changes}}
</input_content>

<instructions>
Hãy giúp tôi:
1. Tạo timeline điều tra nhanh.
2. Xác định vùng hệ thống đáng nghi nhất.
3. Nêu 3 nguyên nhân gốc (Root cause) có xác suất cao nhất.
4. Đề xuất các bước kiểm tra (Verify) theo thứ tự ưu tiên.
5. Tách rõ mitigations tạm thời (giảm đau ngay) và root fix lâu dài.
</instructions>`
});

window.promptRegistry.push({
    id: "incident_hotfix",
    title: "Patch nóng (Hotfix) tối thiểu",
    category: "Incident",
    tags: ["emergency", "safe-fix"],
    description: "Đề xuất sửa lỗi nhanh nhưng an toàn tuyệt đối.",
    use_when: ["Cần fix ngay trong 5-10p"],
    fields: [
        { id: "problem", label: "Sự cố", type: "text", required: true },
        { id: "constraints", label: "Ràng buộc hotfix", type: "text", default: "Không downtime, không đổi schema" }
    ],
    template: `<system_directive>
Tôi cần một hotfix tối thiểu, an toàn và nhanh.
</system_directive>

<input_content>
- Sự cố: {{problem}}
- Ràng buộc: {{constraints}}
</input_content>

<instructions>
Hãy:
1. Chỉ ra patch nhỏ nhất có thể giảm thiểu rủi ro ngay lập tức.
2. Nêu rõ tradeoff/tác dụng phụ của patch này.
3. Đề xuất cách verify sau khi deploy (Smoke test).
</instructions>`
});
