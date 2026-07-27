#!/usr/bin/env python3
"""decision-anchoring-crosscheck — FR-010 trust boundary: concept KHÔNG được tự khai số đo;
mọi con số trích trong concept phải khớp output THẬT của decision-liveness.py/decision-guard.py.
Concept dùng convention `<!-- FACT: key=value -->` cho mỗi số đo trích dẫn; script đọc lại các
FACT đó và so với giá trị đo NGAY LÚC CHẠY — không tin lời tự khai lúc viết concept.

CLI:
    decision-anchoring-crosscheck.py check
    decision-anchoring-crosscheck.py --self-test
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "llmwiki/wiki/concepts/decision-anchoring.md"
MECH = ROOT / "harness/mechanisms.yaml"
FACT_RE = re.compile(r'<!--\s*FACT:\s*(\S+?)=(\S+?)\s*-->')


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def real_facts() -> dict:
    dl = _load("decision_liveness", "harness/scripts/decision-liveness.py")
    entries = dl.parse_mechanisms(MECH.read_text(encoding="utf-8"))
    anchored = [e for e in entries if e.get("anchor_symbol")]
    lv_rc = subprocess.run(
        [sys.executable, str(ROOT / "harness/scripts/decision-liveness.py"), "--self-test"],
        capture_output=True).returncode
    gd_rc = subprocess.run(
        [sys.executable, str(ROOT / "harness/scripts/decision-guard.py"), "--self-test"],
        capture_output=True).returncode
    return {
        "total_mechanisms": str(len(entries)),
        "anchored_symbol_count": str(len(anchored)),
        "liveness_self_test_exit": str(lv_rc),
        "guard_self_test_exit": str(gd_rc),
    }


def check() -> int:
    if not CONCEPT.is_file():
        print("· concept chưa tồn tại — chưa tới lúc chạy crosscheck")
        return 0
    claimed = dict(FACT_RE.findall(CONCEPT.read_text(encoding="utf-8")))
    if not claimed:
        print("✗ concept KHÔNG có FACT nào (thiếu <!-- FACT: key=value -->) — không đối chiếu được")
        return 1
    real = real_facts()
    bad = [f"{k}: concept khai {v!r}, thật đo được {real.get(k, '<không đo được>')!r}"
           for k, v in claimed.items() if real.get(k) != v]
    for b in bad:
        print(f"✗ {b}")
    if bad:
        return 1
    print(f"✓ {len(claimed)} FACT trong concept khớp output thật")
    return 0


def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)


def self_test() -> int:
    fails = []
    m = FACT_RE.findall("vd: <!-- FACT: total_mechanisms=999 -->")
    ck("FACT_RE parse đúng 1 cặp key=value", m == [("total_mechanisms", "999")], fails)
    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(check())
