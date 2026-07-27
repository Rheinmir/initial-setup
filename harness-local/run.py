#!/usr/bin/env python3
"""harness-local/run.py — chạy rule RIÊNG của dự án (harness-local/validators/*.py).

Modes:
  run.py hook         # stdin JSON event → chạy mọi validator với event (PreToolUse/Stop)
  run.py files <f...> # pre-commit/CI: chạy validator trên file đổi
  run.py check        # self-test: id P<n> hợp lệ/không trùng/không đụng R · validator compile
  run.py firedrill    # CHỨNG mỗi rule RIÊNG còn cắn: drive bad→phải chặn, good→phải qua
  run.py list         # liệt kê rule từ policy.yaml
Exit 0 = pass · 2 = có rule block (hoặc check/firedrill fail). Fail-open per-validator (1 cái
lỗi không làm gãy phiên/commit). File validator bắt đầu '_' bị BỎ QUA (mẫu/helper).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# HARNESS_LOCAL_DIR: cho CI chạy ENGINE luôn-mới (từ harness-src) trên RULES của repo khác.
# Tách đúng chỗ căng: engine update theo framework, rules/validators ở lại project-owned.
HERE = Path(os.environ.get("HARNESS_LOCAL_DIR") or Path(__file__).resolve().parent)
VDIR = HERE / "validators"


def _validators():
    return sorted(p for p in VDIR.glob("*.py") if not p.name.startswith("_")) if VDIR.is_dir() else []


def _run_one(vpath, args, stdin_text):
    try:
        r = subprocess.run([sys.executable, str(vpath), *args], input=stdin_text,
                           capture_output=True, text=True, timeout=20)
        return r.returncode, (r.stderr or "").strip()
    except Exception:
        return 0, ""   # fail-open: 1 validator lỗi không chặn cả phiên


def _run_all(args, stdin_text):
    fails = []
    for v in _validators():
        rc, err = _run_one(v, args, stdin_text)
        if rc == 2:
            fails.append(err or f"[{v.name}] block")
    if fails:
        print("[harness-local] rule dự án chặn:\n" + "\n".join(fails), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


def _rules():
    try:
        import yaml
        data = yaml.safe_load((HERE / "policy.yaml").read_text(encoding="utf-8")) or {}
        rs = data.get("rules") or []
        return rs if isinstance(rs, list) else []
    except Exception:
        return []


def mode_check():
    probs, seen = [], set()
    for r in _rules():
        rid = str(r.get("id", "")).strip()
        if re.fullmatch(r"R\d+", rid):
            probs.append(f"id {rid}: ĐỤNG namespace framework (R<n>) — đổi sang P<n>")
        elif not re.fullmatch(r"P\d+", rid):
            probs.append(f"id '{rid}': sai format — phải P<n>")
        if rid and rid in seen:
            probs.append(f"id {rid}: trùng")
        seen.add(rid)
        vp = str(r.get("validator", "")).strip()
        if vp and not ((HERE.parent / vp).is_file() or Path(vp).is_file()):
            probs.append(f"{rid}: validator '{vp}' không tồn tại")
    for v in _validators():
        if subprocess.run([sys.executable, "-m", "py_compile", str(v)], capture_output=True).returncode != 0:
            probs.append(f"{v.name}: không compile")
    if probs:
        print("[harness-local check] vi phạm:\n  - " + "\n  - ".join(probs), file=sys.stderr)
        sys.exit(2)
    print(f"[harness-local] OK — {len(_validators())} validator · {len(seen - {''})} rule (P-namespace, không đụng R)")
    sys.exit(0)


def _resolve_validator(vp):
    """path validator (tương đối gốc repo) → Path tuyệt đối, hoặc None."""
    for cand in (HERE.parent / vp, Path(vp)):
        if cand.is_file():
            return cand
    return None


def _event(fx):
    """fixture {path?, content?} → 1 write-event JSON đúng contract validator."""
    fx = fx if isinstance(fx, dict) else {"content": str(fx)}
    return json.dumps({"action": "write",
                       "file_path": fx.get("path") or "harness-local-firedrill.tmp",
                       "content": fx.get("content") or ""})


def mode_firedrill():
    """Fire-drill rule RIÊNG: mỗi rule CÓ validator phải CHỨNG được còn cắn qua fixture tự khai.
    bad→exit2 (chặn), good→exit0 (qua). Rule có validator mà THIẾU fixture = blind-spot → FAIL
    (không im lặng: 'không chứng được rule còn sống' chính là dark-rail của rule đó)."""
    ruled = [r for r in _rules() if str(r.get("validator", "")).strip()]
    dark, unproven, good = [], [], []
    for r in ruled:
        rid = str(r.get("id", "?"))
        vp = _resolve_validator(str(r.get("validator", "")).strip())
        if vp is None:
            dark.append(f"{rid}: validator không tồn tại — rule không thể cắn"); continue
        fx = r.get("fixtures") or {}
        if not (isinstance(fx, dict) and fx.get("bad") is not None and fx.get("good") is not None):
            unproven.append(rid); continue
        rc_bad, _ = _run_one(vp, [], _event(fx["bad"]))
        rc_good, _ = _run_one(vp, [], _event(fx["good"]))
        if rc_bad != 2:
            dark.append(f"{rid}: fixture 'bad' KHÔNG bị chặn (rc={rc_bad}) — rule CHẾT (dark rail)")
        elif rc_good != 0:
            dark.append(f"{rid}: fixture 'good' bị chặn (rc={rc_good}) — rule OVER-BLOCK")
        else:
            good.append(rid)
    for rid in good:
        print(f"  \033[1;32m✓\033[0m {rid}: bad→chặn · good→qua (còn cắn)")
    for rid in unproven:
        print(f"  \033[1;33m!\033[0m {rid}: THIẾU fixtures {{bad, good}} — không chứng được còn cắn", file=sys.stderr)
    for d in dark:
        print(f"  \033[1;31m✗\033[0m {d}", file=sys.stderr)
    if dark or unproven:
        print(f"[harness-local firedrill] {len(good)} chứng · {len(unproven)} chưa-chứng · "
              f"{len(dark)} CHẾT — thêm fixtures:{{bad,good}} vào policy.yaml cho rule chưa-chứng.",
              file=sys.stderr)
        sys.exit(2)
    print(f"[harness-local firedrill] OK — {len(good)}/{len(good)} rule RIÊNG chứng được còn cắn.")
    sys.exit(0)


def mode_list():
    for r in _rules():
        print(f"  {r.get('id', '?')} {r.get('name', '')} — {r.get('statement', '')}")
    print(f"  ({len(_validators())} validator file)")
    sys.exit(0)


def main():
    a = sys.argv[1:]
    if not a:
        mode_check()
    m = a[0]
    if m == "hook":
        _run_all([], sys.stdin.read())
    elif m == "files":
        _run_all(a[1:], "")
    elif m in ("check", "--check"):
        mode_check()
    elif m in ("firedrill", "--firedrill"):
        mode_firedrill()
    elif m in ("list", "--list"):
        mode_list()
    else:
        mode_check()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # fail-open tuyệt đối
