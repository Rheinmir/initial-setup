---
type: draft
title: "huong-dan-repo-files — docs site tương tác file trong repo (ai đụng gì, ở đâu)"
status: proposed
tags: [docs-site-macos, output-report, repo-guide]
timestamp: 2026-07-07
---

# 070726-huong-dan-repo-files

**Status:** proposed

## What
Docs site HTML hướng dẫn DÂY CHUYỀN loop-engineering (GH#15) — thuần scope loop, không phải bản đồ repo tổng quát. Ba mắt xích: `/br` (5 mode interview→compile→slice→run→status), `loop-runner` (vòng propose→verify→revise với 6 phanh: max_iter·budget·no_progress·escalate·diff-jail·test-hash), `checkpoint-trace` (rollback toàn lượt về mốc bất kỳ + 3 tier khả-đảo reversible/compensable/irreversible). Kèm bảng file runtime `br/` (bạn-sửa vs máy-sinh), lệnh↔file, và 6 luật giữ dây chuyền (người-là-cổng-cuối, phanh bất khả xâm phạm, prompt≠an-toàn, R6 exclusive-scope, tier-gate, lens-fill verified:false).

## Output
- `llmwiki/html/070726-huong-dan-repo-files.html` — 6 section: bản đồ dây chuyền (diagram kéo-thả raw→interview→compile→slice→run→status + checkpoint) · 5 mode /br · loop-runner 6 phanh · checkpoint & tier · file runtime & lệnh · luật dây chuyền + checklist. Mind map, theme NÚT GẠT dính đáy sidebar (2 khối dark cùng token, chống FOUC, localStorage), thang chữ COMPACT, offline self-contained, R16 full-path. **Re-scope 2026-07-07**: ghi đè bản "5 vùng repo" cũ để thuần về loop-engineering (feedback user).

## Files
| File | Action |
|------|--------|
| `llmwiki/html/070726-huong-dan-repo-files.html` | created |

## Notes
- Invoked via: `/docs-site-macos` skill.
- Áp dụng LẦN ĐẦU spec theme-toggle + font-floor mới kéo về từ upstream (merge orca 2026-07-07) — thay bản toggle tự-chế trước đó.

## Origin
Phiên 2026-07-07 (issue-15-br-k): user yêu cầu trang hướng dẫn tương tác file repo. Nguồn nội dung: cấu trúc repo thật + các tool GH#15 (br-*, checkpoint, upstream-drift) + 17 luật harness.
