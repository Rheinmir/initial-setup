# 01 — Install Impeccable into your AI coding agent and initialize it

**Why you'd use this:** Impeccable is a skill pack (23 commands + a design-detector hook), not a library you import — it does nothing until it's installed into your AI harness (Claude Code, Cursor, Codex, Gemini CLI, Grok Build, etc.) and initialized against your specific project.

**What it produces:** provider-specific skill files under your project's harness folder (e.g. `.claude/skills/impeccable/`), an optional edit-time hook wired into your harness's hook manifest, and a `PRODUCT.md` capturing durable product context (audience, purpose, voice, constraints).

## Prerequisites

- Node.js >= 22.18.0 (from `package.json` → `engines.node`)
- One of the supported AI harnesses already set up: Claude Code, Cursor, GitHub Copilot, Gemini CLI, Codex CLI, Grok Build, Hermes Agent, OpenCode, Pi, Kiro, Trae, Rovo Dev, Qoder, Mistral Vibe, Veto, or Google Antigravity.

## Steps

Run from the **root of the target project** (not inside the impeccable repo itself):

```bash
npx impeccable install
```

This is interactive by default:
1. It detects installed harness folders/CLIs on your machine (e.g. `~/.claude`, `~/.codex`, project-local `.cursor`) and shows what it found.
2. You confirm or customize the provider list.
3. You choose install scope: current project only, or global (all projects).
4. For Claude Code, Cursor, Codex, GitHub Copilot, and Grok Build, it also offers to install the provider-native **hook** that runs the design detector automatically after UI file edits (default: yes).

### Non-interactive / scripted install

```bash
npx impeccable install -y --providers=claude,codex --scope=project
# or, using the same command under its explicit sub-namespace:
npx impeccable skills install -y --providers=claude,codex --scope=project

# skip the hook manifest entirely
npx impeccable install --no-hooks
```

Valid `--providers` values (from `cli/bin/commands/skills.mjs` → `PROVIDER_ALIASES`): `claude`, `cursor`, `codex`, `gemini`, `github`, `grok`, `hermes`, `kiro`, `opencode`, `pi`, `qoder`, `rovo-dev`, `trae`, `trae-cn`, `vibe`, `veto`, `antigravity`.

### Expected output / exit behavior

On success, exit code `0` and a summary of what was written (which provider folders, whether the hook manifest was installed). Reload/restart your AI harness afterward so it picks up the new skill.

## Initialize the project (run inside your AI agent's chat, not the shell)

Once installed, open your AI coding agent and type:

```
/impeccable init
```

`init` inspects the project, asks only for missing durable product context, and writes `PRODUCT.md` at the project root. It also configures `buildPath` (`"comp"` or `"code"`) in `.impeccable/config.json` when image generation is available.

**Gotcha verified against this repo's own CLI (`cli/bin/cli.js`):** typing `npx impeccable init` in your terminal (instead of `/impeccable init` in the agent chat) fails on purpose:

```
"init" is not a CLI command. Type /impeccable init in your AI coding agent's chat (Claude Code, Cursor, Codex, ...), not in this terminal.
```

## Platform-specific one-time steps (verified in README.npm.md)

- **Codex:** open `/hooks` after install/update and approve the project hook — there is no marketplace/plugin flow for Codex.
- **Grok Build:** run `/hooks-trust` (or launch with `--trust`) once per project folder before `.grok/hooks/` scripts run.
- **Cursor:** switch to the Nightly channel (Settings → Beta) and enable Agent Skills (Settings → Rules).
- **Gemini CLI:** install the preview build (`npm i -g @google/gemini-cli@preview`), then `/settings` → enable "Skills".

## What this looked like in a real project (cross-checked against this machine's own cozyroom integration)

A completed install leaves behind, at the target project root:
- `.claude/skills/impeccable/` — the compiled skill + `scripts/hook.mjs`
- `.claude/settings.local.json` — a `PostToolUse` hook (fast checks after Edit/Write on UI files) and a `Stop` hook (deeper full-rule pass), both invoking `${CLAUDE_PROJECT_DIR}/.claude/skills/impeccable/scripts/hook.mjs`
- `.impeccable/config.json` — shared, committed config (see `04-manage-detector-ignores.md`)
- `PRODUCT.md`, `DESIGN.md` at the project root

## Alternative install paths (only if `npx impeccable install` doesn't fit)

- **Git submodule** (teams that vendor+pin via git): `git submodule add https://github.com/pbakaus/impeccable .impeccable && npx impeccable link --source=.impeccable --providers=claude,cursor`
- **Claude Code plugin marketplace:** `/plugin marketplace add pbakaus/impeccable` then install via `/plugin`
- **Grok Build plugin:** `grok plugin install pbakaus/impeccable#plugin --trust`

Run order: this is step 1 — everything else assumes the skill/CLI is already installed.
