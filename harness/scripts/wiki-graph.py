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
  edge <eid>                   — tra một cạnh theo edge ID ổn định (exit 1 nếu không có)
  cite <page>                  — mọi cạnh chạm <page>, mỗi dòng `eid  from -> to  (type)`
  export --format {json,mermaid,dot}  — xuất toàn đồ thị (`--json` = alias của json)
  --self-test                  — kiểm tất định trên wiki tạm (eid, typed edge, edge/cite)

Ngoài cạnh suy ra từ thân bài, đồ thị còn nhận cạnh CÓ KIỂU khai trong frontmatter
`relations: - {rel: X, to: Y}` (derives-from/depends-on/implements/supports/contradicts/
supersedes) — cùng cú pháp fdk/tools/build-wiki-graph.py đang đọc. Mỗi cạnh mang một
`eid` ổn định (hàm thuần của src|dst|type) để câu trả lời trích được bằng chứng mức cạnh.

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
import functools
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from collections import deque
from contextlib import redirect_stderr, redirect_stdout
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


# `operationalizes` — cạnh wiki (layer: fact|mental-model) → Protocol (skill/rule).
#
# Cùng hình dạng với `touches` (wiki→NGOÀI 6 thư mục nội dung): suy từ thân bài, KHÔNG khai
# tay trong `relations:`, KHÔNG vào ALLOWED_RELS — bài học lịch sử `touches` dập tay 1 lần rồi
# đóng băng ở 0,8% coverage áp dụng y hệt ở đây. Xem llmwiki/wiki/sources/draft/
# 010826-wiki-mental-model-taxonomy.md.
SKILL_TOKEN_RE = re.compile(r"`([\w-]+)`")
_RULE_ID_RE = re.compile(r"^\s*id:\s*(\S+)", re.MULTILINE)


@functools.lru_cache(maxsize=1)
def _policy_rule_ids(root_str: str) -> frozenset:
    """Mọi `id: RNN` khai trong policy.yaml — cache vì scan() gọi hàm này mỗi node."""
    p = Path(root_str) / "harness" / "poc-vendor-neutral" / "policy.yaml"
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return frozenset()
    return frozenset(_RULE_ID_RE.findall(text))


def operationalizes_targets(text: str, repo_root) -> list:
    """Skill/rule mà trang này nhắc trong backtick VÀ tồn tại thật — suy, không cất."""
    root = Path(repo_root)
    rule_ids = _policy_rule_ids(str(root))
    out, seen = [], set()
    for tok in SKILL_TOKEN_RE.findall(text or ""):
        if tok in seen:
            continue
        if (root / "skills" / tok / "SKILL.md").exists():
            seen.add(tok)
            out.append(f"skills/{tok}/SKILL.md")
        elif tok in rule_ids:
            seen.add(tok)
            out.append(f"rule:{tok}")
    return out


def mdlink_targets(text: str) -> list:
    """Đích của mọi ](*.md) trong thân bài (đã bỏ code)."""
    out, seen = [], set()
    for link in MDLINK_RE.findall(strip_code(text)):
        if link and link not in seen:
            seen.add(link)
            out.append(link)
    return out

# ── Edge ID ổn định + cạnh CÓ KIỂU khai trong frontmatter ──────────────────────
# Câu trả lời của /query phải trích được BẰNG CHỨNG ở mức cạnh, không chỉ mức trang;
# muốn trích thì cạnh phải có tên gọi bền qua mỗi lần dựng lại. eid là hàm THUẦN của
# (src, dst, type) nên không cần cất ở đâu cả — dựng lại vẫn ra đúng cái tên cũ.
#
# Cú pháp `relations:` KHÔNG phát minh mới: fdk/tools/build-wiki-graph.py đã đọc
# `- {rel: X, to: Y}` trong frontmatter từ trước (REL_RE của nó), wiki thật đang dùng.
# Ở đây chỉ nhận `to:` (đích là trang wiki); `path:` là cạnh concept→code, đã có
# touches_targets lo. Ba rel mới supports/contradicts/supersedes theo Appendix của PDF.
ALLOWED_RELS = {"derives-from", "depends-on", "implements",
                "supports", "contradicts", "supersedes"}
_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)
_REL_RE = re.compile(r"\{[ \t]*rel[ \t]*:[ \t]*([\w-]+)[ \t]*,[ \t]*to[ \t]*:[ \t]*([^}\s]+)[ \t]*\}")


def edge_id(src: str, dst: str, typ: str) -> str:
    """Tên gọi ổn định của một cạnh — thuần, không phụ thuộc thứ tự dựng hay thời điểm."""
    return "e:" + hashlib.sha1(f"{src}|{dst}|{typ}".encode()).hexdigest()[:8]


def frontmatter_relations(text: str) -> list:
    """[(rel, to)] khai trong frontmatter (KHÔNG cần lib yaml). Rel ngoài whitelist bị bỏ."""
    m = _FM_RE.match(text)
    if not m:
        return []
    return [(rel, to) for rel, to in _REL_RE.findall(m.group(1)) if rel in ALLOWED_RELS]


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
        self.ambiguous_stems: set = set()  # stem trùng ≥2 trang content — TỪ CHỐI phân giải bare-stem
        self.stem_all: dict = {}       # stem -> relpath (mọi trang) — phân giải tham số <page>
        self.relset: set = set()       # set mọi relpath
        self.edges: list = []          # list[(src, dst, type, eid)]; type: wikilink|mdlink|<rel>
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
    # content thắng khi trùng stem (phân giải wikilink) — NHƯNG 2 trang content trùng stem ở
    # khác thư mục (vd concepts/foo.md và entities/foo.md) không được ghi đè âm thầm: đích sẽ
    # bị BIND NHẦM và sinh eid trỏ sai trang mà không ai biết. Đánh dấu ambiguous, từ chối
    # phân giải bare-stem cho các stem đó (wikilink rơi vào broken thay vì trỏ nhầm).
    _stem_counts: dict = {}
    for p in content:
        _stem_counts.setdefault(p.stem, []).append(rel(p))
    g.ambiguous_stems = {stem for stem, paths in _stem_counts.items() if len(paths) > 1}
    for stem, paths in _stem_counts.items():
        if stem not in g.ambiguous_stems:
            g.stem_content[stem] = paths[0]
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
            g.edges.append((srel, dst, "wikilink", edge_id(srel, dst, "wikilink")))
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
            g.edges.append((srel, dst, "mdlink", edge_id(srel, dst, "mdlink")))
            g.out_adj[srel].add(dst)
            g.in_adj[dst].add(srel)

        # Cạnh CÓ KIỂU khai tay trong frontmatter. KHÔNG vào out_adj/in_adj: hai bảng đó
        # đang trả lời "vệ sinh liên kết" (neighbors/orphans đếm theo link thân bài), đổi
        # chúng sẽ lặng lẽ dịch số orphan của wiki thật. Đích không phân giải được → bỏ
        # qua, không tính broken (broken là chuyện của wikilink).
        for rel_type, to in frontmatter_relations(text):
            dst = resolve_page(to, g)
            if dst is None or dst == srel:
                continue
            key = (dst, rel_type)
            if key in seen_edge:
                continue
            seen_edge.add(key)
            g.edges.append((srel, dst, rel_type, edge_id(srel, dst, rel_type)))

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
    if stem in g.ambiguous_stems:
        return None  # 2+ trang content trùng stem — bắt buộc chỉ định đường dẫn có thư mục
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
        for (s, d, t, _e) in g.edges:
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


def cmd_edge(g: Graph, eid: str) -> int:
    """Tra một cạnh theo eid. In JSON MỘT dòng (dễ nhặt trong pipeline), 1 nếu không có."""
    for (s, d, t, e) in g.edges:
        if e == eid:
            print(json.dumps({"eid": e, "from": s, "to": d, "type": t}, ensure_ascii=False))
            return 0
    print(f"[wiki-graph] khong co canh {eid}", file=sys.stderr)
    return 1


def cmd_cite(g: Graph, page: str) -> int:
    """Mọi cạnh inbound+outbound của một trang, kèm eid — nguồn trích dẫn cho /query."""
    target = resolve_page(page, g)
    if target is None:
        sys.stderr.write(f"[wiki-graph] cite: page not found: {page}\n")
        return 0                         # tool truy vấn, không phải gate → fail-open
    for (s, d, t, e) in g.edges:
        if s == target or d == target:
            print(f"{e}  {s} -> {d}  ({t})")
    return 0


def _export_nodes(g: Graph):
    indeg = {r: len(g.in_adj.get(r, set())) for r in g.pages}
    outdeg = {r: len(g.out_adj.get(r, set())) for r in g.pages}
    # Cạnh typed không nằm trong out_adj/in_adj nên không cộng bậc; vẫn phải khai node hai
    # đầu, nếu không mermaid/dot sẽ trỏ tới id chưa định nghĩa.
    typed_ends = {r for (s, d, _t, _e) in g.edges for r in (s, d)}
    nodes = sorted(r for r in g.pages
                   if r in g.content or indeg[r] or outdeg[r] or r in typed_ends)
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
            "edges": [{"eid": e, "from": s, "to": d, "type": t} for (s, d, t, e) in g.edges],
        }
        return json.dumps(obj, ensure_ascii=False, indent=2)

    if fmt == "mermaid":
        out = ["flowchart LR"]
        out += [f'  {idmap[r]}["{_label(r)}"]' for r in nodes]
        for (s, d, t, _e) in g.edges:
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
    for (s, d, t, _e) in g.edges:
        out.append(f"  {idmap[s]} -> {idmap[d]}{'' if t == 'wikilink' else ' [style=dashed]'};")
    out.append("}")
    return "\n".join(out)


def self_test() -> int:
    """Wiki tạm 3 trang → eid ổn định, typed edge từ frontmatter, hai lệnh edge/cite."""
    checks = []
    with tempfile.TemporaryDirectory() as td:
        wiki = Path(td) / "wiki"
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "concepts" / "a.md").write_text("# A\n\nxem [[b]]\n", encoding="utf-8")
        (wiki / "concepts" / "b.md").write_text(
            "---\ntype: concept\nrelations:\n"
            "  - {rel: supports, to: a}\n"
            "  - {rel: khong-hop-le, to: a}\n"
            "---\n\n# B\n", encoding="utf-8")
        (wiki / "concepts" / "c.md").write_text("# C\n", encoding="utf-8")
        g = build_graph(wiki)

        # (1) frontmatter relations → cạnh có type, rel ngoài whitelist bị loại
        types = {t for (_s, _d, t, _e) in g.edges}
        checks.append(("typed edge supports", {"supports", "wikilink"} <= types))
        checks.append(("rel ngoài whitelist bị loại", "khong-hop-le" not in types))
        checks.append(("frontmatter_relations trực tiếp",
                       frontmatter_relations("---\nrelations:\n  - {rel: supports, to: a}\n---\n")
                       == [("supports", "a")]))
        checks.append(("không frontmatter → rỗng", frontmatter_relations("# A\n") == []))

        # (2) edge_id thuần + ổn định
        checks.append(("mọi cạnh có eid",
                       bool(g.edges) and all(len(e) == 4 and e[3].startswith("e:") for e in g.edges)))
        eid = edge_id("concepts/a.md", "concepts/b.md", "wikilink")
        checks.append(("edge_id tất định", eid == edge_id("concepts/a.md", "concepts/b.md", "wikilink")))
        checks.append(("edge_id phân biệt type",
                       eid != edge_id("concepts/a.md", "concepts/b.md", "mdlink")))

        # (3) cite <page> — đủ cả inbound lẫn outbound của a (a->b wikilink, b->a supports)
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_cite(g, "a")
        cite_lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
        checks.append(("cite a đủ 2 cạnh có eid",
                       len(cite_lines) == 2 and all(ln.startswith("e:") for ln in cite_lines)))

        # (4) edge <eid> — trúng thì in JSON + exit 0, trượt thì exit 1
        want = g.edges[0]
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_hit = cmd_edge(g, want[3])
        obj = json.loads(buf.getvalue() or "{}")
        checks.append(("edge <eid> trả đúng cạnh",
                       rc_hit == 0 and obj.get("eid") == want[3]
                       and (obj.get("from"), obj.get("to"), obj.get("type")) == want[:3]))
        with redirect_stderr(io.StringIO()):
            rc_miss = cmd_edge(g, "e:deadbeef")
        checks.append(("edge eid lạ → exit 1", rc_miss == 1))

        # (5) mọi consumer unpack 4 phần vẫn chạy; export json mang thêm "eid"
        exp = json.loads(cmd_export(g, "json"))
        checks.append(("export json có eid",
                       len(exp["edges"]) == len(g.edges) and all("eid" in e for e in exp["edges"])))
        checks.append(("export mermaid/dot còn nguyên",
                       cmd_export(g, "mermaid").startswith("flowchart LR")
                       and cmd_export(g, "dot").startswith("digraph wiki {")))
        _lines, back = cmd_backlinks(g, "a")
        checks.append(("backlinks thấy cạnh typed",
                       any(b["type"] == "supports" for b in back["backlinks"])))

    # (6) bug thật đã tìm thấy: 2 trang content TRÙNG STEM ở khác thư mục từng bị ghi đè âm
    # thầm trong stem_content → wikilink/relations trỏ NHẦM trang mà không ai biết. Giờ phải
    # bị coi là ambiguous và TỪ CHỐI phân giải bare-stem (rơi vào broken, không bind nhầm).
    with tempfile.TemporaryDirectory() as td2:
        wiki2 = Path(td2) / "wiki"
        (wiki2 / "concepts").mkdir(parents=True)
        (wiki2 / "entities").mkdir(parents=True)
        (wiki2 / "concepts" / "dup.md").write_text("# Dup concept\n", encoding="utf-8")
        (wiki2 / "entities" / "dup.md").write_text("# Dup entity\n", encoding="utf-8")
        (wiki2 / "concepts" / "z.md").write_text(
            "---\ntype: concept\nrelations:\n  - {rel: supports, to: dup}\n---\n\n"
            "# Z\n\nxem [[dup]]\n", encoding="utf-8")
        g2 = build_graph(wiki2)
        checks.append(("stem trùng 2 trang content → đánh dấu ambiguous",
                       "dup" in g2.ambiguous_stems))
        checks.append(("resolve_page('dup') TỪ CHỐI (None), không bind nhầm 1 trong 2",
                       resolve_page("dup", g2) is None))
        checks.append(("wikilink [[dup]] rơi vào broken thay vì trỏ nhầm trang",
                       any(b["wikilink"] == "dup" for b in g2.broken)))
        checks.append(("relations to:dup KHÔNG sinh cạnh (đích mơ hồ, không đoán)",
                       not any(d in ("concepts/dup.md", "entities/dup.md") and t == "supports"
                               for (_s, d, t, _e) in g2.edges)))
        checks.append(("dup.md vẫn KHÔNG orphan giả — stem_all vẫn thấy để CLI dùng path đủ",
                       "concepts/dup.md" in g2.relset and "entities/dup.md" in g2.relset))

    # (7) operationalizes_targets — suy quan hệ wiki→Protocol (skill/rule), KHÔNG khai tay
    repo_root = Path(__file__).resolve().parents[2]
    checks.append(("skill hợp lệ → sinh cạnh",
                   "skills/propose/SKILL.md" in operationalizes_targets("Xem `propose` để bắt đầu.", repo_root)))
    checks.append(("rule hợp lệ → sinh cạnh",
                   "rule:R7" in operationalizes_targets("Chặn bởi `R7`.", repo_root)))
    checks.append(("token không tồn tại → KHÔNG sinh cạnh",
                   operationalizes_targets("Xem `khong-ton-tai-gi-ca`.", repo_root) == []))
    checks.append(("đổi tham chiếu → cạnh đổi theo (SC-003, không cache sai)",
                   operationalizes_targets("Xem `plan` để bắt đầu.", repo_root)
                   == ["skills/plan/SKILL.md"]))

    for name, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    bad = [n for n, ok in checks if not ok]
    print("wiki-graph self-test:", "PASS" if not bad else f"FAIL ({len(bad)})")
    return 0 if not bad else 1


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
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())

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

    p = sub.add_parser("edge", parents=[common], help="tra một cạnh theo eid")
    p.add_argument("eid")

    p = sub.add_parser("cite", parents=[common], help="mọi cạnh chạm <page>, kèm eid")
    p.add_argument("page")

    p = sub.add_parser("export", parents=[common], help="xuất toàn đồ thị")
    p.add_argument("--format", choices=["json", "mermaid", "dot"], default="json")
    p.add_argument("--json", action="store_true", help="alias của --format json")

    args = ap.parse_args()

    wiki = Path(args.wiki_dir)
    if not wiki.is_dir():
        sys.stderr.write(f"[wiki-graph] wiki dir not found: {wiki} — fail-open (empty result)\n")
        _fail_open(args)
        sys.exit(0)

    g = build_graph(wiki)

    if args.cmd == "export":
        print(cmd_export(g, "json" if args.json else args.format))
        sys.exit(0)

    if args.cmd == "edge":
        sys.exit(cmd_edge(g, args.eid))

    if args.cmd == "cite":
        sys.exit(cmd_cite(g, args.page))

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
