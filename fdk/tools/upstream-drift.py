#!/usr/bin/env python3
"""upstream-drift — MỘT lệnh thấy trạng thái repo local vs repo gốc framework.

Trả lời 3 câu trong một cái nhìn:
  1. Ta chậm/nhanh bao nhiêu so với upstream? (behind / ahead so với merge-base)
  2. Upstream có gì mới, LOẠI gì? (commit chưa có, gom theo conventional-commit type;
     feat/fix đánh dấu ⭐ "đáng xem", chore/docs "thường").
  3. Cập nhật có ĐỤNG việc mình đang làm không? (file upstream đổi ∩ file local đã sửa
     — commit-since-mergebase HOẶC đang dirty → cờ ⚠ COLLISION = merge sẽ xung đột chỗ đó).

Không tự pull/merge — chỉ HIỂN THỊ để người quyết. Substrate = git.

Usage:
  upstream-drift.py [--root .] [--branch orca] [--fetch] [--ref <git-ref>] [--json]
  upstream-drift.py selftest

--branch orca  → so với origin/orca (mặc định). --ref cho phép trỏ ref bất kỳ (dùng test).
--fetch        → chạy `git fetch` trước (mặc định KHÔNG, dùng ref đã có để nhanh/offline-an-toàn).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_TYPE = re.compile(r"^[0-9a-f]+\s+(\w+)(?:\([^)]*\))?[!]?:")
USEFUL = {"feat", "fix", "perf", "refactor"}   # loại thường đáng kéo về
QUIET = {"chore", "docs", "style", "test", "ci", "build"}


def git(args, root):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def resolve_ref(root, branch, ref):
    if ref:
        return ref
    for cand in (f"origin/{branch}", branch):
        if git(["rev-parse", "--verify", "-q", cand], root).returncode == 0:
            return cand
    return None


def collect(root, branch="orca", ref=None, do_fetch=False):
    root = Path(root)
    if do_fetch:
        git(["fetch", "origin"], root)
    up = resolve_ref(root, branch, ref)
    if not up:
        return {"error": f"không tìm thấy ref upstream (origin/{branch}) — thử --fetch"}
    mb = git(["merge-base", "HEAD", up], root).stdout.strip()
    if not mb:
        return {"error": f"không có merge-base giữa HEAD và {up}"}
    behind = git(["rev-list", "--count", f"{mb}..{up}"], root).stdout.strip()
    ahead = git(["rev-list", "--count", f"{mb}..HEAD"], root).stdout.strip()
    commits = []
    for line in git(["log", "--oneline", f"{mb}..{up}"], root).stdout.splitlines():
        m = _TYPE.match(line)
        commits.append({"line": line, "type": m.group(1) if m else "other"})
    up_files = set(git(["diff", "--name-only", f"{mb}..{up}"], root).stdout.split())
    local_committed = set(git(["diff", "--name-only", f"{mb}..HEAD"], root).stdout.split())
    dirty = set()
    for l in git(["status", "--porcelain"], root).stdout.splitlines():
        if len(l) > 3:
            dirty.add(l[3:].split(" -> ")[-1].strip().strip('"'))
    local_touched = local_committed | dirty
    collisions = sorted(up_files & local_touched)
    return {
        "upstream": up, "behind": int(behind or 0), "ahead": int(ahead or 0),
        "commits": commits, "collisions": collisions,
        "up_files": len(up_files), "local_touched": len(local_touched),
    }


def report(model, out=print):
    if model.get("error"):
        out(f"[upstream-drift] {model['error']}")
        return 2
    b, a = model["behind"], model["ahead"]
    out(f"📡 So với {model['upstream']}:  ⬇ CHẬM {b} commit   ·   ⬆ nhanh {a} commit")
    if b == 0:
        out("   ✓ đã ngang upstream — không có gì để kéo.")
    # gom theo type
    by = {}
    for c in model["commits"]:
        by.setdefault(c["type"], []).append(c["line"])
    order = sorted(by, key=lambda t: (t not in USEFUL, t))
    for t in order:
        star = "⭐" if t in USEFUL else "  "
        out(f"\n {star} {t}  ({len(by[t])})")
        for line in by[t][:12]:
            out(f"      {line}")
        if len(by[t]) > 12:
            out(f"      … +{len(by[t]) - 12} nữa")
    if model["collisions"]:
        out(f"\n ⚠ ĐỤNG {len(model['collisions'])} file mình ĐANG SỬA (merge sẽ xung đột ở đây):")
        for f in model["collisions"]:
            out(f"      {f}")
        out("   → giải trước khi merge; hoặc ưu tiên bản upstream cho file quy-tắc (skill/policy).")
    else:
        out("\n ✓ không đụng file nào mình đang sửa — merge nhiều khả năng sạch.")
    out(f"\n gợi ý: xem chi tiết 1 commit `git show <hash>` · kéo về `git merge {model['upstream']}`")
    return 0


def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        git(["init", "-q", "-b", "main"], root); git(["config", "user.email", "t@t"], root); git(["config", "user.name", "t"], root)
        (root / "shared.py").write_text("v=0\n"); (root / "other.py").write_text("x=0\n")
        git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "base"], root)
        # nhánh upstream: 3 commit — feat sửa shared · chore thêm newfeat · fix sửa other
        git(["checkout", "-q", "-b", "up"], root)
        (root / "shared.py").write_text("v=1\n"); git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "feat(x): sửa shared"], root)
        (root / "newfeat.py").write_text("n=1\n"); git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "chore: thêm file"], root)
        (root / "other.py").write_text("x=up\n"); git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "fix: other"], root)
        # về nhánh local: commit sửa shared.py (collision committed) + để other.py DIRTY (collision dirty)
        git(["checkout", "-q", "main"], root)
        (root / "shared.py").write_text("v=99\n"); git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "local sửa shared"], root)
        (root / "other.py").write_text("x=dirty\n")   # uncommitted dirty, upstream cũng đổi other.py

        m = collect(str(root), ref="up")
        checks = [
            ("behind = 3", m["behind"] == 3),
            ("ahead = 1", m["ahead"] == 1),
            ("phân loại có feat", any(c["type"] == "feat" for c in m["commits"])),
            ("collision bắt shared.py (local committed đụng)", "shared.py" in m["collisions"]),
            ("collision bắt other.py (local DIRTY đụng)", "other.py" in m["collisions"]),
            ("newfeat.py KHÔNG collision (local không đụng)", "newfeat.py" not in m["collisions"]),
        ]

    print("upstream-drift self-test\n" + "-" * 50)
    for name, good in checks:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 50)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="upstream-drift.py", description="Thấy trạng thái local vs repo gốc framework (behind/ahead + commit + collision).")
    p.add_argument("--root", default=".")
    p.add_argument("--branch", default="orca")
    p.add_argument("--ref", default=None, help="ref upstream cụ thể (mặc định origin/<branch>)")
    p.add_argument("--fetch", action="store_true", help="git fetch trước khi so")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.selftest or (argv and argv[0] == "selftest"):
        return selftest()
    m = collect(args.root, args.branch, args.ref, args.fetch)
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=1))
        return 0 if not m.get("error") else 2
    return report(m)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "selftest":
        sys.exit(selftest())
    sys.exit(main(argv))
