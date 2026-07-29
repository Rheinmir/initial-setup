---
type: draft
title: "Output report — br proactive fill (T-260714-01) đã thi công"
status: proposed
tags: [orca-workflow, output-report, br, proactive, issue-15]
timestamp: 2026-07-14
task: T-260714-01
---

# 140726-br-proactive-fill-report
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-07-14

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Task 1 — registry `skills/br/assets/defaults.yaml` (26 điều kiện + spec-kit) | Claude Code | done |
| Task 2 — tool `fdk/tools/br-fill.py` (fill + check-contract + selftest) | Claude Code | done |
| Task 3 — wire `--proactive` vào Mode 1 + gate checksum vào Mode 2 (SKILL.md + mirror) | Claude Code | done |
| Task 4 — verify ATG mảnh 1 (FR-006, đã có từ GH#75) | Claude Code | done (verify-only) |
| Task 5 — chạy thật trên br/payroll + register | Claude Code | done |
| Render HTML companion proposal | OpenCode big-pickle → Claude fallback | done (OpenCode quá watchdog 90s, bị kill) |

## What
Thi công T-260714-01: `/br interview --proactive` — máy tự điền field spec còn thiếu theo thang default (bảng 26 điều kiện) → convention github/spec-kit → lens, chỉ hỏi user tối đa 5 câu; compile có gate checksum hợp đồng (vá G1); xác nhận DAG frame (ATG mảnh 1) đã có sẵn từ GH#75.

## Output
Kết quả đo trên project mẫu `br/payroll` (dữ liệu thật, không demo dựng sẵn):

- **SC-001 PASS** — vòng interview thật trước đây user phải trả lời **12 câu** (001-answers.md); với trạng thái spec-filled hiện tại, `--proactive` để máy điền 1 field và chỉ còn **4 câu hỏi thật** (dưới trần 5).
- **SC-004 PASS** — 0 field carve-out (S2.2, S6.1, S6.2, S7.2, S8.3) xuất hiện trong đề xuất máy điền; mọi đề xuất đều mang `verified: false`. Selftest có case riêng chứng minh carve-out thắng cả khi registry lỡ có entry default cho field đó.
- Field được máy điền trên payroll chính là **S7.5 (giao diện & design system)** — đúng field đã lọt trong lỗ hổng G1 mà council c9dc13d bắt được; nghĩa là nếu mode này tồn tại từ đầu, G1 đã không xảy ra.
- **check-contract** trên BR.clauses.json cũ của payroll trả về đúng thông điệp back-compat ("compile bản cũ, chưa khai fields") và exit 2 — gate chỉ ăn các lần compile mới, không phá dữ liệu cũ.
- **FR-006 (verify-only)** — `frame-lint.py selftest` ALL PASS (gồm case DAG cycle); `build-line-status.py` sinh line-status.json có `depends_on`/`waiting_on` cho 16 frame payroll. Ghi chú trung thực: `frame-lint check` trên payroll báo R3 test-first fail vì 16 frame đã hoàn tất nên acceptance test xanh sẵn — hành vi có sẵn của lint trên pipeline đã xong, không liên quan thay đổi đợt này.
- `medic --ci`: **KHOẺ** — 0 fail · 1 warn · 8 ok (rules 17/17 cắn, code compile sạch, eval không regress).

## Files
| File | Action |
|------|--------|
| `skills/br/assets/defaults.yaml` | created — registry mặc định (5 carve-out + 8 default, nguồn loop-26/spec-kit) |
| `fdk/tools/br-fill.py` | created — fill-chain tất định + checksum hợp đồng + selftest |
| `skills/br/SKILL.md` | modified — Mode 1 bước 3b `--proactive`, Mode 2 `fields:` + gate check-contract |
| `llmwiki/skills/dev-loop/br.md` | modified — mirror parity với canonical |
| `llmwiki/wiki/sources/draft/140726-br-proactive-fill.md` | created — SPEC (gate approved) |
| `llmwiki/wiki/sources/draft/140726-br-proactive-fill-PLAN.md` | created — PLAN thi hành |
| `llmwiki/html/140726-br-proactive-fill-seq.html` | created (gitignored render) — 5 diagram companion |
| `fdk/CAPABILITIES.md` | regenerated |

## Notes
- Invoked via: `/orca-workflow` skill; gate `gate_f5cfd004e73b` approved; goal `/goal` yêu cầu chạy tới khi dùng được.
- Skill `plan` bị disable cho model trong session — PLAN viết tay theo đúng convention của skill.
- Cách dùng: `/br interview --proactive` (hoặc chạy thẳng `python3 fdk/tools/br-fill.py fill --root .`); compile mới thêm bước `python3 fdk/tools/br-fill.py check-contract --root .`.

## Origin
- **Draft:** `wiki/draft/orca/140726-br-proactive-fill-report.md`
- **SPEC/PLAN:** [[140726-br-proactive-fill]] · `140726-br-proactive-fill-PLAN.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
