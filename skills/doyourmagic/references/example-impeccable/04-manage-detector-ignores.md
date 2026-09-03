# 04 — Manage detector ignores (waive false positives at the repo level)

**Why you'd use this:** some detector findings are correct-but-intentional (a semantic status color, a brand font mandated by legal, a legacy directory you're not touching yet). Repeating an inline `impeccable-disable` comment everywhere is noisy — `impeccable ignores` writes a durable, shared, reviewable waiver into `.impeccable/config.json` instead.

**What it produces:** entries under `detector.ignoreRules`, `detector.ignoreFiles`, or `detector.ignoreValues` in `.impeccable/config.json` (shared/committed) or `.impeccable/config.local.json` (per-developer/gitignored).

## Commands (verified in `cli/bin/commands/ignores.mjs`)

```bash
npx impeccable ignores list                                        # show merged, shared, and local ignores

npx impeccable ignores add-rule <rule> [--all-values]               # ignore a whole rule
npx impeccable ignores add-file "src/legacy/**"                     # ignore files by glob
npx impeccable ignores add-value overused-font Inter --reason "Brand font"
npx impeccable ignores add-value design-system-color "*" --file "src/demo.css"

npx impeccable ignores remove-rule <rule>
npx impeccable ignores remove-file <glob>
npx impeccable ignores remove-value <rule> <value>

npx impeccable ignores clear                                        # clear all detector ignores in scope
```

Scope flags:

```bash
--shared     # write .impeccable/config.json (default, committed, team-shared)
--local      # write .impeccable/config.local.json (gitignored, per-developer)
--all        # for remove/clear: apply to both shared and local
```

Value-scoping flags:

```bash
--file <glob>     # scope add-value/remove-value to matching files only
--reason <text>   # store a human-readable justification (shows up in `list`)
```

## What a real, lived-in `.impeccable/config.json` looks like

Cross-checked against an actual project's committed config on this machine (not the impeccable repo's own dogfood config — a separate consuming project). Every `ignoreValues` entry recorded a `reason` string, e.g.:

```json
{
  "rule": "design-system-color",
  "value": "#f87171",
  "files": ["frontend/src/pages/RequestLogPage.tsx"],
  "createdAt": "2026-08-26T17:17:09.108Z",
  "reason": "HTTP status/latency-severity/reachability semantic color, Data Needs Color Rule in DESIGN.md"
}
```

Takeaway: treat `--reason` as required in practice, not optional — an ignore list with no reasons is unreviewable six months later. Every waiver in the real config observed here cited either a design-system rule ("Data Needs Color Rule in DESIGN.md") or "pre-existing, not introduced by this session."

## What to commit vs. gitignore (verified in `README.npm.md`)

**Keep tracked (shared project artifacts):**
- `.impeccable/config.json`
- `.impeccable/live/config.json`
- `.impeccable/design.json`
- `.impeccable/surfaces/*.md`
- `.impeccable/critique/*.md`

**Add to `.gitignore` (ephemeral/per-developer):**

```gitignore
# impeccable-ignore-start
.impeccable/config.local.json
.impeccable/hook.cache.json
.impeccable/hook.pending.json
.impeccable/*.png
.impeccable/review/
.impeccable/questions/
.impeccable/live/server.json
.impeccable/live/sessions/
.impeccable/live/previews/
.impeccable/live/annotations/
.impeccable/live/cache/
.impeccable/live/manual-edit-apply-transaction.json
.impeccable/live/manual-edit-events.jsonl
.impeccable/live/manual-edit-evidence/
.impeccable/live/pending-manual-edits.json
.impeccable/live/deferred-svelte-component-accepts.json
.impeccable/live/*.png
# impeccable-ignore-end
```

`.impeccable/` is intentionally matched **unanchored** (no leading `/`), because in a monorepo the active workspace (and its own `.impeccable/`) can live nested under e.g. `apps/web/`, and an anchored pattern would only match the repo root.

If an ephemeral file was already committed before adding this block, `.gitignore` won't retroactively untrack it — run `git rm --cached <path>` once.

Run order: do this after you've run a scan at least once (`03-cli-anti-pattern-scan.md`) and have real findings to triage — writing ignores speculatively, before you know what fires, just hides signal.
