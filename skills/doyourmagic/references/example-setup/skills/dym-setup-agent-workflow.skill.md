---
name: dym-setup-agent-workflow
description: "Vòng làm việc hằng ngày bằng lệnh CHAT /propose → /plan → /verify-before-commit → /ship và bảng skill theo việc (KHÔNG phải lệnh shell). Gọi khi: 'workflow overstack', 'dùng skill nào', 'propose rồi làm gì'."
---

# Skill: dym-setup-agent-workflow — Vòng làm việc hằng ngày: các lệnh `/<skill>` (CHAT, không phải terminal)

## When to use
- **Tại sao chạy:** đây là phần overstack thật sự thay đổi cách bạn làm việc — agent buộc phải thiết kế trước khi code, và luật ở [02](02-guardrail-cli-and-rules.md) chỉ là lưới an toàn phía dưới.
- **Sinh ra gì:** file wiki dưới `.llmwiki/wiki/` (SPEC draft, PLAN, concept, ADR), cộng commit sạch.
- Gọi qua hub: `/dym-setup agent-workflow` — hoặc trực tiếp `/dym-setup-agent-workflow` nếu đã symlink riêng.

## Steps
### 1. Vòng chuẩn: propose → gate → dispatch → verify

```
/propose thêm endpoint xuất báo cáo tồn kho theo kho
        ↓  sinh SPEC ở .llmwiki/wiki/sources/draft/DDMMYY-<tên>.md — DỪNG chờ bạn duyệt
        ↓  (bạn đọc, sửa, gật)
/plan   DDMMYY-<tên>.md
        ↓  sinh DDMMYY-<tên>-PLAN.md: đường dẫn file chính xác, Interfaces, code từng bước
        ↓
(agent code, hoặc dispatch cho CLI rẻ chạy headless)
        ↓
/verify-before-commit
        ↓  typecheck → lint → test → task_lifecycle → commit → promote draft sang wiki
        ↓
/ship push        (hoặc /ship pr · /ship mr · /ship release)
```

**Hai văn bản, hai người đọc — đừng gộp.** `/propose` sinh **SPEC**: thứ *người* đọc để bấm duyệt ở cổng. `/plan` sinh **PLAN**: thứ bơm thẳng vào một agent context=0 không hỏi lại được. Tỷ lệ độ dài spec:plan ≈ 1:8. Nhồi code-level vào SPEC thì người duyệt không đọc nổi thứ mình đang duyệt và cổng duyệt mất tác dụng.

Cả hai văn bản đều bị luật gác: SPEC thiếu `## Agent Task Assignment` / Sequence diagram / `## Global constraints` → R7 chặn; PLAN thiếu Files / Interfaces / code từng bước → R18 chặn.

**Rẽ nhánh quan trọng:** đầu vào là **sự cố** (bug, regression, "hôm qua còn chạy") thì gọi `/orca-issue` chứ không `/propose` — nó có cổng repro-first: chưa tái hiện được thì chưa được sửa.

### 2. Bảng lệnh theo việc

### Vòng tri thức (wiki)
| Lệnh | Dùng khi |
|---|---|
| `/ingest` | vừa thả tài liệu thô vào `raw/` → distill thành trang wiki |
| `/query <câu hỏi>` | hỏi wiki; trả lời kèm mục Evidence trích edge-id trong graph |
| `/lint` | kiểm tra sức khoẻ wiki: orphan, wikilink gãy, mâu thuẫn, drift code→wiki |
| `/record-episode` | ghi lại một session có cấu trúc cho phiên sau truy hồi |

### Vòng phát triển
| Lệnh | Dùng khi |
|---|---|
| `/propose` | tính năng mới, hoặc chạm code dùng chung |
| `/plan` | SPEC đã duyệt, sắp dispatch |
| `/impact-check` | trước khi sửa một symbol dùng chung — map hết caller |
| `/safe-change` | sửa code dùng chung mà không vỡ caller |
| `/qc-code` | review kiểu senior: security · performance · naming · logic + sinh test tái hiện |
| `/verify-before-commit` | cổng trước mọi `git commit` |
| `/ship` | push / release / PR / MR / merge |
| `/teach-me <thứ>` | hiểu một file/hàm/cơ chế, có chứng bằng chạy thật |

### Onboard & bảo trì
| Lệnh | Dùng khi |
|---|---|
| `/new-project-setup` | dự án **đã có code**, muốn gắn overstack + populate wiki từ code |
| `/onboard-codebase`, `/orca-onboard` | phân tích codebase sâu, dựng wiki + HTML |
| `/harness-update` | dự án đã có overstack bản cũ → nâng bản (xem [05](../dym-setup-maintain/SKILL.md)) |
| `/harness-tour` | xem tận mắt hook chặn mình theo thời gian thực (`short` = R1·R2·R3, `full` = R1–R10) |
| `/health-check` | xác nhận rào còn cắn sau khi update |

Danh mục đầy đủ 87 skill nằm ở `CAPABILITIES.md` trong dự án bạn (sinh bằng code, đếm từ đĩa). Tìm nhanh theo việc cần làm:

```bash
python3 ~/.claude/harness/fdk/tools/build-skill-search.py    # lệnh SHELL, sinh index
```

### 3. Chọn đúng lối vào cho dự án mới

| Tình huống | Lối vào |
|---|---|
| Dự án **từ con số 0**, chưa có code | dán nguyên nội dung `00-New-Project.md` của repo vào agent — nó chạy 4 pha: cài → kickoff 3 câu → knowledge base → scaffold MVP |
| Dự án **đã có codebase** | `/new-project-setup` |
| Đã có overstack bản cũ | `/harness-update` |

⚠️ `00-New-Project.md` (PHA 0) bảo agent "ĐỌC `llmwiki/AGENT.md` + `llmwiki/CLAUDE.md`". Với bản installer hiện tại, hai file đó **không được seed xuống dự án** — `--with-wiki` chỉ tạo `.llmwiki/{wiki/…, raw, html, .harness-stamp}`. Agent sẽ báo không tìm thấy. Thay bằng: đọc `CAPABILITIES.md` ở gốc dự án và `.llmwiki/html/overstack.html`. Prompt cũng viết đường dẫn `llmwiki/…` không dấu chấm ở PHA 2 — dịch sang `.llmwiki/…` khi làm theo.

### 4. Vì sao không đo được như `02`

Không có lệnh nào trong file này có mã thoát để đối chiếu — chúng chạy bên trong phiên agent. Phần được kiểm chứng ở đây là: **tên skill và mô tả** (đọc từ `skills/<tên>/SKILL.md` trong repo), **luồng propose→plan** (đọc `skills/propose/SKILL.md` và `skills/plan/SKILL.md`), và **các luật gác hai văn bản đó** (R7/R18 trong `policy.yaml`). Hành vi thực tế của từng skill khi chạy thì chưa đo.

## Rules
- Làm đúng thứ tự Steps; lệnh nào ghi rc đo được thì đối chiếu rc, không đoán.
