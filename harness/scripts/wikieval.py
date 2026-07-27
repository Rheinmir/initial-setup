#!/usr/bin/env python3
"""WikiEval — turn wiki golden pages into a CI-blocking eval suite (build-now slice).

The assertion CASCADE per golden runs cheap -> expensive and short-circuits:

  tier 1  DETERMINISTIC asserts in pure code  (equals / contains / icontains /
          not-contains / regex / is-json / is-sql-ish) run on the candidate output.
          If a golden declares `asserts`, tier 1 alone decides pass/fail -> cheap exit.
  tier 2  embedding / similarity                (OPTIONAL — only reached when a golden
          has NO deterministic asserts). Skipped+noted unless an embedding backend is
          configured (see harness/wikieval.config.yaml). A stdlib 'difflib' lexical
          backend is available offline; real semantic embeddings are quarantined.
  tier 3  LLM-rubric judge                       = THE ADAPTER (verified: false). A stub
          `judge(output, rubric) -> {score, reason}` lives below the boundary and is
          NEVER called from this engine in deterministic mode — escalated goldens are
          reported as "needs-judge" only.

Goldens live as Markdown files under <wiki>/sources/evals/ (fdk/wiki framework · llmwiki/wiki
downstream — auto-detect, xem _default_evals_dir) with YAML frontmatter:
    id:       (optional) golden id — defaults to the filename stem
    input:    the prompt / question
    expected: the reference answer (used by tier-2 similarity)
    rubric:   (optional) instructions for the tier-3 judge
    asserts:  (optional list) deterministic checks, e.g.
              - 'contains:Origin'
              - 'regex:(?i)\\borigin\\b'
              - 'is-json'
              - 'equals:bar'
              - 'is-sql-ish'

The candidate output for each golden is supplied via `--outputs outputs.json` (a map
golden-id -> output string), so the engine is fully runnable + testable WITHOUT any model.

Modes (exit codes: 0 ok, 1 usage/load error, 2 regression):
    (default)            run the cascade and print a report
    --write-baseline     run, then write per-golden pass/score baseline JSON
    --check              run, compare to the committed baseline, exit 2 on ANY regression
                         (deterministic diff report)

Baseline default path: harness/metrics/eval-baseline.json
Config   default path: harness/wikieval.config.yaml   (the ONE adapter; verified:false)
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # the engine needs structured frontmatter (lists) -> require pyyaml
    yaml = None

# repo root = .../setup/setup  (harness/scripts/wikieval.py -> parents[2])
REPO_ROOT = Path(__file__).resolve().parents[2]
def _default_evals_dir(root: Path) -> Path:
    """fdk/wiki (repo framework) nếu có, else llmwiki/wiki (downstream) — khớp hooklib.find_wiki_dir.
    Goldens sống ở <wiki>/sources/evals; downstream không có fdk/ nên fall-through đúng."""
    for cand in (root / "fdk" / "wiki" / "sources" / "evals",
                 root / "llmwiki" / "wiki" / "sources" / "evals"):
        if cand.is_dir():
            return cand
    return root / "llmwiki" / "wiki" / "sources" / "evals"  # fallback = quy ước downstream
DEFAULT_EVALS_DIR = _default_evals_dir(REPO_ROOT)
DEFAULT_BASELINE = REPO_ROOT / "harness" / "metrics" / "eval-baseline.json"
DEFAULT_CONFIG = REPO_ROOT / "harness" / "wikieval.config.yaml"

FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", re.DOTALL)
SKIP_BASENAMES = {"README.md", "_template.md", "index.md", "log.md"}
EPS = 1e-9
SCHEMA = "wikieval-baseline/v1"
SQL_FIRST = ("select", "insert", "update", "delete", "with", "create", "alter", "drop", "merge", "explain")
SQL_CLAUSE = (" from ", " into ", " set ", " table ", " values", " where ")


# ───────────────────────────── tier 1: deterministic asserts ─────────────────────────────

def _split_assert(spec):
    """'contains:foo' -> ('contains', 'foo'); 'is-json' -> ('is-json', None).

    split on the FIRST colon only, so regex/equals args may themselves contain ':'.
    """
    if ":" in spec:
        op, arg = spec.split(":", 1)
        return op.strip(), arg
    return spec.strip(), None


def _is_sql_ish(text):
    """Heuristic smell-test: starts with a SQL verb AND carries a clause keyword or ';'."""
    t = text.strip().lstrip("(").strip()
    if not t:
        return False
    first = t.split(None, 1)[0].lower()
    if first not in SQL_FIRST:
        return False
    tl = " " + t.lower()
    return any(c in tl for c in SQL_CLAUSE) or t.rstrip().endswith(";")


def eval_assert(spec, output):
    """Return (passed: bool, op: str). Unknown ops fail closed (fail-safe)."""
    op, arg = _split_assert(spec)
    a = arg or ""
    if op == "equals":
        return output.strip() == a.strip(), op
    if op == "contains":
        return a in output, op
    if op == "icontains":
        return a.lower() in output.lower(), op
    if op == "not-contains":
        return a not in output, op
    if op == "regex":
        try:
            return re.search(a, output) is not None, op
        except re.error:
            return False, op
    if op == "is-json":
        try:
            json.loads(output.strip())
            return True, op
        except Exception:
            return False, op
    if op == "is-sql-ish":
        return _is_sql_ish(output), op
    return False, f"unknown-op:{op}"   # fail-safe: an unrecognized assert never passes


# ───────────────────────────── tier 2: similarity (optional) ─────────────────────────────

def tier2_similarity(output, expected, cfg):
    """Return (score|None, label). score is None when tier-2 is skipped (with a reason)."""
    emb = (cfg or {}).get("embedding") or {}
    backend = str(emb.get("backend") or "none").strip().lower()
    if backend in ("none", ""):
        return None, "tier2 disabled (embedding.backend: none)"
    if backend in ("difflib", "lexical"):
        import difflib
        score = round(difflib.SequenceMatcher(None, output, expected or "").ratio(), 4)
        return score, "tier2-lexical-difflib"
    # a real embedding model id -> the engine does NOT bundle it. Quarantined: only the
    # adapter knows how to load real embeddings. Skip+note (fail-safe) until wired.
    return None, f"tier2 skipped: embedding backend '{backend}' not available (adapter, verified:false)"


# ───────────────────────────── tier 3: ADAPTER BOUNDARY (verified: false) ─────────────────────────────

def judge(output, rubric, config=None):
    """tier-3 LLM-rubric judge — THE quarantined adapter (verified: false).

    STUB. The deterministic engine NEVER calls this. It returns an UNDECIDED verdict
    (score=None) so a half-wired adapter can never auto-pass a golden (fail-safe).

    To finalize tier-3: render config['judge']['rubric_prompt'] with {input}/{expected}/
    {rubric}/{output}, send it as one Messages API user turn to config['judge']['model'],
    parse {"score","reason"} from the reply, then flip `verified: true` in
    harness/wikieval.config.yaml. That single edit (+ this function) is the whole change.
    """
    return {
        "score": None,
        "reason": "tier-3 LLM-rubric judge not wired (adapter, verified:false). "
                  "See harness/wikieval.config.yaml: judge.model + judge.rubric_prompt.",
    }


# ───────────────────────────── cascade ─────────────────────────────

def run_golden(g, output, cfg):
    """Run the cascade for one golden against its candidate output. Returns a result dict."""
    gid = g["id"]
    if output is None:
        return {"id": gid, "status": "no-output", "pass": None, "score": None,
                "decided_by": None, "detail": "no candidate output supplied via --outputs"}
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False)

    asserts = g.get("asserts") or []
    if asserts:  # ── tier 1 (cheap, decisive) ──
        checks = []
        for spec in asserts:
            ok, op = eval_assert(spec, output)
            checks.append({"assert": spec, "op": op, "pass": bool(ok)})
        passed = all(c["pass"] for c in checks)
        return {"id": gid, "status": "ok", "pass": passed, "score": 1.0 if passed else 0.0,
                "decided_by": "tier1-asserts", "checks": checks}

    # ── tier 2 (optional similarity) ──
    score, label = tier2_similarity(output, g.get("expected") or "", cfg)
    if score is not None:
        thr = float(((cfg or {}).get("embedding") or {}).get("threshold", 0.8))
        return {"id": gid, "status": "ok", "pass": score >= thr, "score": score,
                "decided_by": label, "detail": f"similarity {score} vs threshold {thr}"}

    # ── tier 3 (adapter; NOT called) ──
    return {"id": gid, "status": "needs-judge", "pass": None, "score": None,
            "decided_by": "tier3-judge",
            "detail": f"{label}; escalated to LLM-rubric judge (adapter, verified:false) — not run"}


# ───────────────────────────── loaders ─────────────────────────────

def _require_yaml():
    if yaml is None:
        sys.exit("[wikieval] PyYAML is required to parse golden frontmatter. pip install pyyaml")


def load_config(path):
    p = Path(path)
    if not p.is_file():
        return {}
    _require_yaml()
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_goldens(evals_dir):
    _require_yaml()
    base = Path(evals_dir)
    if not base.is_dir():
        sys.exit(f"[wikieval] evals dir not found: {base}")
    out, seen = [], {}
    for p in sorted(base.rglob("*.md")):
        if p.name in SKIP_BASENAMES:
            continue
        m = FRONTMATTER_RE.match(p.read_text(encoding="utf-8"))
        if not m:
            continue
        data = yaml.safe_load(m.group(1))
        if not isinstance(data, dict):
            continue
        if not any(k in data for k in ("input", "expected", "asserts")):
            continue  # has frontmatter but is not an eval golden
        gid = str(data.get("id") or p.stem)
        if gid in seen:
            sys.exit(f"[wikieval] duplicate golden id '{gid}': {seen[gid]} and {p}")
        seen[gid] = p
        out.append({"id": gid, "path": str(p), "input": data.get("input"),
                    "expected": data.get("expected"), "rubric": data.get("rubric"),
                    "asserts": data.get("asserts") or []})
    return out


def load_outputs(path):
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        sys.exit(f"[wikieval] --outputs file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        sys.exit("[wikieval] --outputs must be a JSON object mapping golden-id -> output")
    return data


# ───────────────────────────── baseline + diff ─────────────────────────────

def build_baseline(results, evals_dir):
    decided = sum(1 for r in results if r["pass"] is not None)
    passed = sum(1 for r in results if r["pass"] is True)
    goldens = {}
    for r in results:
        entry = {"pass": r["pass"], "score": r["score"], "decided_by": r["decided_by"]}
        if "checks" in r:
            entry["asserts"] = [c["assert"] for c in r["checks"]]
        goldens[r["id"]] = entry
    try:
        rel = str(Path(evals_dir).resolve().relative_to(REPO_ROOT))
    except ValueError:
        rel = str(evals_dir)
    return {"schema": SCHEMA, "generated_by": "harness/scripts/wikieval.py",
            "generated_at": date.today().isoformat(), "evals_dir": rel,
            "summary": {"goldens": len(results), "decided": decided, "passed": passed},
            "goldens": goldens}


def diff_against_baseline(baseline, results):
    """Return (regressions, notes). A regression = a metric dropped below baseline."""
    cur = {r["id"]: r for r in results}
    base = baseline.get("goldens", {})
    regressions, notes = [], []
    for gid in sorted(base):
        b, c = base[gid], cur.get(gid)
        if c is None:
            regressions.append((gid, "golden missing now (coverage dropped)"))
            continue
        bp, cp, bs, cs = b.get("pass"), c.get("pass"), b.get("score"), c.get("score")
        if bp is True and cp is not True:
            regressions.append((gid, f"pass {bp} -> {cp} (decided_by {c.get('decided_by')})"))
        elif isinstance(bs, (int, float)) and isinstance(cs, (int, float)) and cs < bs - EPS:
            regressions.append((gid, f"score {bs} -> {cs}"))
    for gid in sorted(cur):
        if gid not in base:
            notes.append((gid, "new golden (not in baseline)"))
    return regressions, notes


# ───────────────────────────── report ─────────────────────────────

_MARK = {True: "PASS", False: "FAIL", None: "----"}


def print_report(results, evals_dir, n_outputs):
    decided = sum(1 for r in results if r["pass"] is not None)
    passed = sum(1 for r in results if r["pass"] is True)
    try:
        rel = str(Path(evals_dir).resolve().relative_to(REPO_ROOT))
    except ValueError:
        rel = str(evals_dir)
    print(f"WikiEval — {len(results)} goldens | outputs: {n_outputs} | dir: {rel}")
    width = max((len(r["id"]) for r in results), default=4)
    for r in sorted(results, key=lambda x: x["id"]):
        mark = _MARK[r["pass"]]
        decided_by = r.get("decided_by") or "-"
        if "checks" in r:
            npass = sum(1 for c in r["checks"] if c["pass"])
            extra = f"({npass}/{len(r['checks'])} asserts)"
            fails = [c["assert"] for c in r["checks"] if not c["pass"]]
            if fails:
                extra += "  x " + ", ".join(fails)
        else:
            extra = r.get("detail", "")
        print(f"  {mark}  {r['id']:<{width}}  {decided_by:<22}  {extra}")
    print(f"Summary: decided {passed}/{decided}" + (f" passed (of {len(results)} goldens)" if decided else " (nothing decided)"))


# ───────────────────────────── self-test ─────────────────────────────

def self_test(evals_dir, cfg):
    """Deterministic engine validation, no model, fully reproducible. For every golden that
    declares tier-1 `asserts`, run those asserts against the golden's OWN `expected` reference
    answer. The reference answer MUST satisfy the asserts that encode the rule it documents —
    if it does, the deterministic tier-1 cascade and the goldens are coherent. This is what
    makes the wikieval adapter's `verified: true` honest: the deterministic engine is proven
    here; only the tier-3 LLM-rubric judge stays a separate, disabled adapter."""
    if not Path(evals_dir).is_dir():
        # Engine GLOBAL không mang goldens repo (UAT canary 260718) → chứng ENGINE bằng fixture
        # hermetic thay vì chết; goldens thật vẫn được chứng khi chạy trong repo.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "fixture.md").write_text(
                "---\ntype: eval\nid: engine-fixture\ninput: \"q\"\n"
                "expected: \"Origin section is required.\"\n"
                "asserts:\n  - 'contains:Origin'\n  - 'regex:(?i)required'\n---\n",
                encoding="utf-8")
            print("[wikieval selftest] evals dir vắng → hermetic engine-fixture (global engine)")
            return self_test(d, cfg)
    goldens = load_goldens(evals_dir)
    with_asserts = [g for g in goldens if g.get("asserts")]
    if not with_asserts:
        print("[wikieval selftest] no golden declares tier-1 asserts — nothing deterministic to validate.")
        return 1
    all_ok = True
    print(f"[wikieval selftest] {len(with_asserts)} golden(s) with tier-1 asserts (asserts vs own `expected`):")
    for g in sorted(with_asserts, key=lambda x: x["id"]):
        r = run_golden(g, g.get("expected") or "", cfg)
        ok = r.get("pass") is True and r.get("decided_by") == "tier1-asserts"
        all_ok = all_ok and ok
        detail = ""
        if "checks" in r:
            fails = [c["assert"] for c in r["checks"] if not c["pass"]]
            if fails:
                detail = "  x " + ", ".join(fails)
        print(f"  {'[OK ]' if ok else '[FAIL]'} {g['id']:<18} expected satisfies its own asserts{detail}")
    print("SELFTEST: ALL PASS" if all_ok else "SELFTEST: FAILED")
    return 0 if all_ok else 1


# ───────────────────────────── main ─────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="WikiEval — wiki goldens as a CI-blocking eval suite.")
    ap.add_argument("--evals-dir", default=str(DEFAULT_EVALS_DIR))
    ap.add_argument("--outputs", default=None, help="JSON map golden-id -> candidate output")
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--write-baseline", action="store_true", help="write per-golden pass/score baseline")
    ap.add_argument("--check", action="store_true", help="compare to baseline; exit 2 on regression")
    ap.add_argument("--self-test", action="store_true", help="deterministic: each golden's asserts vs its own expected (validates the tier-1 engine, no model)")
    ap.add_argument("--json", action="store_true", help="emit raw run results as JSON")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.self_test:
        sys.exit(self_test(args.evals_dir, cfg))
    goldens = load_goldens(args.evals_dir)
    outputs = load_outputs(args.outputs)
    results = [run_golden(g, outputs.get(g["id"]), cfg) for g in goldens]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results, args.evals_dir, len(outputs))

    if args.write_baseline:
        baseline = build_baseline(results, args.evals_dir)
        # Guard chống mất-dữ-liệu-âm-thầm (cháy thật 2026-07-18): chạy thiếu --outputs → 0 golden
        # được chấm → lặng lẽ đè baseline tốt bằng baseline rỗng. Từ chối ghi bản 0-decided đè lên
        # baseline đang có dữ liệu; muốn thật thì xoá file baseline trước (hành động có chủ ý).
        if baseline["summary"]["decided"] == 0 and Path(args.baseline).is_file():
            try:
                old = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
                if old.get("summary", {}).get("decided", 0) > 0:
                    sys.exit("[wikieval] TỪ CHỐI ghi: 0 golden được chấm (thiếu --outputs?) mà baseline "
                             f"hiện có {old['summary']['decided']} decided — đè lên là mất dữ liệu. "
                             "Cấp --outputs rồi chạy lại; thật sự muốn baseline rỗng thì xoá file baseline trước.")
            except SystemExit:
                raise
            except Exception:
                pass  # baseline cũ hỏng/không đọc được → cho ghi (không tệ hơn hiện trạng)
        Path(args.baseline).parent.mkdir(parents=True, exist_ok=True)
        Path(args.baseline).write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            rel = str(Path(args.baseline).resolve().relative_to(REPO_ROOT))
        except ValueError:
            rel = args.baseline
        print(f"[wikieval] baseline written -> {rel} "
              f"({baseline['summary']['passed']}/{baseline['summary']['decided']} decided-passing)")

    if args.check:
        bp = Path(args.baseline)
        if not bp.is_file():
            sys.exit(f"[wikieval] no baseline at {bp} — run with --write-baseline first.")
        baseline = json.loads(bp.read_text(encoding="utf-8"))
        regressions, notes = diff_against_baseline(baseline, results)
        print(f"\n[wikieval --check] baseline {baseline.get('generated_at','?')} "
              f"vs current ({len(results)} goldens)")
        for gid, why in notes:
            print(f"  note  {gid}: {why}")
        if regressions:
            print(f"  REGRESSIONS ({len(regressions)}):")
            for gid, why in regressions:
                print(f"    FAIL  {gid}: {why}")
            print("[wikieval --check] FAILED — metrics dropped below baseline.")
            sys.exit(2)
        print("[wikieval --check] OK — no metric below baseline.")


if __name__ == "__main__":
    main()
