---
type: draft
title: "Gộp trùng lặp: web-clone Mode B vs extract-site Mode 3"
status: proposed
tags: [web-clone, extract-site, dedup, skill-maintenance]
timestamp: 2026-07-23
---

# 230726-webclone-extractsite-dedup

## What
`skills/extract-site/SKILL.md` Mode 3 ("Full-Clone — rebuild to working code") and
`skills/web-clone/SKILL.md` Mode B ("reconstruct") both described the same
`ai-website-cloner-template` pipeline independently — a drift risk (one gets fixed,
the other doesn't). Consolidated: `web-clone` is now the single canonical home for
the reconstruct pipeline; `extract-site` points to it instead of re-describing it.

## Output
- `extract-site` Mode 3 shrunk from a full pipeline re-description to a one-paragraph
  pointer at `/web-clone` Mode B.
- `web-clone` unchanged (already the fuller, two-mode description: snapshot + reconstruct).
- `AGENT.md`/`CLAUDE.md` skill table rows updated for both entries so downstream
  projects pulling this framework (`npx skills add`) see the corrected split too.
- `fdk/CAPABILITIES.md` regenerated (auto-generated, not hand-edited).

## Files
| File | Action |
|------|--------|
| `skills/extract-site/SKILL.md` | modified — Mode 3 replaced with pointer |
| `llmwiki/skills/utils/extract-site.md` | modified — synced mirror |
| `~/.claude/skills/extract-site/SKILL.md` | modified — synced installed copy |
| `llmwiki/AGENT.md` | modified — `web-clone` + `extract-site` rows |
| `llmwiki/CLAUDE.md` | modified — `web-clone` + `extract-site` rows |
| `fdk/CAPABILITIES.md` | regenerated |

## Notes
- Found via `/fable5`-gated duplicate check requested mid-session (installing the
  `fable5` skill surfaced the question of overlapping skills; this is unrelated to
  `fable5` itself, just where the check was triggered from).
- Kept both skills separate on purpose — `extract-site`'s main job (design-token
  extraction: DESIGN.md/tokens.json/css) has no equivalent in `web-clone`, and
  `web-clone`'s Mode A (byte-exact offline snapshot) has no equivalent in
  `extract-site`. Only the reconstruct-to-code path was duplicated.

## Origin
- **Draft:** `wiki/sources/draft/230726-webclone-extractsite-dedup.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
