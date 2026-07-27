#!/usr/bin/env python3
"""bnal-selftest — META-GATE chống drift cho danh sách self-test BNAL.

Vì sao cần: các gate cũ chỉ verify "render == generator" / "config có ADAPT-CHECKLIST", KHÔNG
ai cross-check "MỌI script có --self-test ĐỀU được fdk-gate chạy". Nên thêm một BNAL feature mà
quên wire self-test vào fdk-gate → trôi lọt, không gate nào báo. Đây là cái cross-check đó.

  --check   : mọi harness/scripts/*.py có handler --self-test/selftest PHẢI được fdk-gate khai
              (hoặc nằm trong EXEMPT). Thiếu → exit 2. (Anti-drift: thêm feature quên gate → đỏ.)
  --list    : in discovered (có self-test) vs gated (fdk-gate khai) + thiếu/exempt.

EXEMPT: fdk-gate (chính nó chứa các lệnh self-test), flywheel (test qua shim failure/success-flywheel).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "harness" / "scripts"
GATE = SC / "fdk-gate.py"
EXEMPT = {"fdk-gate", "flywheel", "bnal-selftest"}


def _has_selftest(p: Path) -> bool:
    # Chỉ match dạng QUOTED ('--self-test' / 'selftest' trong so-sánh argv) = handler thật.
    # Match trần từng vồ nhầm docstring nhắc tới --self-test bằng văn xuôi
    # (bnal_config/bnal_guard/bnal_metrics: "không có CLI riêng để --self-test") → drift giả.
    try:
        return bool(re.search(r'["\'](?:--self-test|selftest)["\']', p.read_text(encoding="utf-8")))
    except Exception:
        return False


def discover():
    return {p.stem for p in SC.glob("*.py") if _has_selftest(p)}


def gated():
    try:
        return set(re.findall(r"harness/scripts/([a-z0-9_-]+)\.py", GATE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def main():
    args = sys.argv[1:]
    disc, gat = discover(), gated()
    missing = sorted(disc - gat - EXEMPT)
    if "--list" in args:
        print("discovered (--self-test):", " ".join(sorted(disc)))
        print("gated (fdk-gate khai)   :", " ".join(sorted(gat & disc)))
        print("exempt                  :", " ".join(sorted(EXEMPT)))
        print("THIẾU khỏi gate          :", " ".join(missing) or "(none)")
        return
    # default = --check
    if missing:
        print("[bnal-selftest] DRIFT — script có --self-test nhưng fdk-gate KHÔNG chạy "
              f"({len(missing)}): {', '.join(missing)}\n  → thêm `python3 harness/scripts/<name>.py "
              "--self-test` vào step 'BNAL feature self-tests' của fdk-gate.py (hoặc EXEMPT nếu cố ý).",
              file=sys.stderr)
        sys.exit(2)
    print(f"[bnal-selftest] ✓ {len(disc - EXEMPT)} BNAL self-test đều được fdk-gate chạy — không drift.")


if __name__ == "__main__":
    main()
