---
type: draft
title: UI Contract — form chuẩn frame↔screen↔route (md+html) cho mọi dự án /br
status: proposed
tags: [br, ui-contract, frame, screen, route, issue-15, output-report]
timestamp: 2026-07-12
---

# 120726-ui-contract
**Status:** proposed
**Proposed:** 2026-07-12

## What
Form tổng cấu-trúc-cố-định (contract chốt thực hiện) cho mọi dự án /br: mỗi frame làm gì · UI hoạt động ra sao · frame nào cùng màn · bao nhiêu route thật. Tách trục CODE (frame) khỏi trục HIỂN THỊ (screen/route). Xuất song song md (canonical) + html (review).

## Output
- `frame-template.md`: thêm frontmatter `ui_role` (none|screen|panel|widget|form|action) + `ui_screen`, và section body "## UI hoạt động ra sao".
- `br/ui-layout.yaml` (shape chuẩn project-level): `nav_style` + `screens[]` (id·title·route·frames[]). Sửa file này gom màn không đụng frame.
- Tool `fdk/tools/br-contract.py`: build → `br/UI-CONTRACT.md` + `br/UI-CONTRACT.html` (neumorphic, theme toggle, R16 abs-path). Join 2 trục, đếm frame/màn/route, validate lệch (ghost frame · ui_screen lệch · UI chưa gán màn). selftest offline.
- Skill `br.md`: Mode 7 `/br contract`.
- Chạy thật payroll: 31 frame · 7 màn · 7 route · 0 lệch.

## Files
| File | Action |
|------|--------|
| `skills/br/assets/frame-template.md` | modified (ui_role/ui_screen + UI section) |
| `br/payroll/br/ui-layout.yaml` | created (starter grouping) |
| `fdk/tools/br-contract.py` | created |
| `br/payroll/br/UI-CONTRACT.{md,html}` | generated |
| `llmwiki/skills/dev-loop/br.md` | modified (Mode 7) |

## Notes
- Frame ≠ screen: frame = biên giới code (frame-lint gác); screen = gom hiển thị (ui-layout.yaml). 1 screen ⊇ nhiều frame, tách trục nên regroup không re-slice.
- Invoked via: tích hợp thủ công theo yêu cầu user.

## Origin
- **Draft:** `wiki/sources/draft/120726-ui-contract.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
