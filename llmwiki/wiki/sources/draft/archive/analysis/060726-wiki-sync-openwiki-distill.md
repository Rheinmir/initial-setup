---
type: draft
title: wiki-sync — distill openwiki (neo code→wiki + no-op gate + cron PR)
status: implemented
tags: [wiki-loop, harness, frontier, output-report]
timestamp: 2026-07-06
---

# 060726-wiki-sync-openwiki-distill

**Type:** draft
**Status:** implemented
**Tags:** fdk, wiki-loop, frontier, output-report
**Proposed:** 2026-07-06

## What
Đối chiếu openwiki (langchain-ai, 07/2026) rồi distill 3 cái hay của họ, nấu lại theo khẩu vị overstack, để 4 trục họ từng hơn ("code→wiki drift detection", "no-op gate 0 token + content-hash", "cron→PR không người trông", "chi phí nhập cuộc thấp") đều được phủ — frontier chỉ hơn không kém.

## Output
1. **`harness/scripts/wiki-sync.py`** — neo `<wiki>/.last-sync.json` (gitHead + content-hash). `--check`: cổng no-op tất định (code không đổi kể từ neo → exit 0, 0 token; đổi → map file-đổi→trang-wiki-nhắc-tới, cờ `code-drift` vào `stale.json` cùng schema + flock với wiki_ledger, exit 3; neo hỏng sau rebase → exit 2). `--mark-synced`: chỉ ghi neo khi nội dung wiki thực sự đổi (chống churn cron), tự xoá cờ code-drift đã rà. Test: `harness/tests/wiki-sync-test.sh` (8/8, sandbox git tạm).
2. **`session_start.py` + hàm `wiki_drift`** — đầu phiên in 1 dòng nếu HEAD vượt neo N commit (trước early-exit manifest để downstream v4 cũng nhận; fail-open tuyệt đối).
3. **Skill `/lint`** — bước 0 code-drift gate (no-op → "wiki đã current" là kết quả hợp lệ), bước 9 chốt neo; Rules thêm kỷ luật surgical: docs-impact-plan, soft diff budget, cấm formatting-only, canonical home. **Skill `/ingest`** — docs-impact-plan ở bước 2 + canonical-home + surgical trên trang có sẵn. Sync đủ 3 bản qua `sync-skill.sh`.
4. **`gen-converters.py`** sinh thêm `out/ci/wiki-refresh.yml` — cron daily downstream: self-install harness → wiki-sync check (0 token) → có `ANTHROPIC_API_KEY` thì `claude -p` sửa surgical, không key vẫn PR cờ tất định → PR chỉ diff wiki.
5. **`.template-manifest.json`** thêm `harness/scripts/wiki-sync.py` — downstream nhận qua bộ cài sẵn có, không thêm bước cài.
6. **`overstack.html`** (qua `build-overstack-docs.py`) — mục Wiki viết lại đầy đủ: staleness 2 chiều, vận hành không người trông, kỷ luật surgical, truy hồi nhiều tầng, kèm đối chiếu thẳng thắn với openwiki (cả giới hạn: heuristic nhắc-tên thiên bắt-thừa, CI LLM cần key).

## Files
| File | Action |
|------|--------|
| `harness/scripts/wiki-sync.py` | created |
| `harness/tests/wiki-sync-test.sh` | created |
| `llmwiki/.claude/hooks/session_start.py` | modified |
| `skills/lint/SKILL.md` (+ mirror + bản cài) | modified |
| `skills/ingest/SKILL.md` (+ mirror + bản cài) | modified |
| `harness/poc-vendor-neutral/gen-converters.py` | modified |
| `harness/poc-vendor-neutral/out/ci/wiki-refresh.yml` | generated |
| `.template-manifest.json` | modified |
| `fdk/tools/build-overstack-docs.py` → `llmwiki/html/overstack.html` | modified / regenerated |
| `llmwiki/html/fdk-problem-tree.html` | node p-22 appended |

## Notes
- Invoked via: `/fdk` skill (distill từ so sánh openwiki — clone đọc source `src/agent/utils.ts`, `prompt.ts`).
- Trục overstack vốn hơn giữ nguyên: provenance (Origin/ledger/log), validator nội-wiki, độ tươi trong phiên, đa phiên (flock), gắn dev-loop.
- Điều kiện ship do user đặt: qua bài test 5 project bằng orca-cli + /orchestration trước khi commit.
- Liên quan: [[frontier-gap-scan]], [[harness-enforcement-floor]]

## Origin
- **Draft:** `wiki/sources/draft/060726-wiki-sync-openwiki-distill.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
