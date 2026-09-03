# 07 — Build, test, and extend Impeccable itself (contributor workflow)

**Why you'd use this:** this file is for someone who cloned the `impeccable` repo to modify the tool itself (add a rule, add a harness provider, fix a bug) — not to consume it in another project. If you only want to *use* Impeccable, stop at workflows `01`–`06`.

**What it produces:** a rebuilt `dist/` tree with per-provider skill output, a passing local test run, and (for a real contribution) a PR against `pbakaus/impeccable`.

## Prerequisites (verified in `docs/DEVELOP.md` and `package.json`)

- Bun (the build/test scripts use `bun run …`; some tests still run under plain `node --test`)
- Node.js >= 22.18.0
- `bun install` from the repo root

```bash
bun install
```

## Source-of-truth architecture

The skill lives once, at `skill/SKILL.src.md` (YAML frontmatter + body with `{{placeholder}}` tokens), and a config-driven factory in `scripts/lib/transformers/providers.js` transforms it into every provider's native format. Adding a new provider is a new config entry there plus a placeholder block in `PROVIDER_PLACEHOLDERS` (`scripts/lib/utils.js`) — not a hand-written duplicate skill file per tool.

## Build

```bash
bun run build            # build:skills + copy dist into build/_data/dist
bun run build:skills     # skills only, skip root sync (faster inner loop)
bun run clean            # rm -rf dist build
bun run rebuild          # clean + build
bun run build:browser    # rebuild the standalone browser detector bundle
bun run build:extension  # rebuild the browser extension
```

Output shape: `skill/` source → one directory per provider under `dist/` (e.g. `dist/claude-code/.claude/skills/impeccable/SKILL.md`).

## Test

The test runner has named suites (verified in `scripts/run-tests.mjs` / `scripts/test-suites.mjs`); `npm test`/`bun run test` alone runs the `default` suite:

```bash
bun run test              # default suite
bun run test:core         # fast unit tests
bun run test:detector     # detector rule tests
bun run test:framework    # framework-fixture tests
bun run test:cli-e2e
bun run test:plugin-e2e
bun run test:live-e2e             # Playwright-driven, needs `npx playwright install chromium`
bun run test:skill-behavior       # needs a real LLM provider API key
```

List everything available:

```bash
node scripts/run-tests.mjs --list
```

Some suites are opt-in / CI-gated and need secrets (`ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`) that a local contributor usually doesn't have — expect `test:skill-behavior` and the `*-e2e` provider-backed suites to be skipped or unrunnable locally without them. Cross-checked against `.github/workflows/ci.yml`, which gates those same suites behind `if: env.ANTHROPIC_API_KEY != '' || env.DEEPSEEK_API_KEY != ''` and prints a skip message otherwise — don't treat a local skip as a failure.

## Verify generated output stayed in sync (what CI actually gates on)

CI's real merge gate isn't just "tests green" — it also diffs the committed, generated provider output against a fresh build:

```bash
bun run build
git diff --exit-code -- .agents .claude .cursor .gemini .github/skills plugin \
  cli/engine/detect-antipatterns-browser.js extension/detector
```

If you edit `skill/SKILL.src.md` (or anything the build reads) and don't rebuild before committing, this step fails the PR even though your source edit is "correct." Always run `bun run build` and commit the resulting diff under the paths above alongside a source change.

## Adding a new detector rule

Detector rules live in `cli/engine/registry/antipatterns.mjs` (the rule catalog/metadata) and `cli/engine/rules/checks.mjs` (the actual check implementations: `checkElementBorders`, `checkElementMotion`, `checkElementGlow`, `checkPageTypography`, `checkPageLayout`, `checkHtmlPatterns`). Add fixtures under `tests/fixtures/` and a case in `tests/detect-antipatterns.test.js` / `tests/detect-antipatterns-fixtures.test.mjs` to cover it, then run `bun run test:detector`.

## Release (maintainer-only, included for completeness — verify permissions before running)

```bash
node scripts/release.mjs skill
node scripts/release.mjs cli
node scripts/release.mjs ext
```

## Gotcha (generalizable)

A repo's own `.github/workflows/*.yml` tells you what its **maintainers** must keep green (build reproducibility, its own test matrix) — it is not a template for how *consumers* of the tool should integrate it into their CI (that's `05-ci-integration.md`). Conflating the two produces a bloated, wrong CI step in a consumer project (e.g. running `bun run test:live-e2e` against your own app, which builds and tests Impeccable, not your app).

Run order: only relevant if you're modifying Impeccable itself; otherwise this is a dead end from `01`–`06`.
