# 📊 DASHBOARD — Project Status

> **⚡ Quick Context** — Tóm tắt dự án chỉ trong 10 giây cho Agent mới tham gia (hoặc tái xây dựng context cho session mới).

## 🧭 Quick Context

| Key                  | Value                                                  |
| -------------------- | ------------------------------------------------------ |
| **Project**          | [Tên Dự Án]                                            |
| **Phase**            | 🚧 ACTIVE / ⏸️ PAUSED / ✅ COMPLETED                   |
| **Sprint/Milestone** | [Tên/Mục tiêu của chặng công việc hiện tại]            |
| **Progress**         | [Số lượng task đã làm / Tổng task] — [Tiến độ tóm tắt] |
| **Blocking**         | 🟡 [Các issue/blocker chưa giải quyết, nếu có]         |
| **Last Updated**     | [Timestamp cập nhật gần nhất]                          |
| **Last Agent**       | `[Tên Agent/Vai trò cập nhật cuối cùng]`               |

**Summary:** Báo cáo tóm tắt tình hình hiện tại (chỉ dài từ 1-3 câu). Ghi rõ: những gì vừa được giải quyết, những gì là bước tiếp theo. Đừng lan man.

---

## 👥 Active Team (Roles / Agents)

| Agent ID    | Role   | Status                                    |
| ----------- | ------ | ----------------------------------------- |
| `[Agent 1]` | [Role] | ✅ Hoàn thành / 🟡 Sẵn sàng / ⏸️ Đang đợi |
| `[Agent 2]` | [Role] | 🟢 Đang xử lý TASK-XYZ                    |

---

## 📋 Tasks

### TODO (Sắp tới)

| ID       | Title              | Role          | Priority |
| -------- | ------------------ | ------------- | -------- |
| TASK-XXX | [Tên Task cần làm] | [Agent xử lý] | P1 / P2  |

### IN PROGRESS (Đang xử lý)

| ID       | Title               | Agent            | Started    |
| -------- | ------------------- | ---------------- | ---------- |
| TASK-YYY | [Tên Task đang làm] | [Agent đang làm] | YYYY-MM-DD |

### DONE (Đã hoàn thành)

| ID       | Title              | Agent         | Date       |
| -------- | ------------------ | ------------- | ---------- |
| TASK-ZZZ | [Tên Task đã xong] | [Agent xử lý] | YYYY-MM-DD |

---

## 📅 Timeline (Activity Log)

- `[YYYY-MM-DD]` [Tên Agent] — STARTED: [Tóm tắt công việc vừa bắt đầu]
- `[YYYY-MM-DD]` [Tên Agent] — COMPLETED: [Tóm tắt công việc đã xong]
- `[YYYY-MM-DD]` [Tên Agent] — VERIFIED: [Tóm tắt kết quả kiểm tra/merge]
