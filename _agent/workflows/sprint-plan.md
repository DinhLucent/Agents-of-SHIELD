---
description: Plan the next sprint and populate the Task Hub backlog.
---

1. Read the instructions in `Skills/Roles/Management/sprint-plan/SKILL.md` (nếu có).
2. Khi lập kế hoạch Sprint và phân chia task, bạn PHẢI cập nhật file `.hub/backlog.yaml`.
3. BẮT BUỘC sử dụng cấu trúc đã được định nghĩa tại `templates/BACKLOG_TEMPLATE.yaml` để ghi `backlog.yaml` cho chuẩn mực.
4. **Quy định chi tiết về cách viết SPRINT và gom nhóm TASK (Cực kỳ quan trọng):**
   - **Phân chia Sprint rõ ràng:** Giữa các Sprint PHẢI bắt buộc được phân tách bằng block comment thật nổi bật `# ════ SPRINT X — [Tên mục tiêu Sprint] ════`.
   - **Kích cỡ Sprint hợp lý:** Không dồn quá nhiều Task vào một Sprint. Một Sprint nên dài khoảng 5-10 tasks có tính phụ thuộc chặt chẽ và chung 1 chủ đề (Goal).
   - **Tính lệ thuộc (Dependencies):** Các Task trong Sprint 2 thường phải có trường `dependencies` chỉ vào các Task cốt lõi hoàn thành ở Sprint 1. Không để dependency vòng tròn hoặc không thực tế.
   - `assigned_role`: Phải match với role có sẵn của hệ thống.
   - `status`: Chỉ nhận `todo | claimed | in_progress | in_review | done | blocked`.
   - Phải có mảng `acceptance_criteria` thật sự cụ thể để Agent thi công có thể stick [x] khi hoàn thành.
5. Guide the user through planning the next set of tasks, presenting them in the standard YAML format before officially persisting them to the backlog file.
