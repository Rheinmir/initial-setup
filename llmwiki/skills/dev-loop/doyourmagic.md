---
name: doyourmagic
description: Given a freshly-cloned external repo/tool, run clone->explore->analysis->write-workflows to produce a runnable /doyourmagic/<repo-name>/workflows.md doc bundle plus a companion index.html explaining what each workflow file does, run order, and output. Trigger on 'kéo repo mới về', 'clone tool này làm workflow', 'doyourmagic', 'onboard external tool/repo', 'generate workflow docs for this repo', or /doyourmagic.
---

# Skill: doyourmagic

## When to use
- User just cloned or installed a new external repo/CLI/tool and wants a runnable "how do I actually use this thing" doc bundle instead of re-reading the README from scratch each time.
- User says "kéo repo mới về", "doyourmagic <repo>", "làm workflow cho tool này", "generate workflow docs for this repo", "viết hộ cách dùng runnable cho repo này".
- Before folding an external tool into project conventions/CI — produce the doc bundle first so the integration decision is grounded in verified commands, not README paraphrase.

## Steps
1. Clone (if not already local) the target repo into a scratch/sandbox location — never do the exploration phase in place inside the user's project tree.
2. Locate the primary manifest/entry file (`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / etc.) FIRST, before reading prose docs — it gives the real install command, entry point(s)/bin, and the full list of available scripts.
3. Grep top-level docs (README, README.\<variant\>.md, AGENTS.md/CLAUDE.md if present, `docs/`) for a Quick Start / Usage / Installation section, but treat it as a hypothesis, not ground truth.
4. Verify every documented command against the actual source — the CLI's argument parser/subcommand files, and exit codes via the literal `process.exit(...)`/`sys.exit(...)` calls — docs drift from code.
5. Split findings into distinct workflow files by AUDIENCE, not by feature: consumer/end-user workflows (how someone uses this tool in their own project) vs. contributor workflows (how someone modifies the tool itself). Never merge these — conflating them produces workflows that either overreach (asking a consumer to run the tool's own internal test suite) or underreach (omitting the build/test loop a contributor actually needs).
6. If the repo has its own CI config, read it to learn what it gates on, but write a fresh, minimal example for the consumer's CI use case — never copy the tool's own internal CI pipeline as "how you'd integrate this."
7. If a real, independent integration of the tool already exists on the host machine (e.g. a config directory already committed in some other project), read that too — it beats the clone's own bundled fixtures for "what correct real-world usage looks like."
8. Write the output bundle to `doyourmagic/<repo-name>/`:
   - `workflows.md` — an index table (file, one-line purpose, run order/track), a "suggested run order" section, and a short "how this was verified, not just paraphrased" section listing exactly which source files backed each claim.
   - One `NN-<workflow-name>.md` file per distinct workflow, each immediately runnable: concrete copy-pasteable commands, exact paths, expected output/exit behavior, a one-line "why you'd use this", and a one-line "what it produces". Don't force a fixed file count — a single-script tool may only need `workflows.md` + `01-usage.md`.
   - `index.html` — a single self-contained file (inline CSS, no CDN/external assets, no build step, must render correctly opened via `file://`) listing every workflow in run order with a 2-3 sentence explainer and a relative link to its `.md` file.
9. Confirm the result with the user. If they want it turned into an installable skill (not just a one-off doc bundle), hand off to the `new-skill`/`fdk` skill-authoring flow — never silently start scaffolding a skill without asking first.

## Rules
- Never paraphrase a README's command list straight into "runnable" docs — check each command exists in the manifest's scripts / the CLI's `--help` output / the argument parser first.
- Never assume exit-code conventions are 0/1 by default — read the literal exit calls; tools sometimes use specific codes (e.g. 2 = "findings present") that callers must branch on deliberately.
- Never copy a tool's own `.github/workflows/*.yml` into a "how to add this to your CI" doc for the consumer — always write a minimal, purpose-built example instead.
- Keep chat-only/slash commands and real shell CLI commands in separate workflow files — mixing them produces copy-paste failures when a reader tries a chat command in a terminal or vice versa.
- The exploration/clone phase is read-only against the target repo — never modify files inside the cloned tool itself; only write new files under the `doyourmagic/<repo-name>/` output path.
- `index.html` must be self-contained and readable in both light and dark viewing — no external CDN, no absolute local paths.

## Reference example
`references/example-impeccable/` — a full worked run of this skill against `pbakaus/impeccable` (a CLI + multi-agent design-QA skill pack), including the split consumer/contributor tracks and the verification notes. Use it as the concrete shape to match.
