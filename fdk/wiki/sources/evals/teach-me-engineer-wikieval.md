---
type: eval
id: teach-me-engineer-wikieval
title: "teach-me cho engineer — tầng 1 (tier-1 asserts) của wikieval chạy thế nào"
input: "teach me: tầng 1 (tier-1 deterministic asserts) trong harness/scripts/wikieval.py chạy thế nào?"
expected: "Người nghe mặc định là engineer. Đủ bảy phần đúng thứ tự. Cơ chế neo vào hàm thật (run_golden gọi eval_assert cho từng assert; golden có asserts thì tầng 1 tự quyết, all() mới đạt; op lạ fail closed) và có ít nhất một quan sát chạy thật (chạy wikieval.py với một outputs cụ thể, thấy kết quả). Có sơ đồ mermaid. Trade-off (rẻ, tất định, không cần model — đổi lấy việc chỉ bắt được dấu hiệu bề mặt) tách khỏi Giới hạn (regex không cờ mặc định, không hiểu ngữ nghĩa)."
asserts:
  - 'regex:(?s)Tên gọi.*Nguồn gốc.*Lý do tồn tại.*Cơ chế hoạt động.*Trade-off.*Giới hạn.*Vị trí'
  - 'contains:```mermaid'
  - 'regex:eval_assert|run_golden'
  - 'regex:(?i)đã chạy|chạy thật|chạy thử|rc=|exit ?code|python3 harness/scripts/wikieval\.py'
rubric: "ĐẠT nếu: dùng đúng thuật ngữ, không giải thích lại những thứ engineer đã biết; bước Cơ chế trích quan sát runtime cụ thể (đầu vào → kết quả) chứ không mô tả chung; Trade-off và Giới hạn khác nhau thật. KHÔNG đạt nếu chỉ đọc code rồi đoán, hoặc thiếu phần nào trong bảy phần."
---

# Golden: teach-me-engineer-wikieval

Ca người nghe mặc định (engineer). Đo khung bảy phần, sơ đồ, và bằng chứng runtime — ba thứ teach-me hứa với dev.

## Origin
- Phiên 11/09/2026 — distill [dreambigou/eli5](https://github.com/dreambigou/eli5) vào `skills/teach-me/SKILL.md`; eli5 chấm skill bằng 3 ca × 4 assert, chạy có-skill so với không-skill. Ca này là một trong ba ca A/B cũ-vs-mới của teach-me.
