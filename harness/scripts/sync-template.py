#!/usr/bin/env python3
"""One-shot, non-interactive downstream /sync-template (mục tiêu < 1 phút).

Gộp toàn bộ quy trình sync vào 1 lần chạy:
  fetch remote version.json + manifest (song song) → phân loại từng file bằng
  hash 3 mốc (disk ↔ baseline ↔ remote) → tải file cần thiết SONG SONG →
  refresh fingerprint → cài skill ra 3 chỗ → in report.

Phân loại (giống health-check 3 mốc):
  NEW    : thiếu trên disk, có ở remote                → luôn PULL
  SAME   : disk == remote                              → bỏ qua
  CLEAN  : disk == baseline, remote != baseline        → PULL (remote-only update, không mất gì)
  LOCAL  : disk != baseline, remote == baseline        → GIỮ local (bạn đã custom)
  CONFLICT: disk != baseline VÀ remote != baseline     → theo --strategy

--strategy (chỉ ảnh hưởng CONFLICT):
  keep   (default) : giữ local, KHÔNG hỏi. Liệt kê + lưu bản remote vào /tmp để diff.
  pull             : ghi đè bằng remote, backup local -> <file>.local-bak
  backup           : = pull (alias)

Mặc định KHÔNG hỏi gì. Exit 0 = xong. Exit 3 = có CONFLICT cần bạn quyết
(chạy lại với --strategy pull nếu muốn lấy remote).

Usage:
  sync-template.py [--root .] [--branch orca] [--strategy keep|pull]
                   [--dry-run] [--no-install] [--json] [--timeout 6]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SELF = "harness/version.json"
VOLATILE = {
    "llmwiki/wiki/index.md",
    "llmwiki/wiki/log.md",
    "llmwiki/wiki/active-context.md",
    "llmwiki/wiki/decisions.md",
}
SKILL_SKIP = {"README.md", "index.md", "log.md"}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def owner_repo(remote: str):
    m = re.search(r"github\.com[:/]+([^/]+)/([^/.]+)", remote or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def fetch(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "llmwiki-sync"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def git_commit(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def frontmatter(text: str):
    """return (name, description) from YAML frontmatter, else (None, None)."""
    if not text.startswith("---"):
        return None, None
    end = text.find("\n---", 3)
    if end < 0:
        return None, None
    head = text[3:end]
    name = desc = None
    for line in head.splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip()
    return name, desc


# ---- Đường dẫn ĐỘC QUYỀN của overstack đã dời (cũ → mới). Idempotent: chỉ dời khi
#      cũ có + mới chưa có; mới đã có thì bỏ qua (người dùng tự dời rồi). Thêm dòng
#      mỗi lần framework đổi vị trí — downstream sync là tự theo, không cần dặn.
#      Vị trí do tool NGOÀI quy định (.claude/ .github/ .agent) KHÔNG nằm đây.
PATH_MIGRATIONS = [
    ("doyourmagic",          ".overstack/doyourmagic"),   # 2026-09-08 gom artifact về 1 gốc
    (".doyourmagic",         ".overstack/doyourmagic"),
    (".orca-onboard",        ".overstack/onboard"),
    (".understand-anything", ".overstack/graph"),
    (".overstack-kit",       ".overstack/kit"),
]

def migrate_paths(root: Path, dry_run: bool = False):
    """Dời thư mục/file theo PATH_MIGRATIONS. Trả list "cũ → mới" đã dời.
    Dùng `git mv` khi có git để giữ lịch sử; không git → shutil.move."""
    import shutil
    moved = []
    for old, new in PATH_MIGRATIONS:
        src, dst = root / old, root / new
        if not src.exists() or dst.exists():
            continue
        moved.append(f"{old} → {new}")
        if dry_run:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "-C", str(root), "mv", old, new], capture_output=True)
        if r.returncode != 0:
            shutil.move(str(src), str(dst))
    return moved

def _selftest_migrate():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d); (r / ".orca-onboard").mkdir(); (r / ".orca-onboard" / "x").write_text("1")
        assert migrate_paths(r) == [".orca-onboard → .overstack/onboard"]
        assert (r / ".overstack/onboard/x").read_text() == "1" and not (r / ".orca-onboard").exists()
        assert migrate_paths(r) == []                        # idempotent
        (r / ".doyourmagic").mkdir(); (r / ".overstack/doyourmagic").mkdir()
        assert migrate_paths(r) == []                        # đích đã có → không đè
    print("selftest migrate_paths OK")


def okf_migrate(root: Path):
    """Backfill OKF v0.1 in-process: import okf-check.py như module, migrate wiki.
    Fallback subprocess 1 lần nếu import lỗi. Trả (migrated_list, err_or_None).
    Idempotent — file đã có YAML frontmatter được bỏ qua (do migrate_text quyết)."""
    import importlib.util
    okf_path = Path(__file__).resolve().parent / "okf-check.py"
    wiki = root / "llmwiki" / "wiki"
    if not wiki.is_dir():
        return [], None
    try:
        spec = importlib.util.spec_from_file_location("okf_check", okf_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        migrated = []
        for p in mod.content_files(wiki):
            new, changed = mod.migrate_text(p.read_text(encoding="utf-8"), p, wiki)
            if changed:
                p.write_text(new, encoding="utf-8")
                migrated.append(str(p.relative_to(wiki)))
        return migrated, None
    except Exception:
        # fallback: 1 subprocess (vẫn backfill được, không mất khả năng)
        try:
            subprocess.run([sys.executable, str(okf_path), "--migrate", "--root", str(root)],
                           capture_output=True, timeout=30)
            return [], None
        except Exception as e:
            return [], f"{type(e).__name__}: {e}"


def verify_installs(root: Path, home: Path, installed):
    """Kiểm 3 vị trí cài cho mỗi skill. Trả list (name, ok_bool)."""
    out = []
    for name in installed:
        ok = ((root / ".claude/commands" / f"{name}.md").is_file()
              and (home / ".claude/skills" / name / "SKILL.md").is_file()
              and (home / ".claude/commands" / f"{name}.md").is_file())
        out.append((name, ok))
    return out


def append_sync_log(root: Path, line: str):
    logf = root / "llmwiki/wiki/log.md"
    if logf.is_file():
        with logf.open("a", encoding="utf-8") as fh:
            fh.write(line if line.endswith("\n") else line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--branch", default=None, help="override branch (default: từ version.json)")
    ap.add_argument("--strategy", choices=["keep", "pull", "backup"], default="keep")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--full", action="store_true",
                    help="gộp mọi bước hậu-sync vào 1 process: OKF backfill + self-verify + ghi log "
                         "(fingerprint refresh chạy SAU OKF). Không cờ = hành vi cũ y nguyên.")
    ap.add_argument("--timeout", type=int, default=6)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.strategy == "backup":
        args.strategy = "pull"

    root = Path(args.root).resolve()
    manifest_f = root / ".template-manifest.json"
    vfile = root / SELF
    manifest = json.loads(manifest_f.read_text(encoding="utf-8"))
    vj = json.loads(vfile.read_text(encoding="utf-8")) if vfile.is_file() else {}
    remote_url = manifest.get("remote", "")
    branch = args.branch or vj.get("branch", "orca")
    # baseline R0 = hash của REMOTE tại lần sync trước (KHÔNG phải disk).
    # Phân biệt "remote có bản mới" (pull) với "mình đã custom local" (keep) —
    # disk-baseline của health-check không phân biệt được hai ca này.
    base = vj.get("remote_synced") or vj.get("patterns", {})
    owner, repo = owner_repo(remote_url)
    if not owner:
        print(f"[sync] remote URL không parse được: {remote_url}", file=sys.stderr)
        return 2
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"

    # 1) fetch remote version.json + manifest song song
    try:
        with cf.ThreadPoolExecutor(max_workers=2) as ex:
            fv = ex.submit(fetch, f"{raw}/{SELF}", args.timeout)
            fm = ex.submit(fetch, f"{raw}/.template-manifest.json", args.timeout)
            rvj = json.loads(fv.result().decode("utf-8"))
            rmanifest_bytes = fm.result()
            rmanifest = json.loads(rmanifest_bytes.decode("utf-8"))
    except Exception as e:
        print(f"[sync] không lấy được remote ({branch}): {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    remote_pat = rvj.get("patterns", {})
    remote_ver = rvj.get("template_version", "1.0.0")
    # danh sách file = includes remote (canonical) ∪ local, trừ SELF/VOLATILE
    includes = [p for p in dict.fromkeys(rmanifest.get("includes", []) + manifest.get("includes", []))
                if p != SELF and p not in VOLATILE]

    NEW, CLEAN, LOCAL, CONFLICT, SAME = [], [], [], [], []
    for rel in includes:
        rh = remote_pat.get(rel)
        if rel == ".template-manifest.json":
            rh = sha_bytes(rmanifest_bytes)  # manifest hash từ nội dung vừa tải
        f = root / rel
        dh = sha_file(f) if f.is_file() else None
        bh = base.get(rel)
        if rh is None:
            continue  # remote không track & không phải manifest → bỏ
        if dh is None:
            NEW.append(rel)
        elif dh == rh:
            SAME.append(rel)
        elif dh == bh and rh != bh:
            CLEAN.append(rel)
        elif dh != bh and rh == bh:
            LOCAL.append(rel)
        else:
            CONFLICT.append(rel)

    to_pull = list(NEW) + list(CLEAN)
    if args.strategy == "pull":
        to_pull += CONFLICT

    # 2) tải song song
    downloaded, failed = [], []
    if not args.dry_run and to_pull:
        def grab(rel):
            try:
                data = fetch(f"{raw}/{rel}", args.timeout)
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                if rel in CONFLICT and args.strategy == "pull" and dst.is_file():
                    dst.with_suffix(dst.suffix + ".local-bak").write_bytes(dst.read_bytes())
                dst.write_bytes(data)
                return rel, None
            except Exception as e:
                return rel, f"{type(e).__name__}: {e}"
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            for rel, err in ex.map(grab, to_pull):
                (failed if err else downloaded).append(rel if not err else (rel, err))

    # CONFLICT giữ local: lưu bản remote ra /tmp để tiện diff
    conflict_remote_dir = None
    if CONFLICT and args.strategy == "keep" and not args.dry_run:
        conflict_remote_dir = Path("/tmp/sync-template-conflicts")
        conflict_remote_dir.mkdir(parents=True, exist_ok=True)
        def grabc(rel):
            try:
                data = fetch(f"{raw}/{rel}", args.timeout)
                (conflict_remote_dir / rel.replace("/", "_")).write_bytes(data)
            except Exception:
                pass
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            list(ex.map(grabc, CONFLICT))

    # 2a) dời đường dẫn độc quyền đã đổi — luôn chạy, trước mọi bước hậu-sync
    moved = migrate_paths(root, dry_run=args.dry_run)
    for m in moved:
        print(f"[sync] MOVED {m}")

    # 2b) [--full] OKF backfill TRƯỚC fingerprint — migrate có thể đổi file wiki,
    #     fingerprint phải chụp trạng thái SAU migrate để health-check không báo DRIFT giả.
    okf_migrated, okf_err = [], None
    if args.full and not args.dry_run:
        okf_migrated, okf_err = okf_migrate(root)

    # 3) refresh fingerprint (giữ branch, set template_version = remote)
    if not args.dry_run:
        cur = {}
        for rel in [p for p in rmanifest.get("includes", []) if p != SELF and p not in VOLATILE]:
            f = root / rel
            if f.is_file():
                cur[rel] = sha_file(f)
        newvj = {
            "schema": 1,
            "template_version": remote_ver,
            "remote": remote_url,
            "branch": branch,
            "generated_at": vj.get("generated_at", ""),
            "generated_commit": git_commit(root),
            "pattern_count": len(cur),
            "patterns": dict(sorted(cur.items())),
            # snapshot remote tại lần sync này → baseline R0 cho lần sync sau
            "remote_synced": dict(sorted(remote_pat.items())),
        }
        vfile.write_text(json.dumps(newvj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 4) cài skill ra 3 chỗ (chỉ file vừa pull, dưới llmwiki/skills/, có name: frontmatter)
    installed = []
    if not args.no_install and not args.dry_run:
        home = Path.home()
        changed_skills = [r for r in (downloaded if downloaded else to_pull)
                          if r.startswith("llmwiki/skills/") and Path(r).name not in SKILL_SKIP]
        for rel in changed_skills:
            src = root / rel
            if not src.is_file():
                continue
            text = src.read_text(encoding="utf-8", errors="replace")
            name, _ = frontmatter(text)
            if not name:
                continue
            for dst in [root / ".claude/commands" / f"{name}.md",
                        home / ".claude/skills" / name / "SKILL.md",
                        home / ".claude/commands" / f"{name}.md"]:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            installed.append(name)

    # 5) [--full] self-verify 3 vị trí cài + append wiki/log.md (thay Step 8 + Rule log của agent)
    verified, verify_bad = [], []
    if args.full and not args.dry_run:
        verified = verify_installs(root, Path.home(), installed)
        verify_bad = [n for n, ok in verified if not ok]
        pulled_n = len(downloaded) if downloaded else 0
        append_sync_log(root, (
            f"- {vj.get('generated_at', '')} sync-template --full ← {owner}/{repo}@{branch} "
            f"(v{remote_ver}): +{pulled_n} pulled, OKF {len(okf_migrated)} migrated, "
            f"installed {len(installed)} skill, conflict {len(CONFLICT)}"
        ))

    report = {
        "branch": branch, "remote_version": remote_ver,
        "strategy": args.strategy, "dry_run": args.dry_run, "full": args.full,
        "same": len(SAME), "new": NEW, "clean": CLEAN,
        "kept_local": LOCAL, "conflicts": CONFLICT,
        "pulled": downloaded if not args.dry_run else to_pull,
        "failed": failed, "installed": installed,
        "okf_migrated": okf_migrated, "okf_error": okf_err,
        "verify_bad": verify_bad,
        "conflict_remote_dir": str(conflict_remote_dir) if conflict_remote_dir else None,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        tag = "DRY-RUN" if args.dry_run else "SYNCED"
        print(f"[sync] {tag} ← {owner}/{repo}@{branch} (template v{remote_ver}) · strategy={args.strategy}")
        print(f"  same={len(SAME)}  new={len(NEW)}  clean-update={len(CLEAN)}  kept-local={len(LOCAL)}  conflict={len(CONFLICT)}")
        if NEW:    print(f"  + NEW    : {', '.join(NEW)}")
        if CLEAN:  print(f"  ↻ UPDATE : {', '.join(CLEAN)}")
        if LOCAL:  print(f"  = KEPT   : {len(LOCAL)} file bạn đã custom (remote không mới hơn)")
        if CONFLICT:
            verb = "PULLED (backup .local-bak)" if args.strategy == "pull" else "KEPT local"
            print(f"  ⚠ CONFLICT {verb}: {', '.join(CONFLICT)}")
            if args.strategy == "keep":
                print(f"    → bản remote đã lưu ở {conflict_remote_dir} để diff; chạy lại --strategy pull nếu muốn lấy remote.")
        if installed: print(f"  ⚙ installed skills (×3): {', '.join(installed)}")
        if args.full:
            print(f"  ✎ OKF migrated: {len(okf_migrated)}" + (f" — {', '.join(okf_migrated)}" if okf_migrated else ""))
            if okf_err:     print(f"  ✗ OKF error: {okf_err}")
            if verify_bad:  print(f"  ✗ install verify FAILED: {', '.join(verify_bad)}")
            elif installed: print(f"  ✓ install verify OK (×3): {', '.join(installed)}")
        if failed:    print(f"  ✗ FAILED : {failed}")
    # CONFLICT (keep) → 3; lỗi tải / OKF / verify → 1; sạch → 0
    if CONFLICT and args.strategy == "keep":
        return 3
    return 1 if (failed or okf_err or verify_bad) else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest_migrate(); sys.exit(0)
    sys.exit(main())
