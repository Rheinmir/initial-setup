---
type: draft
title: Full luồng /br chạy thật trên Memos — module standalone + artifacts
status: proposed
tags: [memos, br, clone, reverse-br, pipeline, output-report]
timestamp: 2026-07-12
---

# 120726-memos-pipeline-run
**Status:** proposed · **App:** http://localhost:5230/ · 2026-07-12

## What
Chạy full luồng /br trên usememos/memos (bỏ payroll): kéo source → reverse-BR → 12 frame → UI Contract → build từ source & chạy module standalone tại :5230. KHÔNG dùng docker stock.

## Output
- Memos chạy thật từ source (pnpm release + go run) — module standalone 1 binary.
- `br/memos/br/BR.md` (13 clause reverse + 2 NFR), `br/memos/br/frames/` (12 frame), `br/memos/br/ui-layout.yaml` (8 màn), `br/memos/br/UI-CONTRACT.{md,html}` (0 lệch).
- `llmwiki/html/120726-memos-pipeline-run.html` (docs full luồng).

## Files
| File | Action |
|------|--------|
| `br/memos/br/BR.md` | created (reverse) |
| `br/memos/br/frames/*.md` | created (12) |
| `br/memos/br/ui-layout.yaml` + `UI-CONTRACT.{md,html}` | created |
| `llmwiki/html/120726-memos-pipeline-run.html` | created |

## Notes
- Reverse-BR làm TAY (gap G2 /br reverse chưa build). Microservice-by-path (frame n01) mới scoped, chưa mount thật (cần rebuild base + proxy). Source memos ở scratchpad (ephemeral).
- Invoked qua chỉ đạo user "chạy full 1 luồng với memos".

## Origin
Phiên 2026-07-12, chạy pipeline trên memos.
