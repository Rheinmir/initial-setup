---
type: draft
title: 020726-docs-site-fdk-strategy — render concept fdk-dev-strategy thành docs site HTML
tags: [docs-site-macos, output-report, fdk]
timestamp: 2026-07-02
id: 020726-docs-site-fdk-strategy
---

# 020726-docs-site-fdk-strategy
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-07-02

## What
Render trang concept `fdk-dev-strategy` (8 nguyên tắc "Mongol pattern" cho phát triển framework) thành docs site HTML một file theo design system liquid-glass macOS.

## Output
- Site 1 file HTML self-contained (không request ngoài): hero gradient, mind map collapsible kiểu NotebookLM (8 nguyên tắc theo 4 nhóm + nhánh Cách dùng), 6 section theo cycle màu Apple secondary, 4 diagram SVG kéo-thả node (propose→gate→dispatch, đơn vị 10/100/1000, intelligence→OSS, hậu cần→ship), 2 bảng (checklist review proposal, liên kết wiki), sidebar kính có collapse + ripple, scrollbar overlay tự ẩn, a11y đầy đủ (skip-link, focus-visible, reduced-motion).
- Footer chứa đường dẫn tuyệt đối của file (R16).
- Preview: `http://localhost:8765/llmwiki/html/020726-fdk-dev-strategy.html`

## Files
| File | Action |
|------|--------|
| `llmwiki/html/020726-fdk-dev-strategy.html` | created |
| `llmwiki/wiki/sources/draft/020726-docs-site-fdk-strategy.md` | created |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/log.md` | modified |

## Notes
- Invoked via: `/docs-site-macos` skill, arg = `fdk/wiki/concepts/fdk-dev-strategy.md`

## Origin
- **Draft:** `wiki/sources/draft/020726-docs-site-fdk-strategy.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
