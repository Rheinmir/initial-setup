---
type: concept
title: Architecture — setup repo
tags: [orca, onboarding]
timestamp: 2026-06-25
id: architecture
---

# Architecture — setup repo

The repo is NOT an app; it is the **Orca template/skill/harness ecosystem** (Markdown + Python + Shell). 4 layers:

## 1. 3-Step Kickoff Prompts (9 root files)

- `setup.md` — entry point
- `01-Project-Kickoff.md` — agent asks 3 questions → emits `AGENT-business/code.md`
- `02-Setup-Knowledge-Base.md` — scaffolds wiki skeleton
- `03-Scaffold-Application.md` — scaffolds MVP code
- `RESTRUCTURE.md`, `CLAUDE.md`, `.agent`, `.template-manifest.json`

## 2. Published Skills (32 SKILL.md under `skills/`)

Installed via `npx skills add rheinmir/setup`, grouped by loop:

- **wiki-loop**: ingest, query, lint
- **dev-loop**: propose, impact-check, safe-change, verify-before-commit, onboard-codebase, new-project-setup
- **orchestrate**: orca-workflow, orca-onboard, orca-sec-scans, orca-dispatch-reference
- **utils**: caveman family ×7, sync-template, docs-site-macos, md-to-html, harness-tour, harness-update, tour-guide

Canonical source lives in `llmwiki/skills/<loop>/*.md`; `skills/<name>/SKILL.md` are npx-publishable mirrors.

## 3. Harness — Python Guard Engine (25 files under `harness/`)

Deterministic, NO LLM:

- **validators/** — `no_write_raw`, `origin_required`, `okf_frontmatter`, `index_sync`, `folder_structure`, `proposal_complete` — block bad writes at hook layer
- **scripts/** — `install-harness.sh`, `sync-template.py`, `health-check.py`, `okf-check.py`, `audit.py`
- `policy.yaml` + `version.json`
- **evals/** (promptfoo) + **tests/**

## 4. Repo Meta & CI (5 files)

`.github/`, `.claude/`, `.claude-plugin/`, `.pre-commit-config.yaml`

See also: [[onboarding-tour]], [[project-structure]]

## Origin

- **Source:** `.overstack/graph/ONBOARDING.md` (orca-onboard 2026-06-25)
- **Commit:** 97b0952
- **Date:** 2026-06-25
