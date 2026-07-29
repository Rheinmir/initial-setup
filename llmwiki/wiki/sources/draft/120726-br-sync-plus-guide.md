---
type: draft
title: br-sync (ccpm distill) + cẩm nang dùng /br
status: proposed
tags: [br, ccpm, github-issues, docs-site-macos, output-report, issue-15]
timestamp: 2026-07-12
---

# 120726-br-sync-plus-guide
**Status:** proposed
**Proposed:** 2026-07-12

## What
Tích hợp 1 năng lực từ `automazeio/ccpm` (GitHub Issues coordination) vào /br dưới dạng mode `/br sync` — nối từng frame ↔ GitHub sub-issue; kèm cẩm nang HTML đầy đủ cách dùng dây chuyền /br.

## Output
- Tool `fdk/tools/br-sync.py`: sync (tạo sub-issue + issue-mapping.json, idempotent, --dry-run, --epic), status, selftest (5 case offline fake gh). Tái dùng `parse_frontmatter` của frame-lint. KHÔNG làm lại provenance (clause_id/manifest đã sâu hơn ccpm).
- Skill `br.md` thêm Mode 6.
- Cẩm nang `llmwiki/html/120726-huong-dan-br-pipeline.html` (6 section: /br là gì · vòng đời 6 mode · chạy thử A→Z · bộ gác & tool · sự cố & trạng thái · thuật ngữ).

## Files
| File | Action |
|------|--------|
| `fdk/tools/br-sync.py` | created |
| `llmwiki/skills/dev-loop/br.md` | modified (Mode 6) |
| `llmwiki/html/120726-huong-dan-br-pipeline.html` | created |

## Notes
- Đối chiếu ccpm: /br đã có/hơn về spec-first + traceability + worktree + gate; GAP thật là lớp sync GitHub Issues → br-sync lấp đúng đó.
- Chưa tạo issue thật trên repo (chỉ dry-run 31 frame). Tạo issue = hành động ra-ngoài, cần xác nhận.
- Invoked via: `/docs-site-macos` (cẩm nang) + tích hợp thủ công (br-sync).

## Origin
- **Draft:** `wiki/sources/draft/120726-br-sync-plus-guide.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
