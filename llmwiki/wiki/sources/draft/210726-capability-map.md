---
type: draft
title: "Bản đồ quan hệ: năng lực framework ↔ vấn đề đã biết"
status: proposed
tags: [docs-site-macos, output-report, capability-map, problem-tree, isolation]
timestamp: 2026-07-21
---

# 210726-capability-map

## What
Dựng trang đối chiếu 3 nguồn dữ liệu thật (travel-policy.yaml, LOOP_GROUPS trong build-overstack-docs.py, fdk-problem-tree.html) để trả lời câu hỏi: các năng lực framework hiện có đủ cô lập với nhau không.

## Output
Kết luận, đo bằng số chứ không suy diễn:
- 61% (25/41) node vấn đề có ghi scope chạm ≥2 trụ (harness/skills/llmwiki); 12/41 chạm cả 3.
- `stop.py` là điểm hội tụ vật lý của 10 tool riêng biệt, chạy tuần tự — không cô lập theo runtime.
- Taxonomy skill trong `llmwiki/CLAUDE.md` ("wiki-loop", 5 skill) và taxonomy trong code (`LOOP_GROUPS`, chỉ 3 nhóm) đã lệch nhau — 7/83 skill rơi ngoài mind map tự sinh.
- Tầng 3 `framework_only` (16 mục) chỉ mới có validator gác ranh giới từ hôm nay (`travel_policy_sync.py`, bước 0 phiên trước).

**Verdict:** chưa đủ cô lập — ranh giới tồn tại trên giấy (travel-policy 3 tầng, LOOP_GROUPS 3 nhóm) nhưng rò ở đúng chỗ quan trọng nhất.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/210726-capability-map.html` | created |
| `llmwiki/wiki/sources/draft/210726-capability-map.md` | created (report này) |

## Notes
- Invoked via: `/docs-site-macos` skill
- Dữ liệu đọc trực tiếp lúc dựng trang, không hardcode số cũ: `harness/travel-policy.yaml`, `fdk/tools/build-overstack-docs.py` (LOOP_GROUPS), `llmwiki/html/fdk-problem-tree.html` (#tree-data, 67 node).
- Preview: `http://localhost:8765/llmwiki/html/210726-capability-map.html`

## Origin
- **Draft:** `wiki/sources/draft/210726-capability-map.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
