---
type: issue
kind: tech-debt
title: "skills-sync đỏ 2 ngày: sổ skill-provenance không được record sau khi sửa skill"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, ci, skill-provenance, gate]
timestamp: 2026-09-09
id: 090926-skills-sync-provenance-stale
source_session: "phiên 2026-09-09 — rà CI đỏ sau push"
---

# Issue: skills-sync đỏ 2 ngày vì sổ provenance lệch

## Bối cảnh

`skills-sync` đỏ trên `orca` từ commit `8071f3e` (2026-09-08), qua ba commit liên tiếp, mà
không ai biết — CI không có đường báo ra ngoài tab Actions. Gate đỏ là
`fdk/tools/skill-provenance.py check --ci`: checksum của `doyourmagic`, `orca-onboard`
(sửa ở `8071f3e`) và `prd-grade-fe/scripts/viewport-check.mjs` (sửa ở `1913bbc`) lệch so
với `fdk/skills.provenance.json`. Đều là sửa đổi hợp lệ của repo, không phải skill lạ.

Nguyên nhân hệ thống: **không có gì bắt cập nhật sổ khi skill đổi**, nên CI là nơi đầu
tiên biết.

## Đã làm

- `record` lại ba skill → `✓ 89 skill, checksum khớp`.
- Thêm hook pre-commit chạy đúng lệnh CI chạy, `files: ^skills/` — lệch sổ cắn tại máy
  trước khi push. Fire-drill: bẩn một `SKILL.md` → FAIL; khôi phục → PASS.
- Hai lỗ cố ý chấp nhận: máy chưa `pre-commit install`, và `--no-verify`. CI vẫn là sàn.

## Tiêu chí xong

- [x] `repro_cmd` xanh · [x] `medic --ci` 0 fail · [x] fire-drill chỗ cắn sớm
- [x] mirror `GH#144` · [x] dòng ledger này

## Origin
- **Source:** CI run `34221509712`, mirror [GH#144](https://github.com/Rheinmir/setup/issues/144)
- **Commit:** `59bc4d2`
- **Date:** 2026-09-09
