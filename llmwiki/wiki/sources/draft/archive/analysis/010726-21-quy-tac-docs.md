---
title: 010726-21-quy-tac-docs
type: draft
status: proposed
tags: [docs-site-macos, output-report]
proposed: 2026-07-01
id: 010726-21-quy-tac-docs
---

# 010726-21-quy-tac-docs
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-07-01

## What
Render tài liệu `raw/best-pratice.md` ("21 Quy Tắc Không Thể Phá Vỡ") thành một trang HTML macOS-style self-contained, bóc tách và giải thích từng quy tắc mà user đánh dấu "không rõ".

## Output
- Một file HTML self-contained (liquid-glass, sidebar nav + collapse + ripple, mind map collapsible, 3 section theo nhóm quy tắc, 2 diagram node-draggable, copy button, scroll-spy, a11y skip-link/focus-ring/reduced-motion).
- Nội dung chia 3 nhóm đúng theo nguồn:
  - **Code (#1–#10):** localDb.ts mỏng, cấm eval/new Function, không SQL thô (src/lib/db), không nuốt lỗi SSE, validate Zod, không né Husky.
  - **Bảo mật (#11–#20):** resolvePublicCred, buildErrorBody, env option (command injection), CodeQL alert, isLocalOnlyPath (spawn process), PII redaction opt-in.
  - **Quy trình (#19–#21):** worktree, 2 runner (test:unit + test:vitest), release-freeze, tiền tố nhánh + Conventional Commits.
- Mỗi rule nêu *nó là gì* + *tại sao cấm/bắt buộc*, kèm ví dụ code ❌/✅.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/010726-21-quy-tac.html` | created |

## Notes
- Invoked via: `/docs-site-macos` skill
- Nguồn nội dung: `llmwiki/raw/best-pratice.md` (không sửa raw/).
- Các hàm `resolvePublicCred()` / `buildErrorBody()` / `isLocalOnlyPath()` mô tả theo doc; file raw có thể import từ dự án Overstack khác — chưa verify tồn tại trong repo này.
- Preview: `http://localhost:8765/llmwiki/html/010726-21-quy-tac.html`

## Origin
- **Draft:** `wiki/sources/draft/010726-21-quy-tac-docs.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
