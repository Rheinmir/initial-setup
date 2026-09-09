---
type: issue
kind: foundation
title: "Thống nhất install: bootstrap/install.sh kéo file-list từ manifest → ship engine + wire llmwiki hooks"
status: in-progress
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, foundation, install, bootstrap, wiki-graph]
timestamp: 2026-07-05
id: 050726-unify-install-manifest
source_session: "Cài thật 5 dự án test → lộ bootstrap không ship engine"
---

# Issue: thống nhất install path qua manifest

## Vấn đề (một câu)
`bootstrap.sh`/`install.sh` (one-liner chính thức) không ship engine wiki-graph + không wire root `.claude/settings.json` tới `llmwiki/.claude/hooks/stop.py` → wiki-graph không bao giờ regen ở downstream; chỉ `sync-template`/manifest có.

## Bối cảnh & bằng chứng
- Cài thật `curl .../bootstrap.sh | bash --full` vào 1-webservice: Stop hook wire tới `harness/poc-vendor-neutral/bin/harness-events.py`, KHÔNG có `stop.py` regen lẫn `fdk/tools/build-wiki-graph.py`.
- Root settings (Claude Code đọc) không trỏ llmwiki hooks; manifest chỉ ship `llmwiki/.claude/settings.json` (không được đọc ở root).

## Hướng đã làm (bản này)
- `install.sh --with-wiki`: kéo TOÀN BỘ file-list từ `.template-manifest.json` (infra fdk/tools + llmwiki/.claude luôn refresh; còn lại chỉ khi thiếu) → có engine + llmwiki hooks.
- Merge wiring llmwiki hooks vào ROOT `.claude/settings.json` (dạng `$CLAUDE_PROJECT_DIR/llmwiki/.claude/hooks/<ev>.py`, idempotent, giữ harness-events).

## Tiêu chí HOÀN THÀNH
- [x] Sau `--with-wiki`: engine + stop.py có mặt; root settings wire stop.py (giữ harness-events).
- [x] End-to-end: opt-in + code đổi → wiki-graph.html tự sinh, tôn trọng .overstack.yaml.

## Origin
- Raise + implement phiên 2026-07-05. Mirror: GH#51.
