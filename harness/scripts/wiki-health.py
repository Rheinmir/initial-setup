#!/usr/bin/env python3
"""L4 evals tĩnh (0 token): sức khỏe wiki — broken wikilink, orphan, index coverage, stale.

Usage:
  wiki-health.py --wiki-dir llmwiki/wiki [--stale-days 60] [--csv harness/metrics/wiki-health.csv]
                 [--fail-on broken,orphans,index,stale]

Output: JSON ra stdout. --csv append một dòng metric (chạy cron để có trend).
Exit 2 nếu nhóm chỉ định trong --fail-on có vi phạm (mặc định: không fail — chỉ báo cáo).
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

SKIP_BASENAMES = {"README.md", "_template.md",
                  # ledger append-only (code-logger / issue ledger): chứa văn bản LỊCH SỬ
                  # được trích nguyên văn — [[...]] trong đó không phải liên kết sống.
                  "log.md", "ISSUES.md"}
CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
MDLINK_RE = re.compile(r"\]\(([^)#\s]+\.md)\)")
INDEX_ROW_RE = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*[^|]+\s*\|\s*([^|]+)\|", re.MULTILINE)
BARE_DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")

_LO_CACHE: dict = {}


def local_only_stem(stem: str, wiki: Path) -> bool:
    """True nếu một file tên <stem>.md sẽ nằm ở thư mục draft gitignored (local-only cố ý).

    Wikilink trỏ tới draft local-only KHÔNG phải broken — file vắng trên fresh clone là CHỦ Ý.
    Dùng `git check-ignore` (glob khớp kể cả file vắng mặt) → nhất quán local ↔ clone sạch.
    Fail-open: git lỗi → False (vẫn báo broken như cũ).
    """
    if stem not in _LO_CACHE:
        res = False
        for c in (f"sources/draft/{stem}.md", f"draft/{stem}.md", f"draft/orca/{stem}.md"):
            try:
                r = subprocess.run(["git", "check-ignore", "-q", (wiki / c).as_posix()],
                                   capture_output=True, timeout=5)
                if r.returncode == 0:
                    res = True
                    break
            except Exception:
                pass
        _LO_CACHE[stem] = res
    return _LO_CACHE[stem]


def _archived(p: Path) -> bool:
    # archive/ = lịch sử đông cứng (docs-curate dời vào, không bảo trì nữa) —
    # link gãy trong đó không phải nợ sống, quét chỉ tạo nhiễu vĩnh viễn.
    return "archive" in p.parts


def content_files(wiki: Path) -> list[Path]:
    out = []
    for d in CONTENT_DIRS:
        base = wiki / d
        if base.is_dir():
            out += [f for f in base.rglob("*.md")
                    if f.name not in SKIP_BASENAMES and not _archived(f.relative_to(wiki))]
    return sorted(out)


def all_pages(wiki: Path) -> list[Path]:
    return sorted(f for f in wiki.rglob("*.md")
                  if f.name not in SKIP_BASENAMES and not _archived(f.relative_to(wiki)))


# Cây kiến-thức anh em trong CÙNG repo mà một wikilink được phép trỏ tới. `fdk/wiki/`
# là wiki RIÊNG của framework (ADR-001..010, concepts harness/fdk — xem README §fdk/),
# `llmwiki/innovation/` là sổ frontier-scan. Trước đây resolver chỉ quét --wiki-dir nên
# [[ADR-004-...]] / [[frontier-gap-scan]] / [[docs-site-macos-skill]] bị báo broken OAN:
# file có thật, chỉ nằm ở cây bên cạnh.
SIBLING_TREES = ("fdk/wiki", "llmwiki/innovation")
_ID_RE = re.compile(r"^id:\s*(.+?)\s*$", re.MULTILINE)


def sibling_targets(wiki: Path) -> dict:
    """stem + `id:` frontmatter của mọi trang trong các cây anh em → đích wikilink hợp lệ.

    Hai cách đánh địa chỉ đều đang được dùng trong repo: theo TÊN FILE (ADR-004-...) và
    theo `id:` khai trong frontmatter (innovation-110826 sống ở file 110826-innovation.md).
    Resolver phải hiểu cả hai, nếu không thì link đúng vẫn bị báo hỏng.
    """
    repo = wiki
    while repo.parent != repo and not (repo / ".git").is_dir():
        repo = repo.parent
    out: dict = {}
    for tree in SIBLING_TREES:
        base = repo / tree
        if not base.is_dir():
            continue
        for f in base.rglob("*.md"):
            if f.name in SKIP_BASENAMES:
                continue
            out.setdefault(f.stem, f)
            head = f.read_text(encoding="utf-8", errors="replace")[:800]
            m = _ID_RE.search(head)
            if m:
                out.setdefault(m.group(1).strip().strip('"\''), f)
    return out


_CODE_FENCE_RE = re.compile(r"```.*?```", re.S)
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")


def prose_only(text: str) -> str:
    """Bỏ fenced code block + inline code trước khi quét wikilink.

    [[...]] trong code là cú-pháp-ví-dụ hoặc bash test ([[ "$1" == x ]]) —
    không phải liên kết; quét cả code từng sinh ~20 broken-link giả."""
    return _CODE_SPAN_RE.sub("", _CODE_FENCE_RE.sub("", text))


def git_last_commit_ts(repo_cwd: Path, file: Path):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(file)],
            cwd=repo_cwd, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return int(out) if out else None
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-dir", required=True)
    ap.add_argument("--stale-days", type=int, default=60)
    ap.add_argument("--csv")
    ap.add_argument("--fail-on", default="", help="csv: broken,orphans,index,summary,stale")
    args = ap.parse_args()

    wiki = Path(args.wiki_dir)
    if not wiki.is_dir():
        print(f"wiki dir khong ton tai: {wiki}", file=sys.stderr)
        sys.exit(1)

    pages = content_files(wiki)
    # đích wikilink = MỌI trang trong cây wiki (kể cả skills/) — trước chỉ lấy CONTENT_DIRS
    # nên [[fdk]]/[[failure-flywheel]] (trang thật dưới skills/) bị báo broken oan;
    # orphan/index vẫn đo trên content_files như cũ.
    stems = dict(sibling_targets(wiki))          # cây anh em: đích hợp lệ, ưu tiên THẤP nhất
    stems.update({p.stem: p for p in all_pages(wiki)})
    stems.update({p.stem: p for p in pages})
    rel = {p: p.relative_to(wiki).as_posix() for p in pages}

    # 1. broken wikilinks + inbound graph
    broken = []
    inbound = {p: 0 for p in pages}
    for src in all_pages(wiki):
        text = prose_only(src.read_text(encoding="utf-8", errors="replace"))
        for name in WIKILINK_RE.findall(text):
            name = name.strip()
            target = stems.get(name)
            if target is None:
                if not local_only_stem(name, wiki):   # wikilink→draft local-only ≠ broken
                    broken.append({"from": src.relative_to(wiki).as_posix(), "wikilink": name})
            elif target != src and target in inbound:  # inbound chỉ đo trên content pages
                inbound[target] += 1
        for link in MDLINK_RE.findall(text):
            cand = (src.parent / link).resolve()
            for p in pages:
                if p.resolve() == cand and p != src:
                    inbound[p] += 1

    # 2. orphans: trang nội dung không có inbound link nào
    orphans = [rel[p] for p, n in inbound.items() if n == 0]

    # 3. index coverage
    idx_text = (wiki / "index.md").read_text(encoding="utf-8") if (wiki / "index.md").is_file() else ""
    idx_refs = {m.lstrip("./") for m in MDLINK_RE.findall(idx_text)}
    idx_names = {m.strip() for m in WIKILINK_RE.findall(idx_text)}
    indexed = set(idx_refs) | {rel[p] for p in pages if p.stem in idx_names}
    missing_index = sorted(set(rel.values()) - indexed)
    extra_index = sorted(r for r in idx_refs if r not in set(rel.values()))

    # 3b. summary chất lượng thấp: cột Summary chỉ là ngày tháng trơ (vô dụng —
    # ngày đã có sẵn trong tên file), thường do agent lười gõ khi thêm row.
    bare_date_summary = []
    for m in INDEX_ROW_RE.finditer(idx_text):
        name, link, summary = m.group(1), m.group(2), m.group(3).strip()
        if BARE_DATE_RE.match(summary):
            bare_date_summary.append(f"{name}({link})")

    # 4. stale (theo git)
    now = datetime.datetime.now().timestamp()
    stale = []
    for p in pages:
        ts = git_last_commit_ts(wiki, p)
        if ts and (now - ts) > args.stale_days * 86400:
            stale.append({"file": rel[p], "days": int((now - ts) / 86400)})

    report = {
        "date": datetime.date.today().isoformat(),
        "pages": len(pages),
        "broken_wikilinks": broken,
        "orphans": orphans,
        "missing_in_index": missing_index,
        "extra_in_index": extra_index,
        "bare_date_summary": bare_date_summary,
        "stale": stale,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        header = "date,pages,broken,orphans,missing_index,extra_index,stale\n"
        if not csv_path.is_file():
            csv_path.write_text(header, encoding="utf-8")
        with open(csv_path, "a", encoding="utf-8") as f:
            f.write(
                f"{report['date']},{len(pages)},{len(broken)},{len(orphans)},"
                f"{len(missing_index)},{len(extra_index)},{len(stale)}\n"
            )

    fail_groups = {g.strip() for g in args.fail_on.split(",") if g.strip()}
    failed = (
        ("broken" in fail_groups and broken)
        or ("orphans" in fail_groups and orphans)
        or ("index" in fail_groups and (missing_index or extra_index))
        or ("summary" in fail_groups and bare_date_summary)
        or ("stale" in fail_groups and stale)
    )
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
