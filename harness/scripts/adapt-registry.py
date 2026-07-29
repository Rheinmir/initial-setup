#!/usr/bin/env python3
"""adapt-registry — the standing answer to "what is still unverified, and where?"

The `/build-now-adapt-later` skill (llmwiki/skills/dev-loop/build-now-adapt-later.md)
quarantines every unknown behind ONE adapter, seeds it with a best-guess default, and
marks it so a human or a returning agent can find it later. Those marks are a small,
fixed vocabulary:

    verified: false        the adapter's flag — the guess is NOT yet confirmed
    # ASSUMPTION (...)      a single quarantined constant, sourced but unverified
    ⚠️                      a "to be verified" item / advisory emphasis
    ADAPT-CHECKLIST        the finalize procedure that flips the guess to verified

Until now those marks lived only as prose scattered across files. There was no one
command an agent could run to enumerate the outstanding unknowns, and no gate that
fails when the quarantine leaks. This script is that registry and that gate.

Modes
  --report  (default)  Print the "outstanding unknowns" board — grouped by adapter
                       boundary (file), each row is line · marker · verified-state,
                       and each adapter header names the nearest ADAPT-CHECKLIST that
                       finalizes it. ALWAYS (re)writes harness/metrics/unknowns.json
                       with one flat record {file,line,marker,verified} per mark.

  --check   (exit 2)   The leak-gate (skill Step 7: "quarantined values must not leak
                       past the adapter"). Fails when EITHER:
                         (1) the same quarantined constant name is defined in ≥2 files
                             — once with its ASSUMPTION marker, and again as a hard-
                             coded literal somewhere else (the guess escaped the
                             adapter), or pinned with the marker in two files at once; OR
                         (2) a real `verified: false` adapter has no ADAPT-CHECKLIST
                             anywhere near it (no documented way to finalize it).
                       Prints the offenders and exits 2. Otherwise exits 0.

Heuristics are deliberately conservative and fail-open: a missing git, an unreadable
or binary file, or a parse error is skipped, never crashed on. The leak test only
counts distinctive names with a genuinely hard-coded right-hand side, so it never
flags an adapter that merely *reads* its own config (e.g. `x = cfg.get("stale_days")`).

Wire `--check` into pre-commit and CI next to harness-lint; run `--report` whenever
you pick the project back up.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# This file lives at <repo>/harness/scripts/adapt-registry.py
DEFAULT_REPO = Path(__file__).resolve().parents[2]
SELF_REL = "harness/scripts/adapt-registry.py"     # never scan ourselves (we hold the marker words)
OUT_REL = "harness/metrics/unknowns.json"

WARN = "⚠"                                     # ⚠ (base char; covers ⚠ and ⚠️)

# ── marker vocabulary (loose — for the board / JSON inventory) ──────────────────────────
MARKERS = (
    ("verified:false", re.compile(r"verified\s*:\s*false", re.I)),
    ("ASSUMPTION",      re.compile(r"ASSUMPTION")),
    ("⚠️",              re.compile(re.escape(WARN))),
    ("ADAPT-CHECKLIST", re.compile(r"ADAPT-CHECKLIST")),
)

# ── strict forms (for the gate — anchored so prose / strings don't qualify) ─────────────
RE_VERIFIED_FALSE_DECL = re.compile(r"^\s*verified\s*:\s*false\b", re.I)   # a real YAML flag
RE_VERIFIED_TRUE_DECL  = re.compile(r"^\s*verified\s*:\s*true\b", re.I)
RE_CHECKLIST_HEADING   = re.compile(r"^#{1,6}\s*ADAPT-CHECKLIST")          # a canonical provider
RE_ASSIGN_LHS          = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*[:=]")

# binary / non-text we never read
SKIP_EXT = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".webp",
            ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz", ".tgz", ".bin"}

# RHS tokens that mean "this is a read / computed value, not a hard-coded duplicate"
READ_TOKENS = (".get(", "cfg", "config", "arch", "getattr", "environ", "os.",
               "(", ")", "[", "]", "{", "}")


# ── git plumbing (fail-open) ────────────────────────────────────────────────────────────
def tracked_files(repo):
    try:
        out = subprocess.run(["git", "ls-files"], cwd=str(repo),
                             capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    return [p for p in out.splitlines() if p]


def read_text(repo, rel):
    if Path(rel).suffix.lower() in SKIP_EXT:
        return None
    try:
        return (repo / rel).read_text(encoding="utf-8")
    except Exception:                              # binary / unreadable → skip (fail-open)
        return None


# ── leak-test predicates ────────────────────────────────────────────────────────────────
# Khoá schema config CHUNG — tái xuất hợp lệ ở NHIỀU adapter song song (mỗi adapter có
# `verified`/`enabled`/`threshold`… riêng). KHÔNG phải hằng-số-ẩn-số đặc trưng → không tính leak.
GENERIC_KEYS = {
    "verified", "enabled", "threshold", "model", "mode", "status", "tracked", "trigger",
    "disposable", "source", "kind", "timeout", "budget", "backend", "rubric", "category",
    # parallel BNAL adapters legitimately share these schema keys (e.g. failure-flywheel ↔
    # success-flywheel both carry recurrence_threshold + distill.prompt) — not a leak.
    "recurrence_threshold", "prompt",
    # loop-guard schema: PER-FRAME guards (frame-lint frame template) are a schema
    # deliberately separate from the GLOBAL loop-runner defaults (loop-runner.config.yaml
    # documents this: guards set per-frame by /br) — sharing the key names is by-design,
    # values even differ (global max_iter:6 vs frame default 3). Same key ≠ leaked guess.
    "max_iter", "budget_seconds", "no_progress_k", "escalate_after_iter",
    # generic config key colliding across unrelated subsystems (web-crawl assumption vs the
    # lume/ Go LLM clients' `endpoint = defaultEndpoint` const-ref) — name clash, not a copy.
    "endpoint",
}


def is_distinctive(name):
    """Conservative: only names unlikely to collide by accident across files.

    Loại khoá schema chung (GENERIC_KEYS): nhiều adapter song song cùng có chúng là CỐ Ý,
    không phải một ẩn số bị nhân bản → tránh false-positive khi repo có nhiều *.config.yaml.
    """
    if name in GENERIC_KEYS:
        return False
    return len(name) >= 6 or "_" in name or name.isupper()


def rhs_is_hardcoded_literal(line):
    """True iff the assignment's RHS is a plain literal (number / bool / string / clean
    bareword) and NOT a read or computed expression — i.e. a genuine hard-coded copy."""
    m = re.match(r"^\s*[A-Za-z_][A-Za-z0-9_-]*\s*[:=]\s*(.*)$", line)
    if not m:
        return False
    rhs_raw = m.group(1)
    if any(tok in rhs_raw for tok in READ_TOKENS):     # call / subscript / config read → not a copy
        return False
    rhs = re.sub(r"\s+#.*$", "", rhs_raw)              # strip trailing yaml comment
    rhs = re.sub(r"\s+//.*$", "", rhs).strip()         # strip trailing // comment
    if not rhs:
        return False
    return bool(
        re.fullmatch(r"(?i)(true|false|yes|no|null|none)", rhs)
        or re.fullmatch(r"-?\d+(\.\d+)?", rhs)
        or re.fullmatch(r'"[^"]*"', rhs)
        or re.fullmatch(r"'[^']*'", rhs)
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", rhs)   # clean scalar, nothing trailing (no comma)
    )


def shared_depth(a, b):
    n = 0
    for x, y in zip(a.split("/"), b.split("/")):
        if x != y:
            break
        n += 1
    return n


# ── scan ────────────────────────────────────────────────────────────────────────────────
def scan(repo):
    files = [f for f in tracked_files(repo) if f not in (SELF_REL, OUT_REL)]
    texts = {}
    markers = []                  # flat {file,line,marker,verified}
    verified_state = {}           # rel -> True / False / None  (real flag only)
    checklist_files = set()       # rel mentioning ADAPT-CHECKLIST anywhere
    providers = set()             # rel with a real `# ADAPT-CHECKLIST` heading
    assumption_homes = {}         # const-name -> set(rel) where ASSUMPTION-tagged

    for rel in files:
        txt = read_text(repo, rel)
        if txt is None:
            continue
        texts[rel] = txt
        lines = txt.splitlines()

        state = None
        for ln in lines:
            if RE_VERIFIED_FALSE_DECL.match(ln):
                state = False
                break
            if state is None and RE_VERIFIED_TRUE_DECL.match(ln):
                state = True
        verified_state[rel] = state

        has_ckl = False
        for i, ln in enumerate(lines, 1):
            if RE_CHECKLIST_HEADING.match(ln):
                providers.add(rel)
            for label, rx in MARKERS:
                if rx.search(ln):
                    if label == "ADAPT-CHECKLIST":
                        has_ckl = True
                    markers.append({"file": rel, "line": i, "marker": label})
                    if label == "ASSUMPTION":
                        m = RE_ASSIGN_LHS.match(ln)
                        if m:
                            assumption_homes.setdefault(m.group(1), set()).add(rel)
        if has_ckl:
            checklist_files.add(rel)

    # attach each marker's owning-file verified state (None = no real flag in that file)
    for rec in markers:
        rec["verified"] = verified_state.get(rec["file"])

    return {
        "files": files, "texts": texts, "markers": markers,
        "verified_state": verified_state, "checklist_files": checklist_files,
        "providers": providers, "assumption_homes": assumption_homes,
    }


def nearest_checklist(rel, data):
    """The ADAPT-CHECKLIST that finalizes `rel`: an explicit in-text reference wins,
    else the heading-provider sharing the deepest path prefix, else any provider."""
    texts, providers, ckl = data["texts"], data["providers"], data["checklist_files"]
    pool = providers or ckl
    if not pool:
        return None
    txt = texts.get(rel, "")
    # explicit reference: the file names a provider's path or basename
    for p in sorted(pool):
        if p == rel:
            continue
        if p in txt or Path(p).name in txt:
            return p
    if rel in pool:                                 # self-contained checklist
        return rel
    return max(sorted(pool), key=lambda p: (shared_depth(rel, p), -len(p)))


# ── leak gate ───────────────────────────────────────────────────────────────────────────
def find_leaks(data):
    """Offenders for skill Step 7. Returns (const_leaks, unlinked_adapters)."""
    homes = data["assumption_homes"]
    texts = data["texts"]
    const_leaks = []      # (name, [(file,line,reason), ...])

    for name, home_files in sorted(homes.items()):
        if not is_distinctive(name):
            continue
        sites = []
        # signal 1: pinned with its ASSUMPTION marker in ≥2 files at once
        if len(home_files) >= 2:
            for hf in sorted(home_files):
                sites.append((hf, None, "ASSUMPTION-pinned here"))
        # signal 2: hard-coded literal copy of the same name OUTSIDE its adapter (code/config only)
        assign_rx = re.compile(r"^\s*" + re.escape(name) + r"\s*[:=]")
        for rel, txt in texts.items():
            if rel in home_files or rel.endswith(".md"):     # skip the adapter & prose/docs
                continue
            for i, ln in enumerate(txt.splitlines(), 1):
                if assign_rx.match(ln) and rhs_is_hardcoded_literal(ln):
                    sites.append((rel, i, "hard-coded literal: " + ln.strip()[:60]))
        if sites and (len(home_files) >= 2 or any(s[1] is not None for s in sites)):
            # only a true cross-file spread counts (home + ≥1 external site, or ≥2 homes)
            external = [s for s in sites if s[0] not in home_files]
            if len(home_files) >= 2 or external:
                rows = [(hf, None, "ASSUMPTION-pinned here") for hf in sorted(home_files)]
                rows += external
                const_leaks.append((name, rows))

    # condition 2: a real verified:false adapter with no ADAPT-CHECKLIST nearby
    unlinked = []
    for rel, state in data["verified_state"].items():
        if state is not False:
            continue
        if rel in data["checklist_files"]:
            continue
        if nearest_checklist(rel, data) is None:
            unlinked.append(rel)
    return const_leaks, unlinked


# ── outputs ─────────────────────────────────────────────────────────────────────────────
def emit_json(repo, data):
    recs = [{"file": m["file"], "line": m["line"], "marker": m["marker"],
             "verified": m["verified"]} for m in data["markers"]]
    adapters = sorted(r for r, s in data["verified_state"].items() if s is False)
    doc = {
        "generated_by": "harness/scripts/adapt-registry.py",
        "summary": {
            "tracked_scanned": len(data["files"]),
            "markers": len(recs),
            "verified_false_adapters": adapters,
            "adapt_checklist_sources": sorted(data["providers"]),
            "quarantined_constants": sorted(data["assumption_homes"]),
        },
        "markers": recs,
    }
    out = repo / OUT_REL
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out
    except Exception as exc:                        # fail-open: never crash the report on write
        print(f"  (warn: could not write {OUT_REL}: {exc})", file=sys.stderr)
        return None


def report(repo, data):
    M = data["markers"]
    adapters = sorted(r for r, s in data["verified_state"].items() if s is False)
    by_file = {}
    for m in M:
        by_file.setdefault(m["file"], []).append(m)

    print("OUTSTANDING UNKNOWNS — adapt registry  (/build-now-adapt-later)")
    print(f"  scanned {len(data['files'])} tracked files · {len(M)} markers · "
          f"{len(adapters)} verified:false adapter(s)\n")

    # Tier 1 — the real unknowns: verified:false adapters, fully expanded.
    if adapters:
        print("UNVERIFIED ADAPTERS  (verified:false — guesses pending conformance)")
        for rel in adapters:
            ckl = nearest_checklist(rel, data)
            consts = sorted(n for n, fs in data["assumption_homes"].items() if rel in fs)
            print(f"\n  ■ {rel}    [verified: false]")
            print(f"      finalize via → {ckl or '(NONE — UNLINKED!)'}")
            if consts:
                print(f"      quarantined constants (must live ONLY here): {', '.join(consts)}")
            rows = sorted((m for m in by_file.get(rel, []) if m["marker"] != "ADAPT-CHECKLIST"),
                          key=lambda m: (m["line"], m["marker"]))
            for m in rows:
                print(f"        L{m['line']:<4} {m['marker']}")
    else:
        print("UNVERIFIED ADAPTERS  : none (no verified:false flag found)")

    # Tier 2 — ASSUMPTION-tagged constants living outside any adapter (would be unusual).
    stray = sorted(n for n, fs in data["assumption_homes"].items()
                   if all(data["verified_state"].get(f) is not False for f in fs))
    if stray:
        print("\nQUARANTINED CONSTANTS OUTSIDE A verified:false ADAPTER (review):")
        for n in stray:
            print(f"  {n} — in {', '.join(sorted(data['assumption_homes'][n]))}")

    # Tier 3 — advisory ⚠️ that are NOT inside an adapter: emphasis, not adapter unknowns.
    warn_files = {}
    for m in M:
        if m["marker"] == "⚠️" and data["verified_state"].get(m["file"]) is not False:
            warn_files[m["file"]] = warn_files.get(m["file"], 0) + 1
    if warn_files:
        total = sum(warn_files.values())
        print(f"\nADVISORY ⚠️ MARKERS  ({total} across {len(warn_files)} files — emphasis, not adapter unknowns):")
        for f in sorted(warn_files):
            print(f"  {f}  ({warn_files[f]})")

    # Footer — where the finalize procedures live.
    if data["providers"]:
        print("\nADAPT-CHECKLIST sources (finalize procedures):")
        for p in sorted(data["providers"]):
            print(f"  {p}")

    out = emit_json(repo, data)
    if out:
        print(f"\nwrote {OUT_REL}  ({len(M)} marker records)")


def check(repo, data):
    const_leaks, unlinked = find_leaks(data)
    print("LEAK-GATE — quarantined values must not leak past the adapter (skill Step 7)\n")
    print(f"  scanned {len(data['files'])} tracked files · "
          f"{len(data['assumption_homes'])} quarantined constant(s) · "
          f"{sum(1 for s in data['verified_state'].values() if s is False)} verified:false adapter(s)")

    fail = False
    if const_leaks:
        fail = True
        print(f"\n  LEAK — same quarantined constant defined in ≥2 files ({len(const_leaks)}):")
        for name, rows in const_leaks:
            print(f"    • {name}")
            for f, ln, why in rows:
                loc = f"{f}:{ln}" if ln else f
                print(f"        {loc} — {why}")
    if unlinked:
        fail = True
        print(f"\n  LEAK — verified:false adapter with no ADAPT-CHECKLIST nearby ({len(unlinked)}):")
        for f in sorted(unlinked):
            print(f"    • {f}")

    emit_json(repo, data)
    if fail:
        print("\n[adapt-registry] FAIL (exit 2): the adapter boundary has leaked.", file=sys.stderr)
        sys.exit(2)
    print("\n[adapt-registry] ✓ no leaks — every guess stays behind its adapter, "
          "every adapter has a finalize path.")


def main():
    ap = argparse.ArgumentParser(
        description="adapt-registry — registry + leak-gate for /build-now-adapt-later markers")
    ap.add_argument("--report", action="store_true",
                    help="print the outstanding-unknowns board and write unknowns.json (default)")
    ap.add_argument("--check", action="store_true",
                    help="run the leak-gate; exit 2 on any leak (use in pre-commit / CI)")
    ap.add_argument("--root", default=None,
                    help="repo root to scan (default: this script's repo)")
    args = ap.parse_args()
    repo = Path(args.root).resolve() if args.root else DEFAULT_REPO

    data = scan(repo)
    if args.check:
        check(repo, data)
    else:
        report(repo, data)


if __name__ == "__main__":
    main()
