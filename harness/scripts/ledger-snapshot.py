#!/usr/bin/env python3
"""ledger-snapshot — ký ức máy-local sống sót mất máy/mất repo (maintainer gap #2, 2026-07-18).

Vấn đề: toàn bộ bộ nhớ thứ cấp (flywheel failures/successes, memory episodic, events, scratch-log,
unknowns, tasks, audit) là JSONL gitignored MỘT MÁY — mất máy là mất não; mem-rank export chỉ phủ
memory và phải gọi tay. Tool này gom CẢ CỤM thành một tarball có manifest, prune giữ N bản,
và được SessionEnd hook gọi fail-open — backup không chờ ai nhớ.

Đích mặc định: ~/.claude/overstack-snapshots/<repo-slug>/ (sống sót xoá-repo/worktree).
Muốn sống sót MẤT MÁY: trỏ env OVERSTACK_SNAPSHOT_DIR vào thư mục có sync (iCloud/Drive/NAS)
— tool không tự chọn cloud giùm (dữ liệu có audit/command-snippets, đích off-machine là quyết
định của người).

  export [--quiet] [--keep N]   gom ledger → snap-<ts>.tar.gz + manifest; prune còn N bản (mặc 7)
  import <tar.gz>               restore: *.jsonl append-dedupe theo dòng (bản local thắng);
                                *.json state (tasks/unknowns) chỉ ghi khi local CHƯA có
  list                          liệt kê snapshot hiện có
  --self-test                   round-trip tất định trong tmp

Baselines (*-baseline.json, version.json) KHÔNG vào snapshot — regen được từ đĩa, đừng chở rác.
"""
import io
import json
import os
import re
import sys
import tarfile
import time
from pathlib import Path

# ledger nào được chở — append-only jsonl + state json; KHÔNG chở baseline (regen được)
REPO_GLOBS = ("harness/metrics/*.jsonl", ".claude/audit/*.jsonl")
REPO_FILES = ("harness/metrics/unknowns.json", "harness/metrics/tasks.json")
SKIP = re.compile(r"baseline|version\.json")


def _root(argv):
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            return Path(argv[i + 1]).resolve()
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def _dest(root: Path) -> Path:
    base = os.environ.get("OVERSTACK_SNAPSHOT_DIR")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(root)).strip("-")[-60:]
    d = Path(base) if base else Path.home() / ".claude" / "overstack-snapshots" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def _collect(root: Path):
    out = []
    for g in REPO_GLOBS:
        out += [p for p in root.glob(g) if p.is_file() and not SKIP.search(p.name)]
    out += [root / f for f in REPO_FILES if (root / f).is_file()]
    return sorted(set(out))


def export(root: Path, quiet=False, keep=7) -> Path:
    files = _collect(root)
    dest = _dest(root)
    ts = time.strftime("%Y%m%d-%H%M%S")
    tar_path = dest / f"snap-{ts}.tar.gz"
    manifest = {"schema": "ledger-snapshot/v1", "root": str(root), "ts": ts,
                "files": [str(p.relative_to(root)) for p in files]}
    with tarfile.open(tar_path, "w:gz") as tf:
        mb = json.dumps(manifest, ensure_ascii=False, indent=1).encode()
        info = tarfile.TarInfo("manifest.json"); info.size = len(mb)
        tf.addfile(info, io.BytesIO(mb))
        for p in files:
            tf.add(p, arcname=str(p.relative_to(root)))
    snaps = sorted(dest.glob("snap-*.tar.gz"))
    for old in snaps[:-max(1, keep)]:
        old.unlink()
    if not quiet:
        print(f"✓ snapshot {tar_path} ({len(files)} ledger, giữ {min(len(snaps), keep)} bản)")
        if not os.environ.get("OVERSTACK_SNAPSHOT_DIR"):
            print("  (cùng-máy khác-chỗ — sống sót mất repo; muốn sống sót MẤT MÁY: "
                  "export OVERSTACK_SNAPSHOT_DIR=<thư mục có sync>)")
    return tar_path


def _merge_jsonl(dst: Path, new_bytes: bytes) -> int:
    have = set(dst.read_text(encoding="utf-8").splitlines()) if dst.is_file() else set()
    added = [l for l in new_bytes.decode("utf-8", "ignore").splitlines() if l.strip() and l not in have]
    if added:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "a", encoding="utf-8") as f:
            f.write("\n".join(added) + "\n")
    return len(added)


def restore(root: Path, tar_path: Path) -> tuple:
    added = skipped = 0
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if m.name == "manifest.json" or not m.isfile():
                continue
            rel = Path(m.name)
            if rel.is_absolute() or ".." in rel.parts:   # chống path-traversal
                skipped += 1; continue
            data = tf.extractfile(m).read()
            dst = root / rel
            if rel.suffix == ".jsonl":
                added += _merge_jsonl(dst, data)
            else:  # state json: local thắng — chỉ restore khi vắng
                if dst.is_file():
                    skipped += 1
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(data)
                    added += 1
    return added, skipped


def self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src, dst2 = Path(d) / "src", Path(d) / "restore"
        (src / "harness" / "metrics").mkdir(parents=True)
        (src / ".claude" / "audit").mkdir(parents=True)
        (src / "harness" / "metrics" / "failures.jsonl").write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        (src / "harness" / "metrics" / "tasks.json").write_text('{"T-1":{"state":"done"}}', encoding="utf-8")
        (src / "harness" / "metrics" / "eval-baseline.json").write_text('{"x":1}', encoding="utf-8")  # phải bị loại
        os.environ["OVERSTACK_SNAPSHOT_DIR"] = str(Path(d) / "snaps")
        tar_path = export(src, quiet=True)
        names = tarfile.open(tar_path).getnames()
        dst2.mkdir()
        a1, _ = restore(dst2, tar_path)
        a2, _ = restore(dst2, tar_path)          # lần 2 phải dedupe hết jsonl
        got = (dst2 / "harness" / "metrics" / "failures.jsonl").read_text(encoding="utf-8")
        ok = ("harness/metrics/failures.jsonl" in names and "manifest.json" in names
              and not any("baseline" in n for n in names)
              and a1 == 3 and a2 == 0 and '{"a":1}' in got and '{"b":2}' in got)
        del os.environ["OVERSTACK_SNAPSHOT_DIR"]
    print("ledger-snapshot self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if "--self-test" in args:
        sys.exit(self_test())
    root = _root(args)
    if args and args[0] == "export":
        keep = int(args[args.index("--keep") + 1]) if "--keep" in args else 7
        export(root, quiet="--quiet" in args, keep=keep); return
    if args and args[0] == "import":
        if len(args) < 2:
            print("usage: ledger-snapshot.py import <snap.tar.gz>", file=sys.stderr); sys.exit(2)
        a, s = restore(root, Path(args[1]))
        print(f"restored: +{a} dòng/file, {s} giữ bản local"); return
    if args and args[0] == "list":
        for p in sorted(_dest(root).glob("snap-*.tar.gz")):
            print(f"  {p.name}  {p.stat().st_size//1024}KB")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
