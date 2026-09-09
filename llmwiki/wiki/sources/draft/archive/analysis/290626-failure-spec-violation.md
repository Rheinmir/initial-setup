---
type: draft
title: Candidate rule from recurring spec-violation failures
status: proposed
tags: [flywheel, draft, failure, spec-violation]
timestamp: 2026-06-29
---

# 290626-failure-spec-violation

## What
`spec-violation` recurred **3×** (threshold 3). Flywheel seeds this rule stub so the pattern becomes reusable instead of repeating. SEED — a human runs `/propose`; never auto-promoted.

## Rule (TODO — needs human distillation)
> TODO: distil the rule from these 3 `spec-violation` failures. (Distil model is the quarantined adapter — `harness/failure-flywheel.config.yaml` `distill.model` = `null`.)

## Failures observed (3)

| Summary | Seen |
|---|---|
| R3 scanner harness-events.py m_stop khong skip gitignored -> Stop-hook nag tren file archive | 2026-06-28 19:09:44 |
| R3 scanner audit.py detect khong skip gitignored -> 18 archive false-positive; audit --fix se nhoi 18 file vao | 2026-06-28 19:09:44 |
| R9 scanner okf-check.py content_files khong skip gitignored (latent) | 2026-06-28 19:09:44 |

## Origin
- **Source:** `flywheel.py --kind failure --draft spec-violation` from `harness/metrics/failures.jsonl` (3 failures, recurrence >= 3).
- **Adapter:** `harness/failure-flywheel.config.yaml` (verified=True, distill.model=null).
- **Date:** 2026-06-29
