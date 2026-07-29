---
type: issue
kind: foundation
title: "Reachability sweep: skill-shipped trỏ tool .py không ship → user gọi skill lỗi (GH#54)"
status: in-progress
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, foundation, reachability, install, skill, AP-1]
timestamp: 2026-07-05
id: 050726-reachability-sweep-skill-tools
source_session: "Audit AP-1 các issue <#20 + test guard skill→tool"
---

# Issue: reachability sweep skill→tool (GH#54)

## Vấn đề (một câu)
Nhiều skill ship xuống user (`llmwiki/skills/**`) bảo chạy `python3 harness/scripts/X.py` nhưng X.py framework-only → user gọi skill gặp tool thiếu (vd GH#9 query→mem-rank, GH#8 skill-usage).

## Điều tra & phân loại (11 tham chiếu)
- **VỠ THẬT (ship):** health-check.py, okf-check.py, sync-template.py, archetype.py, query-log.py, code-logger.py, mem-rank.py (+ dep bnal_config.py, mem-rank.config.yaml), skill-usage.py.
- **False-positive (nhắc tên, không chạy):** wiki-health.py (health-check.md "anh em cùng tầng"), build-overstack-docs.py (docs-site "xem …") — regex test siết `python3 …` tự loại.

## Đã làm
- Thêm 9 file (tool vỡ + dep) vào `.template-manifest.json`.
- Test guard `wiki-graph-user-reachability-test.sh` mục C: quét skill-shipped, chỉ bắt dạng `python3 …X.py`, assert ship. 9/9 pass. Verify install thật: 9 tool tới nơi.

## Tiêu chí HOÀN THÀNH
- [x] Mọi tool `python3 …` trong skill-shipped đều trong manifest; CI đỏ nếu tái phạm.
- [x] Install thật kéo đủ.

## Origin
- Audit + fix phiên 2026-07-05. Mirror GH#54. framework-dev-antipatterns AP-1.
