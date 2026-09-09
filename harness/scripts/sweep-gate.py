#!/usr/bin/env python3
"""sweep-gate — institutionalise Boris Cherny's "Sweeper" archetype. overstack ACCRETES (keeps
adding features/rules/skills); this counts additions since the last Sweep and NUDGES a cleanup
pass (simplify / unship / merge) once it crosses a threshold — the cadence the framework lacked.

  --check        count counted-glob files now vs the last-sweep baseline; nudge if delta >= threshold.
  --mark         record the current counts as the new baseline (run AFTER a sweep).
  --self-test    deterministic count+delta+mark in a temp dir (fdk-gate BNAL self-test).

The ONE adapter = harness/sweep-gate.config.yaml (sweep_threshold, counted_globs — verified:false).
Counting + delta are deterministic, built now (dogfoods bnal_config + bnal_metrics). Baseline marker
is a local gitignored JSON (per-checkout cadence). Advisory only — never blocks.
"""
import glob
import os
import sys
from pathlib import Path

import bnal_config
import bnal_metrics

_FALLBACK = {"verified": False, "sweep_threshold": 12,
             "counted_globs": ["harness/scripts/*.py", "harness/*.config.yaml",
                               "harness/validators/*.py", "skills/*/SKILL.md"]}
_MARKER = "sweep-marker.json"


def _counts(root: Path, globs):
    """Deterministic: {glob: file-count} under root."""
    return {g: len(glob.glob(str(root / g))) for g in globs}


def _baseline(root: Path):
    recs = bnal_metrics.read(root, _MARKER)
    return recs[-1] if recs else {}


def status(root: Path, cfg):
    globs = cfg.get("counted_globs", _FALLBACK["counted_globs"])
    now = _counts(root, globs)
    base = _baseline(root).get("counts", {})
    delta = sum(max(0, now.get(g, 0) - base.get(g, 0)) for g in globs)
    total = sum(now.values())
    return now, delta, total


def mark(root: Path, cfg):
    now, _, total = status(root, cfg)
    bnal_metrics.append(root, _MARKER, {"counts": now, "total": total},
                        comment="sweep-gate baseline (local)")
    return total


def check(root: Path, cfg) -> str:
    thr = int(cfg.get("sweep_threshold", 12))
    _, delta, total = status(root, cfg)
    if not _baseline(root):
        return f"[sweep-gate] chưa có baseline — chạy `sweep-gate.py --mark` để chốt mốc Sweep đầu (tổng {total})."
    if delta >= thr:
        return (f"⟳ [sweep-gate] đã THÊM {delta} đơn vị kể từ Sweep cuối (ngưỡng {thr}) → đến lúc "
                f"SWEEP: /simplify, gỡ trùng/merge, unship cái không dùng, /tidy. "
                f"Xong chạy `sweep-gate.py --mark`. (Boris: Sweeper là thói quen, không phải khi-nhớ-ra.)")
    return f"[sweep-gate] +{delta}/{thr} kể từ Sweep cuối — chưa cần gọt."


def self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness").mkdir()
        (root / "s").mkdir()
        cfg = {"verified": False, "sweep_threshold": 2, "counted_globs": ["s/*.py"]}
        for i in range(2):
            (root / "s" / f"a{i}.py").write_text("x", encoding="utf-8")
        mark(root, cfg)                                   # baseline = 2
        _, delta0, _ = status(root, cfg)
        for i in range(3):                                # add 3 → delta 3 >= threshold 2
            (root / "s" / f"b{i}.py").write_text("x", encoding="utf-8")
        _, delta1, _ = status(root, cfg)
        msg = check(root, cfg)
        ok = delta0 == 0 and delta1 == 3 and "SWEEP" in msg
        mark(root, cfg)                                   # re-mark → delta back to 0
        _, delta2, _ = status(root, cfg)
        ok = ok and delta2 == 0
    print("sweep-gate self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--root" in args:
        i = args.index("--root"); root = Path(args[i + 1]); del args[i:i + 2]
    if "--self-test" in args:
        sys.exit(self_test())
    cfg = bnal_config.load(root, "sweep-gate", _FALLBACK)
    if "--mark" in args:
        print(f"[sweep-gate] baseline Sweep đã chốt (tổng {mark(root, cfg)} đơn vị)."); return
    print(check(root, cfg))   # default = --check


if __name__ == "__main__":
    main()
