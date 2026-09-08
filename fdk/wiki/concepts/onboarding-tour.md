---
type: concept
title: Onboarding Tour
tags: [orca, onboarding]
timestamp: 2026-06-25
id: onboarding-tour
---

# Onboarding Tour

A 10-step guided tour of the setup repo:

1. **`setup.md`** — what the repo is (copy `llmwiki/`, feed 01 → 02 → 04)
2. **`01-Project-Kickoff.md`** — agent asks 3 questions, emits `AGENT-business/code.md`
3. **`02-Setup-Knowledge-Base.md`** — scaffolds wiki skeleton
4. **`03-Scaffold-Application.md`** — scaffolds MVP code
5. **`skills/` catalog** — 32 skills by loop
6. **`orca-workflow`** — hottest orchestration skill (16 commits); propose → gate → dispatch
7. **`orca-onboard`** — this onboarding pipeline (24 commits)
8. **`docs-site-macos`** — HOTTEST file overall (27 commits, 50KB); glassmorphism HTML doc generator
9. **`harness/validators/*.py`** — deterministic guard engine (Origin required, no raw writes)
10. **`install-harness.sh` + `sync-template.py`** — install & keep downstream projects in sync

See also: [[architecture]]

## Origin

- **Source:** `.overstack/graph/ONBOARDING.md` (orca-onboard 2026-06-25)
- **Commit:** 97b0952
- **Date:** 2026-06-25
