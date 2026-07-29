---
type: draft
title: codebase-map-payroll — render CODEBASE-MAP.md thành docs-site
status: proposed
tags: [docs-site-macos, output-report, br, payroll, ground-truth]
timestamp: 2026-07-12
---

# 120726-codebase-map-payroll
**Status:** proposed
**Proposed:** 2026-07-12

## What
Render `br/payroll/docs/CODEBASE-MAP.md` thành site macOS-style single-file HTML — giải thích ground-truth + bản đồ dây chuyền /br (6 phần) để user tự hiểu lại codebase.

## Output
Trang HTML self-contained (glass light-blue, sidebar nav, mind map, 1 sequence diagram kéo-thả, theme toggle, code-copy, a11y) gồm 6 section: ground-truth là gì · dây chuyền /br · cây thư mục · component mẫu p13 · bộ gác frame-lint R1–R9 + manifest + loop-cost · đang ở đâu/kế tiếp.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/120726-codebase-map-payroll.html` | created |
| `br/payroll/docs/CODEBASE-MAP.md` | nguồn (phiên trước) |

## Notes
- Invoked via: `/docs-site-macos` skill
- Auto-host: `http://localhost:8765/llmwiki/html/120726-codebase-map-payroll.html`

## Origin
- **Draft:** `wiki/sources/draft/120726-codebase-map-payroll.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
