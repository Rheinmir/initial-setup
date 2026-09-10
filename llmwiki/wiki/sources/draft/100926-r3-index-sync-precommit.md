---
type: issue
kind: tech-debt
title: "R3 index-sync chỉ CI bắt: draft mới thiếu dòng index lọt qua pre-commit"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, ci, index-sync, pre-commit]
timestamp: 2026-09-10
id: 100926-r3-index-sync-precommit
source_session: "phiên 95e2c1ee — xử lý GH#150"
---

# Issue: R3 index-sync chỉ có CI gác

## Origin

CI tự mở [GH#150](https://github.com/Rheinmir/setup/issues/150): job `harness` trên `orca`
đỏ ở bước R3 index-sync, commit `8f0a24f`, log `THIEU trong index:
sources/draft/100926-install-seed-skipped-on-migrate.md`.

## Tái hiện

- Commit `52f3334` (phiên khác) thêm draft `100926-install-seed-skipped-on-migrate.md` mà
  không thêm dòng vào `llmwiki/wiki/index.md`.
- Ở HEAD `9cd53d0`: `git show HEAD:llmwiki/wiki/index.md | grep -c
  100926-install-seed-skipped-on-migrate` → `0`, tức bản đã commit đỏ thật.
- Working tree lại xanh, chỉ vì hook đã tự chèn dòng đó mà chưa ai commit. Đây là cái bẫy
  "xanh ở máy, đỏ trên CI" quen thuộc: phải so bản đã commit, không so đĩa.

## Vì sao CI là nơi đầu tiên biết

`.pre-commit-config.yaml` dời R3 sang CI theo issue #18 — bộ fire-drill đầy đủ không chạy
mỗi commit nữa. Ý đó đúng cho cả bộ, nhưng R3 rẻ (đo: 2.26 s cho `llmwiki/wiki`, 0.71 s cho
`fdk/wiki`) và lỗi của nó chỉ phát sinh khi có trang wiki mới.

## Đã làm

- Commit dòng index còn thiếu.
- Thêm hook `wiki-index-sync` vào pre-commit, **chỉ chạy khi đổi file**
  `^(fdk|llmwiki)/wiki/.*\.md$`. Giữ tinh thần #18 (không chạy cả bộ mỗi commit), vẫn chặn
  đúng lớp lỗi này.
- Fire-drill, tái hiện đúng kịch bản của issue: draft mới đã stage, index KHÔNG stage →
  `Failed`, rc=1. Stage dòng index → `Passed`, rc=0. Pre-commit stash phần chưa stage trước
  khi chạy hook, nên hook thấy đúng trạng thái sẽ được commit.

## Nợ mở, không chặn

- Prompt CI yêu cầu đổi nhãn sang `ready-for-agent`, nhưng repo chưa có nhãn đó (chỉ có
  `ready-for-human`). Chưa tự tạo nhãn.
