#!/usr/bin/env python3
"""bnal_metrics — shared by-code JSONL capture (gitignore + fail-open). ONE place replacing the
_ensure_gitignored / _metrics_file / _read / write_all that were copy-pasted into the
capture features (flywheel, mem-rank, token-budget). Capture must never break the session.

proof: harness/scripts/flywheel.py
(thư viện dùng chung, không có CLI riêng — exercised transitively bởi flywheel.py --self-test,
import trực tiếp bnal_metrics)"""
import json
from pathlib import Path


def _file(root, rel):
    return Path(root) / "harness" / "metrics" / rel


def ensure_gitignored(root, rel, comment=""):
    try:
        (Path(root) / "harness" / "metrics").mkdir(parents=True, exist_ok=True)
        gi = Path(root) / ".gitignore"
        cur = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
        line = f"harness/metrics/{rel}"
        if line not in cur:
            with open(gi, "a", encoding="utf-8") as f:
                f.write(f"\n# {comment or 'bnal metrics (local)'}\n{line}\n")
    except Exception:
        pass


def append(root, rel, rec, comment=""):
    try:
        ensure_gitignored(root, rel, comment)
        with open(_file(root, rel), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read(root, rel):
    try:
        lines = _file(root, rel).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def write_all(root, rel, recs, comment=""):
    try:
        ensure_gitignored(root, rel, comment)
        with open(_file(root, rel), "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception:
        pass
