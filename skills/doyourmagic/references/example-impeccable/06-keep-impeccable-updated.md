# 06 — Update, verify, and maintain an existing Impeccable install

**Why you'd use this:** Impeccable ships frequent skill/command updates; an install done once in `01-install-and-init.md` goes stale. This is the maintenance loop, not first-time setup.

**What it produces:** refreshed skill files under your harness folder(s), and (for Codex/Grok) a re-trust prompt when the hook manifest itself changed.

## Check for updates without applying them

```bash
npx impeccable check
```

## Apply updates

```bash
npx impeccable update
```

Equivalent long form: `npx impeccable skills update` (the top-level `install`/`update`/`link`/`check`/`help` verbs are shorthand for the `skills` subcommand — verified in `cli/bin/cli.js`'s `SKILL_COMMANDS` set).

### Platform-specific re-approval after update

- **Codex:** tracks trust by hook *definition*. If the update changed `.codex/hooks.json`, open `/hooks` again and re-approve — this is expected, not a bug.
- **Grok Build:** re-run `/hooks-trust` (or relaunch with `--trust`) if `.grok/hooks/impeccable.json` changed.

## If you installed via git submodule instead of `npx impeccable install`

```bash
git submodule update --remote .impeccable
npx impeccable link --source=.impeccable --providers=claude,cursor
```

`link` symlinks skill folders from `.impeccable/dist/universal/` into your harness folders and leaves any existing real (non-symlinked) skill directory untouched unless you pass `--force`.

## Debugging a hook that isn't firing / is firing unexpectedly

Set an audit log path in the **shared** config (`.impeccable/config.json`, under the `hook` key) or via the legacy env var:

```json
{ "hook": { "enabled": true, "auditLog": ".impeccable/hook-debug.ndjson" } }
```

```bash
IMPECCABLE_HOOK_LOG=.impeccable/hook-debug.ndjson
```

This writes one NDJSON line per hook invocation. Leave it unset for normal use — it's a debug knob, not a default.

## Reset hook consent (rare)

Your per-developer choice of "install the hook, yes/no" is remembered in the gitignored `.impeccable/config.local.json`. To be asked again, delete that key or the file, or pass `--no-hooks` on a specific `install`/`update` run to skip the hook for that run only (without recording a new preference).

## Gotcha (generalizable)

If the installer aborts because an existing hook manifest (`.claude/settings.local.json`, `.codex/hooks.json`, etc.) is malformed, it does **not** silently overwrite it — rerun with `--force` to back it up as `.bak` first. Don't reach for `--force` reflexively; read the abort message, since a malformed manifest can also mean a hand-edit you intended to keep.

Run order: recurring maintenance step — run periodically after `01`, independent of `02`–`05`.
