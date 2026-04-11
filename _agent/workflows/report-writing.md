---
description: Quy trình Viết Báo Cáo Tiến Độ (Progress Report) & Cập Nhật Dashboard
---

# Quy trình tạo Báo Cáo Tiến Độ và cập nhật Dashboard cho AI Agent

Là một AI Agent, bạn cần giao tiếp tiến độ một cách RÕ RÀNG, CẤU TRÚC, và LIÊN TỤC với đội ngũ (hoặc các session agent thay thế bạn tiếp theo). Bạn phải tuân thủ chuẩn mực báo cáo dựa trên hai file template đã được hệ thống định nghĩa.

⚠️ KHÔNG bao giờ tự bịa ra cách cấu trúc file báo cáo, KHÔNG bao giờ viết nội dung một cách ngẫu nhiên, tạo "rác", hoặc viết lan man. Mỗi token sinh ra phải chứa mật độ thông tin cao nhất có thể.

### 📋 MỤC TIÊU TIÊU CHUẨN:

1. **Lưu trữ Context (Ngữ Cảnh):** Việc lập báo cáo (Progress Report/Handoff) giúp LLM ở các lần chat và session sau có thể đọc lại mà không bị mất đi "trí nhớ" về thiết kế và kiến trúc.
2. **Cập Nhật Toàn Cảnh (Macro):** Khái niệm `DASHBOARD` giúp mọi hệ thống Agent nắm được tổng quát tình trạng của toàn dự án chỉ trong nháy mắt.

---

## Giai đoạn 1: Tạo Progress Report / Handoff

_(Báo cáo ở cấp độ Ticket / Task cụ thể)_

Bất cứ khi nào bạn hoàn thành một tác vụ (task), hoặc cần kết thúc phiên làm việc mà task bị nghẽn (blocker), hoặc chưa hoàn thiện (bàn giao cho agent khác xử lý), bạn PHẢI tạo 1 Progress Report:

1. **Đọc Template:** Nếu cần thiết, bạn hãy đọc file mẫu `templates/PROGRESS_REPORT_TEMPLATE.md` từ thư mục gốc của agent skillset hoặc dự án.
2. **Thu Thập Dữ Liệu:**
   - Cần liệt kê chính xác cấu trúc những gì đã thực thi, và file nào đang đóng vai trò quan trọng.
   - Nhận định chính xác Bug/Issue đang tồn đọng thực tế chứ không phải suy đoán vô căn cứ.
   - Xác định rõ nhiệm vụ của công đoạn/ticket tiếp theo cần để lại dấu ấn gì.
3. **Tạo Báo Cáo Mới:**
   - Viết ra một file markdown theo đúng chuẩn cấu trúc ở template. Khuyến nghị đặt trong một thư mục quy ước (ví dụ: `.hub/handoffs/TASK-XXX.md` hoặc `reports/TASK-XXX.md`).
   - Yêu cầu điền đầy đủ và súc tích dữ liệu thực tế.

---

## Giai đoạn 2: Cập Nhật DASHBOARD

_(Báo cáo ở cấp độ Dự án tổng thể)_

Khi một hạng mục chính được thay đổi (Ví dụ: Một Task chuyển từ TODO sang IN PROGRESS, hoặc hoàn tất DONE), bạn PHẢI cập nhật file `DASHBOARD.md` của dự án (Tất nhiên bạn phải kiểm tra dự án có file này không. Nếu chưa có, xem xét tạo mới từ `templates/DASHBOARD_TEMPLATE.md`).

1. **Cập Nhật "Quick Context":**
   - Thay đổi biến `Last Updated` thành thời gian chính xác hiện tại (YYYY-MM-DD).
   - Thay đổi biến `Last Agent` thành tên của Agent chịu trách nhiệm (Vai trò hiện tại của bạn).
   - Chỉnh sửa `Progress` hoặc `Summary` một cách cô đọng (tuyệt đối không qua 3 câu). Đừng liệt kê vòng vo.
2. **Đồng bộ `.hub/backlog.yaml` (Rất quan trọng):**
   - TÌM kiếm Ticket tương ứng trong file `backlog.yaml`.
   - CẬP NHẬT `status` thành giá trị hợp lệ: `todo | claimed | in_progress | in_review | done | blocked`.
   - CẬP NHẬT `started_at`, `completed_at`, hoặc `output_files` tuỳ theo việc bắt đầu hay kết thúc ticket.
3. **Chuyển Trạng Thái Task trên DASHBOARD:**
   - Di chuyển các dòng chứa Task ID tương ứng qua lại giữa các bảng: `TODO` -> `IN PROGRESS` -> `DONE`.
   - Nếu khởi tạo task mới, luôn định danh và thêm vào bảng `TODO`.
4. **Cập Nhật "Timeline":**
   - Thêm 1 gạch đầu dòng mô tả nhanh bằng các từ khóa dạng log hành động ở Timeline của ngày hôm nay. (Ví dụ: `- [2026-04-03] fullstack-agent - COMPLETED: Triển khai 2 API Endpoint cho Login/Signup`).

---

## LỜI KHUYÊN & LUẬT LỆ:

- **Ngắn gọn là sức mạnh (Concise & Information Dense):** Thay vì diễn dạt câu chữ hoa mỹ, hãy đưa vào facts, metrics, và trạng thái.
  - ❌ Kém: _"Chào buổi sáng, tôi đã xử lý được kha khá công việc bao gồm thiết kế xong module A nhưng vẫn chưa rõ nguyên do lỗi..."_
  - ✅ Tốt: _"COMPLETED: Thiết kế Module A. BLOCKER: Unresolved CORS Policy Error (Port 3000)."_
- **Sự Chân Thực (No Hallucination):** Tuyệt đối không suy diễn và không ghi nhận báo cáo cho các task bạn cho là "đã chạy thành công" nếu bạn chưa kiểm tra (verify).
- **Trách Nhiệm Đồng Bộ (Sync Check):** Hãy luôn đảm bảo file báo cáo được ghi xuống ổ đĩa, hoặc dashboard được cập nhập, SAU ĐÓ mới thông báo lệnh lên cho người dùng/quản lý biết. Giữ Git Repo History đồng bộ với trạng thái Report càng sát càng tốt.
