#!/usr/bin/env python3
"""grounding-check — validator schema cho verdict của evaluator (tất định, 0-token, KHÔNG LLM).

Tầng grounding (PDF "Graph Engineering" §V): feedback của evaluator phải có CẤU TRÚC
`{decision, claim, reason, required_evidence[]}`. "nhìn ổn" không phải feedback — nó là
schema-invalid, và script này là thứ nói KHÔNG một cách tất định. Ai phát verdict cũng
được: /qc-code, council judge, hay một agent bất kỳ.

Schema (điều kiện hard-fail):
  decision            ∈ {approve, revise}
  claim, reason       str non-empty
  required_evidence   khi decision == "revise": list >= 1 mục str non-empty
  field lạ            chỉ CẢNH BÁO, không fail (forward-compat)

Dùng:
  grounding-check.py --check FILE   # FILE = '-' đọc stdin; exit 0 hợp lệ, exit 2 + liệt kê lỗi
  grounding-check.py --self-test
"""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = {"decision", "claim", "reason"}
DECISIONS = {"approve", "revise"}
KNOWN = REQUIRED | {"required_evidence"}


def check_verdict(obj: dict) -> list:
    """Trả danh sách lỗi schema; [] = hợp lệ."""
    errs = []
    missing = REQUIRED - set(obj)
    if missing:
        errs.append("thiếu field: " + ", ".join(sorted(missing)))
    if obj.get("decision") not in DECISIONS:
        errs.append("decision phải là approve|revise")
    for k in ("claim", "reason"):
        if not str(obj.get(k, "")).strip():
            errs.append(f"{k} rỗng")
    if obj.get("decision") == "revise":
        ev = obj.get("required_evidence")
        if not (isinstance(ev, list) and ev and all(str(x).strip() for x in ev)):
            errs.append("revise bắt buộc required_evidence[] >= 1 mục non-empty")
    return errs


def unknown_fields(obj: dict) -> list:
    return sorted(set(obj) - KNOWN)


def load_verdict(text: str):
    """Trả (obj|None, errs) — text không phải object JSON là lỗi schema, không phải lỗi hạ tầng."""
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None, ['không phải JSON — verdict phải là object JSON theo schema ("nhìn ổn" không đạt)']
    if not isinstance(obj, dict):
        return None, [f"verdict phải là object JSON, không phải {type(obj).__name__}"]
    return obj, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", metavar="FILE", help="file JSON verdict ('-' = stdin)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.check:
        ap.print_help()
        sys.exit(0)
    sys.exit(cmd_check(a.check))


def cmd_check(src: str) -> int:
    if src == "-":
        text = sys.stdin.read()
    else:
        try:
            text = Path(src).read_text(encoding="utf-8")
        except OSError as e:
            # hạ tầng lỗi (không đọc được file) → fail-open, không phá phiên
            print(f"grounding-check: không đọc được {src} ({e}) — bỏ qua (fail-open)", file=sys.stderr)
            return 0
    obj, errs = load_verdict(text)
    if obj is not None:
        errs = check_verdict(obj)
        for f in unknown_fields(obj):
            print(f"grounding-check: cảnh báo — field lạ '{f}' (bỏ qua, forward-compat)", file=sys.stderr)
    if errs:
        print("grounding-check: verdict KHÔNG hợp lệ", file=sys.stderr)
        for e in errs:
            print(f"  ✗ {e}", file=sys.stderr)
        return 2
    print("grounding-check: verdict hợp lệ ✓")
    return 0


def self_test():
    """6 case theo PLAN — mỗi case: verdict vào, hợp-lệ/không ra."""
    cases = [
        ("approve hợp lệ (field lạ chỉ warn)",
         '{"decision":"approve","claim":"diff không có lỗi nặng","reason":"4 mục đều >= 8/10","score":9}', True),
        ("revise hợp lệ",
         '{"decision":"revise","claim":"paginate() bỏ sót phần tử cuối","reason":"off-by-one ở paginate.py:42",'
         '"required_evidence":["test qc-off-by-one-pagination chạy ĐỎ"]}', True),
        ("revise thiếu required_evidence",
         '{"decision":"revise","claim":"paginate() bỏ sót phần tử cuối","reason":"off-by-one ở paginate.py:42"}', False),
        ("decision lạ",
         '{"decision":"looks-good","claim":"ok","reason":"ok"}', False),
        ("claim rỗng",
         '{"decision":"approve","claim":"   ","reason":"4 mục đều >= 8/10"}', False),
        ("free-text 'nhìn ổn' (không phải JSON)",
         'nhìn ổn', False),
    ]
    ok = True
    for label, text, want_valid in cases:
        obj, errs = load_verdict(text)
        if obj is not None:
            errs = check_verdict(obj)
        passed = (not errs) == want_valid
        print(f"  {'✓' if passed else '✗'} {label}"
              f"{'' if passed else '  → ' + ('hợp lệ' if not errs else '; '.join(errs))}")
        ok = ok and passed
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
