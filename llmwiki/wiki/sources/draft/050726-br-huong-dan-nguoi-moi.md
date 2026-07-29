---
type: draft
title: "br-huong-dan-nguoi-moi — docs site hướng dẫn /br cho người mới (có ảnh chụp)"
status: proposed
tags: [docs-site-macos, output-report, br, issue-15, guide]
timestamp: 2026-07-05
---

# 050726-br-huong-dan-nguoi-moi

**Status:** proposed

## What
Docs site HTML hướng dẫn từng bước, dễ hiểu cho người mới bắt đầu dùng chức năng `/br` (dây chuyền Ralph), kèm "ảnh chụp màn hình" minh hoạ (mockup macOS: cửa sổ Terminal + trình duyệt) dựng lại từ output CHẠY THẬT của công cụ.

## Output
- `llmwiki/html/050726-br-huong-dan-nguoi-moi.html` — 6 section: /br là gì · Chuẩn bị (raw/) · 5 bước dùng · Đọc màn hình status · Hỏi&đáp (FAQ collapse) · Checklist sẵn sàng. Có mind map, 4 "ảnh chụp" mockup (Terminal chuẩn bị · trang câu hỏi interview · Terminal run · trang line-status), checklist tick được, dark-mode, R16 full-path, offline self-contained.
- "Ảnh chụp" line-status dựng theo dữ liệu THẬT: demo 3 frame (1 xanh · 1 kẹt + diff-jail cắn + clause assumed S4.2 · 1 chưa chạy) chạy qua `build-line-status.py`.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/050726-br-huong-dan-nguoi-moi.html` | created |

## Notes
- Invoked via: `/docs-site-macos` skill.
- "Ảnh chụp màn hình" là mockup HTML/CSS trung thực (không phải PNG rời) để giữ self-contained; nội dung transcribe từ output thật (selftest + build-line-status trên demo br/).
- Bổ trợ cho tài liệu kỹ thuật `050726-ralph-pipeline-docs.html` (bản này dành cho NGƯỜI DÙNG mới, không cần biết code).

## Origin
Phiên GH#15 2026-07-05 (issue-15-br-k): user yêu cầu render HTML hướng dẫn cho người mới, có ảnh chụp màn hình. Nền: [[050726-ralph-pipeline-build]] · skill `br`.
