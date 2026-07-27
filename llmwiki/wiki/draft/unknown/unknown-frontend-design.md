---
type: unknown-ledger
title: "unknown — frontend-design (anthropics/skills)"
status: open
source_task: T-260717-02
source_spec: wiki/sources/draft/170726-absorb-six-sources.md
timestamp: 2026-07-17
---

# Unknown ledger — frontend-design

> **Nợ unknown** — model đã *fill-first* (điền default để không chặn việc), *find-out-later* (chờ thông tin thật để trả nợ). KHÔNG chặn cổng; hiện ra ở `/lint` để không chìm. Đóng khoảng hở giữa `(default)` và `[CẦN LÀM RÕ]`. Xem `[[150726-unknown-ledger]]`.
>
> Thêm/đóng mục bằng `python3 harness/scripts/unknown-ledger.py` — đừng sửa số U-NN bằng tay.

## U-01 — skill frontend-design có tồn tại trong anthropics/skills không?
- **Trace:** FR-005 · SPEC `170726-absorb-six-sources.md` · task `T-260717-02`
- **Đã fill (default):** giả định CÓ — T3 verify đầu tiên trước khi distill
- **Cần verify:** clone --depth 1 anthropics/skills rồi ls skills/
- **Rủi ro nếu default sai:** thấp — không có thì T3 rút gọn, không hỏng task khác
- **Status:** resolved
- **Resolved:** CÓ — scratchpad/anthropic-skills/skills/frontend-design · fix: T3 chạy đủ (frontend-design-delta.md) · 2026-07-17

## Origin
- Sinh bởi `/propose` (SPEC `170726-absorb-six-sources`, Assumption A-1) — WebFetch trang repo không render được danh sách skill nên chưa xác nhận `frontend-design` tồn tại.
- Trả nợ: `unknown-ledger.py --resolve --file unknown-frontend-design.md --id U-01 --value … --fixed … --date …`.
- **Commit:** _(verify-before-commit điền)_
