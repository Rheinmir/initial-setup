---
type: draft
title: 300726-hook-skill-layers
status: proposed
tags: [cursor-animated-sites, output-report]
timestamp: 2026-07-30
---

# 300726-hook-skill-layers

## What
Walkthrough tương tác (cursor đi qua cây file, tự-bước hoặc tự-chạy chậm) giải thích đúng thứ tự 8 lớp lifecycle của Claude Code + overstack khi user gõ một câu vào ô chat: SessionStart → UserPromptSubmit → Claude quyết định → nạp Skill → PreToolUse (validators) → code thật (harness/scripts) → PostToolUse → lặp lại → Stop (medic --ci) → SessionEnd, kèm 2 ví dụ THẬT đã xảy ra ngay trong hội thoại (rule R16 report-show-path chặn 1 lần Write; medic --ci FAIL vì overstack.html cũ).

## Files
| File | Action |
|------|--------|
| `llmwiki/html/300726-hook-skill-layers.html` | created |

## Notes
- Invoked via: `/cursor-animated-sites` (layer trên `/docs-site-macos`), nối tiếp câu hỏi "chính xác business flow khi gõ vào thì cross ntn" trong cùng hội thoại
- Xem tại `http://localhost:8765/llmwiki/html/300726-hook-skill-layers.html`

## Origin
- **Draft:** `wiki/sources/draft/300726-hook-skill-layers.md`
- **Commit:** _(verify-before-commit điền)_
