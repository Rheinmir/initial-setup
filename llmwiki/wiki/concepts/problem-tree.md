---
type: concept
title: "Problem-tree — sổ cây vấn đề xuyên session"
status: active
tags: [problem-tree, ledger, systems-thinking, harness, R16, R17]
timestamp: 2026-07-02
id: problem-tree
---

# Problem-tree — sổ cây vấn đề xuyên session

## Nó là gì

Một file HTML duy nhất (`llmwiki/html/problem-tree.html`; riêng repo framework dùng `fdk-problem-tree.html`) đóng vai trò **ledger append-only** cho mọi vấn đề quy trình/framework của dự án: mỗi node là một bài toán, nối cha→con theo phả hệ (vấn đề mới sinh ra từ vấn đề nào). Nó giải bài toán "tri thức *đang vướng gì, đã giải tới đâu* bay hơi giữa các session" — thay ký ức hội thoại bằng artifact có cấu trúc, có thang đo, có lịch sử.

## Cách đọc

- **Data** nằm trong block `<script type="application/json" id="tree-data">` — cập nhật chỉ sửa JSON, không đụng markup. Node: `{id, parent, title, desc, status, scope, date, solvedBy?, session?, pending?}`.
- **Scope theo 3 trụ** (harness / skills / llmwiki): lời giải đã được cài vào mấy trụ. **Màu theo độ phủ, không theo status**: 0/3 đỏ (nghiêm trọng nhất — chưa có gì) → 1/3 cam → 2/3 vàng → **3/3 xanh lá — CHỈ khi giải trọn cả ba**. Mỗi thẻ hiện checklist ✓/✗ từng trụ.
- **Append-only**: không xoá node; giải xong thì đổi `status` + ghi `solvedBy` (skill/rule/commit nào).
- **Node `pending` (nét đứt)**: thẻ ghi-tạm do hook tự xả — chờ người/AI chưng lọc (distill) về đúng nhánh.
- Nội dung viết tiếng Việt thường; thuật ngữ kèm giải nghĩa trong ngoặc (rule skill fdk — HTML cho người đọc).

## Trigger — ai ghi sổ, khi nào

1. **Hard trigger (R17, hook SessionEnd)** — code thuần, 0 token: phiên có diff/untracked chạm bề mặt framework (`skills/ harness/ llmwiki/ fdk/`) mà sổ chưa được cập nhật → hook tự append thẻ `pending`. Đảm bảo bất biến "tắt app bình thường thì cây vẫn nằm đúng chỗ". Fail-open khi dự án không có sổ.
2. **Soft trigger (skill)** — `orca-workflow` § "Sổ vấn đề quy trình": phiên phát hiện/giải vấn đề quy trình → cập nhật node. Repo framework: `/fdk` là người gác, rà sổ trước khi kết thúc turn.
3. **Backfill (định kỳ)** — `/orca-eval` quét session cũ vét những vấn đề chỉ được bàn miệng (không có diff). Transcript là source of truth; sổ là index nên recall chỉ trễ, không mất.
4. **R16 (validator report-show-path)** — mọi HTML dưới `llmwiki/html/` phải tự khai đường dẫn tuyệt đối của mình (footer) — người xem biết file nằm đâu.

## Travel — vì sao dự án nào cũng có

Convention nằm ở các trụ **được distribute**: skill `orca-workflow` (mọi dự án nạp), hook `session_end.py` + validator (đi cùng harness khi bootstrap — tiền lệ `ADR-005`), template sổ rỗng do `install.sh` seed (chỉ khi chưa tồn tại). Cố ý KHÔNG nằm trong `fdk` vì fdk không distribute (`ADR-004`).

## Origin

- **Nguồn:** session 020726 — thiết kế ledger + R16/R17 + proposal `sources/draft/020726-orca-issue-ledger-travel.md` (task T-260702-01, node p-02/p-04 của chính cây này).
- **Code:** `llmwiki/.claude/hooks/session_end.py::flush_problem_tree`, `harness/validators/report_show_path.py`, `harness/templates/problem-tree-template.html`, policy R16/R17.
