# 03 — Run the standalone anti-pattern detector from the shell

**Why you'd use this:** no AI agent required. `impeccable detect` is a real terminal command (verified in `cli/bin/cli.js` and `cli/engine/cli/main.mjs`) that runs 61 deterministic rules against your HTML/CSS/JSX/TSX/Vue/Svelte files — useful for a quick local check, a pre-commit script, or feeding CI (see `05-ci-integration.md`).

**What it produces:** a findings report to stdout (human-readable or JSON), and a process exit code you can branch on.

## Prerequisites

- The `impeccable` package available via `npx` (no install step required for `detect` alone — it doesn't need the skill/hook install from `01-install-and-init.md`).
- Optional: `puppeteer` (listed as an `optionalDependencies` in `package.json`) if you want to scan a live URL instead of local files.

## Basic scans

```bash
# Scan a directory
npx impeccable detect src/

# Scan a single file
npx impeccable detect index.html

# Scan a live URL (requires Puppeteer)
npx impeccable detect https://example.com

# Shorthand: if the first arg looks like a path/URL, "detect" can be omitted
npx impeccable src/
```

The path-vs-command disambiguation is real logic in `cli/bin/cli.js` (`looksLikeDetectTarget`) — flags, URLs, path-shaped strings, and existing files/dirs are treated as scan targets; anything else is treated as a command name and fails loudly if unrecognized.

## Flags (verified in `cli/engine/cli/main.mjs`)

```bash
npx impeccable detect --json .              # machine-readable output, for CI/tooling
npx impeccable detect --fast src/           # regex-only mode, skips jsdom (faster, less accurate)
npx impeccable detect --no-config src/      # raw scan, ignore project .impeccable/config.json
npx impeccable detect --no-inline-ignores src/   # also ignore in-file impeccable-disable comments
npx impeccable detect --help
```

`-json` and `-fast` (single dash) are normalized to `--json`/`--fast` by the CLI, so either form works.

## Exit codes (verified: `process.exit(primary.length > 0 ? 2 : 0)` in `cli/engine/cli/main.mjs`)

- `0` — no issues found
- `2` — anti-patterns detected
- `1` — a real error (bad args, scan failure)

This is the contract to branch on in scripts / CI, not stdout text-matching.

## What it catches (verified against README + `cli/engine/registry/antipatterns.mjs`)

- **AI slop tells:** side-tab accent borders, gradient text on headings, purple/violet gradients, cyan-on-dark palettes, glowing accents on dark mode, border+border-radius clashes
- **Typography:** overused fonts (Inter, Roboto, Arial, system defaults), flat type hierarchy, single font family
- **Color & contrast:** WCAG AA violations, gray text on colored backgrounds, pure black/white
- **Layout:** nested cards, monotonous spacing, everything-centered layouts
- **Motion:** bounce/elastic easing, layout-property transitions
- **Quality:** tiny body text, cramped padding, long line lengths, small touch targets

## Suppressing a specific false positive inline (no config file needed)

```html
<!-- impeccable-disable overused-font: exported brand doc -->
```

Also available: `impeccable-disable-line` / `impeccable-disable-next-line` for single-line scope. Works in any comment syntax. Bypassed by `--no-inline-ignores` or `--no-config`.

For persistent, repo-shared waivers instead of one-off inline comments, see `04-manage-detector-ignores.md`.

Run order: independent of `01`/`02` — this works even without installing the skill into an AI harness. Do this before `05-ci-integration.md` (get the local exit-code contract right first).
