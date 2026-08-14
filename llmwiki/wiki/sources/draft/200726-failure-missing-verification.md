---
type: draft
title: Candidate rule from recurring missing-verification failures
status: proposed
tags: [flywheel, draft, failure, missing-verification]
timestamp: 2026-07-20
---

# 200726-failure-missing-verification

## What
`missing-verification` recurred **5×** (threshold 3). Flywheel seeds this rule stub so the pattern becomes reusable instead of repeating. SEED — a human runs `/propose`; never auto-promoted.

## Rule (TODO — needs human distillation)
> TODO: distil the rule from these 5 `missing-verification` failures. (Distil model is the quarantined adapter — `harness/failure-flywheel.config.yaml` `distill.model` = `null`.)

## Failures observed (5)

| Summary | Seen |
|---|---|
| Tạo artifact (frontend-design-delta.md) nhưng quên wire vào luồng đọc (hallmark SKILL.md) — năng lực có mặt nh | 2026-07-18 00:05:44 |
| design-variety.py: engine viết xong, concept hứa, KHÔNG gì gọi (ca thứ 4 của lớp) — capproof bêu UNPROVEN, giả | 2026-07-18 09:30:17 |
| fnmatch glob dùng cho travel_policy_sync.py cho segment '*' vượt qua '/' — assert sai bị chính --demo self-che | 2026-07-20 17:04:18 |
| install-harness.sh đọc travel-policy.yaml lúc runtime từ $SRC (có thể là clone remote cũ) thay vì đóng băng cù | 2026-07-20 17:04:18 |
| kết luận 'BM25 auto-inject là ngõ cụt' được rút ra từ tập prompt lẫn 22.863 tool-result + 4.412 message subage | 2026-07-20 17:04:18 |

## Origin
- **Source:** `flywheel.py --kind failure --draft missing-verification` from `harness/metrics/failures.jsonl` (5 failures, recurrence >= 3).
- **Adapter:** `harness/failure-flywheel.config.yaml` (verified=True, distill.model=null).
- **Date:** 2026-07-20
