#!/usr/bin/env python3
"""docs-curate — sắp xếp gọn kho tài liệu LOCAL (llmwiki/html/*.html + sources/draft/*.md) đang
phình to, BẰNG CODE (tất định). Triết lý 3 tầng (không chỉ "merge"):

  KEEP     canonical/active — overstack.html, index.html, cheatsheet, health-dashboard, docs mới.
  ARCHIVE  render ephemeral — cặp proposal đã xong (draft+seq), bản bị thay thế (vN cũ,
           master-wiki←overstack), report cũ → dời vào archive/ (GIỮ, không xoá).
  PROMOTE  bản chất quý → wiki — draft đứng-một-mình (không có seq) thường chứa phân tích/quyết
           định nên LÊN wiki ADR/concept (travel + sống sót clone). Tool chỉ ĐỀ XUẤT; agent (skill
           /docs-curate) đọc nội dung rồi promote bằng phán đoán — KHÔNG auto-promote.

Vì sao bằng code: phân loại + dời + re-index là tất định; phần cần đọc-hiểu (promote cái gì,
merge ra sao) để cho agent. Đây là backbone; skill là tay lái.

Subcommands:
  plan                 (mặc định) in BẢNG phân loại + kế hoạch + gợi ý promote — KHÔNG đụng file.
  apply [--keep-dates N]  dời nhóm ARCHIVE vào archive/, rồi reindex. N = số mốc-ngày gần nhất giữ active (mặc 2).
  reindex              chỉ chạy lại build-docs-index + index_sync --fix + ghi log.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "llmwiki" / "html"
DRAFT = ROOT / "llmwiki" / "wiki" / "sources" / "draft"
HTML_ARC = HTML / "archive"
DRAFT_ARC = DRAFT / "archive"

# canonical/active — không bao giờ archive (khớp theo substring)
CANONICAL = ("overstack.html", "index.html", "skills-cheatsheet", "health-dashboard")
# bản bị thay thế tường minh (file → bản thay thế nó)
SUPERSEDED = {"280626-framework-master-wiki.html": "overstack.html"}
SKIP_DRAFT = ("README.md", "_template.md")
TASKS = ROOT / "harness" / "metrics" / "tasks.json"
_TASK_DONE = ("done", "completed", "shipped")


def _task_states() -> dict:
    """JOIN với code-logger: T-id → state. Fail-open (không có store → {})."""
    try:
        d = json.loads(TASKS.read_text(encoding="utf-8"))
        return {k: (v.get("state") if isinstance(v, dict) else str(v)) for k, v in d.items()}
    except Exception:
        return {}


def _draft_task(name: str):
    """Đọc `task: T-...` trong frontmatter draft — tín hiệu vòng đời tất định."""
    try:
        head = (DRAFT / name).read_text(encoding="utf-8", errors="ignore")[:800]
        m = re.search(r"^task:\s*(T-\S+)", head, re.M)
        return m.group(1) if m else None
    except Exception:
        return None


def _date_key(name: str):
    """DDMMYY ở đầu tên → khoá sắp xếp yymmdd (mới = lớn); None nếu không có."""
    m = re.match(r"(\d{2})(\d{2})(\d{2})-", name)
    if not m:
        return None
    dd, mm, yy = m.groups()
    return int(yy) * 10000 + int(mm) * 100 + int(dd)


def _is_canonical(name: str) -> bool:
    return any(c in name for c in CANONICAL)


PLAN_SUFFIX = "-PLAN"


def _is_plan(name: str) -> bool:
    """`DDMMYY-<tên>-PLAN.md` — kế hoạch thi hành do /plan sinh (đi kèm SPEC cùng stem)."""
    return name.endswith(f"{PLAN_SUFFIX}.md")


def _spec_stem(stem: str) -> str:
    """stem của PLAN → stem của SPEC. `140726-x-PLAN` → `140726-x`. Không phải PLAN thì giữ nguyên."""
    return stem[: -len(PLAN_SUFFIX)] if stem.endswith(PLAN_SUFFIX) else stem


def classify():
    htmls = sorted(p.name for p in HTML.glob("*.html"))
    drafts = sorted(p.name for p in DRAFT.glob("*.md") if p.name not in SKIP_DRAFT)
    draft_stems = {d[:-3] for d in drafts}

    # vN superseded: gom theo base, archive mọi vN < max
    vmax = {}
    for h in htmls:
        m = re.match(r"(.*)-v(\d+)\.html$", h)
        if m:
            base, v = m.group(1), int(m.group(2))
            vmax[base] = max(vmax.get(base, 0), v)

    out = {}  # name -> (kind, action, reason)
    for h in htmls:
        if _is_canonical(h):
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
            base = ms.group(1)
            if base in draft_stems:
                out[h] = ("html", "archive", f"cặp proposal với {base}.md (đã xong)")
            else:
                out[h] = ("html", "archive", "seq orphan (không còn draft)")
            continue
        out[h] = ("html", "report", "report/doc một-lần")

    tstates = _task_states()
    for d in drafts:
        # bộ ba một feature: SPEC `<stem>.md` + PLAN `<stem>-PLAN.md` + `<stem>-seq.html`.
        # PLAN là văn bản THI HÀNH (ephemeral) — nó archive theo SPEC, KHÔNG bao giờ promote lên wiki.
        stem = _spec_stem(d[:-3])
        if (HTML / f"{stem}-seq.html").is_file():
            reason = "PLAN của cặp proposal (archive theo SPEC)" if _is_plan(d) else "cặp proposal (đã xong; promote bản chất trước)"
            out[d] = ("draft", "archive", reason)
        elif _is_plan(d):
            out[d] = ("draft", "archive", "PLAN thi hành (ephemeral — không promote)")
        else:
            out[d] = ("draft", "promote?", "draft đứng-một-mình → cân nhắc LÊN wiki ADR/concept")
        # JOIN vòng đời (2026-07-18, feedback "lint chẳng biết propose nào outdated"): draft khai
        # `task: T-id`, code-logger biết state thật — nối hai đầu là outdated/treo thành TẤT ĐỊNH,
        # không cần ai nhớ flip status tay.
        tid = _draft_task(d)
        st = tstates.get(tid) if tid else None
        if st in _TASK_DONE:
            out[d] = ("draft", "archive", f"OUTDATED — task {tid} đã {st}; promote bản chất (nếu có) rồi archive")
        elif st == "rejected":
            out[d] = ("draft", "archive", f"OUTDATED — task {tid} bị rejected (proposal chết)")
        elif st == "superseded":
            out[d] = ("draft", "archive", f"SUPERSEDED — task {tid} scope còn lại đã chuyển sang issue riêng, xem note trong tasks.json")
        elif st:  # proposed/approved/dispatched — vòng còn sống, tuổi không được archive nó
            out[d] = ("draft", "keep", f"⏱ TREO — task {tid} còn `{st}`: cần người quyết làm-tiếp hay reject, KHÔNG archive theo tuổi")
    return out


def _resolve_reports(out, keep_dates):
    """report/promote? có ngày: giữ active nếu thuộc N mốc-ngày gần nhất; cũ hơn → archive."""
    dated = {n: _date_key(n) for n, (_k, a, _r) in out.items() if a in ("report", "promote?") and _date_key(n)}
    if not dated:
        return
    recent = sorted(set(dated.values()), reverse=True)[:max(1, keep_dates)]
    for n, dk in dated.items():
        kind, action, reason = out[n]
        if dk in recent:
            out[n] = (kind, "keep" if action == "report" else "promote?", reason + " (gần đây — giữ active)")
        else:
            out[n] = (kind, "archive", reason + " (cũ → archive)")
    for n, (kind, action, reason) in list(out.items()):   # report không-ngày → giữ active
        if action == "report":
            out[n] = (kind, "keep", reason)


def cmd_plan(keep_dates=2):
    out = classify()
    _resolve_reports(out, keep_dates)
    order = ["keep", "archive", "promote?", "report"]
    label = {"keep": "✅ GIỮ (canonical/active)", "archive": "📦 ARCHIVE (dời vào archive/)",
             "promote?": "⬆️  PROMOTE? (cân nhắc lên wiki — agent đọc rồi quyết)",
             "report": "• report"}
    print(f"docs-curate · plan — {len([1 for v in out.values()])} mục "
          f"(html {sum(1 for k,(t,*_ ) in out.items() if t=='html')} · draft {sum(1 for k,(t,*_ ) in out.items() if t=='draft')})\n")
    for act in order:
        rows = sorted((n, r) for n, (_t, a, r) in out.items() if a == act)
        if not rows:
            continue
        print(f"{label.get(act, act)}  ({len(rows)})")
        for n, r in rows:
            print(f"    {n:<46} {r}")
        print()
    nkeep = sum(1 for v in out.values() if v[1] == "keep")
    narc = sum(1 for v in out.values() if v[1] == "archive")
    nprom = sum(1 for v in out.values() if v[1] == "promote?")
    print(f"→ keep {nkeep} · archive {narc} · promote-suggest {nprom}.  Chạy: docs-curate.py apply")
    print("  PROMOTE là phán đoán của agent (đọc draft → viết ADR/concept), tool không tự làm.")
    return out


def _ensure_gitignore():
    """archive/ phải GIỮ local-only (html/draft vốn gitignored top-level; subfolder thoát pattern
    → phải ignore tường minh, kẻo file local bị track/push)."""
    gi = ROOT / ".gitignore"
    want = ["llmwiki/html/archive/", "llmwiki/wiki/sources/draft/archive/"]
    try:
        txt = gi.read_text(encoding="utf-8") if gi.is_file() else ""
        add = [w for w in want if w not in txt]
        if add:
            gi.write_text(txt.rstrip("\n") + "\n" + "\n".join(add) + "\n", encoding="utf-8")
            print("  ✓ .gitignore: thêm archive/ (giữ local-only)")
    except Exception:
        pass


# archive KHÔNG để phẳng — gom theo CHỨC NĂNG (subfolder), và index lại (kể cả file đã archive)
CATEGORIES = [
    ("proposals", "📋 Proposals (đã xong — bộ ba SPEC + PLAN + seq)"),
    ("superseded", "🔁 Bản bị thay thế"),
    ("analysis", "🔬 Phân tích (cân nhắc promote lên wiki)"),
    ("reports", "📰 Reports / docs một-lần"),
]
CAT_LABEL = dict(CATEGORIES)


def _seq_stems():
    """stem của mọi *-seq.html (active + đã archive) → biết draft nào là cặp proposal."""
    stems = set()
    for base in (HTML, HTML_ARC):
        if base.is_dir():
            for p in base.rglob("*-seq.html"):
                stems.add(p.name[:-len("-seq.html")])
    return stems


def _category(name, kind, seq_stems):
    if kind == "html":
        if name.endswith("-seq.html"):
            return "proposals"
        if re.search(r"-v\d+\.html$", name) or "master-wiki" in name:
            return "superseded"
        return "reports"
    stem = _spec_stem(name[:-3])                      # draft .md (PLAN → quy về stem của SPEC)
    if _is_plan(name):
        return "proposals"                            # PLAN luôn nằm cùng nhóm với SPEC của nó
    return "proposals" if stem in seq_stems else "analysis"


def _organize_existing():
    """Gom file đang nằm PHẲNG ở gốc archive/ vào subfolder chức năng (kể cả đã archive từ trước)."""
    seq = _seq_stems()
    n = 0
    for base, kind in ((HTML_ARC, "html"), (DRAFT_ARC, "draft")):
        if not base.is_dir():
            continue
        for p in list(base.iterdir()):
            if p.is_file() and p.suffix in (".html", ".md") and p.name != "INDEX.md":
                d = base / _category(p.name, kind, seq)
                d.mkdir(parents=True, exist_ok=True)
                p.replace(d / p.name)
                n += 1
    return n


def _build_archive_index():
    """Chỉ mục archive theo chức năng → llmwiki/html/archive/INDEX.md (archive vẫn tìm được)."""
    lines = ["# Archive index — tài liệu đã archive (local-only), theo chức năng",
             "",
             "> Sinh bởi `fdk/tools/docs-curate.py`. Archive = GIỮ (không xoá); đây là chỉ mục để tìm lại.", ""]
    total = 0
    for cat, label in CATEGORIES:
        items = []
        hd = HTML_ARC / cat
        if hd.is_dir():
            items += [(p.name, f"{cat}/{p.name}") for p in sorted(hd.glob("*.html"))]
        dd = DRAFT_ARC / cat
        if dd.is_dir():
            items += [(p.name, f"../../wiki/sources/draft/archive/{cat}/{p.name}") for p in sorted(dd.glob("*.md"))]
        if not items:
            continue
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        lines += [f"- [{nm}]({rel})" for nm, rel in items]
        lines.append("")
        total += len(items)
    lines.append("---")
    lines.append(f"Tổng **{total}** file đã archive.")
    HTML_ARC.mkdir(parents=True, exist_ok=True)
    (HTML_ARC / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return total


def cmd_apply(keep_dates=2):
    out = classify()
    _resolve_reports(out, keep_dates)
    _ensure_gitignore()
    seq = _seq_stems()
    moved = 0
    for n, (kind, action, _r) in sorted(out.items()):
        if action != "archive":
            continue
        base = HTML if kind == "html" else DRAFT
        arc = HTML_ARC if kind == "html" else DRAFT_ARC
        cat = _category(n, kind, seq)
        src = base / n
        dstdir = arc / cat
        dstdir.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            src.replace(dstdir / n)
            moved += 1
            print(f"  📦 {kind}/{n} → archive/{cat}/")
    print(f"docs-curate · apply — archive {moved} mục mới (theo chức năng). Sắp xếp + re-index…")
    cmd_reindex()
    return moved


def cmd_reindex():
    # 0) sắp xếp file đã-archive vào nhóm chức năng (kể cả vào archive rồi)
    reorg = _organize_existing()
    if reorg:
        print(f"  🗂  sắp xếp {reorg} file đã-archive vào nhóm chức năng")
    # 1) dashboard html (active)
    r = subprocess.run([sys.executable, str(ROOT / "fdk" / "tools" / "build-docs-index.py")],
                       capture_output=True, text=True)
    if r.stdout or r.stderr:
        print("  " + (r.stdout or r.stderr).strip().splitlines()[-1])
    # 2) wiki index (R3) — git-aware bỏ qua draft gitignored
    subprocess.run([sys.executable, str(ROOT / "harness" / "validators" / "index_sync.py"),
                    "--wiki-dir", str(ROOT / "llmwiki" / "wiki"), "--fix"], capture_output=True, text=True)
    # 3) chỉ mục ARCHIVE theo chức năng
    n = _build_archive_index()
    print(f"  ✓ build-docs-index + index_sync --fix + archive/INDEX.md ({n} file đã archive, theo nhóm)")


def main():
    args = sys.argv[1:]
    keep = 2
    if "--keep-dates" in args:
        keep = int(args[args.index("--keep-dates") + 1])
    cmd = args[0] if args and not args[0].startswith("-") else "plan"
    if cmd == "apply":
        cmd_apply(keep)
    elif cmd == "reindex":
        cmd_reindex()
    else:
        cmd_plan(keep)


if __name__ == "__main__":
    main()
