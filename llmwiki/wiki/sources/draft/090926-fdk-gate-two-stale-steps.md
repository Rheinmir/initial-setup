---
type: issue
kind: tech-debt
title: "fdk-gate 2 step đỏ tồn từ ddd366d: wikilink trỏ mirror skills đã bỏ + task chưa đăng ký; kéo theo R7 trên 2 proposal cũ"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, ci, fdk-gate, wiki-health, task-lifecycle, r7]
timestamp: 2026-09-09
id: 090926-fdk-gate-two-stale-steps
source_session: "phiên 2026-09-09 — user: 'tiến hành xử luôn đừng raise gì cả'"
---

# Issue: fdk-gate 2 step đỏ tồn từ ddd366d

## Bối cảnh

`fdk-gate` (pre-push) đỏ 2/21 step **từ trước phiên** (kiểm tại `ddd366d`): L4 wiki-health
và task-lifecycle. Push trước đó vẫn lọt vì hook pre-push không cắn trên máy này.

- **wiki-health**: `ddd366d` bỏ `llmwiki/wiki/skills` (mirror thứ ba, cố ý) nhưng 6 file
  wiki vẫn `[[failure-flywheel]] [[fdk]] [[trace-grader]] [[hallmark]] [[docs-site-macos]]
  [[playwright-verify]]` → 9 wikilink hỏng; `[[adapt-modes-taxonomy]]` trỏ trang đã đổi tên.
- **task-lifecycle**: `080926-prd-grade-fe-PLAN.md` trỏ `T-260908-01` không có trong
  `harness/metrics/tasks.json`.

## Đã làm

- Wikilink → link tương đối tới bản canonical `skills/<name>/SKILL.md` (kiểm từng đường
  dẫn tồn tại); `[[adapt-modes-taxonomy]]` → `[[adapt-modes]]`. Commit `e2314dc`.
- Backfill `T-260908-01` đủ chuỗi proposed→approved→dispatched→done theo tiền lệ GH#108.
- **Hệ quả bậc hai** — CI tự mở [GH#146](https://github.com/Rheinmir/setup/issues/146):
  chạm 2 draft 03/07 (chỉ thay wikilink) làm job "validate .md đổi" soi chúng bằng R7 và
  báo thiếu `## Global constraints`. Cả hai đã ship (medic chạy mỗi phiên; v1.0.6 harden
  dưới v1.1.0). Đổi status `implemented` **chưa đủ**: rule R7 trong `policy.yaml` là
  `when_contains: ["## Plan", "proposed"]` — soi chuỗi toàn file, không đọc frontmatter.
  Thêm mục `## Global constraints` ngắn ghi rõ lý do. Commit `8adbca1`.
- Bẫy công cụ ghi lại: `sed '0,/re/s//x/'` là cú pháp GNU, BSD sed **nuốt im lặng** — một
  lần commit hụt vì thế; đổi sang python.

## Tiêu chí xong

- [x] tái hiện đỏ (fdk-gate 19/21, R7 local) · [x] fdk-gate 21/21 · [x] `medic --ci` 0 fail
- [x] CI xanh tại `8adbca1` (harness + skills-sync) · [x] dòng ledger này

## Origin
- **Source:** fdk-gate tại `ddd366d`; CI run harness cho `e2314dc`, mirror [GH#146](https://github.com/Rheinmir/setup/issues/146)
- **Commit:** `e2314dc`, `8adbca1`
- **Date:** 2026-09-09
