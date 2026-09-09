#!/usr/bin/env python3
"""br-sync — nối FRAME ↔ GitHub sub-issue (distill automazeio/ccpm, GH#15).

ccpm dùng GitHub Issues làm lớp phối hợp: epic-issue + sub-issue mỗi task, một
`issue-mapping.json` nối task-local ↔ issue#, để team thấy tiến độ và hand-off không
mất context. /br đã có `raise-issue` (mirror 1 chiều) + commit-per-frame; cái THIẾU là
map từng frame thành một sub-issue. Tool này lấp đúng chỗ đó — KHÔNG làm lại provenance
(clause_id/manifest đã sâu hơn ccpm), chỉ thêm lớp đồng bộ GitHub mỏng trên `gh`.

DETERMINISTIC (build + selftest ở đây): đọc frontmatter frame → dựng payload issue
(title/body/label), bỏ qua frame đã map, ghi/đọc `issue-mapping.json`, gom trạng thái.
QUARANTINED (verified:false): lệnh `gh` thật — inject qua `gh_fn` để test offline không
đụng repo thật.

Usage:
  br-sync.py sync   <frames-dir> --root . [--repo owner/repo] [--label br-frame] [--epic] [--dry-run]
  br-sync.py status <frames-dir> --root .                # đọc mapping + trạng thái issue
  br-sync.py selftest
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# reuse the frame frontmatter parser from frame-lint (same dir, hyphen name → load by path)
_fl_path = Path(__file__).with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("_framelint", _fl_path)
_fl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fl)
parse_frontmatter = _fl.parse_frontmatter

MAP_NAME = "issue-mapping.json"


# ── payload builders (pure — the testable core) ─────────────────────────────
def frame_payload(fm, frame_path, label):
    """Build the (title, body, labels) an issue would carry for one frame."""
    fid = fm.get("frame_id") or frame_path.stem
    clauses = fm.get("clause_ids") or []
    muc = (fm.get("muc_tieu") or "").strip()
    kind = fm.get("kind") or "frame"
    title = f"[{fid}] {muc[:70]}" if muc else f"[{fid}]"
    body = (
        f"**Frame:** `{fid}` (kind: {kind})\n"
        f"**Clause:** {', '.join(clauses) if clauses else '—'}\n"
        f"**Mục tiêu:** {muc or '—'}\n\n"
        f"**Scope:** `{', '.join(fm.get('scope_code') or [])}`\n"
        f"**Frame file:** `{frame_path.as_posix()}`\n\n"
        f"---\n_Managed by `/br sync`. Nguồn chân lý là frame + clause; issue này chỉ để "
        f"phối hợp/tiến độ. Commit gắn `{fid}` truy về đây._"
    )
    return title, body, [label, "br"]


def epic_payload(frames_dir, frame_ids, label):
    title = f"[epic] /br pipeline — {frames_dir.parent.name}"
    lines = "\n".join(f"- [ ] `{fid}`" for fid in frame_ids)
    body = (
        f"Epic tổng hợp dây chuyền `/br`. Mỗi frame là một sub-issue.\n\n"
        f"**Frames ({len(frame_ids)}):**\n{lines}\n\n"
        f"---\n_Managed by `/br sync`._"
    )
    return title, body, [label, "br", "epic"]


# ── gh adapter (quarantined) ────────────────────────────────────────────────
def _real_gh(args):
    """Run `gh <args>`; return stdout. Raises on failure."""
    proc = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _issue_number_from_url(url):
    """https://github.com/o/r/issues/1234 → 1234."""
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return int(tail) if tail.isdigit() else None


def _create_issue(gh_fn, repo, title, body, labels, dry_run):
    if dry_run:
        print(f"    [dry-run] would create issue: {title!r} labels={labels}")
        return None, None
    args = ["issue", "create", "--title", title, "--body", body]
    if repo:
        args += ["--repo", repo]
    for lb in labels:
        args += ["--label", lb]
    url = gh_fn(args)
    return _issue_number_from_url(url), url


# ── mapping io ──────────────────────────────────────────────────────────────
def _map_path(frames_dir):
    return Path(frames_dir) / MAP_NAME


def load_mapping(frames_dir):
    p = _map_path(frames_dir)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"repo": None, "epic": None, "frames": {}}


def save_mapping(frames_dir, mapping):
    _map_path(frames_dir).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _frame_files(frames_dir):
    return [f for f in sorted(Path(frames_dir).glob("*.md")) if f.name != "index.md"]


# ── commands ────────────────────────────────────────────────────────────────
def cmd_sync(frames_dir, root, repo, label, epic, dry_run, gh_fn=None):
    gh_fn = gh_fn or _real_gh
    frames_dir = Path(frames_dir)
    mapping = load_mapping(frames_dir)
    if repo:
        mapping["repo"] = repo
    frame_ids, created = [], 0
    for f in _frame_files(frames_dir):
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"  [skip] {f.name}: {e}")
            continue
        fid = fm.get("frame_id") or f.stem
        frame_ids.append(fid)
        if fid in mapping["frames"] and mapping["frames"][fid].get("issue"):
            print(f"  [ok]   {fid} → #{mapping['frames'][fid]['issue']} (đã map)")
            continue
        title, body, labels = frame_payload(fm, f, label)
        num, url = _create_issue(gh_fn, mapping.get("repo"), title, body, labels, dry_run)
        if num:
            mapping["frames"][fid] = {"issue": num, "url": url}
            created += 1
            print(f"  [new]  {fid} → #{num}")
    if epic and not mapping.get("epic") and not dry_run:
        t, b, l = epic_payload(frames_dir, frame_ids, label)
        num, url = _create_issue(gh_fn, mapping.get("repo"), t, b, l, dry_run)
        if num:
            mapping["epic"] = {"issue": num, "url": url}
            print(f"  [epic] #{num}")
    if not dry_run:
        save_mapping(frames_dir, mapping)
        print(f"  synced: {created} issue mới · {len(frame_ids)} frame · map → {_map_path(frames_dir)}")
    else:
        print(f"  dry-run: {len(frame_ids)} frame (không ghi mapping, không gọi gh)")
    return 0


def cmd_status(frames_dir, root, gh_fn=None):
    gh_fn = gh_fn or _real_gh
    mapping = load_mapping(frames_dir)
    if not mapping["frames"]:
        print("  chưa sync frame nào (chạy `br-sync.py sync` trước)")
        return 0
    repo = mapping.get("repo")
    print(f"  repo: {repo or '(default)'} · epic: {mapping.get('epic') or '—'}")
    for fid, info in sorted(mapping["frames"].items()):
        num = info.get("issue")
        try:
            state = gh_fn((["issue", "view", str(num), "--json", "state", "-q", ".state"]
                          + (["--repo", repo] if repo else []))).lower()
        except Exception as e:
            state = f"?({e})"
        print(f"    #{num:<6} {fid:<30} {state}")
    return 0


# ── selftest (offline — fake gh, tmp frames) ────────────────────────────────
def selftest():
    import tempfile
    ok = True

    def fail(m):
        nonlocal ok
        ok = False
        print("  [FAIL]", m)

    FRAME = """---
schema_version: 0
frame_id: {fid}
created_by: slicer
parent_br: BR.md
clause_ids: [C1.1]
parent_br_hash: x
muc_tieu: "Người dùng nhập X rồi hệ thống tính Y và lưu vào sổ cái"
scope_code: ["app/{fid}.py"]
scope_test: ["tests/{fid}.py"]
acceptance_test: "true"
---
# {fid}
## Nghiệp vụ
n
## Input
i
## Tiêu chí nghiệm thu
t
## Ngoài phạm vi
o
"""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "frame-a.md").write_text(FRAME.format(fid="frame-a"), encoding="utf-8")
        (d / "frame-b.md").write_text(FRAME.format(fid="frame-b"), encoding="utf-8")

        # 1. payload shape — title carries frame_id, body carries clause + provenance note
        fm = parse_frontmatter((d / "frame-a.md").read_text())
        title, body, labels = frame_payload(fm, d / "frame-a.md", "br-frame")
        if "frame-a" not in title:
            fail("title thiếu frame_id")
        if "C1.1" not in body or "Managed by" not in body:
            fail("body thiếu clause/provenance note")
        if "br-frame" not in labels:
            fail("label thiếu")

        # 2. fake gh assigns incrementing issue numbers; sync creates 2, mapping persisted
        counter = {"n": 100}
        calls = []

        def fake_gh(args):
            calls.append(args)
            if args[:2] == ["issue", "create"]:
                counter["n"] += 1
                return f"https://github.com/o/r/issues/{counter['n']}"
            return "open"
        cmd_sync(d, ".", repo="o/r", label="br-frame", epic=False, dry_run=False, gh_fn=fake_gh)
        m = load_mapping(d)
        if m["frames"].get("frame-a", {}).get("issue") != 101 or m["frames"].get("frame-b", {}).get("issue") != 102:
            fail(f"mapping sai sau sync: {m['frames']}")
        creates = [c for c in calls if c[:2] == ["issue", "create"]]
        if len(creates) != 2:
            fail(f"phải tạo đúng 2 issue, tạo {len(creates)}")

        # 3. idempotent — re-sync tạo 0 issue mới (bỏ qua frame đã map)
        calls.clear()
        cmd_sync(d, ".", repo="o/r", label="br-frame", epic=False, dry_run=False, gh_fn=fake_gh)
        if any(c[:2] == ["issue", "create"] for c in calls):
            fail("re-sync KHÔNG được tạo issue mới (idempotent)")

        # 4. dry-run tạo 0 issue + không ghi mapping cho frame mới
        (d / "frame-c.md").write_text(FRAME.format(fid="frame-c"), encoding="utf-8")
        calls.clear()
        cmd_sync(d, ".", repo="o/r", label="br-frame", epic=False, dry_run=True, gh_fn=fake_gh)
        if calls:
            fail("dry-run không được gọi gh")
        if "frame-c" in load_mapping(d)["frames"]:
            fail("dry-run không được ghi mapping")

        # 5. url → number parse
        if _issue_number_from_url("https://github.com/o/r/issues/1234/") != 1234:
            fail("parse issue number sai")

    print("br-sync self-test:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-sync.py", description="Nối frame ↔ GitHub sub-issue (ccpm distill).")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="tạo sub-issue cho frame chưa map + ghi issue-mapping.json")
    s.add_argument("frames_dir")
    s.add_argument("--root", default=".")
    s.add_argument("--repo", default=None, help="owner/repo (mặc định: repo hiện tại của gh)")
    s.add_argument("--label", default="br-frame")
    s.add_argument("--epic", action="store_true", help="tạo thêm 1 epic-issue liệt kê frame")
    s.add_argument("--dry-run", action="store_true", help="in việc sẽ làm, KHÔNG gọi gh, KHÔNG ghi mapping")
    s.set_defaults(func=lambda a: cmd_sync(a.frames_dir, a.root, a.repo, a.label, a.epic, a.dry_run))
    st = sub.add_parser("status", help="đọc mapping + trạng thái open/closed mỗi issue")
    st.add_argument("frames_dir")
    st.add_argument("--root", default=".")
    st.set_defaults(func=lambda a: cmd_status(a.frames_dir, a.root))
    t = sub.add_parser("selftest", help="offline test (fake gh)")
    t.set_defaults(func=lambda a: selftest())
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(args.func(args))
