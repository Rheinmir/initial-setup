---
type: entity
title: Project Structure
tags: [orca, onboarding]
timestamp: 2026-06-25
id: project-structure
---

# Project Structure

| Entry | Role |
|-------|------|
| `setup.md` | Usage instructions for the setup repo |
| `01-Project-Kickoff.md` | Kickoff prompt — asks 3 questions, emits AGENT files |
| `02-Setup-Knowledge-Base.md` | Kickoff prompt — scaffolds wiki skeleton |
| `03-Scaffold-Application.md` | Kickoff prompt — scaffolds MVP code |
| `skills/` | 32 published skills (npx-publishable) |
| `harness/` | Python guard engine — validators, scripts, policy, evals |
| `llmwiki/` | Template payload + canonical skill sources |
| `.template-manifest.json` | Sync surface for template operations |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.github/` | CI/CD workflows |

## Hot Files (by commit volume)

| File | Commits |
|------|---------|
| `docs-site-macos/SKILL.md` | 27 |
| `orca-onboard/SKILL.md` | 24 |
| `orca-workflow/SKILL.md` | 16 |
| `install-harness.sh` | 12 |

See also: [[architecture]]

## Origin

- **Source:** `.overstack/graph/ONBOARDING.md` (orca-onboard 2026-06-25)
- **Commit:** 97b0952
- **Date:** 2026-06-25
