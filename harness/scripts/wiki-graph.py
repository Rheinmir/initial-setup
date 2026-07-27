#!/usr/bin/env python3
"""Wiki knowledge-graph query (0 token, no-LLM) — hỏi "cái gì trỏ tới X".

Dựng một đồ thị có hướng TRONG BỘ NHỚ từ `[[wikilink]]` và `](*.md)` link trên 6
thư mục nội dung (concepts, entities, sources, draft, architecture, tours — lấy
trực tiếp từ harness/wikidirs.py, single source of truth). wiki-health.py đã quét
cạnh nhưng VỨT BỎ chiều inbound nên không trả lời được "trang nào link tới đây";
script này giữ cả hai chiều và mở ra các truy vấn đồ thị tất định.

Subcommands:
  backlinks <page>             — trang nào trỏ TỚI <page> (đảo chiều của wiki-health)
  neighbors <page> [--depth N] — hàng xóm trong bán kính N (vô hướng, BFS)
  orphans                      — trang nội dung 0 inbound (không ai trỏ tới)
  broken                       — wikilink trỏ tới đích không tồn tại
                                 (BỎ QUA draft local-only đã .gitignore — như wiki-health)
  export --format {json,mermaid,dot}  — xuất toàn đồ thị

Mọi subcommand nhận `--wiki-dir` (mặc định llmwiki/wiki); các truy vấn nhận `--json`.
Git-aware: link tới draft đã gitignore KHÔNG bị tính broken (nhất quán local↔fresh-clone).
Fail-open: thiếu wiki dir → in kết quả rỗng + exit 0 (không chặn pipeline/cron).

Ví dụ:
  wiki-graph.py backlinks fdk
  wiki-graph.py neighbors fdk --depth 2
  wiki-graph.py orphans --json
  wiki-graph.py broken --wiki-dir llmwiki/wiki
  wiki-graph.py export --format mermaid > graph.mmd
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

# --- Reuse wiki-health.py's regex + skip-set (shared scripts không được sửa → copy theo
#     chủ ý để hai tool đồng nhất cách nhận diện cạnh). ---
SKIP_BASENAMES = {"README.md", "_template.md"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
MDLINK_RE = re.compile(r"\]\(([^)#\s]+\.md)\)")

# ── NGUỒN CHÂN LÝ DUY NHẤT cho "cái gì link tới cái gì" ─────────────────────────
# Trước 2026-07-20 có HAI bản cài trả lời cùng câu hỏi này, không chia sẻ dòng code
# nào: file này (query cho agent) và fdk/tools/build-wiki-graph.py (vẽ cho người).
# Đo được chúng LỆCH THẬT: 208 cạnh wikilink so với 164 — và mỗi bên sai một kiểu:
#   · bản này KHÔNG bỏ code-fence → đếm cả [[...]] trong khối code là cạnh thật
#   · bản kia bỏ code-fence đúng nhưng BỎ SÓT [[trang#anchor]] và ](file.md)
# Không bên nào là tập cha của bên kia, nên không thể chọn bừa một bên. Hàm dưới hợp
# cái đúng của cả hai; build-wiki-graph.py import nó thay vì tự bắt regex.
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_RE = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    """Bỏ code-fence + inline-code — [[...]] trong ví dụ code KHÔNG phải liên kết thật."""
    return _INLINE_RE.sub(" ", _FENCE_RE.sub(" ", text))


def wikilink_targets(text: str) -> list:
    """Đích của mọi [[wikilink]] trong THÂN BÀI (đã bỏ code), giữ thứ tự, khử trùng."""
    out, seen = [], set()
    for name in WIKILINK_RE.findall(strip_code(text)):
        n = name.strip()
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


# `touches` — cạnh CONCEPT → CODE. Suy ra, KHÔNG cất.
#
# Trước 2026-07-20 quan hệ này được `fdk/tools/wiki-relations.py` DẬP VÀO frontmatter
# đúng một lần (02/07) rồi đóng băng: 21 cạnh trên tổng 2.559 (0,8%) trong khi nó là
# thứ DUY NHẤT không graph nào khác làm được — code-graph chỉ biết code↔code, wiki-link
# chỉ biết wiki↔wiki. Root: một sự thật SUY RA ĐƯỢC bị cất như sự thật ĐƯỢC KHAI; cất
# rồi thì nó không tự cập nhật. `wikilink` không bao giờ cũ vì nó được suy lại mỗi lần
# dựng — `touches` phải theo đúng cơ chế đó.
#
# LƯU Ý ngược với wikilink_targets: hàm này KHÔNG được strip_code, vì path nằm CHÍNH
# TRONG inline-code. Điều kiện chống false-positive giữ nguyên bản gốc: phải có "/" và
# phải TỒN TẠI trên đĩa.
CODE_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|js|ts|sh|yaml|yml|json|html))`")

# 2026-07-22: đây là nguồn CHUẨN cho câu hỏi "wiki nói về code nào" (content-based, tất
# định). provenance-log.jsonl (đề xuất, xem llmwiki/wiki/concepts/log-model.md) KHÔNG được
# suy lại quan hệ này bằng heuristic thời gian — sẽ tệ hơn hàm này, đừng làm lại.


def touches_targets(text: str, repo_root) -> list:
    """Path code mà trang này nhắc tới trong backtick VÀ có thật trên đĩa."""
    root = Path(repo_root)
    out, seen = [], set()
    for cp in CODE_PATH_RE.findall(text or ""):
        cp = cp.strip()
        if cp and cp not in seen and "/" in cp and (root / cp).exists():
            seen.add(cp)
            out.append(cp)
    return out


def mdlink_targets(text: str) -> list:
    """Đích của mọi ](*.md) trong thân bài (đã bỏ code)."""
    out, seen = [], set()
    for link in MDLINK_RE.findall(strip_code(text)):
        if link and link not in seen:
            seen.add(link)
            out.append(link)
    return out

_DEFAULT_CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")


def _content_dirs() -> tuple:
    """Lấy CONTENT_DIRS từ harness/wikidirs.py (single source of truth). Fail-open → default."""
    harness_dir = Path(__file__).resolve().parent.parent  # .../harness
    if str(harness_dir) not in sys.path:
        sys.path.insert(0, str(harness_dir))
    try:
        import wikidirs  # harness/wikidirs.py
        dirs = tuple(getattr(wikidirs, "CONTENT_DIRS", ()))
        return dirs or _DEFAULT_CONTENT_DIRS
    except Exception:
        return _DEFAULT_CONTENT_DIRS


CONTENT_DIRS = _content_dirs()

_LO_CACHE: dict = {}


def local_only_stem(stem: str, wiki: Path) -> bool:
    """True nếu một file <stem>.md sẽ nằm ở thư mục draft gitignored (local-only cố ý).

    Ý tưởng mượn nguyên từ wiki-health.py: wikilink trỏ tới draft local-only KHÔNG phải
    broken — file vắng trên fresh clone là CHỦ Ý. `git check-ignore` khớp glob kể cả khi
    file vắng mặt → nhất quán giữa máy local và clone sạch. Fail-open: git lỗi → False.
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


def content_files(wiki: Path) -> list:
    """Các trang nội dung (6 dir), bỏ README/_template. Fail-open: dir vắng → bỏ qua."""
    out = []
    for d in CONTENT_DIRS:
        base = wiki / d
        if base.is_dir():
            out += [f for f in base.rglob("*.md") if f.name not in SKIP_BASENAMES]
    return sorted(out)


def all_pages(wiki: Path) -> list:
    """Mọi .md trong wiki (kể cả index/log/decisions ở gốc) — đây là tập NGUỒN của cạnh."""
    return sorted(f for f in wiki.rglob("*.md") if f.name not in SKIP_BASENAMES)


class Graph:
    """Đồ thị có hướng đã dựng: node = relpath, cạnh luôn KẾT THÚC tại một trang nội dung."""

    def __init__(self) -> None:
        self.wiki: Path = Path(".")
        self.pages: list = []          # mọi relpath (nguồn tiềm năng của cạnh)
        self.content: set = set()      # relpath thuộc 6 content dir (đích hợp lệ + xét orphan)
        self.stem_content: dict = {}   # stem -> relpath (chỉ content) — phân giải wikilink
        self.stem_all: dict = {}       # stem -> relpath (mọi trang) — phân giải tham số <page>
        self.relset: set = set()       # set mọi relpath
        self.edges: list = []          # list[(src, dst, "wikilink"|"mdlink")]
        self.out_adj: dict = {}        # src -> set(dst)
        self.in_adj: dict = {}         # dst -> set(src)
        self.in_unresolved: dict = {}  # tên-đích-local-only -> {src: type} (cho backlinks draft vắng)
        self.broken: list = []         # list[{"from": relpath, "wikilink": name}]


def build_graph(wiki: Path) -> Graph:
    """Đọc mỗi trang đúng MỘT lần, dựng adjacency hai chiều + danh sách broken (git-aware)."""
    g = Graph()
    g.wiki = wiki
    content = content_files(wiki)
    allp = all_pages(wiki)

    def rel(p: Path) -> str:
        return p.relative_to(wiki).as_posix()

    g.content = {rel(p) for p in content}
    g.pages = [rel(p) for p in allp]
    g.relset = set(g.pages)
    for p in content:                       # content thắng khi trùng stem (phân giải wikilink)
        g.stem_content[p.stem] = rel(p)
    for p in allp:                          # đã sort → deterministic; setdefault giữ bản đầu
        g.stem_all.setdefault(p.stem, rel(p))
    # Index path tuyệt đối cho md-link (chỉ content, như wiki-health) → tra cứu O(1).
    path_index = {p.resolve(): rel(p) for p in content}

    g.out_adj = {r: set() for r in g.pages}
    g.in_adj = {r: set() for r in g.pages}
    broken_seen: set = set()

    for src in allp:
        srel = rel(src)
        text = src.read_text(encoding="utf-8", errors="replace")
        seen_edge: set = set()  # khử trùng cạnh (dst, type) trong cùng một file

        for name in wikilink_targets(text):
            dst = g.stem_content.get(name)
            if dst is None:
                if local_only_stem(name, wiki):          # trỏ draft gitignored → KHÔNG broken
                    g.in_unresolved.setdefault(name, {})[srel] = "wikilink"
                else:
                    k = (srel, name)
                    if k not in broken_seen:
                        broken_seen.add(k)
                        g.broken.append({"from": srel, "wikilink": name})
                continue
            if dst == srel:
                continue
            key = (dst, "wikilink")
            if key in seen_edge:
                continue
            seen_edge.add(key)
            g.edges.append((srel, dst, "wikilink"))
            g.out_adj[srel].add(dst)
            g.in_adj[dst].add(srel)

        for link in mdlink_targets(text):
            cand = (src.parent / link).resolve()
            dst = path_index.get(cand)
            if dst is None or dst == srel:
                continue
            key = (dst, "mdlink")
            if key in seen_edge:
                continue
            seen_edge.add(key)
            g.edges.append((srel, dst, "mdlink"))
            g.out_adj[srel].add(dst)
            g.in_adj[dst].add(srel)

    return g


def resolve_page(arg: str, g: Graph):
    """Phân giải tham số <page> (stem / basename / relpath, có hoặc không .md) → relpath node."""
    a = arg.strip().lstrip("./")
    if a.startswith("wiki/"):
        a = a[len("wiki/"):]
    stem = a[:-3] if a.endswith(".md") else a
    if a in g.relset:
        return a
    if a + ".md" in g.relset:
        return a + ".md"
    if stem in g.stem_content:
        return g.stem_content[stem]
    if stem in g.stem_all:
        return g.stem_all[stem]
    for rp in g.pages:                      # fallback: khớp basename
        base = rp.rsplit("/", 1)[-1]
        if base == a or base[:-3] == stem:
            return rp
    return None


def _stem_of(arg: str) -> str:
    s = arg.strip().lstrip("./")
    if s.startswith("wiki/"):
        s = s[len("wiki/"):]
    s = s.rsplit("/", 1)[-1]
    return s[:-3] if s.endswith(".md") else s


def _label(relpath: str) -> str:
    return relpath.rsplit("/", 1)[-1][:-3]   # bỏ thư mục + đuôi .md


# --------------------------- subcommands ---------------------------

def cmd_backlinks(g: Graph, page: str):
    target = resolve_page(page, g)
    stem = _stem_of(page)
    rows = set()
    if target is not None:
        for (s, d, t) in g.edges:
            if d == target:
                rows.add((s, t))
    for s, t in g.in_unresolved.get(stem, {}).items():   # draft local-only / vắng trên đĩa
        rows.add((s, t))
    rows = sorted(rows)
    found = target is not None or stem in g.in_unresolved
    obj = {
        "page": page,
        "resolved": target,
        "found": found,
        "local_only": target is None and stem in g.in_unresolved,
        "count": len(rows),
        "backlinks": [{"from": s, "type": t} for s, t in rows],
    }
    if not found:
        return [f"backlinks: page not found: {page}"], obj
    label = target if target else f"{stem} (local-only/absent draft)"
    lines = [f"backlinks: {label}  [{len(rows)}]"]
    lines += [f"  <- {s}  [{t}]" for s, t in rows] or ["  (none)"]
    return lines, obj


def cmd_neighbors(g: Graph, page: str, depth: int):
    target = resolve_page(page, g)
    if target is None:
        return [f"neighbors: page not found: {page}"], {"page": page, "resolved": None, "neighbors": {}}
    visited = {target: 0}
    levels: dict = {}
    q = deque([target])
    while q:
        cur = q.popleft()
        d = visited[cur]
        if d >= depth:
            continue
        for n in g.out_adj.get(cur, set()) | g.in_adj.get(cur, set()):
            if n not in visited:
                visited[n] = d + 1
                levels.setdefault(d + 1, []).append(n)
                q.append(n)
    out1 = g.out_adj.get(target, set())
    in1 = g.in_adj.get(target, set())
    obj = {"page": page, "resolved": target, "depth": depth,
           "neighbors": {str(d): sorted(ns) for d, ns in levels.items()}}
    lines = [f"neighbors: {target}  (depth {depth})"]
    if not levels:
        lines.append("  (no neighbors)")
    for d in sorted(levels):
        lines.append(f"  depth {d}:")
        for n in sorted(levels[d]):
            if d == 1:
                arrow = "/".join([a for a, ok in (("->", n in out1), ("<-", n in in1)) if ok]) or "--"
                lines.append(f"    {arrow} {n}")
            else:
                lines.append(f"     . {n}")
    return lines, obj


def cmd_orphans(g: Graph):
    orph = sorted(r for r in g.content if not g.in_adj.get(r))
    obj = {"count": len(orph), "orphans": orph}
    lines = [f"orphans (content pages, 0 inbound): {len(orph)}"]
    lines += [f"  {r}" for r in orph] or ["  (none)"]
    return lines, obj


def cmd_broken(g: Graph):
    items = sorted(g.broken, key=lambda b: (b["wikilink"], b["from"]))
    obj = {"count": len(items), "broken": items}
    lines = [f"broken wikilinks (dangling, excl. gitignored drafts): {len(items)}"]
    lines += [f"  [[{b['wikilink']}]]  <- {b['from']}" for b in items] or ["  (none)"]
    return lines, obj


def _export_nodes(g: Graph):
    indeg = {r: len(g.in_adj.get(r, set())) for r in g.pages}
    outdeg = {r: len(g.out_adj.get(r, set())) for r in g.pages}
    nodes = sorted(r for r in g.pages if r in g.content or indeg[r] or outdeg[r])
    return nodes, indeg, outdeg


def cmd_export(g: Graph, fmt: str) -> str:
    nodes, indeg, outdeg = _export_nodes(g)
    idmap = {r: f"n{i}" for i, r in enumerate(nodes)}
    orphan_ids = [idmap[r] for r in nodes if r in g.content and indeg[r] == 0]

    if fmt == "json":
        obj = {
            "stats": {
                "nodes": len(nodes),
                "edges": len(g.edges),
                "content_pages": len(g.content),
                "orphans": sum(1 for r in g.content if indeg[r] == 0),
                "broken": len(g.broken),
            },
            "nodes": [{"id": r, "label": _label(r), "content": r in g.content,
                       "in": indeg[r], "out": outdeg[r]} for r in nodes],
            "edges": [{"from": s, "to": d, "type": t} for (s, d, t) in g.edges],
        }
        return json.dumps(obj, ensure_ascii=False, indent=2)

    if fmt == "mermaid":
        out = ["flowchart LR"]
        out += [f'  {idmap[r]}["{_label(r)}"]' for r in nodes]
        for (s, d, t) in g.edges:
            out.append(f"  {idmap[s]} {'-->' if t == 'wikilink' else '-.->'} {idmap[d]}")
        if orphan_ids:
            out.append("  classDef orphan stroke-dasharray:4 3,fill:#fff0f0;")
            out.append("  class " + ",".join(orphan_ids) + " orphan;")
        return "\n".join(out)

    # dot
    out = ["digraph wiki {", "  rankdir=LR;", "  node [shape=box, fontsize=10];"]
    for r in nodes:
        attrs = f'label="{_label(r)}"'
        if r in g.content and indeg[r] == 0:
            attrs += ", style=dashed, color=red"
        out.append(f"  {idmap[r]} [{attrs}];")
    for (s, d, t) in g.edges:
        out.append(f"  {idmap[s]} -> {idmap[d]}{'' if t == 'wikilink' else ' [style=dashed]'};")
    out.append("}")
    return "\n".join(out)


def _fail_open(args) -> None:
    """Thiếu wiki dir → in benign empty + exit 0 (đây là tool truy vấn, không phải gate)."""
    if args.cmd == "export":
        fmt = getattr(args, "format", "json")
        if fmt == "mermaid":
            print("flowchart LR")
        elif fmt == "dot":
            print("digraph wiki {\n}")
        else:
            print(json.dumps({"stats": {"nodes": 0, "edges": 0, "content_pages": 0,
                                        "orphans": 0, "broken": 0}, "nodes": [], "edges": []},
                             ensure_ascii=False, indent=2))
    elif getattr(args, "json", False):
        empty = {"backlinks": {"count": 0, "backlinks": []}, "neighbors": {"neighbors": {}},
                 "orphans": {"count": 0, "orphans": []}, "broken": {"count": 0, "broken": []}}
        print(json.dumps(empty.get(args.cmd, {}), ensure_ascii=False, indent=2))
    else:
        print(f"[wiki-graph] {args.cmd}: wiki dir missing — empty result")


def main() -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--wiki-dir", default="llmwiki/wiki",
                        help="wiki content root (default: llmwiki/wiki)")

    ap = argparse.ArgumentParser(prog="wiki-graph.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("backlinks", parents=[common], help="trang nào trỏ tới <page>")
    p.add_argument("page")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("neighbors", parents=[common], help="hàng xóm trong bán kính N")
    p.add_argument("page")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("orphans", parents=[common], help="trang nội dung 0 inbound")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("broken", parents=[common], help="wikilink trỏ đích không tồn tại")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("export", parents=[common], help="xuất toàn đồ thị")
    p.add_argument("--format", choices=["json", "mermaid", "dot"], default="json")

    args = ap.parse_args()

    wiki = Path(args.wiki_dir)
    if not wiki.is_dir():
        sys.stderr.write(f"[wiki-graph] wiki dir not found: {wiki} — fail-open (empty result)\n")
        _fail_open(args)
        sys.exit(0)

    g = build_graph(wiki)

    if args.cmd == "export":
        print(cmd_export(g, args.format))
        sys.exit(0)

    if args.cmd == "backlinks":
        lines, obj = cmd_backlinks(g, args.page)
    elif args.cmd == "neighbors":
        lines, obj = cmd_neighbors(g, args.page, args.depth)
    elif args.cmd == "orphans":
        lines, obj = cmd_orphans(g)
    elif args.cmd == "broken":
        lines, obj = cmd_broken(g)
    else:  # unreachable (subparser required)
        ap.error("unknown command")
        return

    if getattr(args, "json", False):
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
