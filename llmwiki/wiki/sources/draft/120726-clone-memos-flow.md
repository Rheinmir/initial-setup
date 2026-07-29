---
type: draft
title: Luồng clone Memos thành module/microservice — reference flow + gap analysis
status: proposed
tags: [memos, clone, pipeline, docs-site-macos, gap-analysis, self-improve, output-report]
timestamp: 2026-07-12
---

# 120726-clone-memos-flow
**Status:** proposed
**Proposed:** 2026-07-12

## What
Reference flow I→O để clone Memos (usememos/memos) thành module chạy độc lập + microservice-by-path qua pipeline /br; mỗi step gắn slash command; tự phát hiện điểm thiếu (slash chưa có) + đề xuất tự cải tiến. Docs-site làm tài liệu tham khảo/tinh chỉnh.

## Output
- `llmwiki/html/120726-clone-memos-flow.html` — 6 section: mục tiêu I→O · bản đồ 7 bước · từng step+slash · standalone+microservice-by-path · gap & tự cải tiến · trạng thái thật.
- Phân tích thật (đã kéo repo shallow): Go backend :8081 + React19/Vite, 1-binary serve (pnpm release nhúng SPA). Gap kỹ thuật: memos không có native sub-path → microservice-by-path phải patch Vite base + reverse-proxy.
- **3 gap lệnh tự phát hiện:** G1 `/br ingest-repo`, G2 `/br reverse` (chưng BR ngược từ code), G3 `/modularize` (đóng gói module+microservice).

## Files
| File | Action |
|------|--------|
| `llmwiki/html/120726-clone-memos-flow.html` | created |
| (scratchpad) `memos-src` | shallow clone (ephemeral, không track) |

## Notes
- TRUNG THỰC: mới kéo repo + phân tích + thiết kế luồng; CHƯA clone thành app chạy. 2/7 bước DONE, 3 PLANNED, 2 GAP.
- Pipeline /br thiết kế build-xuôi-từ-BR → clone-ngược-từ-repo lộ 2 gap (reverse BR, ingest repo).
- Invoked via: `/docs-site-macos`.

## Origin
- **Draft:** `wiki/sources/draft/120726-clone-memos-flow.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
