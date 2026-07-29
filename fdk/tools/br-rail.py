#!/usr/bin/env python3
"""br-rail — công tắc "Rail" của dây chuyền /br: bật/tắt gate MỀM của harness.

"On the rails" = đang trong tầm kiểm soát (harness gác). MẶC ĐỊNH ON — auto-on cả phiên
khi dùng /br (default = on nên không cần cơ chế thêm). Ba trạng thái:
  on    — gác đầy đủ (mặc định).
  off   — tắt gate MỀM cho tới khi bật lại (phiên).
  skip  — bỏ gate MỀM ĐÚNG MỘT lần chạy rồi TỰ bật lại (one-shot) + cảnh báo.

AN TOÀN (quyết định user 2026-07-13): off/skip CHỈ tắt gate MỀM — frame-lint R7 content,
visual-qa UI, assumption-gate. PHANH CỨNG (diff-jail · test-hash · scope-clean của loop-runner)
+ luật cấu trúc (R1–R6) + hook bảo mật/liêm-chính repo KHÔNG BAO GIỜ tắt qua đây. Không footgun.

State: `br/.rail` = "on"|"off" (persistent); `br/.rail-skip` = cờ one-shot (consume xong xoá).

Usage:
  br-rail.py status [--root .]         # trạng thái + nhắc toggle (LUÔN in reminder)
  br-rail.py on|off|skip [--root .]
  br-rail.py consume [--root .]        # (máy gọi) trả effective mode + xoá skip
  br-rail.py selftest
"""
import argparse
import sys
from pathlib import Path

REMINDER = "  ↺ Rail bật/tắt được: `/br rail on` (gác đủ) · `off` (tắt gate mềm) · `skip` (bỏ 1 lần). Phanh cứng + bảo mật KHÔNG tắt qua đây."


def _paths(root):
    br = Path(root) / "br"
    return br / ".rail", br / ".rail-skip"


def get_state(root):
    """persistent state: 'on' (mặc định) | 'off'."""
    rail, _ = _paths(root)
    if rail.exists():
        v = rail.read_text(encoding="utf-8").strip().lower()
        if v in ("on", "off"):
            return v
    return "on"


def set_state(root, mode):
    rail, skip = _paths(root)
    rail.parent.mkdir(parents=True, exist_ok=True)
    if mode == "skip":
        skip.write_text("1", encoding="utf-8")
        return
    rail.write_text(mode, encoding="utf-8")
    if skip.exists():
        skip.unlink()


def consume(root):
    """effective mode cho MỘT lần chạy; skip là one-shot → xoá sau khi đọc.
    Trả 'on' | 'off' | 'skip'. off/skip ⇒ tắt gate mềm."""
    rail, skip = _paths(root)
    if skip.exists():
        skip.unlink()
        return "skip"
    return get_state(root)


def soft_off(effective):
    """gate mềm có bị tắt không (off hoặc skip)."""
    return effective in ("off", "skip")


def cmd_status(root):
    rail, skip = _paths(root)
    state = get_state(root)
    pending_skip = skip.exists()
    icon = "🟢" if state == "on" and not pending_skip else "🟡"
    print(f"{icon} Rail: {state.upper()}" + (" · skip đang chờ (bỏ gate mềm lần chạy tới)" if pending_skip else ""))
    print(f"   gate mềm (R7 content · visual-qa · assumption-gate): {'TẮT' if (state=='off' or pending_skip) else 'BẬT'}")
    print("   phanh cứng (diff-jail · test-hash · scope-clean) + bảo mật: LUÔN BẬT")
    print(REMINDER)
    return 0


def cmd_set(root, mode):
    set_state(root, mode)
    if mode == "on":
        print("🟢 Rail ON — harness gác đầy đủ.")
    elif mode == "off":
        print("🟡 Rail OFF — ĐÃ TẮT gate mềm (R7/visual-qa/assumption) tới khi `/br rail on`. Phanh cứng vẫn gác.")
    else:
        print("🟡 Rail SKIP — bỏ gate mềm ĐÚNG lần chạy tới rồi TỰ bật lại. Phanh cứng vẫn gác.")
    print(REMINDER)
    return 0


def cmd_consume(root):
    eff = consume(root)
    print(eff)  # máy đọc dòng đầu
    if soft_off(eff):
        print(f"⚠️  gate mềm BỎ QUA lần chạy này (rail={eff}). Phanh cứng vẫn gác.", file=sys.stderr)
    return 0


def selftest():
    import tempfile
    ok = True

    def chk(c, m):
        nonlocal ok
        if not c:
            ok = False
            print("  [FAIL]", m)

    with tempfile.TemporaryDirectory() as td:
        chk(get_state(td) == "on", "mặc định phải ON")
        chk(consume(td) == "on", "consume mặc định = on")
        chk(not soft_off("on"), "on không tắt gate mềm")
        set_state(td, "off")
        chk(get_state(td) == "off", "set off không giữ")
        chk(soft_off(consume(td)) is True, "off ⇒ soft_off")
        chk(get_state(td) == "off", "off vẫn bền sau consume")
        set_state(td, "on")
        chk(get_state(td) == "on", "on ghi đè off")
        set_state(td, "skip")
        chk(consume(td) == "skip", "skip đọc = skip")
        chk(consume(td) == "on", "skip là ONE-SHOT — lần sau về on")
        # skip không đổi persistent state
        set_state(td, "off"); set_state(td, "skip")
        chk(consume(td) == "skip", "skip trước")
        chk(consume(td) == "off", "sau skip về persistent off (không phải on)")

    print("br-rail self-test:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-rail.py", description="Công tắc Rail của /br (bật/tắt gate mềm harness).")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("on", "off", "skip"):
        sp = sub.add_parser(name); sp.add_argument("--root", default="."); sp.set_defaults(func=lambda a, n=name: cmd_set(a.root, n))
    st = sub.add_parser("status"); st.add_argument("--root", default="."); st.set_defaults(func=lambda a: cmd_status(a.root))
    c = sub.add_parser("consume"); c.add_argument("--root", default="."); c.set_defaults(func=lambda a: cmd_consume(a.root))
    t = sub.add_parser("selftest"); t.set_defaults(func=lambda a: selftest())
    return p


if __name__ == "__main__":
    _a = build_parser().parse_args()
    sys.exit(_a.func(_a))
