# 05 — Wire the detector into your own project's CI

**Why you'd use this:** catch AI-slop / design anti-patterns on every PR to *your* project, without an AI agent in the loop — CI just needs Node and a shell.

**What it produces:** a CI job that fails the build (non-zero exit) when new anti-patterns are introduced, plus a JSON findings artifact you can upload or post as a PR comment.

> Note: this is a workflow for *consumers* of Impeccable in their own repo's CI. It is different from `07-contributor-build-and-test.md`, which covers Impeccable's own internal CI for building/testing the tool itself (`.github/workflows/ci.yml` inside the impeccable repo) — don't copy that file into your project, it builds and tests Impeccable, not your app.

## Minimal GitHub Actions step

```yaml
- name: Design anti-pattern scan
  run: npx impeccable detect --json src/ | tee impeccable-findings.json
  # detect exits 2 when findings exist, 0 when clean, 1 on a real error
```

Because `detect` exits `2` on findings, the step above fails the job automatically — no extra `if` logic needed. If you want to upload the JSON report even on failure:

```yaml
- name: Design anti-pattern scan
  id: impeccable
  run: npx impeccable detect --json src/ > impeccable-findings.json
  continue-on-error: true

- name: Upload findings
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: impeccable-findings
    path: impeccable-findings.json

- name: Fail if anti-patterns found
  if: steps.impeccable.outcome == 'failure'
  run: exit 1
```

## Respecting your repo's waivers in CI

By default `detect` reads the same `.impeccable/config.json` / `.impeccable/config.local.json` your team already committed (see `04-manage-detector-ignores.md`), so CI and local runs agree. Don't add `--no-config` in CI unless you deliberately want a stricter, waiver-blind gate (e.g. a scheduled "drift" audit separate from the PR-blocking check).

## Node version

`package.json` declares `"engines": { "node": ">=22.18.0" }` — pin your CI runner's Node setup step to at least that, or `detect` may behave unpredictably on older runtimes.

## Gotcha (generalizable)

Don't lift a tool's *own* CI workflow file as a template for how consumers should integrate it. This repo's `.github/workflows/ci.yml` runs `bun install`, `bun run build`, `bun run test:*`, and asset-diff checks — none of that is relevant to a project that merely *depends on* Impeccable via `npx`. Read the README's "Exit Codes" / "CLI" section for the consumer-facing contract instead, and verify the exit codes against the actual CLI source (here: `cli/engine/cli/main.mjs`) rather than trusting the docs alone.

Run order: after `03` (know the exit-code contract locally) and `04` (waivers already tuned) — wiring an untuned detector straight into a blocking CI gate produces immediate false-positive noise.
