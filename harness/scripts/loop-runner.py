#!/usr/bin/env python3
"""LoopRunner — deterministic guardrailed agent-loop driver (loop-engineering).

Wrap ANY step with `propose → deterministic-verify → (critique → revise)` and
enforce hard termination guards so an autonomous agent loop can never spin forever,
burn unbounded budget, or "argue its way around" a failing check.

BUILD-NOW / ADAPT-LATER boundary
--------------------------------
DETERMINISTIC, built-and-tested now (this file):
  • the control loop                       propose → verify → guards → revise → repeat
  • the VERIFY step                        a shell cmd; exit-code 0 == pass (pytest/tsc/lint)
  • all termination guards                 max_iter, wall-clock budget, no-progress, escalate
  • progress detection                     sha256 state-hash of workspace-relevant paths
  • the run-log artifact                   JSON: iterations, verdicts, termination reason
  • reflexion                              append a one-line "lesson" to a wiki episodic page

QUARANTINED, the ONE adapter (verified:false, see harness/loop-runner.config.yaml):
  • the LLM critique/revise step           NOT implemented here. The loop calls a `revise.cmd`
                                           shell hook (stub/no-op by default) so the whole loop
                                           is runnable + testable WITHOUT any LLM. Wiring the
                                           real LLM = edit one config field, then flip verified.

KEY INVARIANT: deterministic verify (exit code) is preferred over LLM self-judgment — the
agent cannot talk a failing test into passing. The guards are MANDATORY and all enforced.

Usage
-----
  loop-runner.py run --verify "<cmd>" [--config harness/loop-runner.config.yaml]
                     [--revise "<cmd>"] [--state "<glob>" ...] [--log <path>]
                     [--max-iter N] [--budget-seconds S] [--no-progress-k K]
                     [--escalate-after N] [--episodic <path>] [--cwd <dir>] [--quiet]
  loop-runner.py selftest        # 7 deterministic scenarios, no LLM, no external deps

Guards 5 & 6 (added for the Ralph frame-loop, GH#15 — council 031/032):
  • --scope   diff-jail: files edited OUTSIDE these globs are reverted each iter
              (keeps in-scope state frozen → no-progress trips on out-of-scope-only edits).
  • --protect test-hash: these files (e.g. the frame's own tests) must NOT change;
              a change stops the loop FAIL-CLOSED. Prompt-instructions are not a safety
              layer (council 5/5) — these deterministic checks are.

CLI flags override config; config provides the (quarantined) defaults.
Process exit code: 0 = SUCCESS, 2 = MAX_ITER, 3 = TIMEOUT, 4 = NO_PROGRESS,
                   5 = ESCALATE, 6 = PROTECT_VIOLATION.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import yaml
except ImportError:  # fail-soft: the loop + selftest never depend on PyYAML
    yaml = None

# ── Verdicts (the deterministic contract every consumer reads) ──────────────
SUCCESS = "SUCCESS"
MAX_ITER = "MAX_ITER"
TIMEOUT = "TIMEOUT"
NO_PROGRESS = "NO_PROGRESS"
ESCALATE = "ESCALATE"
PROTECT_VIOLATION = "PROTECT_VIOLATION"  # guard 6 — protected file (e.g. a test) was tampered
FLAKY = "FLAKY"  # guard 7 — verify passed but a confirm re-run disagreed (non-hermetic oracle)

EXIT_CODE = {SUCCESS: 0, MAX_ITER: 2, TIMEOUT: 3, NO_PROGRESS: 4, ESCALATE: 5,
             PROTECT_VIOLATION: 6, FLAKY: 7}

# Fail-safe defaults, used when no config file is present. A guard set to 0/None
# is DISABLED — except max_iter, which is the always-on hard backstop.
DEFAULTS = {
    "guards": {
        "max_iter": 6,
        "budget_seconds": 900,
        "no_progress_k": 2,
        "escalate_after_iter": 0,
    },
    "progress": {"state_paths": []},
    "scope": {"code_globs": [], "protect_globs": []},  # guards 5 (diff-jail) + 6 (test-hash)
    "reflexion": {"episodic_memory_page": None, "enabled": True},
    "run_log": {"path": None},
    "revise": {"cmd": None},
}

_OUTPUT_TAIL = 600  # chars of verify/revise output kept per iteration in the run-log


def _now_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Progress detection: deterministic state-hash ────────────────────────────
def compute_state_hash(state_paths, cwd):
    """sha256 over the workspace-relevant state. Empty paths → constant sentinel
    so the caller can DISABLE no-progress detection (fail-safe: never stop on a
    signal we cannot actually measure)."""
    if not state_paths:
        return None  # no measurable state → no-progress detection is off
    base = Path(cwd)
    h = hashlib.sha256()
    seen = []
    for pat in state_paths:
        if any(c in pat for c in "*?["):
            seen.extend(sorted(base.glob(pat)))
        else:
            seen.append(base / pat)
    files = []
    for m in sorted(set(seen), key=str):
        if m.is_dir():
            files.extend(sorted(p for p in m.rglob("*") if p.is_file()))
        else:
            files.append(m)
    for f in sorted(set(files), key=str):
        try:
            rel = f.relative_to(base)
        except ValueError:
            rel = f
        h.update(str(rel).encode())
        try:
            if f.is_file():
                h.update(b"\x00")
                h.update(f.read_bytes())
            else:
                h.update(b"\xff")  # path absent this iteration
        except OSError:
            h.update(b"\xfe")
    return h.hexdigest()


# ── Guards 5 & 6: scope diff-jail + protected-file (test) hashing ───────────
# Guard 5 (diff-jail): after each revise, files the agent changed OUTSIDE the
# frame's scope_code are reverted. Because reverting keeps the in-scope state
# frozen, the existing no-progress guard then trips — an agent that only edits
# out-of-scope files makes no measurable progress and the loop stops. This is why
# scope_code and state_paths should be the SAME writable region (the /br run
# orchestrator sets both from the frame). Prompt-instructions are NOT a safety
# layer (council 5/5) — this deterministic revert is.
# Guard 6 (test-hash): the agent must not edit its own tests. Protected files are
# hashed at loop start; if any changes after a revise, the loop stops FAIL-CLOSED.
import fnmatch as _fnmatch


def _in_globs(rel_posix, globs):
    return any(_fnmatch.fnmatch(rel_posix, g) for g in (globs or []))


def _hash_paths(globs, cwd):
    """sha256 over every real file matching `globs` (gitignore-style, `**` recursive).
    Returns {} if no globs — guard disabled."""
    if not globs:
        return {}
    base = Path(cwd)
    out = {}
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if _in_globs(rel, globs):
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _git_root_prefix(cwd):
    """cwd's path relative to the repo top-level, posix, no trailing slash ('' if cwd IS
    the repo root). git always reports changed-file paths relative to the repo TOP-LEVEL,
    even when invoked from a subdirectory — so when --root is a subdir nested inside a
    bigger repo (e.g. br/payroll inside issue-15-br-k), every git-reported path must be
    re-based to cwd before comparing against scope_globs, or ALL files (even in-scope
    ones) look "out of scope" and never get committed (bug found running the payroll
    pipeline, GH#15)."""
    proc = subprocess.run("git rev-parse --show-toplevel", shell=True, cwd=str(cwd),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    top = Path(proc.stdout.strip())
    try:
        rel = Path(cwd).resolve().relative_to(top.resolve()).as_posix()
    except ValueError:
        return ""
    return "" if rel == "." else rel


def _rebase_to_cwd(paths, cwd):
    """Strip cwd's repo-root prefix from each git-reported path. Paths outside cwd
    (e.g. a dirty file elsewhere in the repo) are left as-is — they SHOULD show as
    out-of-scope, that part of the bug report is correct behavior."""
    prefix = _git_root_prefix(cwd)
    if not prefix:
        return paths
    p = prefix + "/"
    return [f[len(p):] if f.startswith(p) else f for f in paths]


def git_changed_files(cwd):
    """Default diff source: tracked-modified + untracked files, as rel posix paths.
    Fail-safe: if git is unavailable, return [] (guard becomes a no-op rather than
    crashing the loop)."""
    proc = subprocess.run("git status --porcelain --untracked-files=all",
                          shell=True, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    files = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        files.append(path.strip('"'))
    return _rebase_to_cwd(files, cwd)


def git_changed_vs(baseline, cwd):
    """Files changed in cwd — union of (diff vs baseline, if given) and the current
    working-tree changes. Rel posix paths. This is the ACTUAL frame→code footprint,
    recorded into the run-log so `/br status` shows real files, not just intended scope."""
    files = set(git_changed_files(cwd))
    if baseline:
        proc = subprocess.run(f"git diff --name-only {baseline}", shell=True, cwd=str(cwd),
                              capture_output=True, text=True)
        if proc.returncode == 0:
            files |= set(_rebase_to_cwd(
                [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()], cwd))
    return sorted(files)


def git_commit_all(message, cwd):
    """Commit ALL changes in cwd (the isolated worktree) with `message`. Returns the
    new commit sha, or None on failure. `--no-verify` avoids the pre-commit hook
    recursion (see memory precommit-r13). Never touches main — the worktree branch
    holds it until a human merges."""
    subprocess.run("git add -A", shell=True, cwd=str(cwd), capture_output=True, text=True)
    c = subprocess.run(f'git commit --no-verify -m {json.dumps(message)}',
                       shell=True, cwd=str(cwd), capture_output=True, text=True)
    if c.returncode != 0:
        return None
    r = subprocess.run("git rev-parse HEAD", shell=True, cwd=str(cwd), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def git_revert(paths, cwd):
    """Revert out-of-scope changes: `git checkout --` tracked files, delete untracked.
    `paths` from git_changed_files/git_changed_vs are a MIX: cwd-relative for files
    inside --root (rebased), repo-root-relative for files outside it (e.g. an unrelated
    dirty file elsewhere in a bigger repo) — see _rebase_to_cwd. A single `cwd` cannot
    resolve both forms correctly (git pathspecs are cwd-relative, not repo-root-relative),
    so every git call here runs from the repo TOP-LEVEL with the path re-based back to
    repo-root-relative first — resolves regardless of how deep --root is nested."""
    prefix = _git_root_prefix(cwd)
    proc = subprocess.run("git rev-parse --show-toplevel", shell=True, cwd=str(cwd),
                          capture_output=True, text=True)
    top = proc.stdout.strip() if proc.returncode == 0 else str(cwd)
    base = Path(cwd)
    for rel in paths:
        f = base / rel
        # `rel` may already be repo-root-relative (outside --root) OR cwd-relative
        # (inside --root, stripped by _rebase_to_cwd) — the string alone can't tell
        # which, so resolve by what actually exists on disk at the repo top-level.
        root_rel = rel
        if prefix and not (Path(top) / rel).exists() and f.exists():
            root_rel = f"{prefix}/{rel}"
        r = subprocess.run(f"git ls-files --error-unmatch -- {root_rel}",
                           shell=True, cwd=top, capture_output=True, text=True)
        if r.returncode == 0:
            subprocess.run(f"git checkout -- {root_rel}", shell=True, cwd=top,
                           capture_output=True, text=True)
        elif f.exists():
            try:
                f.unlink()
            except OSError:
                pass


# ── Reflexion: append one short lesson line to a managed wiki episodic page ──
_EPISODIC_HEADER = """---
type: concept
tags: [loop-runner, episodic-memory, reflexion]
---

# loop-runner — episodic memory (reflexion lessons)

Append-only lesson log written by `harness/scripts/loop-runner.py` on each failed
verify iteration. Managed file: code owns it, humans read it to carry lessons into the
next loop run. Created lazily on the first failing run (never at plan time).

## Origin
- Auto-managed by `harness/scripts/loop-runner.py` (reflexion step).

## Lessons
"""


def append_lesson(page_path, iteration, verify_cmd, exit_code, state_moved):
    """Append a one-line lesson on failure. Lazily creates the page with a valid
    OKF frontmatter + `## Origin` so it stays a structurally-valid wiki file."""
    if not page_path:
        return
    page = Path(page_path)
    page.parent.mkdir(parents=True, exist_ok=True)
    fresh = not page.exists()
    if state_moved is False:
        why = "state unchanged — revise made no progress (wrong edit target / non-actionable critique)"
    elif state_moved is True:
        why = "state changed but verify still red — critique may be off-target"
    else:
        why = "verify still red (progress detection off)"
    line = (
        f"- [{_now_iso()}] iter {iteration} · verify `{verify_cmd}` exit {exit_code} "
        f"· lesson: {why}\n"
    )
    with page.open("a", encoding="utf-8") as fh:
        if fresh:
            fh.write(_EPISODIC_HEADER)
        fh.write(line)


# ── The deterministic control loop ──────────────────────────────────────────
# DETERMINISM GUARD (harass-test finding, 2026-07-06): the loop rewrites files and
# re-runs `verify` many times per second. Python caches compiled bytecode in __pycache__
# keyed by source mtime — when a rewrite lands within the same mtime tick as the previous
# one, the interpreter reuses the STALE .pyc and verify judges OLD code. That silently
# produces false RED (a fixed frame escalates) AND false GREEN (a broken frame passes) —
# fatal for a pipeline whose whole premise is "verify exit-code is the trusted arbiter".
# Fix: run verify/revise with bytecode writing DISABLED so imports always read source.
# Harmless for non-Python verify commands. PYTHONHASHSEED pins hash-order for repeatability.
def _child_env():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONHASHSEED", "0")
    return env


def _run_cmd(cmd, cwd):
    proc = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True,
                          env=_child_env())
    tail = ((proc.stdout or "") + (proc.stderr or ""))[-_OUTPUT_TAIL:]
    return proc.returncode, tail


def run_loop(
    *,
    verify_cmd,
    revise_cmd=None,
    max_iter=6,
    budget_seconds=0,
    no_progress_k=0,
    escalate_after_iter=0,
    state_paths=None,
    scope_globs=None,
    protect_globs=None,
    changed_files_fn=None,
    revert_fn=None,
    baseline_ref=None,
    commit_on_success=False,
    commit_message=None,
    confirm_runs=0,
    episodic_page=None,
    reflexion_enabled=True,
    cwd=".",
    clock=time.monotonic,
    log_path=None,
    quiet=False,
):
    """Drive propose → verify → (critique → revise) under MANDATORY guards.

    Returns a run-log dict (also written to `log_path` as JSON if given).
    `clock` is injectable so the wall-clock guard is testable without sleeping.
    """
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1 (it is the hard backstop guard)")
    cwd = Path(cwd)
    state_paths = state_paths or []
    scope_globs = scope_globs or []
    protect_globs = protect_globs or []
    changed_files_fn = changed_files_fn or git_changed_files
    revert_fn = revert_fn or git_revert
    # Guard 6 baseline — hash the protected (test) files ONCE, before any revise.
    protect_baseline = _hash_paths(protect_globs, cwd)
    started_at = _now_iso()
    start = clock()
    iterations = []
    verdict = None
    reason = ""
    prev_hash = None
    streak = 0  # consecutive iterations with an unchanged state-hash
    it = 0

    while True:
        # GUARD 1 — wall-clock budget (checked before doing more work)
        elapsed = clock() - start
        if budget_seconds and elapsed >= budget_seconds:
            verdict, reason = TIMEOUT, f"wall-clock budget {budget_seconds}s exceeded ({elapsed:.1f}s)"
            break
        # GUARD 2 — max iterations (always-on hard backstop)
        if it >= max_iter:
            verdict, reason = MAX_ITER, f"reached max_iter={max_iter} without a passing verify"
            break

        it += 1
        # PROPOSE is the prior state (initial proposal, or last iter's revise).
        # VERIFY — deterministic; exit-code 0 == pass. The agent cannot override this.
        t0 = clock()
        exit_code, out_tail = _run_cmd(verify_cmd, cwd)
        rec = {
            "iter": it,
            "ts": _now_iso(),
            "verify_exit": exit_code,
            "duration_s": round(clock() - t0, 4),
            "verify_output_tail": out_tail,
        }

        if exit_code == 0:
            rec["state_hash"] = None
            rec["unchanged_streak"] = streak
            # GUARD 7 — CONFIRM (hermeticity, council finding 2026-07-06): a green verify
            # is only trusted if it REPRODUCES. Re-run it confirm_runs extra times; ANY
            # disagreement means the oracle is non-hermetic (flaky test, stale cache, hidden
            # state) → verdict FLAKY, fail-closed, never commit. This is what catches a
            # "SUCCESS with no code change" false-green that a single run cannot.
            confirm_exits = []
            for _ in range(max(0, confirm_runs)):
                ce, _ct = _run_cmd(verify_cmd, cwd)
                confirm_exits.append(ce)
            rec["confirm_exits"] = confirm_exits
            iterations.append(rec)
            if any(ce != 0 for ce in confirm_exits):
                verdict, reason = FLAKY, (
                    f"verify passed then a confirm re-run FAILED (exits={confirm_exits}) — "
                    f"non-hermetic/flaky oracle, refusing to trust green")
            else:
                verdict, reason = SUCCESS, f"verify passed on iteration {it}" + (
                    f" (+{confirm_runs} confirm)" if confirm_runs else "")
            break

        # progress detection on this failed iteration
        cur_hash = compute_state_hash(state_paths, cwd)
        if cur_hash is not None and prev_hash is not None and cur_hash == prev_hash:
            streak += 1
        else:
            streak = 0
        prev_hash = cur_hash
        rec["state_hash"] = cur_hash
        rec["unchanged_streak"] = streak
        iterations.append(rec)

        # REFLEXION — record a lesson from this failure
        if reflexion_enabled and episodic_page:
            state_moved = None
            if cur_hash is not None:
                state_moved = streak == 0  # streak 0 here means hash differed from prev
            append_lesson(episodic_page, it, verify_cmd, exit_code, state_moved)

        # GUARD 3 — no-progress (state-hash unchanged for K consecutive iterations)
        if no_progress_k and cur_hash is not None and streak >= no_progress_k:
            verdict, reason = NO_PROGRESS, (
                f"state-hash unchanged for {no_progress_k} consecutive iterations"
            )
            break
        # GUARD 4 — escalate-to-human (soft cap: hand off, don't silently give up)
        if escalate_after_iter and it >= escalate_after_iter:
            verdict, reason = ESCALATE, (
                f"reached escalate_after_iter={escalate_after_iter} — handing off to a human"
            )
            break

        # CRITIQUE → REVISE: THE QUARANTINED ADAPTER.
        # Real system: revise_cmd invokes the LLM (read verify output → edit code).
        # Default: stub/no-op so the loop runs deterministically without any LLM.
        if revise_cmd:
            r_exit, r_tail = _run_cmd(revise_cmd, cwd)
            rec["revise_exit"] = r_exit
            rec["revise_output_tail"] = r_tail
        else:
            rec["revise_exit"] = None  # no-op stub (LLM adapter not wired)

        # GUARD 6 — test-hash (fail-closed): the agent must not touch its own tests.
        if protect_baseline:
            cur = _hash_paths(protect_globs, cwd)
            if cur != protect_baseline:
                changed = sorted(set(cur) ^ set(protect_baseline)) or \
                    sorted(k for k in cur if cur.get(k) != protect_baseline.get(k))
                rec["protect_violation"] = changed
                verdict, reason = PROTECT_VIOLATION, (
                    f"protected file(s) changed by revise (fail-closed): {changed}"
                )
                break
        # GUARD 5 — scope diff-jail: revert edits OUTSIDE scope_code. Reverting keeps
        # the in-scope state frozen, so no-progress trips on an out-of-scope-only edit.
        if scope_globs:
            changed = changed_files_fn(cwd)
            outside = [f for f in changed
                       if not _in_globs(f, scope_globs) and not _in_globs(f, protect_globs)]
            if outside:
                revert_fn(outside, cwd)
                rec["scope_reverted"] = outside

    # Record the ACTUAL frame→code footprint (files the loop changed), and — if asked —
    # commit them into the isolated worktree (never main). Both feed traceability:
    # git blame → frame (via commit message), and /br status → real changed files.
    # FINAL SCOPE SWEEP (the prerequisite: "control the frame's code so it can never
    # touch outside its scope"). Per-iteration diff-jail can be short-circuited when the
    # loop breaks on another guard (e.g. PROTECT_VIOLATION fires BEFORE the diff-jail
    # step), leaving a stray out-of-scope edit on disk. So on EVERY termination we revert
    # every changed file not in scope_code. Result: the surviving worktree is PROVABLY
    # scope-clean — changed_files ⊆ scope_code, always — no matter why the loop stopped.
    attempted_out_of_scope = []
    if scope_globs:
        stray = [f for f in git_changed_vs(baseline_ref, cwd) if not _in_globs(f, scope_globs)]
        if stray:
            attempted_out_of_scope = stray
            revert_fn(stray, cwd)
    changed_files = git_changed_vs(baseline_ref, cwd)
    out_of_scope = [f for f in changed_files if not _in_globs(f, scope_globs)] if scope_globs else []
    scope_clean = (not out_of_scope) if scope_globs else None
    commit_sha = None
    if commit_on_success and verdict == SUCCESS and changed_files and scope_clean is not False:
        commit_sha = git_commit_all(commit_message or "frame: loop success", cwd)

    log = {
        "tool": "loop-runner",
        "verdict": verdict,
        "reason": reason,
        "iterations_run": it,
        "changed_files": changed_files,
        "scope_clean": scope_clean,
        "out_of_scope_files": out_of_scope,
        "attempted_out_of_scope": attempted_out_of_scope,
        "commit": commit_sha,
        "verify_cmd": verify_cmd,
        "revise_cmd": revise_cmd,
        "guards": {
            "max_iter": max_iter,
            "budget_seconds": budget_seconds,
            "no_progress_k": no_progress_k,
            "escalate_after_iter": escalate_after_iter,
            "scope_globs": scope_globs,
            "protect_globs": protect_globs,
        },
        "state_paths": state_paths,
        "started_at": started_at,
        "ended_at": _now_iso(),
        "elapsed_s": round(clock() - start, 4),
        "iterations": iterations,
    }
    if log_path:
        lp = Path(log_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not quiet:
        _print_summary(log, log_path)
    return log


def _print_summary(log, log_path):
    print(f"\nLoopRunner verdict: {log['verdict']}  ({log['reason']})")
    print(f"  iterations run : {log['iterations_run']}   elapsed: {log['elapsed_s']}s")
    for r in log["iterations"]:
        sh = (r.get("state_hash") or "—")
        sh = sh[:8] if sh != "—" else sh
        print(
            f"  iter {r['iter']}: verify exit={r['verify_exit']} "
            f"state={sh} streak={r.get('unchanged_streak', 0)}"
        )
    if log_path:
        print(f"  run-log: {log_path}")


# ── Config loading + CLI override merge ─────────────────────────────────────
def load_config(path):
    cfg = json.loads(json.dumps(DEFAULTS))  # deep copy of defaults
    if not path:
        return cfg
    p = Path(path)
    if not p.exists():
        print(f"[loop-runner] config not found: {path} — using built-in defaults", file=sys.stderr)
        return cfg
    if yaml is None:
        print("[loop-runner] PyYAML missing — using built-in defaults", file=sys.stderr)
        return cfg
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for section, vals in data.items():
        if isinstance(vals, dict) and isinstance(cfg.get(section), dict):
            cfg[section].update(vals)
        else:
            cfg[section] = vals
    return cfg


def cmd_run(args):
    cfg = load_config(args.config)
    g = cfg["guards"]
    settings = dict(
        verify_cmd=args.verify,
        revise_cmd=args.revise if args.revise is not None else cfg["revise"].get("cmd"),
        max_iter=args.max_iter if args.max_iter is not None else g["max_iter"],
        budget_seconds=args.budget_seconds if args.budget_seconds is not None else g["budget_seconds"],
        no_progress_k=args.no_progress_k if args.no_progress_k is not None else g["no_progress_k"],
        escalate_after_iter=args.escalate_after if args.escalate_after is not None else g["escalate_after_iter"],
        state_paths=args.state if args.state else cfg["progress"].get("state_paths") or [],
        scope_globs=args.scope if args.scope else cfg.get("scope", {}).get("code_globs") or [],
        protect_globs=args.protect if args.protect else cfg.get("scope", {}).get("protect_globs") or [],
        baseline_ref=args.baseline,
        commit_on_success=args.commit_on_success,
        commit_message=args.commit_message,
        confirm_runs=args.confirm,
        episodic_page=args.episodic if args.episodic is not None else cfg["reflexion"].get("episodic_memory_page"),
        reflexion_enabled=cfg["reflexion"].get("enabled", True),
        cwd=args.cwd,
        log_path=args.log if args.log is not None else cfg["run_log"].get("path"),
        quiet=args.quiet,
    )
    log = run_loop(**settings)
    return EXIT_CODE.get(log["verdict"], 1)


# ── Embedded unit self-test (no LLM, no external deps) ──────────────────────
def _py(code):
    """Build a shell cmd running an inline python snippet with the SAME interpreter."""
    return f'{sys.executable} -c {json.dumps(code)}'


def _scenario(name, **kw):
    quiet = kw.pop("_quiet", True)
    log = run_loop(quiet=quiet, **kw)
    return name, log


def selftest():
    results = []
    fake = {"n": 0}

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        episodic = d / "episodic.md"  # redirected: self-test NEVER touches the real wiki

        # 1) SUCCESS — counter file; verify passes on the 3rd call. Verify mutates
        #    the counter, so the state-hash moves each iter → no-progress can't fire.
        counter = d / "counter"
        counter.write_text("0")
        verify_pass3 = _py(
            "import pathlib,sys;"
            f"p=pathlib.Path({json.dumps(str(counter))});"
            "n=int(p.read_text() or 0)+1;p.write_text(str(n));"
            "sys.exit(0 if n>=3 else 1)"
        )
        results.append(_scenario(
            "SUCCESS@3", verify_cmd=verify_pass3, revise_cmd=None,
            max_iter=10, no_progress_k=2, state_paths=[str(counter)],
            episodic_page=str(episodic), cwd=str(d),
        ))

        # 2) MAX_ITER — verify never passes; revise APPENDS a line each iter so the
        #    state-hash moves → no-progress never fires → only max_iter stops it.
        work = d / "work.txt"
        work.write_text("")
        verify_fail = _py("import sys;sys.exit(1)")
        revise_touch = _py(
            "import pathlib,time;"
            f"p=pathlib.Path({json.dumps(str(work))});"
            "p.write_text(p.read_text()+f'edit-{time.time_ns()}\\n')"
        )
        results.append(_scenario(
            "MAX_ITER@3", verify_cmd=verify_fail, revise_cmd=revise_touch,
            max_iter=3, no_progress_k=2, state_paths=[str(work)],
            episodic_page=str(episodic), cwd=str(d),
        ))

        # 3) NO_PROGRESS — verify never passes; revise is a no-op stub → state frozen
        #    → unchanged for k=2 consecutive iters → stops at iter 3.
        frozen = d / "frozen.txt"
        frozen.write_text("constant")
        results.append(_scenario(
            "NO_PROGRESS@3", verify_cmd=verify_fail, revise_cmd=None,
            max_iter=10, no_progress_k=2, state_paths=[str(frozen)],
            episodic_page=str(episodic), cwd=str(d),
        ))

        # 4) TIMEOUT — fake clock; wall-clock budget enforced without sleeping.
        def fake_clock():
            fake["n"] += 1
            return (fake["n"] - 1) * 3  # 0,3,6,9,... seconds
        results.append(_scenario(
            "TIMEOUT", verify_cmd=verify_fail, revise_cmd=None,
            max_iter=100, no_progress_k=0, budget_seconds=5,
            state_paths=[], cwd=str(d), clock=fake_clock,
        ))

        # 5) ESCALATE — soft cap hands off to a human at iter 2.
        results.append(_scenario(
            "ESCALATE@2", verify_cmd=verify_fail, revise_cmd=None,
            max_iter=100, no_progress_k=0, escalate_after_iter=2,
            state_paths=[], cwd=str(d),
        ))

        # 6) SCOPE_JAIL — revise edits an OUT-OF-SCOPE file each iter; the diff-jail
        #    reverts it, so the in-scope state stays frozen → NO_PROGRESS at k=2.
        sd = d / "scope"; sd.mkdir()
        (sd / "inn").mkdir(); (sd / "inn" / "keep.txt").write_text("stable")
        (sd / "outt").mkdir()
        revise_out = _py(
            "import pathlib,time;"
            f"p=pathlib.Path({json.dumps(str(sd / 'outt' / 'junk.txt'))});"
            "p.write_text(f'junk-{time.time_ns()}')"
        )
        fake_changed = lambda c: [q.relative_to(c).as_posix()
                                  for q in Path(c).rglob("*") if q.is_file() and "junk" in q.name]
        fake_revert = lambda paths, c: [ (Path(c) / r).unlink() for r in paths if (Path(c) / r).exists() ]
        results.append(_scenario(
            "SCOPE_JAIL@3", verify_cmd=verify_fail, revise_cmd=revise_out,
            max_iter=10, no_progress_k=2, state_paths=["inn/**"], scope_globs=["inn/**"],
            changed_files_fn=fake_changed, revert_fn=fake_revert, cwd=str(sd),
        ))
        scope_evidence = any(r.get("scope_reverted") for r in results[-1][1]["iterations"])
        # post-condition: after diff-jail reverts, NO out-of-scope file survives → scope_clean
        scope_clean_evidence = (results[-1][1].get("scope_clean") is True
                                and not results[-1][1].get("out_of_scope_files"))

        # 7) PROTECT — revise tampers with a protected (test) file → fail-closed at iter 1.
        pd = d / "protect"; pd.mkdir()
        (pd / "prot").mkdir(); (pd / "prot" / "t.txt").write_text("original test")
        revise_tamper = _py(
            "import pathlib,time;"
            f"p=pathlib.Path({json.dumps(str(pd / 'prot' / 't.txt'))});"
            "p.write_text(f'tampered-{time.time_ns()}')"
        )
        results.append(_scenario(
            "PROTECT@1", verify_cmd=verify_fail, revise_cmd=revise_tamper,
            max_iter=10, no_progress_k=0, protect_globs=["prot/**"], cwd=str(pd),
        ))
        protect_evidence = any(r.get("protect_violation") for r in results[-1][1]["iterations"])

        # 8) COMMIT_ON_SUCCESS — in a real temp git repo: on SUCCESS the loop records the
        #    actual changed files AND commits them into the worktree branch (traceability).
        gd = d / "gitrepo"; gd.mkdir()
        def _git(cmd):
            subprocess.run(cmd, shell=True, cwd=str(gd), capture_output=True, text=True)
        _git("git init -q"); _git("git config user.email t@t"); _git("git config user.name t")
        work = gd / "work.txt"; work.write_text("todo")
        _git("git add -A"); _git('git commit -q -m base --no-verify')
        verify_done = _py(
            "import pathlib,sys;"
            f"p=pathlib.Path({json.dumps(str(work))});"
            "sys.exit(0 if 'done' in p.read_text() else 1)"
        )
        revise_done = _py(
            "import pathlib;"
            f"p=pathlib.Path({json.dumps(str(work))});p.write_text('done')"
        )
        commit_log = run_loop(
            verify_cmd=verify_done, revise_cmd=revise_done, max_iter=5, no_progress_k=0,
            state_paths=[str(work)], cwd=str(gd), commit_on_success=True,
            commit_message="frame(selftest): mark done [S0.0]", quiet=True,
        )
        results.append(("COMMIT_ON_SUCCESS", commit_log))
        commit_made = bool(commit_log.get("commit"))
        changed_captured = commit_log.get("changed_files") == ["work.txt"]
        # verify the commit really landed with our message
        _sha = subprocess.run("git log -1 --pretty=%s", shell=True, cwd=str(gd),
                              capture_output=True, text=True).stdout.strip()
        commit_msg_ok = _sha == "frame(selftest): mark done [S0.0]"

        # 10) FLAKY/CONFIRM guard — a verify that passes the first time but FAILS a confirm
        #     re-run must be FLAKY, not SUCCESS (non-hermetic oracle → false-green refused).
        flk = d / "flaky"; flk.mkdir()
        ctr = flk / "ctr"; ctr.write_text("0")
        # verify: exit 0 on the 1st call, exit 1 thereafter — green then flakes red on confirm
        verify_flaky = _py(
            "import pathlib,sys;"
            f"p=pathlib.Path({json.dumps(str(ctr))});"
            "n=int(p.read_text());p.write_text(str(n+1));sys.exit(0 if n==0 else 1)"
        )
        flaky_log = run_loop(
            verify_cmd=verify_flaky, revise_cmd=None, max_iter=3, no_progress_k=0,
            confirm_runs=2, state_paths=[], cwd=str(flk), quiet=True,
        )
        results.append(("FLAKY_CONFIRM", flaky_log))

        # 9) STALE-PYC GUARD (regression for the harass-test finding): _run_cmd must run
        #    children with bytecode writing OFF, so a fast file rewrite is never judged
        #    against a cached .pyc. Assert no __pycache__ appears when importing via _run_cmd.
        pyd = d / "pyc"; pyd.mkdir()
        (pyd / "m.py").write_text("v = 2\n")
        _run_cmd(f'{sys.executable} -c "import m"', pyd)
        stale_pyc_guard = not list(pyd.glob("__pycache__/*.pyc"))

        episodic_written = episodic.exists()

    # Assertions (required scenarios 1-3 + guard-proof scenarios 4-5)
    expect = {
        "SUCCESS@3": (SUCCESS, 3),
        "MAX_ITER@3": (MAX_ITER, 3),
        "NO_PROGRESS@3": (NO_PROGRESS, 3),
        "TIMEOUT": (TIMEOUT, None),
        "ESCALATE@2": (ESCALATE, 2),
        "SCOPE_JAIL@3": (NO_PROGRESS, 3),
        "PROTECT@1": (PROTECT_VIOLATION, 1),
        "COMMIT_ON_SUCCESS": (SUCCESS, 2),
        "FLAKY_CONFIRM": (FLAKY, 1),
    }
    print("LoopRunner self-test (no LLM) — deterministic guard scenarios\n" + "-" * 62)
    ok = True
    for name, log in results:
        want_verdict, want_iter = expect[name]
        got_iter = log["iterations_run"]
        passed = log["verdict"] == want_verdict and (want_iter is None or got_iter == want_iter)
        ok = ok and passed
        tag = "PASS" if passed else "FAIL"
        iters = f"iter={got_iter}" + (f"/exp {want_iter}" if want_iter is not None else "")
        print(f"  [{tag}] {name:<14} verdict={log['verdict']:<11} {iters:<14} ({log['reason']})")
    print("-" * 62)
    print(f"  reflexion: episodic page written by failing runs = {episodic_written}")
    print(f"  guard 5 evidence: scope diff-jail reverted out-of-scope edits = {scope_evidence}")
    print(f"  guard 6 evidence: protected-file tamper recorded              = {protect_evidence}")
    print(f"  trace evidence  : changed_files captured = {changed_captured} · commit made = {commit_made} · msg ok = {commit_msg_ok}")
    print(f"  scope post-check: no out-of-scope file survived (scope_clean) = {scope_clean_evidence}")
    print(f"  determinism     : verify children write no .pyc (stale-pyc guard) = {stale_pyc_guard}")
    ok = (ok and scope_evidence and protect_evidence and changed_captured and commit_made
          and commit_msg_ok and scope_clean_evidence and stale_pyc_guard)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


# ── Entry point ─────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="loop-runner.py",
        description="Deterministic guardrailed agent-loop driver (propose→verify→revise + guards).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run the guarded loop around a VERIFY shell command")
    r.add_argument("--verify", required=True, help="shell cmd; exit 0 == pass (e.g. 'pytest -q')")
    r.add_argument("--config", default=None, help="path to loop-runner.config.yaml")
    r.add_argument("--revise", default=None, help="shell cmd for the (adapter) revise step; default = config/no-op")
    r.add_argument("--state", action="append", default=None, help="state-hash path/glob (repeatable)")
    r.add_argument("--scope", action="append", default=None, help="diff-jail: glob the agent MAY edit (repeatable); edits outside are reverted")
    r.add_argument("--protect", action="append", default=None, help="test-hash: glob the agent must NOT edit (repeatable); a change stops the loop fail-closed")
    r.add_argument("--baseline", default=None, help="git ref to diff against for the run-log's changed_files (actual frame→code footprint)")
    r.add_argument("--commit-on-success", action="store_true", help="on SUCCESS, commit changes into the (isolated worktree) branch — never main")
    r.add_argument("--commit-message", default=None, help="commit message (e.g. 'frame(<id>): <goal> [clauses]')")
    r.add_argument("--confirm", type=int, default=0, help="on green, re-run verify N more times; any disagreement → FLAKY (hermeticity guard)")
    r.add_argument("--log", default=None, help="run-log JSON output path")
    r.add_argument("--max-iter", type=int, default=None)
    r.add_argument("--budget-seconds", type=float, default=None)
    r.add_argument("--no-progress-k", type=int, default=None)
    r.add_argument("--escalate-after", type=int, default=None)
    r.add_argument("--episodic", default=None, help="episodic-memory wiki page for reflexion lessons")
    r.add_argument("--cwd", default=".", help="working directory for verify/revise commands")
    r.add_argument("--quiet", action="store_true")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("selftest", help="run 5 deterministic guard scenarios (no LLM)")
    s.set_defaults(func=lambda _a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
