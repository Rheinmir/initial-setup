---
name: failure-flywheel
description: Capture each agent failure, bucket and count it deterministically, and when a failure class recurs past a threshold, scaffold a candidate rule/skill stub into the propose->gate flow so the same mistake becomes a guardrail instead of repeating. Hamel's create->label->fix->repeat flywheel, self-evolving. Trigger when the user says "log this failure", "record the mistake", "why does this keep happening", "turn failures into rules", "failure taxonomy", "what keeps breaking", or invokes /failure-flywheel. Also run --report periodically to see the top recurring failure classes.
---

# Skill: failure-flywheel

Turn recurring failures into rules. Capture by code, count deterministically, draft a stub for a human to approve — never auto-promote.

## When to use
- A task failed in a way that could recur (invented an API, broke a test, ignored a rule, over-built). Record it so it is counted, not forgotten.
- Periodically (end of session, or every N failures): `--report` to see which failure class recurs most.
- When a class crosses the recurrence threshold: `--draft <category>` to seed a candidate rule, then run `/propose` to finish it.

Do NOT use to auto-write rules. This skill seeds the gate; a human always approves.

## The flywheel (Hamel: create -> label -> fix -> repeat)
The slow human step is "notice the same mistake keeps happening and turn it into a rule." This makes the mechanical 90% deterministic (capture + taxonomy + count + scaffold) and refuses to fake the 10% that needs judgement (what the rule actually is).

## Commands
```bash
# 1. CAPTURE — append one failure (BY CODE; failures.jsonl is gitignored local history)
python3 harness/scripts/failure-flywheel.py record <category> "<summary>" [--detail "..."]

# 2. REPORT — deterministic taxonomy: group by category, COUNT, leaderboard (most-frequent
#    first) + first/last seen + which classes are eligible to draft
python3 harness/scripts/failure-flywheel.py --report

# 3. DRAFT — only if <category> recurs >= recurrence_threshold: scaffold a STUB proposal at
#    llmwiki/wiki/sources/draft/DDMMYY-failure-<category>.md and STOP for human approval
python3 harness/scripts/failure-flywheel.py --draft <category> [--date YYYY-MM-DD]
```

## Steps
1. On a failure, `record` it under the closest taxonomy category (see the config). Capture never blocks — an unlisted category is still recorded and flagged in `--report`.
2. Run `--report` to read the leaderboard. A class marked `DRAFT` has recurred >= the threshold.
3. For an eligible class, `--draft <category>`. It writes a valid draft STUB (OKF frontmatter + `## Origin`, deliberately no `## Plan` so it passes the R7 gate as a seed) containing a templated "TODO: distill rule from these N failures" + the failure list.
4. The stub STOPS for you. Run `/propose` to turn it into a complete, gated rule/skill. FailureFlywheel never auto-promotes — the gate stays human.

## The adapter boundary (build-now-adapt-later)
Everything above is deterministic and built now. The ONE quarantined unknown is `harness/failure-flywheel.config.yaml` (`verified: false`): the recurrence threshold and taxonomy are best-guesses, and the "distill failures -> rule" model is absent. While it is unset, `--draft` inserts a human-TODO stub instead of an auto-written rule. Finalize later by editing only that one file — calibrate the threshold, name a distill model, flip `verified: true`.

## Rules
- Capture is fail-open — recording a failure must never break the session.
- Never auto-promote. `--draft` seeds `/propose`; a human approves.
- The draft filename date is fixed (`--date`, default 2026-06-29, **ISO `YYYY-MM-DD` only** — not the `DDMMYY` wiki filename convention) for determinism; real use can stamp today. A malformed `--date` now exits 2 with a clear error instead of silently falling back to the default (fixed 2026-07-20 after that exact silent-fallback shipped a wrong-dated draft file).
- Do not hard-code the threshold or taxonomy anywhere but the config — that is the adapter.

## Related
- `harness/scripts/code-logger.py` — same by-code, gitignored-JSONL, fail-open capture pattern.
- `llmwiki/skills/dev-loop/propose.md` — the gate this feeds.
- `llmwiki/skills/dev-loop/build-now-adapt-later.md` — the quarantine pattern the config follows.
