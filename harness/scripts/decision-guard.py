#!/usr/bin/env python3
"""decision-guard — bắt xoá-vật-lý một mục mechanisms.yaml có anchor_symbol/live_probe mà
KHÔNG đi qua status: retired. So diff THEO TỪNG id (FR-010, đóng nợ U-03) — không so nguyên
file, để hai người sửa hai mục KHÁC NHAU trong cùng file cùng một merge không báo oan nhau.

CLI:
    decision-guard.py check [--from REF] [--to REF]   # mặc định REF cũ=HEAD, REF mới=working tree
    decision-guard.py --self-test
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MECH_PATH = ROOT / "harness/mechanisms.yaml"


def _load_liveness():
    spec = importlib.util.spec_from_file_location(
        "decision_liveness", ROOT / "harness/scripts/decision-liveness.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_dl = _load_liveness()


def _read_at(ref, path: Path, root: Path) -> str:
    """ref=None -> đọc working tree; ref='HEAD' (hoặc bất kỳ) -> đọc bản đã commit."""
    if ref is None:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    out = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{path.relative_to(root)}"],
                          capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def find_silent_deletes(old_text: str, new_text: str) -> list:
    """Trả list id bị XOÁ VẬT LÝ (có mặt ở old, vắng ở new). So THEO ID — không so nguyên
    file — nên hai mục KHÁC NHAU cùng đổi trong 1 merge không báo oan nhau (FR-010, U-03)."""
    old_ids = {e["id"] for e in _dl.parse_mechanisms(old_text) if e.get("anchor_symbol") or e.get("live_probe")}
    new_ids = {e["id"] for e in _dl.parse_mechanisms(new_text)}
    return [oid for oid in old_ids if oid not in new_ids]


def cmd_check(args):
    old_text = _read_at(args.from_ref, MECH_PATH, ROOT)
    new_text = _read_at(args.to_ref, MECH_PATH, ROOT) if args.to_ref else MECH_PATH.read_text(encoding="utf-8")
    if not old_text:
        print("· không đọc được bản cũ (ref không hợp lệ hoặc file mới tạo) — bỏ qua")
        return 0
    silent = find_silent_deletes(old_text, new_text)
    if not silent:
        print("✓ không có mục nào bị xoá vật lý ngoài status: retired")
        return 0
    for sid in silent:
        print(f"✗ mục '{sid}' đã BIẾN MẤT khỏi mechanisms.yaml mà không qua status: retired "
              f"(FR-009 — WHY biến mất không dấu vết, sửa lại bằng status: retired thay vì xoá dòng)")
    return 0  # BÁO CÁO, KHÔNG CHẶN (FR-006/Global constraints) — /lint gọi khi nghi ngờ


def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)


def self_test() -> int:
    fails = []

    old = ("mechanisms:\n"
           "  - id: a\n    live_probe: x\n"
           "  - id: b\n    live_probe: y\n")

    new_silent = "mechanisms:\n  - id: a\n    live_probe: x\n"
    ck("phát hiện xoá lén (b biến mất)", find_silent_deletes(old, new_silent) == ["b"], fails)

    new_retired = ("mechanisms:\n  - id: a\n    live_probe: x\n"
                   "  - id: b\n    live_probe: y\n    status: retired\n")
    ck("xoá hợp lệ (status: retired, id còn) -> không báo", find_silent_deletes(old, new_retired) == [], fails)

    # FR-010 race: hai mục KHÁC NHAU cùng đổi trong 1 merge (thêm mục mới + retire mục khác)
    new_race = ("mechanisms:\n  - id: a\n    live_probe: x\n"
                "  - id: b\n    live_probe: y\n    status: retired\n"
                "  - id: c\n    live_probe: z\n")
    ck("FR-010 race: thêm mục mới + retire mục khác cùng merge -> không báo oan (đóng nợ U-03)",
       find_silent_deletes(old, new_race) == [], fails)

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="decision-anchoring xoá-vật-lý guard")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("check")
    p.add_argument("--from", dest="from_ref", default="HEAD")
    p.add_argument("--to", dest="to_ref", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if args.cmd == "check":
        sys.exit(cmd_check(args))
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
