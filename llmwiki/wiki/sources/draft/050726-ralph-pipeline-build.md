---
type: draft
title: "ralph-pipeline-build — thi công step 1–4 dây chuyền Ralph + docs site (GH#15)"
status: proposed
tags: [ralph, br, docs-site-macos, build-report, issue-15]
timestamp: 2026-07-05
---

# 050726-ralph-pipeline-build

**Status:** proposed
**Type:** build-report (đồ nghề đã dựng + selftest xanh — KHÁC 4 proposal thiết kế trước đó).

## What
Thi công đồ nghề tất định cho cả 4 step dây chuyền Ralph (GH#15) theo plan council 031/032, cộng một docs site HTML (dựng bằng /docs-site-macos) vẽ toàn dây chuyền + nội dung wiki + nhật ký deviation.

## Output
- Hub skill `/br` (5 mode: interview · compile · slice · run · status) — đăng ký đủ 6 mặt, medic xanh.
- 4 đồ nghề tất định, mỗi cái selftest xanh:
  - `frame-lint.py` — 5 luật (schema · scope · test-first · freshness · DAG), 6 fixture BAD/GOOD.
  - `loop-runner.py` — thêm 2 phanh (guard 5 diff-jail + guard 6 test-hash PROTECT_VIOLATION exit 6), 7 kịch bản.
  - `build-line-status.py` — monitor tất định (5 trạng thái + traceback + `--check`).
  - `spec-template.md` — bộ specs chuẩn S1–S10.
- Docs site: `llmwiki/html/050726-ralph-pipeline-docs.html` (mind map + 5 diagram kéo-thả + wiki content + nhật ký deviation, offline, dark-mode, R16 full-path).

## Files
| File | Action |
|------|--------|
| `skills/br/SKILL.md` + mirror `llmwiki/skills/dev-loop/br.md` | created |
| `skills/br/assets/spec-template.md` | created |
| `fdk/tools/frame-lint.py` | created |
| `fdk/tools/build-line-status.py` | created |
| `harness/scripts/loop-runner.py` | modified (guard 5+6 + selftest 5→7) |
| `harness/loop-runner.config.yaml` | modified (scope section) |
| `harness/scripts/sync-skills.py` | modified (LOOP_MAP += br) |
| `fdk/tools/build-overstack-docs.py` | modified (LOOP_GROUPS += br) |
| `.claude-plugin/marketplace.json` · `llmwiki/AGENT.md` · `llmwiki/CLAUDE.md` | modified (đăng ký br) |
| `fdk/CAPABILITIES.md` · `llmwiki/html/overstack.html` | regenerated |
| `llmwiki/html/050726-ralph-pipeline-docs.html` | created (docs site) |

## Notes
- Invoked via: `/docs-site-macos` (docs) + `/fdk` (thi công framework).
- Deviation so với plan (ghi trong docs mục 06): frame-lint dùng fnmatch (không pathlib `**`); diff-jail tận dụng no-progress sẵn có (scope==state); monitor đọc `BR.clauses.json` tất định; đăng ký skill cần 6 mặt.
- CHƯA làm (việc kế): chạy 1 BR THẬT đi trọn dây chuyền (cần user chọn tài liệu vào `raw/`) + demo 1 lần cố tình phá scope để chứng minh phanh cắn trên đường thật; wire adapter `claude -p` (`verified:false`).
- medic `--ci`: 0 fail (warn "pre-commit chưa cài" là môi trường có sẵn, không liên quan).

## Agent Task Assignment
- Claude (phiên /fdk, nhánh issue-15): đã dựng đồ nghề + selftest + docs. Bước kế = end-to-end 1 BR thật sau khi user duyệt + cung cấp tài liệu.
- User: xem docs site, chọn project/tài liệu mẫu cho lần chạy thật.

Sequence diagram: xem `llmwiki/html/050726-ralph-pipeline-docs.html`.

## Origin
Phiên GH#15 2026-07-05 (issue-15-br-k): user chỉ đạo /docs-site-macos + thi công step 1–4. Nền: [[050726-ralph-interview-pipeline]] · [[050726-ralph-slice-frames]] · [[050726-ralph-loop-gate]] · [[050726-ralph-monitor]] · council-report-032.
