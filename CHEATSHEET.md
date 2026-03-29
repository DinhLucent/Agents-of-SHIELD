# 📋 CHEATSHEET — Hướng dẫn nhanh cho CEO

> Mở file này khi không biết nên làm gì. Tìm tình huống → làm theo.

---

## 🚀 Bắt đầu dự án mới

| Bước | Bạn làm | Agent nào |
|------|---------|-----------|
| 1 | Mô tả dự án (tech stack, yêu cầu, quy mô) | → `producer-agent` hoặc `cto-agent` |
| 2 | AI đề xuất đội hình → Bạn approve | → AI cập nhật `active_agents` |
| 3 | AI chạy `/sprint-plan` → Tasks vào Hub | → Bạn duyệt sprint plan |
| 4 | Mở session từng Agent → Nó tự lấy task | → Bạn review mỗi output |

---

## 🔧 Các tình huống phổ biến

| Tình huống | Mở Agent | Action |
|-----------|----------|--------|
| **Dự án mới** | `producer-agent` | Mô tả dự án → AI phân tích → đề xuất team → sprint plan |
| **Thêm feature** | `producer-agent` | Mô tả feature → AI chia tasks → gán roles → vào Hub |
| **Bug report** | `qa-lead-agent` | Mô tả bug → AI tạo task priority + gán role |
| **Hotfix khẩn** | `security-agent` → `backend-agent` | Đánh giá → Fix → Review → Deploy |
| **Scope change** | `cto-agent` | Mô tả thay đổi → AI đánh giá impact → plan |
| **Sprint mới** | `producer-agent` | `/sprint-plan` → Tasks mới vào Hub |
| **Release** | `release-manager-agent` | `/release-checklist` → deploy → monitor |
| **Thiếu role** | AI tự báo → Bạn mở session mới | Thuê Agent mới theo `RECRUITMENT.md` |
| **Code review** | `lead-programmer-agent` | `/code-review` |
| **Security audit** | `security-agent` | `/deep-scan` |
| **Performance issue** | `performance-analyst-agent` | `/perf-profile` |
| **UI/UX feedback** | `ux-designer-agent` | Mô tả issue → AI đề xuất fix |
| **Retrospective** | `producer-agent` | `/retrospective` cuối sprint |

---

## 🤔 Không biết mở Agent nào?

```
→ Mở producer-agent. Nó sẽ phân loại và điều phối cho bạn.
```

---

## 📝 Mỗi session bạn cần nói gì?

### Lần đầu (dự án mới):
```
"Tôi muốn xây [mô tả dự án].
 Tech: [stack].
 Yêu cầu đặc biệt: [bảo mật cao / real-time / mobile-first / ...]
 Quy mô: [nhỏ / trung bình / lớn]"
```

### Session tiếp theo (Agent đã có Hub):
```
"Lấy task từ Hub và thực hiện"
```
→ Agent tự đọc Dashboard + backlog + handoffs → tự làm.

### Khi có vấn đề mới:
```
"Vấn đề: [mô tả]. Tạo task vào Hub."
```

---

## 🔄 Workflow hàng ngày

```
Sáng:  Mở DASHBOARD.md → Check tiến độ tổng
       Producer: "Sprint status?"
       
Làm:   Mở Agent theo task cần làm → Nó tự lấy từ Hub
       Review output → Approve / yêu cầu sửa
       
Cuối:  Check DASHBOARD.md → Xem tasks đã done hôm nay
       Phát hiện vấn đề → Tạo task mới vào Hub
```

---

## ⚡ Slash Commands hay dùng

| Command | Khi nào |
|---------|---------|
| `/brainstorm` | Ý tưởng mới, chưa rõ ràng |
| `/sprint-plan` | Lên kế hoạch sprint, tạo tasks |
| `/code-review` | Review code trước khi merge |
| `/deep-scan` | Kiểm tra bảo mật |
| `/gate-check` | Kiểm tra sẵn sàng chuyển phase |
| `/release-checklist` | Chuẩn bị release |
| `/retrospective` | Cuối sprint, rút kinh nghiệm |

---

## 📊 Check tiến độ

Mở `DASHBOARD.md` → Xem:
- **Quick Context** → Phase hiện tại, % hoàn thành
- **Task Board** → Ai đang làm gì
- **Timeline** → Lịch sử gần đây

---

## ⚠️ Quy tắc nhớ

1. **Mô tả, không chỉ định** → Để AI đề xuất approach, bạn duyệt
2. **1 Agent 1 session** → Không gộp nhiều role trong 1 session
3. **Luôn review** → AI làm xong → bạn approve → mới tiếp
4. **Hub là trung tâm** → Mọi task đều qua Hub, không làm ngoài
