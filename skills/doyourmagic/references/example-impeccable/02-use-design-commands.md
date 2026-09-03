# 02 — Use the 23 `/impeccable` design commands day-to-day

**Why you'd use this:** once installed (see `01-install-and-init.md`), Impeccable's actual value is a shared design vocabulary you invoke inside your AI agent's chat while building or revising UI — not a CLI you run standalone. This file is the command reference plus copy-pasteable invocations.

**What it produces:** UI changes made by your AI agent, following Impeccable's anti-slop guidance (no overused fonts, no gray-on-color text, no nested cards, no bounce easing, etc.), plus optional artifacts like `.impeccable/critique/*.md` review reports and `.impeccable/design.json`.

## How to invoke

All 23 commands route through one skill, typed **in your AI agent's chat**:

```
/impeccable <command> [optional target/description]
```

Type `/impeccable` alone to see the full list inside your harness.

## Full command table (verified against README.npm.md's authoritative list)

| Command | What it does |
|---|---|
| `/impeccable craft` | Full shape-then-build flow with visual iteration |
| `/impeccable init` | One-time setup (see `01-install-and-init.md`) |
| `/impeccable document` | Generate root `DESIGN.md` from existing project code |
| `/impeccable extract` | Pull reusable components and tokens into the design system |
| `/impeccable shape` | Plan UX/UI before writing code |
| `/impeccable critique` | UX design review: hierarchy, clarity, emotional resonance |
| `/impeccable audit` | Technical quality checks (a11y, performance, responsive) |
| `/impeccable polish` | Final pass, design-system alignment, shipping readiness |
| `/impeccable bolder` | Amplify boring designs |
| `/impeccable quieter` | Tone down overly bold designs |
| `/impeccable distill` | Strip to essence |
| `/impeccable harden` | Error handling, i18n, text overflow, edge cases |
| `/impeccable onboard` | First-run flows, empty states, activation paths |
| `/impeccable animate` | Add purposeful motion |
| `/impeccable colorize` | Introduce strategic color |
| `/impeccable typeset` | Fix font choices, hierarchy, sizing |
| `/impeccable layout` | Fix layout, spacing, visual rhythm |
| `/impeccable delight` | Add moments of joy |
| `/impeccable overdrive` | Add technically extraordinary effects |
| `/impeccable clarify` | Improve unclear UX copy |
| `/impeccable adapt` | Adapt for different devices |
| `/impeccable optimize` | Performance improvements |
| `/impeccable live` | Visual variant mode: iterate on elements live in the browser |

## Copy-pasteable examples (verified in README.npm.md)

```
/impeccable audit blog           # Audit blog hub + post pages
/impeccable critique landing     # UX design review
/impeccable polish settings      # Final pass before shipping
/impeccable harden checkout      # Add error handling + edge cases
```

Or skip the command name and just describe what you want:

```
/impeccable redo this hero section
```

## Pin a frequently used command to its own shortcut

```
/impeccable pin audit
```

This creates a standalone `/audit` shortcut so you don't have to type `/impeccable audit` every time.

## Suggested first-use order on an existing project

1. `/impeccable init` (once — see `01-install-and-init.md`)
2. `/impeccable document` — generates `DESIGN.md` from what already exists, so later commands have a baseline to align to
3. `/impeccable audit <surface>` or `/impeccable critique <surface>` — see where the surface stands today
4. `/impeccable polish <surface>` — apply fixes

## Gotcha (generalizable)

These are **agent-chat commands, not shell commands** — running `/impeccable audit` in a terminal does nothing (there is no such CLI subcommand; see `03-cli-anti-pattern-scan.md` for the actual terminal-runnable surface). Don't assume every documented "command" in a skill's README is shell-executable — verify against the CLI's own argument parser (`cli/bin/cli.js`) before writing it as a shell snippet.

Run order: step 2, after install (`01`). Independent of the CLI workflows (`03`–`06`); this is the AI-agent-mediated path, those are the standalone-tool path.
