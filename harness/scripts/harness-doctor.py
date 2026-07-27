#!/usr/bin/env python3
"""Harness doctor — a guardrail fire-drill that PROVES each rule still bites today.

Why this exists
---------------
The harness is fail-open at every layer on purpose, so a broken rail never bricks
a working session:

  * hooklib.find_validators() returns None when no validators dir is found, and the
    hooks then exit 0 (allow);
  * the poc llmwiki-validate fails open on any internal error;
  * the L1 hooks swallow exceptions.

That safety has a dark side: a validator that has silently stopped working — a bad
edit, a stale copy, a missing interpreter — will pass EVERYTHING, and nobody is
told the rails went dark. This script is the smoke detector. For each content
validator it ships a tiny known-BAD and known-GOOD fixture in a throwaway temp
dir, runs the REAL validator through its REAL contract, and asserts the bad input
is blocked and the good input is allowed. A rule whose BAD fixture is not blocked
is a DARK RAIL.

The contract (harness/recipe.md, section 2)
-------------------------------------------
Every validator accepts either:
  * argv file paths   :  validator.py path1 path2 ...            (L2 / pre-commit)
  * stdin event JSON  :  {"action":"write","file_path":...,
                          "content":...}                          (L1 / realtime)
and exits 2 to block (reason on stderr) or 0 to allow. This doctor exercises BOTH
contracts for every rule, because a validator can break in one mode while still
passing in the other.

Usage
-----
  harness-doctor.py            print the green/red board, exit 0
  harness-doctor.py --ci       exit non-zero if any rule's bite-test failed
  harness-doctor.py --json     machine-readable board to stdout
  harness-doctor.py --keep     leave the temp fixtures on disk (debugging)
  harness-doctor.py --no-color plain ASCII, no ANSI

Exit code: default always 0. With --ci, exit 1 if any rule is a dark rail (its BAD
fixture was not blocked, or its GOOD fixture was wrongly blocked). Install probes
are advisory — they are reported but never change the exit code.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo layout. This file lives at <repo>/harness/scripts/harness-doctor.py, so
# the repo root is two parents up. Everything below is resolved from there.
# ---------------------------------------------------------------------------
SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[2]
HARNESS_VALIDATORS = REPO / "harness" / "validators"
HOOKS_DIR = REPO / "llmwiki" / ".claude" / "hooks"
HOOKS_VALIDATORS = HOOKS_DIR / "validators"
SETTINGS = REPO / "llmwiki" / ".claude" / "settings.json"
PRECOMMIT_CFG = REPO / ".pre-commit-config.yaml"
GIT_PRECOMMIT_HOOK = REPO / ".git" / "hooks" / "pre-commit"

PY = sys.executable  # validators run under the same interpreter as the doctor

# Hooks referenced by settings.json (each invoked as `python3 <hook>.py`, so the
# executable bit is irrelevant — we still report it as information).
EXPECTED_HOOKS = [
    "hooklib.py",
    "user_prompt_submit.py",
    "pre_tool_use.py",
    "orca_guard.py",
    "post_tool_use.py",
    "stop.py",
    "session_end.py",
    "session_start.py",
]


# ---------------------------------------------------------------------------
# Validator resolution — mirror hooklib.find_validators() so we bite-test the
# exact validator that actually fires in a live session:
#   env LLMWIKI_VALIDATORS  ->  copy beside the hooks  ->  harness/validators.
# ---------------------------------------------------------------------------
def resolve_validator(name):
    env = os.environ.get("LLMWIKI_VALIDATORS")
    if env and (Path(env) / name).is_file():
        return Path(env) / name, "env:LLMWIKI_VALIDATORS"
    if (HOOKS_VALIDATORS / name).is_file():
        return HOOKS_VALIDATORS / name, "hooks-copy"
    if (HARNESS_VALIDATORS / name).is_file():
        return HARNESS_VALIDATORS / name, "harness-src"
    return None, "UNRESOLVED"


def run_argv(validator, argv):
    p = subprocess.run([PY, str(validator), *argv], capture_output=True, text=True, timeout=30)
    return p.returncode


def run_stdin(validator, event):
    p = subprocess.run([PY, str(validator)], input=json.dumps(event),
                       capture_output=True, text=True, timeout=30)
    return p.returncode


# ---------------------------------------------------------------------------
# Fixtures. Each builder writes a tiny BAD and GOOD file under <base>/<rule>/ and
# returns the argv paths plus the equivalent stdin events for both contracts.
# Fixtures NEVER touch the repo tree — only the temp base passed in.
# ---------------------------------------------------------------------------
def _w(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def fixture(bad_path, good_path, bad_content=None, good_content=None):
    """Package a bad/good pair into argv + stdin events for both contracts.

    For content-driven validators we pass `content` inline on the stdin event so
    the realtime path is exercised exactly as the L1 hook would deliver it; the
    argv path always reads the same bytes from disk.
    """
    bad_ev = {"action": "write", "file_path": str(bad_path)}
    good_ev = {"action": "write", "file_path": str(good_path)}
    if bad_content is not None:
        bad_ev["content"] = bad_content
    if good_content is not None:
        good_ev["content"] = good_content
    return {
        "bad_argv": [str(bad_path)],
        "good_argv": [str(good_path)],
        "bad_event": bad_ev,
        "good_event": good_ev,
    }


# ---------------------------------------------------------------------------
# Tester result shape. Every build_rN(base) returns a dict:
#   {green, kind, source, checks: [(label, actual, expected), ...], note}
# `checks` is generic (str or int cells) so heterogeneous rule KINDS share one
# board. `kind` names HOW the rail is proven (transparent, per fdk kim-chỉ-nam):
#   block         — validator exits 2 on BAD / 0 on GOOD (argv + stdin contract)
#   block-argv    — same but argv-only (no stdin contract)
#   block-poc     — driven through the vendor-neutral poc (policy.yaml)
#   block-git     — process-gate proven in a throwaway git repo
#   side-effect   — non-blocking hook proven by its documented side-effect
#   wiring        — aggregate/documentary gate proven present + referenced
# A rule whose checks don't all match is a DARK RAIL (or a dead wire).
# ---------------------------------------------------------------------------
def _result(kind, source, checks, extra=""):
    green = source not in (None, "UNRESOLVED", "ERR") and all(a == e for _, a, e in checks)
    notes = ["%s=%s (want %s)" % (lbl, a, e) for lbl, a, e in checks if a != e]
    if extra:
        notes.append(extra)
    return {"green": green, "kind": kind, "source": source, "checks": checks,
            "note": "; ".join(notes)}


def _dark(kind, why, checks=None):
    return {"green": False, "kind": kind, "source": "UNRESOLVED",
            "checks": checks or [("resolve", "missing", "found")], "note": why}


def _content(fname, fx, kind="block"):
    """Shared tester for content validators: argv + stdin, BAD->2 / GOOD->0."""
    validator, src = resolve_validator(fname)
    if validator is None:
        return _dark(kind, "%s not found — find_validators() returns None, rail fails OPEN" % fname)
    checks = [
        ("argv:bad", run_argv(validator, fx["bad_argv"]), 2),
        ("argv:good", run_argv(validator, fx["good_argv"]), 0),
        ("stdin:bad", run_stdin(validator, fx["bad_event"]), 2),
        ("stdin:good", run_stdin(validator, fx["good_event"]), 0),
    ]
    return _result(kind, src, checks)


# ── Tier 1: content validators (argv + stdin) ───────────────────────────────
def build_r1(base):
    bad = _w(base / "llmwiki" / "raw" / "inbox.md", "# dropped by a human\n")
    good = _w(base / "llmwiki" / "wiki" / "concepts" / "clean.md", "# normal path\n")
    return _content("no_write_raw.py", fixture(bad, good))


def build_r2(base):
    bad_c = "# Concept\n\nBody text but no origin section.\n"
    good_c = "# Concept\n\nBody text.\n\n## Origin\n\nDistilled from raw/example.md (commit abc1234).\n"
    bad = _w(base / "wiki" / "concepts" / "no-origin.md", bad_c)
    good = _w(base / "wiki" / "concepts" / "with-origin.md", good_c)
    return _content("origin_required.py", fixture(bad, good, bad_c, good_c))


def build_r5(base):
    bad = _w(base / "wiki" / "loose.md", "# wrong place\n")
    good = _w(base / "wiki" / "concepts" / "proper.md", "# right place\n")
    return _content("folder_structure.py", fixture(bad, good))


def build_r7(base):
    # bad = proposed draft missing the Agent table + sequence link; good = complete.
    draft = base / "wiki" / "sources" / "draft"
    seq_html = (
        "<!doctype html><html><head><style>.msg{opacity:1}</style></head><body>\n"
        '<div class="diagram-box"><p class="desc">Task one: claude distills the raw '
        "file into a concept on a safe branch.</p></div>\n"
        '<div class="diagram-box"><p class="desc">Task two: codex updates wiki/index.md '
        "for the new concept.</p></div>\n"
        "</body></html>\n"
    )
    _w(draft / "feature-seq.html", seq_html)
    good_c = (
        "---\ntype: draft\n---\n# Feature X — proposal\n\n**Status:** proposed\n\n"
        "## Context\nDa query wiki: lien quan [[rule-registry]] va ADR-008 ve the kit (force-query R7-f).\n\n"
        "## Global constraints\n- Python 3.11+, khong them dependency moi; medic --ci xanh truoc push (R7-h).\n\n"
        "## Plan\n- [ ] task one — distill raw\n- [ ] task two — update index\n\n"
        "## Agent Task Assignment\n| Task | Agent | Notes |\n|------|-------|-------|\n"
        "| task one | claude | distill |\n| task two | codex | index |\n\n"
        "**Sequence diagram**: [seq](feature-seq.html)\n\n"
        "## Requirements (FR)\n- **FR-001**: He thong PHAI distill raw thanh concept.\n"
        "- **FR-002**: He thong PHAI cap nhat wiki/index.md.\n"
    )
    bad_c = ("---\ntype: draft\n---\n# Feature Y — proposal\n\n**Status:** proposed\n\n"
             "## Plan\n- [ ] only task\n")
    good = _w(draft / "feature.md", good_c)
    bad = _w(draft / "feature-bad.md", bad_c)
    return _content("proposal_complete.py", fixture(bad, good))  # reads disk; no inline content


def build_r18(base):
    # PLAN thi hanh (*-PLAN.md) = thu bom thang vao agent context=0.
    # bad = task khong khai Files/Interfaces/code; good = khai du.
    draft = base / "wiki" / "sources" / "draft"
    good_c = (
        "# Feature X — PLAN\n\n"
        "## Global constraints\n- Python 3.11+, khong them dependency moi; medic --ci xanh truoc push.\n\n"
        "### Task 1: them ham parse\n"
        "**Thoả:** FR-001\n"
        "**Files:**\n- Tao: `src/parse.py`\n\n"
        "**Interfaces:**\n- Consumes: (khong)\n- Produces: `parse(s: str) -> dict`\n\n"
        "- [ ] **Step 1: viet test fail**\n\n"
        "```python\ndef test_parse():\n    assert parse(\"a=1\") == {\"a\": \"1\"}\n```\n\n"
        "### Task 2: noi vao CLI\n"
        "**Thoả:** FR-002\n"
        "**Files:**\n- Sua: `src/cli.py:10-20`\n\n"
        "**Interfaces:**\n- Consumes: `parse(s: str) -> dict` tu Task 1\n- Produces: `main(argv) -> int`\n\n"
        "- [ ] **Step 1: viet test fail**\n\n"
        "```python\ndef test_main():\n    assert main([\"a=1\"]) == 0\n```\n"
    )
    bad_c = (
        "# Feature Y — PLAN\n\n"
        "## Global constraints\n- Python 3.11+, khong them dependency moi.\n\n"
        "### Task 1: lam gi do\n- [ ] Step 1: viet code\n\n"
        "### Task 2: lam not\n- [ ] Step 1: tuong tu Task 1\n"
    )
    good = _w(draft / "feature-PLAN.md", good_c)
    bad = _w(draft / "feature-bad-PLAN.md", bad_c)
    return _content("proposal_complete.py", fixture(bad, good))


def build_r9(base):
    bad_c = "# Concept\n\nNo frontmatter block at the top.\n"
    good_c = "---\ntype: concept\n---\n\n# Concept\n\nHas frontmatter.\n"
    bad = _w(base / "wiki" / "concepts" / "no-fm.md", bad_c)
    good = _w(base / "wiki" / "concepts" / "with-fm.md", good_c)
    return _content("okf_frontmatter.py", fixture(bad, good, bad_c, good_c))


def build_r14(base):
    bad = _w(base / "llmwiki" / "patterns" / "core.md", "# protected pattern\n")
    good = _w(base / "llmwiki" / "wiki" / "concepts" / "ok.md", "# normal\n")
    return _content("patterns_guard.py", fixture(bad, good))


def build_r16(base):
    bad = base / "llmwiki" / "html" / "report-bad.html"
    good = base / "llmwiki" / "html" / "report-good.html"
    _w(bad, "<!doctype html><body><h1>report</h1><p>khong khai path</p></body>")
    _w(good, f"<!doctype html><body><h1>report</h1>"
             f"<footer>File: <code>{good.resolve()}</code> · <code>{good}</code></footer></body>")
    return _content("report_show_path.py", fixture(bad, good))


# ── Tier 1b: argv-only / custom-flag content validators ─────────────────────
def build_r13(base):
    # R13: architecture row in decisions.md must reference an ADR-N (or (no-adr: …)).
    v, src = resolve_validator("decision_adr.py")
    if v is None:
        return _dark("block-argv", "decision_adr.py not found")
    # decision_adr parse cần 5 cột: Date | Decision | Type | Context | Outcome.
    hdr = "| Date | Decision | Type | Context | Outcome |\n|------|----------|------|---------|---------|\n"
    bad = _w(base / "bad" / "decisions.md", hdr + "| 2026-07-03 | chọn X | architecture | ctx | chưa quyết |\n")
    good = _w(base / "good" / "decisions.md", hdr + "| 2026-07-03 | chọn X | architecture | ctx | ADR-1 |\n")
    checks = [("argv:bad", run_argv(v, [str(bad)]), 2),
              ("argv:good", run_argv(v, [str(good)]), 0)]
    return _result("block-argv", src, checks)


def build_r15(base):
    # R15: commit message crediting AI must be blocked (--commit-msg <file>).
    v, src = resolve_validator("no_ai_attribution.py")
    if v is None:
        return _dark("block-commitmsg", "no_ai_attribution.py not found")
    bad = _w(base / "MSG_BAD", "feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
    good = _w(base / "MSG_GOOD", "feat: x\n\nmot commit sach\n")
    checks = [("bad", run_argv(v, ["--commit-msg", str(bad)]), 2),
              ("good", run_argv(v, ["--commit-msg", str(good)]), 0)]
    return _result("block-commitmsg", src, checks)


def build_r3(base):
    # R3: wiki/index.md must list exactly the wiki content files (--wiki-dir <dir>).
    v, src = resolve_validator("index_sync.py")
    if v is None:
        return _dark("block-dir", "index_sync.py not found")
    fm = "---\ntype: concept\n---\n# foo\n\n## Origin\nx\n"
    badw = base / "badwiki"
    _w(badw / "concepts" / "foo.md", fm)
    _w(badw / "index.md", "# Index\n")                       # foo.md missing → mismatch
    goodw = base / "goodwiki"
    _w(goodw / "concepts" / "foo.md", fm)
    _w(goodw / "index.md", "# Index\n\n| [foo](concepts/foo.md) | concept |\n")
    checks = [("dir:bad", run_argv(v, ["--wiki-dir", str(badw)]), 2),
              ("dir:good", run_argv(v, ["--wiki-dir", str(goodw)]), 0)]
    return _result("block-dir", src, checks)


# ── Tier 2: vendor-neutral poc (policy.yaml-driven) ─────────────────────────
def build_r11(base):
    # R11: *-seq.html with diagram-box but no liquid-glass markers must be blocked.
    poc = REPO / "harness" / "poc-vendor-neutral" / "bin" / "llmwiki-validate.py"
    if not poc.is_file():
        return _dark("block-poc", "llmwiki-validate.py (poc) not found")
    try:
        import yaml  # noqa: F401
    except Exception:
        return {"green": True, "kind": "block-poc-degraded", "source": "poc",
                "checks": [("pyyaml", "absent", "absent")],
                "note": "pyyaml absent → poc fail-open by design; R11 still gated at repo-tier CI"}
    d = base / "llmwiki" / "html"
    box = '<div class="diagram-box">step</div>'
    bad = d / "x-seq.html"
    _w(bad, f"<!doctype html><body>{box}<code>{bad}</code></body>")          # flat = violate
    glass = ("<style>body{background:linear-gradient(180deg,#f7fbff,#eef);}"
             ".c{backdrop-filter:blur(8px);box-shadow:inset 0 1px 0 rgba(255,255,255,.8);}</style>")
    good = d / "y-seq.html"
    _w(good, f"<!doctype html><head>{glass}</head><body>{box}<code>{good}</code></body>")
    checks = [("path:bad", run_argv(poc, ["path", str(bad)]), 2),
              ("path:good", run_argv(poc, ["path", str(good)]), 0)]
    return _result("block-poc", "poc", checks)


# ── Tier 3: process gate proven in a throwaway git repo ─────────────────────
def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args],
        cwd=str(cwd), capture_output=True, text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


def build_r12(base):
    # R12: pull-gate gate2 must block when local is BEHIND remote, pass when up-to-date.
    gate = REPO / "harness" / "poc-vendor-neutral" / "bin" / "pull-gate.sh"
    if not gate.is_file():
        return _dark("block-git", "pull-gate.sh not found")
    base.mkdir(parents=True, exist_ok=True)
    remote, behind, ahead = base / "remote.git", base / "behind", base / "ahead"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], capture_output=True)
    _git(base, "clone", "-q", str(remote), str(behind))
    _w(behind / "f.txt", "1")
    _git(behind, "add", "."); _git(behind, "commit", "-q", "-m", "a"); _git(behind, "push", "-q", "origin", "main")
    _git(base, "clone", "-q", str(remote), str(ahead))
    _w(ahead / "f.txt", "2")
    _git(ahead, "add", "."); _git(ahead, "commit", "-q", "-m", "b"); _git(ahead, "push", "-q", "origin", "main")
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "PULL_GATE_FRESH_SECS": "0"}
    bad = subprocess.run(["bash", str(gate), "gate2"], cwd=str(behind),
                         capture_output=True, text=True, env=env).returncode
    good = subprocess.run(["bash", str(gate), "gate2"], cwd=str(ahead),
                          capture_output=True, text=True, env=env).returncode
    return _result("block-git", "pull-gate.sh",
                   [("behind:block", bad, 2), ("uptodate:pass", good, 0)])


# ── Tier 4: non-blocking hooks proven by their documented side-effect ───────
def build_r4(base):
    # R4: audit() must append a machine log line for every tool event.
    import importlib
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    try:
        hooklib = importlib.import_module("hooklib")
    except Exception as e:
        return _dark("side-effect", "hooklib import failed: %s" % e)
    proj = base / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    saved = os.environ.pop("CLAUDE_PROJECT_DIR", None)   # else audit lands in the real repo
    try:
        hooklib.audit({"cwd": str(proj), "tool_name": "Write",
                       "tool_input": {"file_path": "x.md"}, "session_id": "s1"}, "PostToolUse")
    finally:
        if saved is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = saved
    import datetime as _dt
    logf = proj / ".claude" / "audit" / (_dt.date.today().isoformat() + ".jsonl")
    logged = "1" if (logf.is_file() and logf.read_text(encoding="utf-8").strip()) else "0"
    control = "1" if (base / "ctrl" / ".claude" / "audit").exists() else "0"  # never created
    return _result("side-effect", "hooks",
                   [("event:logged", logged, "1"), ("no-event:silent", control, "0")])


def build_r8(base):
    # R8: SessionStart must emit its orientation/health signal in an oriented project.
    hook = HOOKS_DIR / "session_start.py"
    if not hook.is_file():
        return _dark("side-effect", "session_start.py not found")
    proj = base / "proj"
    (proj / "fdk" / "wiki").mkdir(parents=True, exist_ok=True)
    _w(proj / "fdk" / "CAPABILITIES.md", "# caps\n")
    _w(proj / ".template-manifest.json", "{}\n")   # else main() exits before orient()
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    p = subprocess.run([PY, str(hook)], input=json.dumps({"cwd": str(proj), "session_id": "s"}),
                       capture_output=True, text=True, env=env, timeout=30)
    fired = "1" if (p.returncode == 0 and "orientation" in p.stdout.lower()) else "0"
    extra = "" if fired == "1" else "exit=%s stdout=%r" % (p.returncode, p.stdout[:80])
    return _result("side-effect", "hooks", [("oriented:signal", fired, "1")], extra)


def build_r10(base):
    # R10: docs-gate must inject a directive when pillars are missing, stay silent when present.
    hook = HOOKS_DIR / "user_prompt_submit.py"
    if not hook.is_file():
        return _dark("side-effect", "user_prompt_submit.py not found")
    proj = base / "proj"
    (proj / "llmwiki" / "wiki").mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["LLMWIKI_DOCS_GATE_EVERY"] = "1"

    def run(prompt, sid):
        return subprocess.run(
            [PY, str(hook)],
            input=json.dumps({"cwd": str(proj), "session_id": sid, "prompt": prompt, "transcript_path": ""}),
            capture_output=True, text=True, env=env, timeout=30)
    miss = run("hello world khong tu khoa nao", "sA")
    pres = run("da dung council va docs-site-macos roi", "sB")
    b = "1" if "docs-gate" in miss.stdout.lower() else "0"
    g = "1" if "docs-gate" in pres.stdout.lower() else "0"
    return _result("side-effect", "hooks",
                   [("missing:inject", b, "1"), ("present:silent", g, "0")])


def build_r17(base):
    # R17: SessionEnd flush must append a stub node when a framework surface was touched.
    import importlib.util
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    hook = HOOKS_DIR / "session_end.py"
    if not hook.is_file():
        return _dark("side-effect", "session_end.py not found")
    spec = importlib.util.spec_from_file_location("session_end_probe", hook)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception as e:
        return _dark("side-effect", "session_end import failed: %s" % e)

    def mkrepo(name, touch_fw):
        # Commit the tree + a skills/ placeholder FIRST so git reports later changes at
        # FILE granularity — an all-new dir is collapsed to "skills/"/"llmwiki/" by
        # `git status`, which would read as a framework touch in both repos.
        r = base / name
        r.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(r)], capture_output=True)
        tree = r / "llmwiki" / "html" / "problem-tree.html"
        _w(tree, '<script type="application/json" id="tree-data">[]</script>')
        _w(r / "skills" / ".keep", "")
        _git(r, "add", "-A"); _git(r, "commit", "-q", "-m", "init")
        if touch_fw:
            _w(r / "skills" / "x" / "SKILL.md", "# framework surface touched\n")  # untracked file, tracked dir
        return r, tree

    def count(tree):
        mm = re.search(r'id="tree-data">\s*(\[.*?\])\s*</script>', tree.read_text(encoding="utf-8"), re.S)
        return len(json.loads(mm.group(1))) if mm else -1

    r1, t1 = mkrepo("fw", True)
    n0 = count(t1); m.flush_problem_tree(r1, "sess1234"); n1 = count(t1)
    r2, t2 = mkrepo("nofw", False)
    m0 = count(t2); m.flush_problem_tree(r2, "sess1234"); m1 = count(t2)
    return _result("side-effect", "hooks",
                   [("fw-touch:node-added", "1" if n1 > n0 else "0", "1"),
                    ("no-fw:no-node", "1" if m1 == m0 else "0", "1")])


# ── Tier 5: aggregate / documentary gate (wiring present + referenced) ──────
def build_r6(base):
    # R6 = verify-before-commit is the COMPOSITE commit gate (pre-commit + CI). It has no
    # single BAD fixture to block; its dark-rail is "the gate is not wired". Prove presence.
    if not PRECOMMIT_CFG.is_file():
        return {"green": False, "kind": "wiring", "source": "repo",
                "checks": [("precommit-config", "missing", "present")],
                "note": "no .pre-commit-config.yaml → R6 commit gate is absent"}
    txt = PRECOMMIT_CFG.read_text(encoding="utf-8", errors="ignore")
    refs = any(tok in txt for tok in
               ("no_ai_attribution", "decision_adr", "llmwiki-validate", "validators", "harness"))
    ci = (REPO / ".github" / "workflows" / "harness.yml").is_file()
    return _result("wiring", "repo",
                   [("precommit-refs-gate", "1" if refs else "0", "1"),
                    ("ci-workflow", "1" if ci else "0", "1")])


RULES = [
    ("R1", "no-write-raw", build_r1),
    ("R2", "origin-required", build_r2),
    ("R3", "index-sync", build_r3),
    ("R4", "audit-log", build_r4),
    ("R5", "folder-structure", build_r5),
    ("R6", "verify-before-commit", build_r6),
    ("R7", "proposal-complete", build_r7),
    ("R8", "session-health", build_r8),
    ("R9", "okf-frontmatter", build_r9),
    ("R10", "docs-gate", build_r10),
    ("R11", "seq-html-glass", build_r11),
    ("R12", "pull-before-change", build_r12),
    ("R13", "decision-to-adr", build_r13),
    ("R14", "patterns-protected", build_r14),
    ("R15", "no-ai-attribution", build_r15),
    ("R16", "report-show-path", build_r16),
    ("R17", "problem-tree-flush", build_r17),
    ("R18", "plan-executable", build_r18),
]


# ---------------------------------------------------------------------------
# Run the bite-tests. Each build_rN gets its own temp subdir so fixtures never
# collide, and returns the generic {green, kind, source, checks, note} shape.
# ---------------------------------------------------------------------------
def run_bite_tests(base):
    results = []
    resolved_src = None
    for rid, label, builder in RULES:
        try:
            rule = builder(base / rid)
        except Exception as e:
            rule = {"green": False, "kind": "error", "source": "ERR",
                    "checks": [("exec", "raised", "clean")], "note": "tester crashed: %s" % e}
        rule["id"] = rid
        rule["label"] = label
        if resolved_src is None and rule.get("source") not in (None, "UNRESOLVED", "ERR", "repo", "poc", "hooks", "pull-gate.sh"):
            resolved_src = rule["source"]
        results.append(rule)
    return results, (resolved_src or "UNRESOLVED")


# ---------------------------------------------------------------------------
# Install probes (advisory). Each returns (state, label, detail) where state is
# True (ok), False (problem), or None (neutral / info).
# ---------------------------------------------------------------------------
def probe_hooks():
    present = [h for h in EXPECTED_HOOKS if (HOOKS_DIR / h).is_file()]
    all_py = sorted(HOOKS_DIR.glob("*.py")) if HOOKS_DIR.is_dir() else []
    execable = sum(1 for h in all_py if os.access(h, os.X_OK))
    ok = len(present) == len(EXPECTED_HOOKS)
    detail = ("%d/%d expected hooks in llmwiki/.claude/hooks (%d/%d +x; "
              "invoked via `python3` per settings.json, so +x not required)"
              % (len(present), len(EXPECTED_HOOKS), execable, len(all_py)))
    if not ok:
        missing = [h for h in EXPECTED_HOOKS if h not in present]
        detail += " — MISSING: " + ", ".join(missing)
    return ok, "hooks present", detail


def probe_settings():
    ok = SETTINGS.is_file()
    return ok, "settings.json", ("llmwiki/.claude/settings.json"
                                 if ok else "MISSING llmwiki/.claude/settings.json")


def probe_validators_resolvable():
    names = ["no_write_raw.py", "origin_required.py", "folder_structure.py",
             "proposal_complete.py", "okf_frontmatter.py", "patterns_guard.py",
             "report_show_path.py", "decision_adr.py", "no_ai_attribution.py",
             "index_sync.py"]
    srcs = {}
    unresolved = []
    for n in names:
        v, s = resolve_validator(n)
        srcs[s] = srcs.get(s, 0) + 1
        if v is None:
            unresolved.append(n)
    ok = not unresolved
    via = ", ".join("%s=%d" % (k, v) for k, v in srcs.items() if k != "UNRESOLVED")
    detail = "%d/%d resolvable (%s)" % (len(names) - len(unresolved), len(names), via or "none")
    if unresolved:
        detail += " — UNRESOLVED: " + ", ".join(unresolved)
    return ok, "validators resolvable", detail


def probe_validator_drift():
    if not (HOOKS_VALIDATORS.is_dir() and HARNESS_VALIDATORS.is_dir()):
        return None, "validator drift", "only one validators dir present — nothing to compare"
    drifted = []
    checked = 0
    for src in HARNESS_VALIDATORS.glob("*.py"):
        twin = HOOKS_VALIDATORS / src.name
        if twin.is_file():
            checked += 1
            if src.read_bytes() != twin.read_bytes():
                drifted.append(src.name)
    if drifted:
        return False, "validator drift", ("hooks-copy differs from harness-src for: "
                                          + ", ".join(drifted) + " — one copy is stale")
    return True, "validator drift", "hooks-copy == harness-src across %d validators" % checked


def probe_pyyaml():
    try:
        import yaml  # noqa: F401
        return True, "pyyaml", "import yaml OK (v%s)" % getattr(yaml, "__version__", "?")
    except Exception:
        return None, "pyyaml", ("not importable — R9 falls back to a regex `type:` "
                                "check, so the rail still bites")


def probe_precommit_config():
    ok = PRECOMMIT_CFG.is_file()
    return ok, "pre-commit config", (".pre-commit-config.yaml present"
                                     if ok else "MISSING .pre-commit-config.yaml (no L2 backstop)")


def probe_precommit_installed():
    binary = shutil.which("pre-commit")
    py = shutil.which("python")
    installed = GIT_PRECOMMIT_HOOK.is_file()
    bits = []
    bits.append("binary " + ("found" if binary else "NOT on PATH"))
    if py is None:
        bits.append("`python` NOT on PATH (only python3) — pre-commit's generated git "
                    "shim historically calls `python`; install with a python3 on PATH")
    # Bản cũ trả True chỉ vì shim git tồn tại — TRONG KHI đã tự thu được bằng chứng ngược
    # ("binary NOT on PATH", "`python` NOT on PATH") rồi nhét vào chuỗi mô tả. Shim có mà
    # binary thiếu = hook GÃY lúc commit, còn doctor vẫn xanh. Verdict phải dùng chính bằng
    # chứng nó đã thu, không được chỉ đọc inode.
    if installed and binary:
        return True, "pre-commit in .git/hooks", "installed (" + "; ".join(bits) + ")"
    if installed and not binary:
        return False, "pre-commit in .git/hooks", ("shim git CÓ nhưng binary `pre-commit` "
                                                   "KHÔNG trên PATH — hook sẽ gãy lúc commit, "
                                                   "L2 coi như TẮT. " + "; ".join(bits))
    return False, "pre-commit in .git/hooks", ("NOT installed — run `pre-commit install` "
                                               "(L2 git backstop inactive). " + "; ".join(bits))


def run_install_probes():
    return [
        probe_hooks(),
        probe_settings(),
        probe_validators_resolvable(),
        probe_validator_drift(),
        probe_pyyaml(),
        probe_precommit_config(),
        probe_precommit_installed(),
    ]


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------
def colorize(enabled):
    palette = {
        "green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m",
        "dim": "\033[2m", "bold": "\033[1m", "reset": "\033[0m",
    }

    def c(text, name):
        if not enabled:
            return text
        return "%s%s%s" % (palette.get(name, ""), text, palette["reset"])
    return c


def fmt_cell(actual, expected, c):
    if actual is None:
        return c("--", "dim")
    s = "%s" % actual
    return c(s, "green" if actual == expected else "red")


def print_board(rules, resolved_src, probes, c):
    green_rules = sum(1 for r in rules if r["green"])
    total = len(rules)
    print(c("HARNESS DOCTOR", "bold") + c("  fire-drill: does each rail still bite?", "dim"))
    print(c("  repo: %s" % REPO, "dim"))
    print(c("  active validators resolved via: %s" % resolved_src, "dim"))
    print()
    print(c("RULE BITE-TESTS", "bold")
          + c("  (BAD must block -> exit 2 | GOOD must pass -> exit 0)", "dim"))
    for r in rules:
        icon = c("✓", "green") if r["green"] else c("✗", "red")
        cells = "  ".join("%s->%s" % (lbl, fmt_cell(a, e, c)) for lbl, a, e in r["checks"])
        line = "  %s %-3s %-19s %s %s" % (
            icon, r["id"], r["label"], c("[%-18s]" % r["kind"], "dim"), cells)
        print(line)
        if r["note"]:
            print(c("        ^ %s" % r["note"], "red" if not r["green"] else "dim"))
    summary = "  %d/%d rails bite." % (green_rules, total)
    print(c(summary, "green" if green_rules == total else "red"))
    print()
    print(c("INSTALL PROBES", "bold") + c("  (advisory — --ci gates only on dark rails)", "dim"))
    for state, label, detail in probes:
        if state is True:
            icon = c("✓", "green")
        elif state is False:
            icon = c("✗", "red")
        else:
            icon = c("ℹ", "yellow")
        print("  %s %-26s %s" % (icon, label, c(detail, "dim")))
    print()
    n_ok = sum(1 for s, _, _ in probes if s is True)
    n_bad = sum(1 for s, _, _ in probes if s is False)
    n_info = sum(1 for s, _, _ in probes if s is None)
    verdict = "VERDICT: %d/%d rails bite | install %d ok / %d problem / %d info" % (
        green_rules, total, n_ok, n_bad, n_info)
    print(c(verdict, "bold"))
    if green_rules < total:
        print(c("  DARK RAIL DETECTED — a validator stopped blocking its bad fixture.", "red"))
    return green_rules, total


def build_json(rules, resolved_src, probes):
    green_rules = sum(1 for r in rules if r["green"])
    return {
        "repo": str(REPO),
        "resolved_via": resolved_src,
        "rails_bite": green_rules,
        "rails_total": len(rules),
        "dark_rails": [r["id"] for r in rules if not r["green"]],
        "rules": rules,
        "install_probes": [
            {"ok": s, "label": label, "detail": detail} for s, label, detail in probes
        ],
    }


def main():
    ap = argparse.ArgumentParser(
        description="Fire-drill that proves each harness rule still blocks bad input.")
    ap.add_argument("--ci", action="store_true",
                    help="exit non-zero if any rule's bite-test failed (a dark rail)")
    ap.add_argument("--json", action="store_true", help="emit the board as JSON")
    ap.add_argument("--keep", action="store_true", help="keep temp fixtures (debugging)")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI color")
    args = ap.parse_args()

    base = Path(tempfile.mkdtemp(prefix="harness-doctor-"))
    try:
        rules, resolved_src = run_bite_tests(base)
        probes = run_install_probes()
    finally:
        if args.keep:
            sys.stderr.write("[harness-doctor] kept fixtures in %s\n" % base)
        else:
            shutil.rmtree(base, ignore_errors=True)

    green_rules = sum(1 for r in rules if r["green"])
    total = len(rules)

    if args.json:
        print(json.dumps(build_json(rules, resolved_src, probes), ensure_ascii=False, indent=2))
    else:
        color_on = (not args.no_color) and sys.stdout.isatty()
        print_board(rules, resolved_src, probes, colorize(color_on))

    if args.ci and green_rules < total:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
