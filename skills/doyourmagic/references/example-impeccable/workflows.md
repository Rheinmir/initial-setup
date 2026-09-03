# Impeccable — workflow bundle

Generated from a read-only exploration of the `impeccable` repo (npm package `impeccable`, bin `cli/bin/cli.js`, v3.6.1) — a design skill pack + anti-pattern detector CLI for AI coding agents. This bundle splits everything a developer needs into two tracks:

- **Consumer track (`01`–`06`)** — you added `impeccable` to a project and want to use it.
- **Contributor track (`07`)** — you cloned `impeccable` itself to change the tool.

| # | File | Purpose | Track |
|---|------|---------|-------|
| 1 | [01-install-and-init.md](01-install-and-init.md) | Install the skill/hook into your AI harness, then run `/impeccable init` to bootstrap `PRODUCT.md` | Consumer — setup |
| 2 | [02-use-design-commands.md](02-use-design-commands.md) | Reference + copy-paste examples for all 23 `/impeccable` commands (audit, critique, polish, harden, ...) run inside your AI agent's chat | Consumer — daily use |
| 3 | [03-cli-anti-pattern-scan.md](03-cli-anti-pattern-scan.md) | Run the 61-rule detector standalone from the shell (`npx impeccable detect`), no AI agent needed | Consumer — daily use |
| 4 | [04-manage-detector-ignores.md](04-manage-detector-ignores.md) | Waive false positives durably via `impeccable ignores`, and what to commit vs. gitignore under `.impeccable/` | Consumer — tuning |
| 5 | [05-ci-integration.md](05-ci-integration.md) | Wire `impeccable detect --json` into your own project's CI as a blocking gate | Consumer — CI |
| 6 | [06-keep-impeccable-updated.md](06-keep-impeccable-updated.md) | `impeccable update`/`check`/`link`, re-trust prompts, hook debug logging | Consumer — maintenance |
| 7 | [07-contributor-build-and-test.md](07-contributor-build-and-test.md) | Build the provider-specific `dist/` output, run the test suites, add a detector rule, cut a release | Contributor |

## Suggested run order

First-time adopter: `01` → `02` and `03` in either order (agent-mediated vs. standalone-CLI paths are independent) → `04` once you have real findings to triage → `05` once local waivers are tuned → `06` as an ongoing habit.

Contributor: skip straight to `07`; it doesn't depend on `01`–`06`.

## How this bundle was verified, not just paraphrased

Every runnable command in `01`–`07` was checked against the actual source, not just the README:
- CLI subcommands and flags: `cli/bin/cli.js`, `cli/engine/cli/main.mjs`
- `npm`/`bun` scripts: `package.json` → `scripts`
- Ignore-management commands: `cli/bin/commands/ignores.mjs`
- Exit codes: the literal `process.exit(...)` calls in `cli/engine/cli/main.mjs`
- What a real, lived-in `.impeccable/config.json` looks like: cross-checked against an actual consuming project's committed config on this machine, not just the repo's own docs
- CI split (consumer vs. contributor): `.github/workflows/ci.yml` inside the impeccable repo builds/tests *Impeccable*, and is deliberately not reused as the `05-ci-integration.md` template
