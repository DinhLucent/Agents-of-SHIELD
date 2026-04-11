# 📋 CHEATSHEET — Quick Reference for CEO

> Open this file when you don't know what to do. Find your situation → follow the action.

---

## 🗺️ Giai đoạn Dự án: Lúc nào làm gì? (Step-by-Step Guide)

Nếu đây là lần đầu bạn sử dụng Company này, hãy đi theo lộ trình sau:

| Giai đoạn                    | Mục tiêu                     | Agent cần mở      | Lệnh nên chạy             |
| :--------------------------- | :--------------------------- | :---------------- | :------------------------ |
| **1. Ý tưởng (PLAN)**        | Làm rõ yêu cầu, tính năng    | `producer-agent`  | `/brainstorm`             |
| **2. Thiết kế (DESIGN)**     | Xây dựng kiến trúc, Database | `cto-agent`       | `/map-systems`            |
| **3. Lập trình (IMPLEMENT)** | Viết code thực tế            | `backend-agent`   | _"Pick up task from Hub"_ |
| **4. Kiểm tra (REVIEW)**     | Soi lỗi, bảo mật, chất lượng | `lead-programmer` | `/code-review`            |
| **5. Phát hành (RELEASE)**   | Đóng gói và chạy thật        | `release-manager` | `/release-checklist`      |

> [!TIP]
> **Cách chạy lệnh:** Chỉ cần gõ `/tên-lệnh` (ví dụ `/start`) trực tiếp vào khung chat. Nếu menu không hiện ra, bạn cứ nhấn gửi như tin nhắn bình thường, Agent sẽ tự hiểu.

---

## 🚀 Starting a New Project

| Step | You Do                                             | Which Agent                       |
| ---- | -------------------------------------------------- | --------------------------------- |
| 1    | Describe project (tech stack, requirements, scale) | → `producer-agent` or `cto-agent` |
| 2    | AI suggests team → You approve                     | → AI updates `active_agents`      |
| 3    | AI runs `/sprint-plan` → Tasks go to Hub           | → You review sprint plan          |
| 4    | Open session for each Agent → They grab tasks      | → You review each output          |

---

## 🔧 Common Situations

| Situation             | Open Agent                                  | Action                                                       |
| --------------------- | ------------------------------------------- | ------------------------------------------------------------ |
| **New Project**       | `producer-agent`                            | Describe project → AI analyzes → suggests team → sprint plan |
| **New Feature**       | `producer-agent`                            | Describe feature → AI splits tasks → assigns roles → to Hub  |
| **Bug Report**        | `qa-lead-agent`                             | Describe bug → AI creates prioritized task + assigns role    |
| **Urgent Hotfix**     | `security-agent` → `backend-agent`          | Assess → Fix → Review → Deploy                               |
| **Scope Change**      | `cto-agent`                                 | Describe change → AI assesses impact → plans                 |
| **New Sprint**        | `producer-agent`                            | `/sprint-plan` → New tasks to Hub                            |
| **Release**           | `release-manager-agent`                     | `/release-checklist` → deploy → monitor                      |
| **Missing Role**      | AI reports automatically → Open new session | Hire new Agent per `RECRUITMENT.md`                          |
| **Agent Exhausted**   | AI shows >65% STRESS in Dashboard           | Close current session → Open new session for same role       |
| **Task Done (Fire)**  | `producer-agent`                            | "Run OFFBOARDING for [agent-id]"                             |
| **Code Review**       | `lead-programmer-agent`                     | `/code-review`                                               |
| **Security Audit**    | `security-agent`                            | `/deep-scan`                                                 |
| **Performance Issue** | `performance-analyst-agent`                 | `/perf-profile`                                              |
| **UI/UX Feedback**    | `ux-designer-agent`                         | Describe issue → AI suggests fix                             |
| **Retrospective**     | `producer-agent`                            | `/retrospective` at end of sprint                            |

---

## 🤔 Don't know which Agent to open?

```
→ Open producer-agent. It will sort and orchestrate for you.
```

---

## 📝 What to say in each session?

### First time (new project):

```
"I want to build [project description].
 Tech: [stack].
 Special requirements: [high security / real-time / mobile-first / ...]
 Scale: [small / medium / large]"
```

### Subsequent sessions (Agent Hub is active):

```
"Pick up task from Hub and execute"
```

→ Agent reads Dashboard + backlog + handoffs → works automatically.

### When a new issue arises:

```
"Issue: [description]. Create a task in the Hub."
```

---

## 🔄 Daily Workflow

```
Morning: Open DASHBOARD.md → Check overall progress
         Producer: "Sprint status?"

Work:    Open Agent based on task → Grabs task from Hub
         Review output → Approve / request changes

End:     Check DASHBOARD.md → See completed tasks today
         Found issue? → Create new task in Hub
```

---

## ⚡ Frequently Used Slash Commands

| Command              | When to use                     |
| -------------------- | ------------------------------- |
| `/brainstorm`        | New ideas, unclear concepts     |
| `/sprint-plan`       | Sprint planning, creating tasks |
| `/code-review`       | Code review before merge        |
| `/deep-scan`         | Security check                  |
| `/gate-check`        | Ready to switch phases?         |
| `/release-checklist` | Prep for release                |
| `/retrospective`     | End of sprint, lessons learned  |

---

## 📊 Checking Progress

Open `DASHBOARD.md` → View:

- **Quick Context** → Current Phase, % complete
- **Task Board** → Who is doing what
- **Timeline** → Recent history

---

## ✅ Task Quality Checklist (CEO tự kiểm trước khi assign)

Trước khi giao task cho Agent, đảm bảo task description đạt 5 tiêu chí sau.
Task kém chất lượng = Agent hiểu sai = phải làm lại = đốt token.

| #   | Kiểm tra                 | ❌ Sai                       | ✅ Đúng                                                |
| :-- | :----------------------- | :--------------------------- | :----------------------------------------------------- |
| 1   | **Hành động cụ thể**     | "fix app"                    | "Fix null check in `getUserData()` at `src/auth.js`"   |
| 2   | **Scope rõ ràng**        | "update the login"           | "Update `handleLogin()` in `src/pages/Login.tsx` only" |
| 3   | **Chỉ 1 việc / task**    | "explain AND rewrite"        | Tách: Task A = explain, Task B = rewrite               |
| 4   | **Điều kiện hoàn thành** | "make it better"             | "Done when unit tests pass + no console errors"        |
| 5   | **Context cũ nếu có**    | "continue where we left off" | Ghi rõ quyết định đã thống nhất trước đó               |

> [!TIP]
> Nếu task dùng từ "fix", "improve", "handle" mà không kèm file/function cụ thể → **chưa đủ chất lượng**.

---

## 🤖 Chọn Model phù hợp cho từng Agent (QUAN TRỌNG)

> [!CAUTION]
> Không có cơ chế tự động chặn model yếu. **CEO phải tự chọn model khi mở session.**

| Tier       | Agent                                   | Model tối thiểu       | Lý do                                     | Prompting Tip                                                             |
| :--------- | :-------------------------------------- | :-------------------- | :---------------------------------------- | :------------------------------------------------------------------------ |
| **Tier 1** | `cto-agent`, `technical-director-agent` | Gemini Pro / GPT-4o   | Ra quyết định kiến trúc, cần suy luận sâu | Full structure OK. Dùng XML tags cho Claude. **Không CoT cho o3/o4-mini** |
| **Tier 2** | `qa-lead-agent`, `producer-agent`       | Gemini Flash / Sonnet | Sprint plan, review, phối hợp đội nhóm    | Rõ format output, kèm success criteria                                    |
| **Tier 3** | `backend-agent`, `frontend-agent`       | Gemini Flash          | Viết code theo spec đã rõ ràng            | Ngắn gọn, ít nesting, scope file rõ                                       |
| **Tier 4** | `qa-tester-agent`                       | Flash Lite / Haiku    | Chạy checklist, kiểm tra định lệ          | Prompt cực ngắn, 1 task / 1 prompt                                        |

**Dấu hiệu chọn nhầm model:** Agent không đọc được `ONBOARDING.md`, bỏ qua `role boundary`, tự làm Task không thuộc scope → Đóng session, mở lại bằng model mạnh hơn.

> [!CAUTION]
> **🔴 KHÔNG đổi model giữa session đang chạy.**
> Khi đổi model, model mới sẽ **mất toàn bộ context** (chưa đọc ONBOARDING, chưa biết role, chưa biết task đang làm).
> Kết quả: Agent hành xử như "người mới hoàn toàn" — dễ vi phạm role boundary, code sai scope.
> **Giải pháp đúng:** Đóng session → Mở session mới → Chọn đúng model ngay từ đầu.

---

## 👔 HR — Khi nào thuê / sa thải Agent?

### ➕ Thuê thêm Agent (RECRUIT)

| Tình huống                                                  | Hành động                                                                     |
| :---------------------------------------------------------- | :---------------------------------------------------------------------------- |
| AI báo _"This task requires a role X not in active_agents"_ | Mở `RECRUITMENT.md` → Thêm agent ID vào `active_agents` trong `manifest.yaml` |
| Dự án mở rộng cần thêm chuyên môn (DevOps, Data...)         | Tương tự — thêm agent vào manifest + mở session mới với đúng model            |

**Prompt mẫu khi thuê:** _"Hire `devops-agent` and assign TASK-XXX to them."_ (Nói với `producer-agent`)

### ➖ Sa thải Agent (OFFBOARD)

| Tình huống                                       | Hành động                                                                                 |
| :----------------------------------------------- | :---------------------------------------------------------------------------------------- |
| Giai đoạn DESIGN xong, không cần `cto-agent` nữa | Nói với `producer-agent`: _"Run OFFBOARDING for cto-agent"_ → AI xóa khỏi `active_agents` |
| Agent đang 🟠/🔴 Exhausted (>65% STRESS)         | Đóng session → Mở session mới cùng agent ID đó                                            |
| Task xong hẳn, Agent không cần nữa               | Offboard → Giảm token mỗi session                                                         |

---

## 🚪 Mở Session Mới — Copy-Paste Prompt cho từng vai trò

> [!IMPORTANT]
> **AI KHÔNG TỰ BIẾT nó là ai.** Bạn (CEO) phải nói cho nó biết bằng câu prompt đầu tiên.
> Sau khi nhận prompt, Agent sẽ TỰ ĐỘNG: đọc ONBOARDING → nhận role → đọc Dashboard → claim task → làm việc.

### Kịch bản 1: Bạn muốn AI viết code (backend)

```
Model: Gemini Flash trở lên
Prompt: "Onboard as backend-agent. Read MyTeam/ONBOARDING.md, then pick up task from Hub."
```

### Kịch bản 2: Bạn muốn AI thiết kế kiến trúc

```
Model: Gemini Pro / GPT-4o (BẮT BUỘC)
Prompt: "Onboard as cto-agent. Read MyTeam/ONBOARDING.md, then pick up task from Hub."
```

### Kịch bản 3: Bạn muốn AI review code / bảo mật

```
Model: Gemini Pro / GPT-4o (BẮT BUỘC)
Prompt: "Onboard as security-agent. Read MyTeam/ONBOARDING.md, then pick up task from Hub."
```

### Kịch bản 4: Bạn muốn AI lập sprint plan / quản lý

```
Model: Gemini Flash trở lên
Prompt: "Onboard as producer-agent. Read MyTeam/ONBOARDING.md, then run /sprint-plan."
```

### Kịch bản 5: Bạn muốn AI build UI / dashboard

```
Model: Gemini Flash trở lên
Prompt: "Onboard as fullstack-agent. Read MyTeam/ONBOARDING.md, then pick up task from Hub."
```

### Kịch bản 6: Bạn muốn AI viết test plan / QA

```
Model: Gemini Flash trở lên
Prompt: "Onboard as qa-lead-agent. Read MyTeam/ONBOARDING.md, then pick up task from Hub."
```

### Kịch bản 7: Không biết cần Agent nào

```
Model: Gemini Flash trở lên
Prompt: "Read MyTeam/DASHBOARD.md and tell me what needs to be done next."
```

→ AI sẽ đọc Dashboard, xem task nào đang chờ, và gợi ý bạn nên mở Agent nào.

> [!CAUTION]
> **🔴 KHÔNG đổi model giữa session đang chạy.**
> Model mới sẽ mất toàn bộ context → Agent mất trí nhớ.
> **Đúng:** Đóng session → Mở session mới → Chọn đúng model.

---

## ⚠️ Core Rules to Remember

1. **Describe, Don't Dictate** → Let AI suggest approach, you approve
2. **1 Agent 1 Session** → Don't mix roles in one session
3. **Always Review** → AI finishes → you approve → move on
4. **Hub is the Center** → All tasks go through Hub, no side work
5. **Model matters** → Tier 1 agent = Tier 1 model. Sai model → code tầm bậy
6. **ONBOARDING first** → Agent phải đọc ONBOARDING trước Dashboard, không bao giờ ngược lại
