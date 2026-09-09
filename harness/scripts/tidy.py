#!/usr/bin/env python3
"""tidy — dọn kho nháp (wiki/sources/draft/*.md) + render (llmwiki/html/*.html), tất định, 0 token.
Kế thừa fdk/tools/docs-curate.py (đổi tên 2026-09-09 vì tên cũ không ai gọi) và trả 3 nợ đo được:

  D1  draft ở llmwiki là file git TRACKED → dời bằng `git mv` vào archive/ ĐƯỢC TRACK; đích bị
      .gitignore thì KHÔNG dời file tracked (dời = xoá khỏi repo, wikilink gãy trên clone).
  D2  TUỔI không bao giờ là lý do archive một draft còn sống (status proposed/open/…): chỉ
      status/task đã xong mới archive. Draft không status, không task → "promote?" (giữ active).
  D3  tên ngắn: `tidy`.

Ba tầng giữ nguyên triết lý docs-curate: KEEP (canonical/sống) · ARCHIVE (đã xong/bị thay thế →
archive/<nhóm>/, GIỮ không xoá) · PROMOTE? (draft đứng-một-mình có thể chứa quyết định → agent đọc
rồi viết ADR/concept; tool KHÔNG tự promote).

Subcommands:
  check   đếm draft tầng gốc (không tính thư mục con); exit 3 khi > ngưỡng (--threshold, mặc định 10
          hoặc env OVERSTACK_DRAFT_THRESHOLD). --json cho hook. Không đụng file.
  plan    (mặc định) bảng phân loại — không đụng file.
  apply   dời nhóm ARCHIVE (git mv nếu tracked) rồi reindex.
  reindex sắp xếp archive/ theo nhóm + build-docs-index (nếu có) + index_sync --fix + archive/INDEX.md.

Chạy được ở repo framework lẫn downstream (tự dò llmwiki/wiki · .llmwiki/wiki · wiki). Tool phụ
(build-docs-index, index_sync) tìm REPO-LOCAL rồi GLOBAL ~/.claude/harness — thiếu thì bỏ qua, không lỗi.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS_HOME = Path(os.environ.get("OVERSTACK_HARNESS_HOME", Path.home() / ".claude" / "harness"))
SKIP_DRAFT = ("README.md", "_template.md", "index.md", "log.md")
CANONICAL = ("overstack.html", "index.html", "skills-cheatsheet", "health-dashboard", "wiki-graph.html",
             "problem-tree", "line-status.html")
SUPERSEDED = {"280626-framework-master-wiki.html": "overstack.html"}
PLAN_SUFFIX = "-PLAN"
# status frontmatter: `status: done` (YAML) hoặc `**Status:** done` (draft cũ)
STATUS_RE = re.compile(r"^(?:status:|\*\*Status:\*\*)\s*([A-Za-z-]+)", re.M | re.I)
TASK_RE = re.compile(r"^task:\s*(T-\S+)", re.M)
DONE_STATUS = {"done", "implemented", "shipped", "resolved", "rejected", "superseded", "archived", "closed"}
LIVE_STATUS = {"proposed", "open", "implementing", "approved", "dispatched", "draft", "in-progress", "wip"}
TASK_DONE = ("done", "completed", "shipped")
CATEGORIES = [
    ("proposals", "📋 Proposals (đã xong — SPEC + PLAN + seq)"),
    ("superseded", "🔁 Bản bị thay thế"),
    ("analysis", "🔬 Phân tích (cân nhắc promote lên wiki)"),
    ("reports", "📰 Reports / docs một-lần"),
]


# ── layout ─────────────────────────────────────────────────────────────────────────────
def find_root(start: Path) -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True,
                           text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except Exception:
        pass
    return start


class Layout:
    def __init__(self, root: Path):
        self.root = root
        self.wiki = None
        for cand in (root / "llmwiki" / "wiki", root / ".llmwiki" / "wiki", root / "wiki"):
            if cand.is_dir():
                self.wiki = cand
                break
        if self.wiki is None:
            raise SystemExit("tidy: không tìm thấy wiki (llmwiki/wiki · .llmwiki/wiki · wiki) dưới " + str(root))
        self.draft = self.wiki / "sources" / "draft"
        self.html = self.wiki.parent / "html"
        self.draft_arc = self.draft / "archive"
        self.html_arc = self.html / "archive"
        self.tasks = root / "harness" / "metrics" / "tasks.json"


def tool(root: Path, rel: str):
    for base in (root, HARNESS_HOME):
        p = base / rel
        if p.is_file():
            return p
    return None


# ── git helpers ─────────────────────────────────────────────────────────────────────────
def git(root: Path, *args, check=False):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=20, check=check)


def is_git(root: Path) -> bool:
    try:
        return git(root, "rev-parse", "--is-inside-work-tree").returncode == 0
    except Exception:
        return False


def tracked_set(root: Path) -> set:
    try:
        r = git(root, "ls-files", "-z")
        return {p for p in r.stdout.split("\0") if p} if r.returncode == 0 else set()
    except Exception:
        return set()


def ignored(root: Path, path: Path) -> bool:
    try:
        return git(root, "check-ignore", "-q", str(path)).returncode == 0
    except Exception:
        return False


# ── classify ────────────────────────────────────────────────────────────────────────────
def _date_key(name: str):
    m = re.match(r"(\d{2})(\d{2})(\d{2})-", name)
    if not m:
        return None
    dd, mm, yy = m.groups()
    return int(yy) * 10000 + int(mm) * 100 + int(dd)


def _is_plan(name: str) -> bool:
    return name.endswith(f"{PLAN_SUFFIX}.md")


def _spec_stem(stem: str) -> str:
    return stem[: -len(PLAN_SUFFIX)] if stem.endswith(PLAN_SUFFIX) else stem


def _head(p: Path, n=1200) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:n]
    except Exception:
        return ""


def draft_status(p: Path):
    m = STATUS_RE.search(_head(p))
    return m.group(1).lower() if m else None


def draft_task(p: Path):
    m = TASK_RE.search(_head(p))
    return m.group(1) if m else None


def task_states(L: Layout) -> dict:
    try:
        d = json.loads(L.tasks.read_text(encoding="utf-8"))
        return {k: (v.get("state") if isinstance(v, dict) else str(v)) for k, v in d.items()}
    except Exception:
        return {}


def top_drafts(L: Layout):
    if not L.draft.is_dir():
        return []
    return sorted(p for p in L.draft.glob("*.md") if p.name not in SKIP_DRAFT)


def archived_stems(L: Layout) -> set:
    out = set()
    for base in (L.draft_arc, L.html_arc):
        if base.is_dir():
            for p in base.rglob("*"):
                if p.suffix in (".md", ".html"):
                    out.add(_spec_stem(p.stem.replace("-seq", "")))
    return out


def classify(L: Layout, keep_dates=2):
    """name -> (kind, action, reason). action ∈ keep | archive | promote?"""
    out = {}
    tstates = task_states(L)
    drafts = top_drafts(L)
    # 1) SPEC / draft thường — quyết theo task → status → (không gì) promote?
    spec_action = {}
    for p in drafts:
        if _is_plan(p.name):
            continue
        tid = draft_task(p)
        st = tstates.get(tid) if tid else None
        status = draft_status(p)
        if st in TASK_DONE or st in ("rejected", "superseded"):
            act, why = "archive", f"OUTDATED — task {tid} đã {st}"
        elif st:
            act, why = "keep", f"⏱ TREO — task {tid} còn `{st}`; người quyết làm-tiếp hay reject"
        elif status in DONE_STATUS:
            act, why = "archive", f"OUTDATED — status {status}"
        elif status in LIVE_STATUS:
            act, why = "keep", f"⏱ TREO — status {status}, chưa xong (tuổi không phải lý do archive)"
        else:
            act, why = "promote?", "draft đứng-một-mình, không status/task → đọc rồi quyết (ADR/concept hay archive)"
        out[p.name] = ("draft", act, why)
        spec_action[p.stem] = act
    # 2) PLAN đi theo SPEC của nó
    arc_stems = archived_stems(L)
    for p in drafts:
        if not _is_plan(p.name):
            continue
        stem = _spec_stem(p.stem)
        tid = draft_task(p)
        st = tstates.get(tid) if tid else None
        status = draft_status(p)
        if st in TASK_DONE or st in ("rejected", "superseded") or status in DONE_STATUS:
            out[p.name] = ("draft", "archive", f"OUTDATED — PLAN có {'task ' + tid + ' ' + st if st else 'status ' + status}")
        elif spec_action.get(stem) == "archive" or stem in arc_stems:
            out[p.name] = ("draft", "archive", f"PLAN của SPEC {stem} đã archive (ephemeral — không promote)")
        elif stem in spec_action:
            out[p.name] = ("draft", "keep", f"PLAN đi theo SPEC {stem} còn sống")
        else:
            # PLAN không tìm thấy SPEC ≠ đã xong: không có tín hiệu done thì GIỮ (test/tool có thể trỏ thẳng
            # vào PLAN — ge-acceptance-test.sh hardcode path, đo 2026-09-09 khi apply thật).
            out[p.name] = ("draft", "keep", f"⏱ PLAN không thấy SPEC {stem}.md — giữ (chưa có tín hiệu xong)")
    # 3) html
    htmls = sorted(p.name for p in L.html.glob("*.html")) if L.html.is_dir() else []
    referrers = {}   # html name -> [draft stem nhắc tới nó]
    seq_names = [h for h in htmls if h.endswith("-seq.html")]
    if seq_names:
        for p in drafts:
            if _is_plan(p.name):
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for h in seq_names:
                if h in txt:
                    referrers.setdefault(h, []).append(p.stem)
    vmax = {}
    for h in htmls:
        m = re.match(r"(.*)-v(\d+)\.html$", h)
        if m:
            vmax[m.group(1)] = max(vmax.get(m.group(1), 0), int(m.group(2)))
    dated_reports = {}
    for h in htmls:
        if any(c in h for c in CANONICAL):
            out[h] = ("html", "keep", "canonical/active")
            continue
        if h in SUPERSEDED:
            out[h] = ("html", "archive", "bị thay thế bởi " + SUPERSEDED[h])
            continue
        mv = re.match(r"(.*)-v(\d+)\.html$", h)
        if mv and int(mv.group(2)) < vmax.get(mv.group(1), 0):
            out[h] = ("html", "archive", f"bản cũ (có -v{vmax[mv.group(1)]})")
            continue
        ms = re.match(r"(.*)-seq\.html$", h)
        if ms:
            # cặp seq↔SPEC theo THAM CHIẾU (draft nào nhắc tên file), không theo stem: stem thường lệch
            # (`x-seq.html` ↔ `x-fe.md`) — đo ở bonbon-ai 2026-09-09: 6/7 seq của draft sống bị coi mồ côi.
            stem = ms.group(1)
            owners = referrers.get(h) or [d for d in spec_action if d == stem]
            if owners:
                if all(spec_action.get(o) == "archive" for o in owners):
                    out[h] = ("html", "archive", f"seq của SPEC {owners[0]} đã archive")
                else:
                    out[h] = ("html", "keep", f"seq đi theo SPEC {owners[0]} còn sống")
            elif stem in arc_stems:
                out[h] = ("html", "archive", f"seq của SPEC {stem} đã archive")
            else:
                out[h] = ("html", "archive", "seq mồ côi (không draft nào nhắc tới)")
            continue
        dk = _date_key(h)
        if dk:
            dated_reports[h] = dk
        else:
            out[h] = ("html", "keep", "report không ngày — giữ active")
    # html report có ngày: render ephemeral → giữ N mốc ngày gần nhất, cũ hơn archive (KHÔNG áp cho .md)
    if dated_reports:
        recent = sorted(set(dated_reports.values()), reverse=True)[: max(1, keep_dates)]
        for h, dk in dated_reports.items():
            out[h] = ("html", "keep", "report gần đây — giữ active") if dk in recent \
                else ("html", "archive", f"report cũ (ngoài {keep_dates} mốc ngày gần nhất)")
    return out


def _category(name: str, kind: str, seq_stems: set) -> str:
    if kind == "html":
        if name.endswith("-seq.html"):
            return "proposals"
        if re.search(r"-v\d+\.html$", name) or "master-wiki" in name:
            return "superseded"
        return "reports"
    stem = _spec_stem(name[:-3])
    if _is_plan(name):
        return "proposals"
    return "proposals" if stem in seq_stems else "analysis"


def _seq_stems(L: Layout) -> set:
    stems = set()
    for base in (L.html, L.html_arc):
        if base.is_dir():
            for p in base.rglob("*-seq.html"):
                stems.add(p.name[: -len("-seq.html")])
    return stems


# ── commands ────────────────────────────────────────────────────────────────────────────
def summary(L: Layout, out: dict) -> dict:
    n = len(top_drafts(L))
    return {
        "draft_top": n,
        "outdated": sum(1 for k, (t, a, _) in out.items() if t == "draft" and a == "archive"),
        "promote": sum(1 for k, (t, a, _) in out.items() if t == "draft" and a == "promote?"),
        "html_archive": sum(1 for k, (t, a, _) in out.items() if t == "html" and a == "archive"),
        "draft_dir": str(L.draft),
    }


def cmd_check(L: Layout, threshold: int, as_json: bool) -> int:
    out = classify(L)
    s = summary(L, out)
    s["threshold"] = threshold
    s["over"] = s["draft_top"] > threshold
    if as_json:
        print(json.dumps(s, ensure_ascii=False))
    else:
        flag = "VƯỢT" if s["over"] else "ok"
        print(f"tidy check — draft tầng gốc {s['draft_top']} file (ngưỡng {threshold}: {flag}) · "
              f"outdated {s['outdated']} · promote? {s['promote']} · html archivable {s['html_archive']}")
        if s["over"]:
            print("  → chạy /tidy (plan → promote bản chất → apply) hoặc `tidy.py plan` để xem bảng.")
    return 3 if s["over"] else 0


def cmd_plan(L: Layout, keep_dates=2):
    out = classify(L, keep_dates)
    label = {"keep": "✅ GIỮ", "archive": "📦 ARCHIVE (dời vào archive/)",
             "promote?": "⬆️  PROMOTE? (agent đọc rồi quyết — tool không tự làm)"}
    s = summary(L, out)
    print(f"tidy · plan — {len(out)} mục (draft {s['draft_top']} · html "
          f"{sum(1 for t, *_ in out.values() if t == 'html')}) · wiki: {L.wiki}\n")
    for act in ("keep", "archive", "promote?"):
        rows = sorted((n, r) for n, (_t, a, r) in out.items() if a == act)
        if not rows:
            continue
        print(f"{label[act]}  ({len(rows)})")
        for n, r in rows:
            print(f"    {n:<48} {r}")
        print()
    print(f"→ keep {sum(1 for v in out.values() if v[1] == 'keep')} · archive "
          f"{sum(1 for v in out.values() if v[1] == 'archive')} · promote? {s['promote']}.  "
          f"Chạy: tidy.py apply  (PROMOTE trước khi apply — archive = local có thể mất bản chất quý)")
    return out


def _move(L: Layout, src: Path, dst: Path, trk: set, use_git: bool) -> str:
    """Trả 'git' | 'fs' | 'skip'. File tracked mà đích bị gitignore → skip (D1)."""
    rel = src.relative_to(L.root).as_posix()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if use_git and rel in trk:
        if ignored(L.root, dst):
            return "skip"
        r = git(L.root, "mv", "-k", str(src), str(dst))
        if r.returncode == 0 and dst.is_file():
            return "git"
    shutil.move(str(src), str(dst))
    return "fs"


def cmd_apply(L: Layout, keep_dates=2):
    out = classify(L, keep_dates)
    use_git = is_git(L.root)
    trk = tracked_set(L.root) if use_git else set()
    seq = _seq_stems(L)
    moved, skipped, moved_rows = 0, [], {}
    for n, (kind, action, _r) in sorted(out.items()):
        if action != "archive":
            continue
        base, arc = (L.html, L.html_arc) if kind == "html" else (L.draft, L.draft_arc)
        src = base / n
        if not src.is_file():
            continue
        dst = arc / _category(n, kind, seq) / n
        how = _move(L, src, dst, trk, use_git)
        if how == "skip":
            skipped.append(n)
            continue
        moved += 1
        if kind == "draft":
            moved_rows[n] = dst
        print(f"  📦 {kind}/{n} → {dst.relative_to(L.wiki.parent)}  [{how}]")
    _rewrite_index(L, moved_rows)
    if skipped:
        ig = L.draft_arc.relative_to(L.root)
        print(f"  ⚠ {len(skipped)} file TRACKED không dời vì đích bị .gitignore (dời = xoá khỏi repo): "
              f"{', '.join(skipped[:5])}{'…' if len(skipped) > 5 else ''}\n"
              f"    → bỏ dòng ignore cho `{ig}/` trong .gitignore rồi chạy lại (archive phải travel theo clone).")
    print(f"tidy · apply — archive {moved} mục. Re-index…")
    cmd_reindex(L)
    return moved


def _rewrite_index(L: Layout, moved: dict) -> int:
    """index.md có row trỏ `sources/draft/<name>` (người viết tay, R3) → trỏ sang chỗ mới trong archive/
    để link không gãy; index_sync coi row trỏ archive/ còn file là hợp lệ."""
    idx = L.wiki / "index.md"
    if not moved or not idx.is_file():
        return 0
    text = idx.read_text(encoding="utf-8")
    n = 0
    for name, dst in moved.items():
        old = f"sources/draft/{name}"
        new = dst.relative_to(L.wiki).as_posix()
        if old in text:
            text = text.replace(old, new)
            n += 1
    if n:
        idx.write_text(text, encoding="utf-8")
        print(f"  ✎ index.md: {n} row trỏ sang archive/")
    return n


def _organize_existing(L: Layout, trk: set, use_git: bool) -> int:
    seq = _seq_stems(L)
    n = 0
    for base, kind in ((L.html_arc, "html"), (L.draft_arc, "draft")):
        if not base.is_dir():
            continue
        for p in list(base.iterdir()):
            if p.is_file() and p.suffix in (".html", ".md") and p.name != "INDEX.md":
                dst = base / _category(p.name, kind, seq) / p.name
                if _move(L, p, dst, trk, use_git) != "skip":
                    n += 1
    return n


def _build_archive_index(L: Layout) -> int:
    lines = ["# Archive index — tài liệu đã archive, theo chức năng", "",
             "> Sinh bởi `harness/scripts/tidy.py`. Archive = GIỮ (không xoá); đây là chỉ mục để tìm lại.", ""]
    total = 0
    for cat, label in CATEGORIES:
        items = []
        if (L.html_arc / cat).is_dir():
            items += [(p.name, f"{cat}/{p.name}") for p in sorted((L.html_arc / cat).glob("*.html"))]
        if (L.draft_arc / cat).is_dir():
            rel = os.path.relpath(L.draft_arc, L.html_arc).replace(os.sep, "/")
            items += [(p.name, f"{rel}/{cat}/{p.name}") for p in sorted((L.draft_arc / cat).glob("*.md"))]
        if not items:
            continue
        lines += [f"## {label} ({len(items)})", ""] + [f"- [{nm}]({r})" for nm, r in items] + [""]
        total += len(items)
    lines += ["---", f"Tổng **{total}** file đã archive."]
    L.html_arc.mkdir(parents=True, exist_ok=True)
    (L.html_arc / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return total


def cmd_reindex(L: Layout):
    use_git = is_git(L.root)
    trk = tracked_set(L.root) if use_git else set()
    n = _organize_existing(L, trk, use_git)
    if n:
        print(f"  🗂  sắp xếp {n} file đã-archive vào nhóm chức năng")
    bdi = L.root / "fdk" / "tools" / "build-docs-index.py"   # chỉ repo framework (ROOT tính từ vị trí file)
    if bdi.is_file():
        r = subprocess.run([sys.executable, str(bdi)], capture_output=True, text=True, cwd=L.root)
        tail = (r.stdout or r.stderr).strip().splitlines()
        if tail:
            print("  " + tail[-1])
    isx = tool(L.root, "harness/validators/index_sync.py")
    if isx:
        subprocess.run([sys.executable, str(isx), "--wiki-dir", str(L.wiki), "--fix"],
                       capture_output=True, text=True, cwd=L.root)
    total = _build_archive_index(L)
    print(f"  ✓ reindex: build-docs-index {'✓' if bdi.is_file() else '(không có — bỏ qua)'} · "
          f"index_sync {'✓' if isx else '(không có — bỏ qua)'} · archive/INDEX.md ({total} file)")


def main():
    ap = argparse.ArgumentParser(description="tidy — dọn kho nháp/render, tất định")
    ap.add_argument("cmd", nargs="?", default="plan", choices=["check", "plan", "apply", "reindex"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--threshold", type=int, default=int(os.environ.get("OVERSTACK_DRAFT_THRESHOLD", "10") or 10))
    ap.add_argument("--keep-dates", type=int, default=2, help="html report có ngày: giữ N mốc gần nhất")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    L = Layout(find_root(Path(a.root).resolve()))
    if a.cmd == "check":
        sys.exit(cmd_check(L, a.threshold, a.json))
    if a.cmd == "apply":
        cmd_apply(L, a.keep_dates)
    elif a.cmd == "reindex":
        cmd_reindex(L)
    else:
        cmd_plan(L, a.keep_dates)


if __name__ == "__main__":
    main()
