---
type: issue
kind: tech-debt
title: "index_sync xanh ở máy đỏ trên CI: index.md trỏ file chưa git add"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, ci, index-sync, fresh-clone]
timestamp: 2026-09-09
id: 090926-index-sync-untracked-hole
source_session: "phiên 2026-09-09 — vòng ci-raise-issue chạy thật lần đầu"
---

# Issue: lỗ untracked của index_sync

## Bối cảnh

Ngay sau khi đẩy vòng `ci-raise-issue`, `harness` đỏ ở bước R3 index-sync và vòng mới
dựng **tự mở [GH#145](https://github.com/Rheinmir/setup/issues/145)** — lần chạy thật đầu
tiên, đúng như thiết kế.

Thủ phạm: `llmwiki/wiki/index.md` có dòng trỏ `sources/090926-session-provenance.md` mà
file chưa `git add`. Máy tác giả có file trên đĩa nên xanh; fresh clone không có nên đỏ.
Docstring của `gitignored()` vốn khai mục tiêu "nhất quán giữa máy tác giả và clone sạch",
nhưng `content_files()` vẫn đếm file untracked-không-ignore.

Issue này cũng lộ một bẫy trong chính công cụ mới: `repro_cmd` chỉ rút **dòng đầu** của
một step chạy hai lệnh, chạy lại thấy xanh, suýt kết luận nhầm "khác biệt môi trường".

## Đã làm

- `tracked()` đọc git index (file vừa `git add` đã tính); file chưa add bị loại khỏi
  `content_files` → đỏ ở máy đúng như đỏ trên CI. Fire-drill 3 bước.
- **Sửa lần hai**: tập tracked **rỗng** phải coi như không có git.
  `harness/tests/stop-hook-all-wikis-test.sh` copy cây wiki sang `mktemp` rồi `git init`
  mà không add — ở đó "chưa add" không đồng nghĩa "clone sạch không thấy", và luật mới
  báo THỪA toàn bộ index. Sai ở giả định, không ở ý tưởng.
- Parser rút **trọn khối lệnh** tới mốc `shell:`/`env:`/`##[endgroup]`; `##[error]` không
  phải mốc kết vì phần trước nó là output. self-test 4/4 → 6/6.
- Wire `ci-fail-parse --self-test` vào `fdk-gate` (bnal-selftest đã cắn drift).

## Nợ mở, không chặn

`fdk-gate` còn hai step đỏ **có từ trước phiên này** (đã kiểm tại `ddd366d`): L4
wiki-health và task-lifecycle (`080926-prd-grade-fe-PLAN.md` trỏ task `T-260908-01` không
có trong `tasks.json`). Chưa đụng.

## Tiêu chí xong

- [x] tái hiện được đỏ · [x] `repro_cmd` xanh · [x] `medic --ci` 0 fail
- [x] fire-drill · [x] CI xanh tại `4171c2b` · [x] dòng ledger này

## Origin
- **Source:** CI run `34334849594` + `34336381799`, mirror [GH#145](https://github.com/Rheinmir/setup/issues/145)
- **Commit:** `e123005`, `4171c2b`
- **Date:** 2026-09-09
