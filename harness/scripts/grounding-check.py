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
  grounding-check.py --check FILE   # FILE = '-' đọc stdin
  grounding-check.py --self-test

Exit code (BA giá trị PHÂN BIỆT — một cổng CI chỉ coi 0 là "đã chấm và hợp lệ"):
  0 = verdict hợp lệ theo schema
  2 = verdict ĐỌC ĐƯỢC nhưng schema sai (thiếu field / decision lạ / …)
  3 = hạ tầng lỗi — KHÔNG đọc được FILE (chưa ai ghi verdict). Trước bản vá này, case
      này trả về 0 giống hệt "hợp lệ", nên một cổng chỉ check `rc==0` không phân biệt
      được "chưa ai chấm" với "đã chấm PASS" — gate coi như bị bypass bằng cách không
      sinh output. KHÔNG dùng return 0 ở đây nữa.
"""
import argparse
import json
import os
import sys
from pathlib import Path

REQUIRED = {"decision", "claim", "reason"}
DECISIONS = {"approve", "revise"}
KNOWN = REQUIRED | {"required_evidence"}


def min_evidence(root=None) -> int:
    """Cap thứ 10 của spec §5: 'minimum evidence required for finalization'.

    Khác 9 cap kia — chúng là TRẦN TRÊN (đừng vượt), cái này là SÀN DƯỚI (đừng chốt khi
    chưa đủ bằng chứng). Nên nó không sống trong bộ đếm mà ở cổng CHỐT: verdict `approve`
    là lúc một việc được tuyên bố xong, và đó đúng chỗ hỏi "dựa vào đâu mà xong?".

    Đọc từ `token-budget.config.yaml` để mọi trần nằm chung một chỗ người dùng đã được hỏi.
    Mặc định 0 = tắt, giữ nguyên hành vi cũ (approve không cần bằng chứng) — bật lên là
    quyết định của người dùng, không phải mặc định áp xuống.
    """
    try:
        import re
        p = Path(root or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        cfg = p / "harness" / "token-budget.config.yaml"
        if not cfg.exists():
            return 0
        m = re.search(r"^\s*min_evidence:\s*(\d+)", cfg.read_text(encoding="utf-8"), re.M)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0                                  # fail-open: không đọc được cấu hình thì không siết


def check_verdict(obj: dict, root=None) -> list:
    """Trả danh sách lỗi schema; [] = hợp lệ."""
    errs = []
    need = min_evidence(root)
    if need > 0:
        ev = obj.get("required_evidence")
        n = len([x for x in ev if str(x).strip()]) if isinstance(ev, list) else 0
        if n < need:
            errs.append(f"cần tối thiểu {need} bằng chứng để chốt (đang có {n}) "
                        f"— spec §5 minimum-evidence; đổi ở token-budget.config.yaml")
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
            # hạ tầng lỗi: KHÔNG trả 0 — 0 nghĩa là "verdict hợp lệ", và file thiếu nghĩa là
            # chưa ai chấm gì cả. Một cổng CI chỉ check rc==0 phải phân biệt được 2 ca này,
            # nếu không "quên ghi verdict" trở thành cách bypass gate không tốn công.
            print(f"grounding-check: không đọc được {src} ({e}) — KHÔNG có verdict để chấm", file=sys.stderr)
            return 3
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
            errs = check_verdict(obj, root="/nonexistent-so-min-evidence-tat")
        passed = (not errs) == want_valid
        print(f"  {'✓' if passed else '✗'} {label}"
              f"{'' if passed else '  → ' + ('hợp lệ' if not errs else '; '.join(errs))}")
        ok = ok and passed

    # ── cap thứ 10 spec §5: minimum evidence (SÀN dưới, không phải trần trên) ──────────
    import tempfile
    ev_cases = []
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        (r / "harness").mkdir()
        cfg = r / "harness" / "token-budget.config.yaml"
        approve_0 = {"decision": "approve", "claim": "c", "reason": "r"}
        approve_2 = {"decision": "approve", "claim": "c", "reason": "r",
                     "required_evidence": ["test A đỏ→xanh", "log B dòng 12"]}

        cfg.write_text("budgets:\n  min_evidence: 0\n", encoding="utf-8")
        ev_cases.append(("min_evidence=0 (mặc định): approve KHÔNG cần bằng chứng",
                         check_verdict(approve_0, root=r) == []))
        ev_cases.append(("min_evidence=0: đọc ra đúng 0", min_evidence(r) == 0))

        cfg.write_text("budgets:\n  min_evidence: 2\n", encoding="utf-8")
        errs2 = check_verdict(approve_0, root=r)
        ev_cases.append(("min_evidence=2: approve TAY KHÔNG bị chặn",
                         any("tối thiểu 2" in e for e in errs2)))
        ev_cases.append(("min_evidence=2: approve có 2 bằng chứng thì QUA",
                         check_verdict(approve_2, root=r) == []))
        ev_cases.append(("min_evidence=2: 1 bằng chứng vẫn thiếu → chặn",
                         check_verdict({**approve_2, "required_evidence": ["chỉ một"]}, root=r) != []))
        ev_cases.append(("không có config → fail-open, KHÔNG siết",
                         min_evidence("/nonexistent") == 0))

    for label, passed in ev_cases:
        print(f"  {'✓' if passed else '✗'} {label}")
        ok = ok and passed

    # ── bug thật đã tìm thấy: file verdict KHÔNG tồn tại từng trả rc=0, giống hệt hợp lệ ──
    rc_missing = cmd_check("/nonexistent-verdict-file-xyz.json")
    missing_ok = rc_missing == 3 and rc_missing != 0
    print(f"  {'✓' if missing_ok else '✗'} file verdict thiếu → rc=3 (KHÔNG phải 0, không giả PASS)")
    ok = ok and missing_ok

    with tempfile.TemporaryDirectory() as td3:
        valid_file = Path(td3) / "v.json"
        valid_file.write_text('{"decision":"approve","claim":"c","reason":"r"}', encoding="utf-8")
        rc_valid = cmd_check(str(valid_file))
        three_way_ok = rc_valid == 0 and rc_missing == 3 and rc_valid != rc_missing
        print(f"  {'✓' if three_way_ok else '✗'} 3 mã thoát phân biệt được nhau: hợp lệ=0, hạ tầng lỗi=3")
        ok = ok and three_way_ok

    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
