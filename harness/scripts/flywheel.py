#!/usr/bin/env python3
"""flywheel — ONE self-evolving capture→count→draft machine, polarity-selected by --kind.

  --kind failure : Hamel's create→LABEL→fix→repeat. Capture FAILURES, count recurring classes,
                   draft a candidate RULE stub into propose→gate when a class recurs >= threshold.
  --kind success : the positive mirror (Agentic Context Engineering). Capture WINS (score-gated),
                   count recurring high-value tasks, draft a reusable PLAYBOOK stub.

Merged from failure-flywheel.py + success-flywheel.py (they shared 11/11 functions). The only
real differences — record field, metrics file, score gating, draft template — live in KINDS below.
Capture/config/JSONL plumbing comes from bnal_metrics + bnal_config (shared).

  flywheel.py --kind K record <key> "<summary>" [--score N] [--detail ...]
  flywheel.py --kind K --report
  flywheel.py --kind K --draft <key> [--date YYYY-MM-DD]
  flywheel.py --kind K --self-test
The ONE adapter per kind = harness/<kind>-flywheel.config.yaml (verified:false). Distil model
absent → --draft emits a human-TODO stub, never auto-promotes.
"""
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import bnal_config
import bnal_metrics

DEFAULT_DATE = "2026-06-29"

KINDS = {
    "failure": dict(
        field="category", metrics="failures.jsonl", config="failure-flywheel",
        item="failure", scored=False, slug_prefix="failure", artifact="rule",
        fb={"verified": False, "recurrence_threshold": 3, "taxonomy": [], "distill": {"model": None}}),
    "success": dict(
        field="task", metrics="successes.jsonl", config="success-flywheel",
        item="win", scored=True, slug_prefix="playbook", artifact="playbook",
        fb={"verified": False, "success_threshold": 8, "recurrence_threshold": 3, "distill": {"model": None}}),
}


def _cfg(root, k):
    return bnal_config.load(root, k["config"], k["fb"])


def record(root, k, key, summary, score=None, detail=None):
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           k["field"]: (key or "uncategorized").strip(), "summary": (summary or "").strip()}
    if k["scored"]:
        try:
            rec["score"] = float(score)
        except (TypeError, ValueError):
            rec["score"] = None
    if detail:
        rec["detail"] = detail.strip()
    bnal_metrics.append(root, k["metrics"], rec, comment=f"flywheel {k['config']} raw history (local)")
    return rec


def _rows(root, k, cfg):
    """Rows that count: for success, score>=threshold (or unscored); for failure, all."""
    st = float(cfg.get("success_threshold", 0)) if k["scored"] else None
    out = []
    for r in bnal_metrics.read(root, k["metrics"]):
        if k["scored"]:
            sc = r.get("score")
            if sc is not None and sc < st:
                continue
        out.append(r)
    return out


def leaderboard(root, k, cfg):
    groups = {}
    for r in _rows(root, k, cfg):
        key = r.get(k["field"]) or "uncategorized"
        ts = r.get("ts") or ""
        g = groups.setdefault(key, {"count": 0, "first": ts, "last": ts, "scores": []})
        g["count"] += 1
        if r.get("score") is not None:
            g["scores"].append(r["score"])
        if ts:
            g["first"] = min(g["first"], ts) if g["first"] else ts
            g["last"] = max(g["last"], ts) if g["last"] else ts
    return sorted(groups.items(), key=lambda kv: (-kv[1]["count"], kv[0]))


def report(root, k):
    cfg = _cfg(root, k)
    rt = int(cfg.get("recurrence_threshold", 3))
    ordered = leaderboard(root, k, cfg)
    out = [f"Flywheel[{k['field']}] — {len(ordered)} {k['field']}-classes",
           f"recurrence_threshold = {rt}  (adapter: harness/{k['config']}.config.yaml, verified={cfg.get('verified')})", ""]
    if not ordered:
        out.append(f'(none recorded — flywheel.py --kind ... record <{k["field"]}> "<summary>")')
        return "\n".join(out)
    out.append("Leaderboard (most-frequent first):")
    for i, (key, g) in enumerate(ordered, 1):
        elig = "DRAFT" if g["count"] >= rt else "-"
        avg = f"  avg={sum(g['scores'])/len(g['scores']):.1f}" if g["scores"] else ""
        out.append(f"  {i:>2}  {g['count']:>4}  {key:<22}  {elig:<6}{avg}")
    eligible = [key for key, g in ordered if g["count"] >= rt]
    out.append("")
    out.append("Eligible for --draft (seeds /propose, not auto-promoted):" if eligible
               else f"No class reached threshold ({rt}) yet.")
    out += [f"  flywheel.py --kind {'failure' if not k['scored'] else 'success'} --draft {key}" for key in eligible]
    return "\n".join(out)


def _ddmmyy(s):
    return date.fromisoformat(s).strftime("%d%m%y")


def _slug(s):
    return re.sub(r"[^a-z0-9-]+", "-", (s or "").lower()).strip("-") or "uncategorized"


def draft(root, k, key, date_str=DEFAULT_DATE):
    cfg = _cfg(root, k)
    rt = int(cfg.get("recurrence_threshold", 3))
    distill = (cfg.get("distill") or {}).get("model")
    rows = [r for r in _rows(root, k, cfg) if (r.get(k["field"]) or "uncategorized") == key]
    n = len(rows)
    if n < rt:
        return None, f"'{key}' has {n} {k['item']}(s) < threshold {rt} — not eligible to draft yet."
    out_dir = root / "llmwiki" / "wiki" / "sources" / "draft"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{_ddmmyy(date_str)}-{k['slug_prefix']}-{_slug(key)}.md"
    drepr = "null" if distill is None else str(distill)
    md = ["---", "type: draft",
          f"title: Candidate {k['artifact']} from recurring {key} {k['item']}s",
          "status: proposed", f"tags: [flywheel, draft, {k['slug_prefix']}, {_slug(key)}]",
          f"timestamp: {date_str}", "---", "",
          f"# {_ddmmyy(date_str)}-{k['slug_prefix']}-{_slug(key)}", "",
          "## What",
          f"`{key}` recurred **{n}×** (threshold {rt}). Flywheel seeds this {k['artifact']} stub so "
          f"the pattern becomes reusable instead of repeating. SEED — a human runs `/propose`; never auto-promoted.", "",
          f"## {k['artifact'].capitalize()} (TODO — needs human distillation)",
          f"> TODO: distil the {k['artifact']} from these {n} `{key}` {k['item']}s. (Distil model is the "
          f"quarantined adapter — `harness/{k['config']}.config.yaml` `distill.model` = `{drepr}`.)", "",
          f"## {k['item'].capitalize()}s observed ({n})", "", "| Summary | Seen |", "|---|---|"]
    for r in rows:
        cell = (r.get("summary") or "").replace("|", "\\|").replace("\n", " ")[:110]
        md.append(f"| {cell} | {(r.get('ts') or '').replace('T', ' ')} |")
    md += ["", "## Origin",
           f"- **Source:** `flywheel.py --kind {'failure' if not k['scored'] else 'success'} --draft {key}` "
           f"from `harness/metrics/{k['metrics']}` ({n} {k['item']}s, recurrence >= {rt}).",
           f"- **Adapter:** `harness/{k['config']}.config.yaml` (verified={cfg.get('verified')}, distill.model={drepr}).",
           f"- **Date:** {date_str}", ""]
    out.write_text("\n".join(md), encoding="utf-8")
    return out, f"drafted {k['artifact']} STUB {out} from {n} '{key}' {k['item']}s — STOPS for human approval."


def self_test(k):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness").mkdir()
        thr = "recurrence_threshold: 2\n" + ("success_threshold: 8\n" if k["scored"] else "")
        (root / "harness" / f"{k['config']}.config.yaml").write_text("verified: false\n" + thr, encoding="utf-8")
        for i in range(2):
            record(root, k, "demo", f"item {i}", score=9 if k["scored"] else None)
        if k["scored"]:
            record(root, k, "weak", "low", score=3)            # below threshold → excluded
        rep = report(root, k)
        ok = "demo" in rep and "DRAFT" in rep and (not k["scored"] or "weak" not in rep)
        out, _ = draft(root, k, "demo")
        ok = ok and out is not None and out.exists()
    print(f"flywheel[{k['field']}] self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _opt(args, flag):
    if flag in args:
        i = args.index(flag); v = args[i + 1] if len(args) > i + 1 else None; del args[i:i + 2]; return v
    return None


def main():
    import os
    args = sys.argv[1:]
    kind = _opt(args, "--kind") or "failure"
    if kind not in KINDS:
        print(f"--kind must be failure|success (got {kind})", file=sys.stderr); sys.exit(2)
    k = KINDS[kind]
    root = Path(_opt(args, "--root") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    date_str = _opt(args, "--date") or DEFAULT_DATE
    try:
        date.fromisoformat(date_str)
    except ValueError:
        print(f"--date muốn ISO YYYY-MM-DD, nhận '{date_str}'", file=sys.stderr); sys.exit(2)
    detail = _opt(args, "--detail")
    score = _opt(args, "--score")

    if "--self-test" in args:
        sys.exit(self_test(k))
    if "--report" in args:
        print(report(root, k)); return
    if "--draft" in args:
        i = args.index("--draft")
        if len(args) <= i + 1:
            print("usage: flywheel.py --kind K --draft <key>", file=sys.stderr); sys.exit(2)
        out, msg = draft(root, k, args[i + 1], date_str)
        print(msg, file=sys.stdout if out is not None else sys.stderr)
        sys.exit(0 if out is not None else 1)
    if args and args[0] == "record":
        if len(args) < 3:
            print('usage: flywheel.py --kind K record <key> "<summary>" [--score N]', file=sys.stderr); sys.exit(2)
        rec = record(root, k, args[1], args[2], score, detail)
        print(f"recorded [{kind}/{rec.get(k['field'])}] {rec['summary']}"); return
    print(__doc__)


if __name__ == "__main__":
    main()
