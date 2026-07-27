#!/usr/bin/env python3
"""wiki-core v2 Bước 6: sinh wiki-graph WHITEBOARD — đồ thị quan hệ tự dàn, cho NGƯỜI xem.

Đọc 1+ wiki dir (frontmatter id/relations + ledger.jsonl + stale.json) → 1 file HTML
self-contained (0 request ngoài). Whiteboard: node tự dàn theo lực (force layout thuần JS,
không thư viện), kéo được, pan/zoom, tự fit vào màn hình; hover DÂY → tooltip tên quan hệ;
mặc định chỉ SÁNG wiki chính (primary), các wiki khác mờ đi.

Usage:
  build-wiki-graph.py <primary_wiki> [--also <other_wiki> ...] [-o out.html]
  # vd: build-wiki-graph.py llmwiki/wiki --also fdk/wiki   (mặc định sáng llmwiki, mờ fdk)
"""
import argparse
import ast
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# --- Mảnh A: bộ trích imports language-agnostic self-contained (vendored cạnh file này) ---
_ci_spec = importlib.util.spec_from_file_location("code_imports", Path(__file__).with_name("code_imports.py"))
code_imports = importlib.util.module_from_spec(_ci_spec)
try:
    _ci_spec.loader.exec_module(code_imports)
except Exception:
    code_imports = None   # fail-open: thiếu module → im lặng bỏ enrich imports đa-ngôn-ngữ

# --- Mảnh A2: TRÍCH WIKILINK dùng chung với harness/scripts/wiki-graph.py -------------
# Trước 2026-07-20 file này và wiki-graph.py trả lời CÙNG câu hỏi "cái gì link tới cái gì"
# bằng hai regex khác nhau, không chia sẻ dòng code nào — và LỆCH THẬT: 208 cạnh so với
# 164. Mỗi bên sai một kiểu: bên kia không bỏ code-fence (đếm cả [[...]] trong ví dụ
# code), bên này bỏ code-fence đúng nhưng bỏ sót [[trang#anchor]]. Không bên nào là tập
# cha của bên kia. Nay một nguồn chân lý: wikilink_targets() ở wiki-graph.py.
_wg = None
for _cand in (Path(__file__).resolve().parents[2] / "harness/scripts/wiki-graph.py",
              Path.home() / ".claude/harness/harness/scripts/wiki-graph.py"):
    if _cand.is_file():
        try:
            _s = importlib.util.spec_from_file_location("_wikigraph", _cand)
            _wg = importlib.util.module_from_spec(_s)
            _s.loader.exec_module(_wg)
            break
        except Exception:
            _wg = None   # fail-open: hỏng thì rơi về regex local bên dưới

# --- Mảnh B: bỏ code-fence + inline-code trước khi bắt [[wikilink]] (chống false-positive) ---
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_RE = re.compile(r"`[^`\n]*`")


def _strip_code(text: str) -> str:
    return _INLINE_RE.sub(" ", _FENCE_RE.sub(" ", text))


# --- Mảnh C: kiểm frontmatter YAML "hỏng" ở mức cấu trúc (self-contained, không cần lib yaml) ---
def _frontmatter_ok(fm: str) -> bool:
    """Cân bằng {} [] và số nháy chẵn trên mỗi dòng non-comment → phát hiện YAML hỏng thô."""
    if fm.count("{") != fm.count("}") or fm.count("[") != fm.count("]"):
        return False
    for ln in fm.splitlines():
        if ln.count('"') % 2 or ln.count("'") % 2:
            return False
    return True


def detect_cycles(nodes, edges, rels=("derives-from", "depends-on")):
    """DFS tìm chu trình trên cạnh rels; gắn cờ node + trả list các chu trình (theo id)."""
    id_of = {}
    for n in nodes:
        id_of[n["id"]] = n["id"]
    adj = {}
    for e in edges:
        if e["rel"] in rels:
            adj.setdefault(e["from"], []).append(e["to"])
    cycles, color, stack = [], {}, []

    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in adj.get(u, []):
            if color.get(v) == 1 and v in stack:
                i = stack.index(v)
                cycles.append(stack[i:] + [v])
            elif color.get(v, 0) == 0:
                dfs(v)
        stack.pop()
        color[u] = 2

    for n in list(adj.keys()):
        if color.get(n, 0) == 0:
            dfs(n)
    incycle = {x for c in cycles for x in c}
    for n in nodes:
        if n["id"] in incycle:
            n["in_cycle"] = True
    return cycles

CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)
LINE_RE = {k: re.compile(rf"^{k}[ \t]*:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE) for k in ("id", "type", "title")}
REL_RE = re.compile(r"\{[ \t]*rel[ \t]*:[ \t]*([\w-]+)[ \t]*,[ \t]*(to|path)[ \t]*:[ \t]*([^}\s]+)[ \t]*\}")
WIKILINK_RE = re.compile(r"\[\[([^\]\n|]+)\]\]")

REL_COLORS = {
    "derives-from": "#30b0c7", "depends-on": "#5856d6", "implements": "#34c759",
    "supersedes": "#ff9500", "touches": "#8e8e93", "contradicts": "#ff2d55",
    "imports": "#a0522d", "wikilink": "#9aa4b2",
}
REL_VI = {
    "derives-from": "chưng cất từ (nguồn gốc)", "depends-on": "phụ thuộc vào",
    "implements": "hiện thực (quyết định/ADR)", "supersedes": "thay thế (bản cũ)",
    "touches": "chạm file code", "contradicts": "mâu thuẫn với",
    "imports": "code import code", "wikilink": "liên quan mềm (wikilink trong thân bài)",
}


def scan(wiki: Path, tag: str, nodes, edges, ledger, stale, repo_root=None):
    for d in CONTENT_DIRS:
        base = wiki / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name in {"README.md", "_template.md"}:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            m = FRONTMATTER_RE.match(text)
            fm = m.group(1) if m else ""
            get = lambda k: (LINE_RE[k].search(fm).group(1).strip().strip("'\"") if LINE_RE[k].search(fm) else "")
            pid = get("id") or p.stem
            node = {"id": pid, "path": p.relative_to(wiki).as_posix(), "group": d,
                    "type": get("type") or "?", "title": get("title")[:90], "wiki": tag}
            # Mảnh C: frontmatter hỏng → quarantine, KHÔNG sinh cạnh từ nó (không crash, không bịa)
            if fm and not _frontmatter_ok(fm):
                node["quarantined"] = True
                nodes.append(node)
                continue
            nodes.append(node)
            for rel, kind, tgt in REL_RE.findall(fm):
                edges.append({"from": pid, "rel": rel, "to": tgt, "kind": kind})
            typed_to = {t for _, _, t in REL_RE.findall(fm)}
            raw_body = text[m.end():] if m else text

            # `touches` SUY RA SỐNG, không đọc từ frontmatter đã dập sẵn.
            # Trước đây quan hệ concept→code do wiki-relations.py dập một lần rồi đóng
            # băng ở 21 cạnh (0,8% tổng) — trong khi đây là cầu nối DUY NHẤT giữa hai
            # thế giới (code-graph chỉ biết code↔code, wiki-link chỉ biết wiki↔wiki).
            # Suy lại mỗi lần dựng thì nó không bao giờ cũ, đúng cơ chế của wikilink.
            # Frontmatter vẫn thắng: path đã khai tay thì không nhân đôi.
            if _wg is not None and repo_root:
                for cp in _wg.touches_targets(raw_body, repo_root):
                    if cp not in typed_to:
                        typed_to.add(cp)
                        edges.append({"from": pid, "rel": "touches", "to": cp, "kind": "path"})
            # Nguồn chung nếu nạp được; regex local chỉ là lưới đỡ khi thiếu harness.
            if _wg is not None:
                targets = _wg.wikilink_targets(raw_body)
            else:
                targets = [w.strip() for w in dict.fromkeys(
                    WIKILINK_RE.findall(_strip_code(raw_body)))]
            for w in targets:
                if w and w != pid and w not in typed_to:
                    edges.append({"from": pid, "rel": "wikilink", "to": w, "kind": "to"})
    lp = wiki / "ledger.jsonl"
    if lp.exists():
        for ln in lp.read_text(encoding="utf-8").splitlines()[-300:]:
            try:
                ev = json.loads(ln); ev["wiki"] = tag; ledger.append(ev)
            except ValueError:
                pass
    sp = wiki / "stale.json"
    if sp.exists():
        try:
            for k, v in json.loads(sp.read_text(encoding="utf-8")).items():
                stale[f"{tag}/{k}"] = v
        except ValueError:
            pass


def _layout(nodes, adj, W=1680, H=1080, iters=340):
    """Force layout tất định (port từ bản JS) — bake toạ độ vào HTML tĩnh."""
    import math
    seed = [1337]
    def rnd():
        seed[0] = (seed[0] * 1103515245 + 12345) & 0x7fffffff
        return seed[0] / 0x7fffffff
    for n in nodes:
        n["x"] = W / 2 + (rnd() - .5) * 900
        n["y"] = H / 2 + (rnd() - .5) * 600
        n["vx"] = n["vy"] = 0.0
    by = {n["id"]: n for n in nodes}
    K = 108
    for it in range(iters):
        t = 1 - it / iters
        for i in range(len(nodes)):
            a = nodes[i]
            for j in range(i + 1, len(nodes)):
                b = nodes[j]
                dx, dy = a["x"] - b["x"], a["y"] - b["y"]
                d = math.hypot(dx, dy) or .1
                f = (K * K) / d / d * 10
                a["vx"] += dx / d * f; a["vy"] += dy / d * f
                b["vx"] -= dx / d * f; b["vy"] -= dy / d * f
            a["vx"] += (W / 2 - a["x"]) * .012; a["vy"] += (H / 2 - a["y"]) * .012
        for e in adj:
            a, b = by[e["from"]], by[e["to"]]
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]
            d = math.hypot(dx, dy) or .1
            f = (d - K) * .05
            a["vx"] += dx / d * f; a["vy"] += dy / d * f
            b["vx"] -= dx / d * f; b["vy"] -= dy / d * f
        for n in nodes:
            n["x"] += max(-30, min(30, n["vx"] * t)); n["y"] += max(-30, min(30, n["vy"] * t))
            n["vx"] *= .85; n["vy"] *= .85
    # fit vào canvas với padding
    xs = [n["x"] for n in nodes]; ys = [n["y"] for n in nodes]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = 70
    sx = (W - 2 * pad) / max(1, maxx - minx); sy = (H - 2 * pad) / max(1, maxy - miny)
    s = min(sx, sy)
    for n in nodes:
        n["px"] = pad + (n["x"] - minx) * s
        n["py"] = pad + (n["y"] - miny) * s
    return W, H


def build_static(primary: str, out_abs: str, nodes, edges, ledger, stale):
    """Bản HTML/CSS THUẦN — 0 <script>. Vị trí bake sẵn; hover + lọc bằng CSS :has()."""
    import html as _h
    ids = {n["id"] for n in nodes}
    # khử trùng id, đánh index
    seen = {}; uniq = []
    for n in nodes:
        if n["id"] not in seen:
            seen[n["id"]] = len(uniq); uniq.append(n)
    nodes = uniq; idx = seen
    adj = [e for e in edges if e["from"] in idx and e["to"] in idx and e["from"] != e["to"]]
    CW, CH = _layout(nodes, adj)
    nb = {i: set() for i in range(len(nodes))}
    for e in adj:
        fi, ti = idx[e["from"]], idx[e["to"]]
        nb[fi].add(ti); nb[ti].add(fi)
    # SVG cạnh
    paths = []
    for e in adj:
        a, b = nodes[idx[e["from"]]], nodes[idx[e["to"]]]
        fi, ti = idx[e["from"]], idx[e["to"]]
        dx = (b["px"] - a["px"]) * .3
        d = f'M{a["px"]:.0f} {a["py"]:.0f} C{a["px"]+dx:.0f} {a["py"]:.0f} {b["px"]-dx:.0f} {b["py"]:.0f} {b["px"]:.0f} {b["py"]:.0f}'
        soft = " soft" if e["rel"] == "wikilink" else ""
        col = REL_COLORS.get(e["rel"], "#9aa4b2")
        tip = f'{e["rel"]} — {REL_VI.get(e["rel"], "")}\n{e["from"]} → {e["to"]}'
        paths.append(f'<path class="rel-{e["rel"]} n{fi} n{ti}{soft}" style="stroke:{col}" d="{d}">'
                     f'<title>{_h.escape(tip)}</title></path>')
    # node DOM
    ndoms = []
    for i, n in enumerate(nodes):
        flags = ""
        if stale.get(f'{n["wiki"]}/{n["path"]}'):
            flags += '<span class="flag s">S</span>'
        if n["type"] == "tombstone":
            flags += '<span class="flag t">T</span>'
        cls = "nd" + (" code" if n["wiki"] == "code" else (" other" if n["wiki"] != primary else ""))
        ndoms.append(f'<div id="n{i}" class="{cls}" style="left:{n["px"]:.0f}px;top:{n["py"]:.0f}px" '
                     f'title="{_h.escape(n["wiki"]+"/"+n["path"])}">{_h.escape(n.get("label") or n["id"])}{flags}</div>')
    # CSS hover per-node (:has) — dim tất cả, sáng node hover + hàng xóm + dây của nó
    hov = []
    for i in range(len(nodes)):
        lit = ",".join(f'.wb:has(#n{i}:hover) #n{j}' for j in ([i] + sorted(nb[i])))
        hov.append(lit + "{opacity:1;z-index:5}")
        hov.append(f'.wb:has(#n{i}:hover) path.n{i}{{opacity:.95;stroke-width:3}}')
    hover_css = "\n".join(hov)
    # CSS lọc quan hệ (:has trên checkbox)
    rel_count = {}
    for e in adj:
        rel_count[e["rel"]] = rel_count.get(e["rel"], 0) + 1
    filt_rows = "".join(
        f'<label class="lg"><input type="checkbox" class="filt" id="f-{r}">'
        f'<span style="color:{c}">●</span> {REL_VI[r]} ({rel_count.get(r,0)})</label>' for r, c in REL_COLORS.items())
    filt_css = "\n".join(
        f'.page:has(#f-{r}:checked) path.rel-{r}{{display:inline}}' for r in REL_COLORS)
    return f"""<!DOCTYPE html><html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>wiki-graph (HTML thuần)</title>
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
<style>
:root{{--ink:#0f0f12;--ink2:#4a4a55;--border:rgba(30,90,170,.16)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue','Roboto','Segoe UI',sans-serif;
color:var(--ink);background:linear-gradient(180deg,#f7fbff,#eaf2fd);padding:14px}}
.bar{{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-bottom:10px}}
.bar h1{{font-size:15px;color:#1d1d1f}} .bar .hint{{font-size:11.5px;color:var(--ink2);opacity:.8}}
.lg{{display:inline-flex;gap:5px;align-items:center;font-size:11.5px;color:var(--ink2);cursor:pointer}}
.lg input{{cursor:pointer}}
.page{{position:relative}}
.wb{{position:relative;width:{CW}px;height:{CH}px;margin:0 auto;overflow:hidden;
background:radial-gradient(600px 400px at 30% 20%,rgba(10,132,255,.06),transparent 60%),rgba(255,255,255,.35);
border:1px solid var(--border);border-radius:16px}}
svg{{position:absolute;inset:0;width:100%;height:100%;overflow:visible}}
path{{fill:none;stroke-width:2;opacity:.3;stroke-linecap:round}}
path.soft{{display:none;stroke-dasharray:5 5;opacity:.25}}   /* wikilink ẩn cho tới khi tick lọc */
.page:has(#f-wikilink:checked) path.soft{{display:inline}}
.nd{{position:absolute;transform:translate(-50%,-50%);padding:5px 10px;border-radius:11px;white-space:nowrap;
font-size:12px;font-weight:600;background:rgba(255,255,255,.94);border:1px solid var(--border);
box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 3px 12px rgba(20,40,90,.1);transition:opacity .15s;cursor:default}}
.nd.other{{background:rgba(240,244,252,.9);opacity:.4}}   /* wiki phụ mờ sẵn */
.nd.code{{background:rgba(30,32,40,.9);color:#cfe3fb;font-family:'SF Mono',ui-monospace,Menlo,monospace;font-size:11px;border-color:rgba(120,140,180,.4);opacity:.5}}
.nd .flag{{font-size:9px;font-weight:800;border-radius:999px;padding:0 5px;margin-left:4px}}
.nd .s{{background:rgba(255,149,0,.16);color:#f08c00}} .nd .t{{background:rgba(0,0,0,.08);color:#4a4a55}}
/* hover bất kỳ node → mờ hết, chỉ sáng node đó + hàng xóm + dây của nó */
.wb:has(.nd:hover) .nd{{opacity:.14}}
.wb:has(.nd:hover) path{{opacity:.05}}
{hover_css}
{filt_css}
.legend{{margin-top:8px;font-size:10.5px;color:var(--ink2)}}
.foot{{margin-top:8px;font-size:10px;color:var(--ink2);opacity:.7}}
.foot code{{font-family:'SF Mono',ui-monospace,Menlo,monospace}}
</style></head><body>
<div class="page">
<div class="bar"><h1>🗺️ wiki-graph <span style="font-weight:400;font-size:12px;color:#4a4a55">(HTML thuần — 0 JavaScript)</span></h1>
<span class="hint">Rê chuột lên node = sáng quan hệ của nó · hover dây = tên quan hệ · tick lọc:</span>
{filt_rows}</div>
<div class="wb"><svg viewBox="0 0 {CW} {CH}">{''.join(paths)}</svg>{''.join(ndoms)}</div>
<div class="legend">sáng = wiki chính (<b>{primary}</b>) · mờ = wiki phụ · S stale · T tombstone · dây wikilink ẩn cho tới khi tick lọc</div>
<div class="foot"><code>{out_abs}</code></div>
</div></body></html>"""


def _mk_code_node(path):
    return {"id": path, "path": path, "group": "code", "type": "code",
            "title": path, "wiki": "code", "label": path.rsplit("/", 1)[-1]}


def add_code_nodes(nodes, edges):
    """Thêm node lá cho target của quan hệ `touches` (đường dẫn code) để cạnh wiki→code hiện ra."""
    ids = {n["id"] for n in nodes}
    seen = set()
    for e in edges:
        if e.get("kind") == "path" and e["to"] not in ids and e["to"] not in seen:
            seen.add(e["to"])
            nodes.append(_mk_code_node(e["to"]))


def _py_facts(abs_path):
    """(symbols top-level, tập module import) của 1 file .py — parse bằng ast, fail-open."""
    try:
        tree = ast.parse(Path(abs_path).read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return [], set()
    syms = [n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    return syms, mods


def enrich_code(nodes, edges, repo_root):
    """Opt 1 (imports) + Opt 3 (symbols/commit) cho node code — thuần ast, không cần code-graph MCP.

    - imports: file .py touches → cạnh `imports` tới file .py khác trong repo (1 hop).
    - làm giàu: mỗi node code gắn symbols (def/class) + commit gần nhất.
    """
    root = Path(repo_root)
    # index module-name → relpath (Python/Go/Rust). GH#43: index CẢ basename (import phẳng) LẪN
    # dotted-path-from-root (import qualified theo package: `from app.core import` → app/core.py) +
    # key package cho __init__.py (`import app` → app/__init__.py). setdefault: file quét trước thắng.
    modindex = {}
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if any(seg in rel for seg in (".git/", "node_modules/", ".overstack-kit/", "workspaces/")):
            continue
        modindex.setdefault(p.stem, rel)                       # basename: from store import
        modindex.setdefault(rel[:-3].replace("/", "."), rel)   # dotted-from-root: app.core → app/core.py
        if p.name == "__init__.py":                            # package: app → app/__init__.py
            pkg = rel[: -len("/__init__.py")].replace("/", ".")
            if pkg:
                modindex.setdefault(pkg, rel)
    tsp = code_imports.load_tsconfig_paths(root) if code_imports else {}
    ids = {n["id"] for n in nodes}
    # 1 hop: từ node code (BẤT KỲ ngôn ngữ hỗ trợ) → cạnh imports + node code mới
    for cn in [n for n in nodes if n["wiki"] == "code"]:
        ap = root / cn["path"]
        if not ap.exists() or not code_imports:
            continue
        info = code_imports.extract(str(ap), str(root), tsp)
        targets = list(info.get("resolved", []))                 # TS/JS đã resolve về path
        for m in info.get("_modspecs", []):                       # Python/Go/Rust: resolve qua modindex
            t = modindex.get(m if isinstance(m, str) else "")
            if t:
                targets.append(t)
        for tgt in targets:
            if tgt and tgt != cn["path"]:
                if tgt not in ids:
                    nodes.append(_mk_code_node(tgt)); ids.add(tgt)
                edges.append({"from": cn["path"], "rel": "imports", "to": tgt, "kind": "to"})
    # làm giàu MỌI node code hiện có (gồm cả mới thêm)
    for cn in [n for n in nodes if n["wiki"] == "code"]:
        ap = root / cn["path"]
        if code_imports and ap.exists():
            cn["symbols"] = code_imports.extract(str(ap), str(root), tsp).get("symbols", [])[:20]
        try:
            r = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%h %s", "--", cn["path"]],
                               capture_output=True, text=True, timeout=5)
            cn["commit"] = r.stdout.strip()[:80]
        except Exception:
            pass


def impact_reverse(target, edges, rel="imports", cap=1):
    """Mảnh D: sửa `target` → tập bị ảnh hưởng = trang/file TRỎ TỚI target qua `rel`,
    lan ĐÚNG cap bước (mặc định 1 — cùng kỷ luật cap=1 của propagate_stale, chống storm/chu trình).
    Đây là impact trên import-graph (reverse-imports) — self-contained, không hook/tool ngoài."""
    rev = {}
    for e in edges:
        if e["rel"] == rel:
            rev.setdefault(e["to"], set()).add(e["from"])
    seen, frontier = set(), {target}
    for _ in range(cap):
        nxt = set()
        for t in frontier:
            nxt |= rev.get(t, set())
        nxt -= seen | {target}
        seen |= nxt
        frontier = nxt
    return sorted(seen)


def build_html(primary: str, out_abs: str, nodes, edges, ledger, stale):
    # chỉ giữ cạnh nối 2 node THẬT (bỏ touches→code path, và target không phải node)
    ids = {n["id"] for n in nodes}
    real_edges = [e for e in edges if e["from"] in ids and e["to"] in ids and e["from"] != e["to"]]
    ledger.sort(key=lambda l: l.get("ts", ""), reverse=True)
    data = json.dumps({"nodes": nodes, "edges": real_edges, "ledger": ledger[:200],
                       "stale": stale, "relColors": REL_COLORS, "relVi": REL_VI,
                       "primary": primary}, ensure_ascii=False)
    n_typed = sum(1 for e in real_edges if e["rel"] != "wikilink")
    rel_count = {}
    for e in real_edges:
        rel_count[e["rel"]] = rel_count.get(e["rel"], 0) + 1
    legend = "".join(
        f'<label class="lg{" zero" if rel_count.get(r,0)==0 else ""}" data-rel="{r}">'
        f'<input type="checkbox"><span style="color:{c}">●</span> {REL_VI[r]}'
        f'<span class="cnt">{rel_count.get(r,0)}</span></label>'
        for r, c in REL_COLORS.items())
    wikis = sorted({n["wiki"] for n in nodes})
    return f"""<!DOCTYPE html><html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>wiki-graph whiteboard</title>
<meta name="description" content="Whiteboard đồ thị quan hệ wiki-core v2 — node tự dàn, hover dây xem quan hệ.">
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
<style>
:root{{--ink:#0f0f12;--ink2:#4a4a55;--border:rgba(30,90,170,.16)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue','Roboto','Segoe UI',sans-serif;
color:var(--ink);display:flex;flex-direction:column;height:100vh;overflow:hidden;
background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.10),transparent 60%),
radial-gradient(700px 420px at 95% 15%,rgba(88,86,214,.08),transparent 55%),
linear-gradient(180deg,#f7fbff 0%,#eaf2fd 100%)}}
.bar{{flex:none;padding:12px 18px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;
background:rgba(255,255,255,.6);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}}
.bar h1{{font-size:15px;letter-spacing:-.02em;color:#1d1d1f;margin-right:6px}}
#q{{flex:1;min-width:220px;max-width:420px;padding:7px 12px;border-radius:10px;border:1px solid var(--border);
font-size:13px;background:rgba(255,255,255,.85);color:var(--ink)}}
#q:focus{{outline:none;border-color:#0a84ff;box-shadow:0 0 0 3px rgba(10,132,255,.15)}}
.bar label{{font-size:12px;color:var(--ink2);cursor:pointer;user-select:none;display:flex;gap:4px;align-items:center}}
.bar .sp{{flex:1}} .bar .hint{{font-size:11.5px;color:var(--ink2);opacity:.8}}
.btn{{font-size:12px;padding:6px 12px;border-radius:9px;border:1px solid var(--border);
background:rgba(255,255,255,.85);cursor:pointer;color:var(--ink2)}} .btn:hover{{color:#0a84ff}}
#stage{{flex:1;position:relative;overflow:hidden;cursor:grab}} #stage.grab{{cursor:grabbing}}
#world{{position:absolute;top:0;left:0;transform-origin:0 0}}
#edges{{position:absolute;top:0;left:0;overflow:visible;pointer-events:none}}
#edges path{{fill:none;stroke-width:2;pointer-events:stroke;cursor:help}}
#edges path.soft{{stroke-dasharray:5 5;opacity:.4}}
.nd{{position:absolute;transform:translate(-50%,-50%);padding:6px 11px;border-radius:12px;white-space:nowrap;
font-size:12px;font-weight:600;letter-spacing:-.01em;cursor:grab;user-select:none;
background:rgba(255,255,255,.92);border:1px solid var(--border);
box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 3px 12px rgba(20,40,90,.1);
transition:left .38s cubic-bezier(.4,0,.2,1),top .38s cubic-bezier(.4,0,.2,1),opacity .18s}}
.nd:active{{cursor:grabbing}}
.nd .flag{{font-size:9px;font-weight:800;border-radius:999px;padding:0 5px;margin-left:5px}}
.nd .s{{background:rgba(255,149,0,.16);color:#f08c00}} .nd .t{{background:rgba(0,0,0,.08);color:#4a4a55}}
.nd.dim{{opacity:.16}} .nd.hidden{{display:none}}
.nd.hot{{border-color:#0a84ff;box-shadow:0 0 0 2px rgba(10,132,255,.32);z-index:5}}
.nd.match{{border-color:#0a84ff}}
.nd.wiki-fdk{{background:rgba(240,244,252,.9)}}  /* wiki phụ tông xám lạnh hơn */
.nd.wiki-code{{background:rgba(30,32,40,.9);color:#cfe3fb;font-family:'SF Mono',ui-monospace,Menlo,monospace;font-size:11px;font-weight:500;border-color:rgba(120,140,180,.4)}}
#ac{{position:fixed;z-index:60;background:rgba(255,255,255,.98);border:1px solid var(--border);
border-radius:10px;box-shadow:0 8px 28px rgba(20,40,90,.18);max-height:320px;overflow-y:auto;
min-width:280px;display:none}}
#ac.on{{display:block}}
#ac .it{{padding:7px 12px;font-size:12.5px;cursor:pointer;border-bottom:1px solid rgba(30,90,170,.06);display:flex;gap:8px;align-items:baseline}}
#ac .it:last-child{{border-bottom:none}}
#ac .it:hover,#ac .it.sel{{background:rgba(10,132,255,.1)}}
#ac .it b{{color:var(--ink);font-weight:600}} #ac .it .p{{color:var(--ink2);font-size:10.5px;opacity:.8}}
#ac .it .w{{margin-left:auto;font-size:9.5px;color:var(--ink2);opacity:.7;border:1px solid var(--border);border-radius:6px;padding:0 5px}}
#tip{{position:fixed;z-index:50;pointer-events:none;opacity:0;transition:opacity .1s;
background:rgba(20,28,45,.94);color:#fff;font-size:12px;padding:6px 10px;border-radius:8px;
box-shadow:0 4px 16px rgba(0,0,0,.25);max-width:280px}}
#tip b{{color:#7fc0ff}}
#detail{{position:absolute;left:14px;bottom:14px;max-width:min(560px,60vw);z-index:6;
font-size:12px;color:var(--ink2);background:rgba(255,255,255,.9);backdrop-filter:blur(8px);
border:1px solid var(--border);border-radius:12px;padding:11px 14px;
box-shadow:0 4px 20px rgba(20,40,90,.1);opacity:0;transition:opacity .15s}}
#detail.on{{opacity:1}} #detail b{{color:var(--ink)}}
#detail code,.legend code{{font-family:'SF Mono',ui-monospace,Menlo,monospace;font-size:.92em;
background:rgba(10,132,255,.07);border:1px solid rgba(10,132,255,.1);border-radius:5px;padding:0 4px}}
.legend{{position:absolute;right:14px;top:12px;z-index:6;font-size:10.5px;color:var(--ink2);
background:rgba(255,255,255,.9);border:1px solid var(--border);border-radius:10px;padding:8px 11px;max-width:236px;line-height:1.6}}
.legend .lg{{display:flex;gap:6px;align-items:center;cursor:pointer;padding:2px 0;user-select:none}}
.legend .lg input{{margin:0;cursor:pointer}} .legend .lg:hover{{color:var(--ink)}}
.legend .lg .cnt{{margin-left:auto;font-variant-numeric:tabular-nums;font-size:10px;font-weight:700;
color:var(--ink2);background:rgba(30,90,170,.08);border-radius:999px;padding:0 6px;min-width:20px;text-align:center}}
.legend .lg.zero{{opacity:.4}} .legend .lg.zero .cnt{{background:transparent}}
.legend .lgfoot{{margin-top:6px;padding-top:6px;border-top:1px solid rgba(30,90,170,.1)}}
.foot{{position:absolute;right:14px;bottom:12px;z-index:6;font-size:10px;color:var(--ink2);opacity:.7}}
.foot code{{font-family:'SF Mono',ui-monospace,Menlo,monospace}}
@media(prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style></head><body>
<div class="bar">
  <h1>🗺️ wiki-graph</h1>
  <input type="search" id="q" placeholder="🔎 gõ tên file → Enter chọn, chỉ hiện quan hệ của nó" autocomplete="off">
  <label><input type="checkbox" id="showOther"> hiện cả wiki phụ (đang mờ)</label>
  <label><input type="checkbox" id="showSoft"> kèm dây wikilink mềm</label>
  <span class="sp"></span>
  <button class="btn" id="fit">⤢ fit màn hình</button>
  <span class="hint" id="hint"></span>
</div>
<div id="stage">
  <div id="world"><svg id="edges"></svg></div>
  <div class="legend"><b>Lọc theo quan hệ</b> <span style="opacity:.7">(tick để chỉ hiện loại đó)</span>{legend}<div class="lgfoot"><span style="color:#f08c00">S</span> stale · <span style="color:#4a4a55">T</span> tombstone · <b>sáng</b>=wiki chính, <b style="opacity:.4">mờ</b>=wiki phụ</div></div>
  <div id="detail"></div>
  <div class="foot"><code>{out_abs}</code></div>
</div>
<div id="tip"></div>
<div id="ac"></div>
<script type="application/json" id="data">{data}</script>
<script>
(function(){{
var D=JSON.parse(document.getElementById('data').textContent);
var PRIMARY=D.primary, byId={{}};
D.nodes=D.nodes.filter(function(n){{if(byId[n.id])return false;byId[n.id]=n;return true;}}); // khử trùng id
var stage=document.getElementById('stage'),world=document.getElementById('world'),
    svg=document.getElementById('edges'),tip=document.getElementById('tip'),
    detail=document.getElementById('detail'),hint=document.getElementById('hint'),
    showOther=document.getElementById('showOther'),showSoft=document.getElementById('showSoft');
var W=2200,H=1500;  // toạ độ thế giới (world)
// ---- force layout thuần JS (seed cố định → bố cục ổn định giữa các lần build) ----
var seed=1337; function rnd(){{seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;}}
D.nodes.forEach(function(n){{n.x=W/2+(rnd()-.5)*900;n.y=H/2+(rnd()-.5)*600;n.vx=0;n.vy=0;}});
var adj=D.edges.filter(function(e){{return byId[e.from]&&byId[e.to];}});
var K=108;
for(var it=0;it<320;it++){{
  var t=1-it/320;
  for(var i=0;i<D.nodes.length;i++){{var a=D.nodes[i];
    for(var j=i+1;j<D.nodes.length;j++){{var b=D.nodes[j];
      var dx=a.x-b.x,dy=a.y-b.y,d=Math.sqrt(dx*dx+dy*dy)||.1;
      var f=(K*K)/d/d*10; a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}}
    // trọng lực về tâm (mạnh hơn → cụm gom chặt, fit zoom gần hơn)
    a.vx+=(W/2-a.x)*.012; a.vy+=(H/2-a.y)*.012;}}
  adj.forEach(function(e){{var a=byId[e.from],b=byId[e.to];
    var dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||.1;
    var f=(d-K)*.05; a.vx+=dx/d*f;a.vy+=dy/d*f;b.vx-=dx/d*f;b.vy-=dy/d*f;}});
  D.nodes.forEach(function(n){{n.x+=Math.max(-30,Math.min(30,n.vx*t));n.y+=Math.max(-30,Math.min(30,n.vy*t));n.vx*=.85;n.vy*=.85;}});
}}
svg.setAttribute('width',W);svg.setAttribute('height',H);svg.setAttribute('viewBox','0 0 '+W+' '+H);
world.style.width=W+'px';world.style.height=H+'px';
// ---- tạo node DOM ----
D.nodes.forEach(function(n){{
  var el=document.createElement('div');el.className='nd wiki-'+n.wiki;el.style.left=n.x+'px';el.style.top=n.y+'px';
  var flags=''; if(D.stale[n.wiki+'/'+n.path])flags+='<span class="flag s">S</span>';
  if(n.type==='tombstone')flags+='<span class="flag t">T</span>';
  el.innerHTML=(n.label||n.id)+flags;
  world.appendChild(el); n._el=el; n.hx=n.x; n.hy=n.y;  // hx/hy = vị trí gốc (để trả về khi bỏ chọn)
}});
function place(n,x,y){{n.x=x;n.y=y;n._el.style.left=x+'px';n._el.style.top=y+'px';}}
// ---- vẽ cạnh ----
var paths=[];
adj.forEach(function(e){{var a=byId[e.from],b=byId[e.to];
  var p=document.createElementNS('http://www.w3.org/2000/svg','path');
  p.setAttribute('stroke',D.relColors[e.rel]||'#9aa4b2');
  if(e.rel==='wikilink')p.setAttribute('class','soft');
  p.addEventListener('mouseenter',function(ev){{showTip(ev,'<b>'+e.rel+'</b> — '+(D.relVi[e.rel]||'')+'<br>'+e.from+' → '+e.to);}});
  p.addEventListener('mousemove',moveTip);
  p.addEventListener('mouseleave',hideTip);
  svg.appendChild(p); e._p=p; paths.push(e);
}});
function edgePath(e){{var a=byId[e.from],b=byId[e.to];var dx=(b.x-a.x)*.3;
  e._p.setAttribute('d','M'+a.x+' '+a.y+' C'+(a.x+dx)+' '+a.y+' '+(b.x-dx)+' '+b.y+' '+b.x+' '+b.y);}}
function redraw(){{paths.forEach(function(e){{if(e._p.style.display!=='none')edgePath(e);}});}}
// ---- tooltip dây ----
function showTip(ev,html){{tip.innerHTML=html;tip.style.opacity='1';moveTip(ev);}}
function moveTip(ev){{tip.style.left=(ev.clientX+12)+'px';tip.style.top=(ev.clientY+12)+'px';}}
function hideTip(){{tip.style.opacity='0';}}
// ---- pan / zoom ----
var tx=0,ty=0,sc=1;
function apply(){{world.style.transform='translate('+tx+'px,'+ty+'px) scale('+sc+')';}}
function fit(nodesForFit){{
  var ns=nodesForFit&&nodesForFit.length?nodesForFit:D.nodes;
  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  ns.forEach(function(n){{minx=Math.min(minx,n.x);miny=Math.min(miny,n.y);maxx=Math.max(maxx,n.x);maxy=Math.max(maxy,n.y);}});
  var pad=60,bw=(maxx-minx)+pad*2,bh=(maxy-miny)+pad*2;
  var vw=stage.clientWidth,vh=stage.clientHeight;
  sc=Math.min(vw/bw,vh/bh,2.6); sc=Math.max(sc,.2);  // trần zoom cao → mở lên đã ở gần, chữ đọc được
  tx=(vw-(minx+maxx)*sc)/2; ty=(vh-(miny+maxy)*sc)/2; apply();
}}
stage.addEventListener('wheel',function(ev){{ev.preventDefault();
  var r=stage.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  var ns=Math.min(3,Math.max(.15,sc*(ev.deltaY<0?1.1:.9)));
  tx=mx-(mx-tx)*(ns/sc);ty=my-(my-ty)*(ns/sc);sc=ns;apply();}},{{passive:false}});
var pan=null;
stage.addEventListener('pointerdown',function(ev){{if(ev.target.closest('.nd,.legend,#detail'))return;  // đừng cướp click của UI (legend/panel)
  pan={{x:ev.clientX-tx,y:ev.clientY-ty}};stage.classList.add('grab');stage.setPointerCapture(ev.pointerId);}});
stage.addEventListener('pointermove',function(ev){{if(!pan)return;tx=ev.clientX-pan.x;ty=ev.clientY-pan.y;apply();}});
stage.addEventListener('pointerup',function(){{pan=null;stage.classList.remove('grab');}});
// ---- kéo node ----
var drag=null;
D.nodes.forEach(function(n){{n._el.addEventListener('pointerdown',function(ev){{
  ev.stopPropagation();drag={{n:n,sx:ev.clientX,sy:ev.clientY,ox:n.x,oy:n.y}};
  n._el.style.transition='none';n._el.setPointerCapture(ev.pointerId);}});
  n._el.addEventListener('pointermove',function(ev){{if(!drag||drag.n!==n)return;
    n.x=drag.ox+(ev.clientX-drag.sx)/sc;n.y=drag.oy+(ev.clientY-drag.sy)/sc;
    n._el.style.left=n.x+'px';n._el.style.top=n.y+'px';redraw();}});
  n._el.addEventListener('pointerup',function(){{drag=null;n._el.style.transition='';}});
  // hover thẻ = xem trước dây quan hệ + node liên quan (chưa click); + tooltip quan hệ với node đang chọn
  n._el.addEventListener('mouseenter',function(ev){{
    if(!sel&&!drag){{hover=n;refresh();}}
    showTip(ev, nodeTipHtml(n));}});
  n._el.addEventListener('mousemove',moveTip);
  n._el.addEventListener('mouseleave',function(){{if(!sel&&hover===n){{hover=null;refresh();}}hideTip();}});
  // click nhẹ = chỉ sáng + panel (KHÔNG zoom); double-click = hút vệ tinh + fit
  n._el.addEventListener('click',function(ev){{ev.stopPropagation();
    clearTimeout(n._ct);n._ct=setTimeout(function(){{onClick(n);}},230);}});
  n._el.addEventListener('dblclick',function(ev){{ev.stopPropagation();
    clearTimeout(n._ct);onDbl(n);}});
}});
// ---- focus 1 node: chỉ node + hàng xóm sáng, còn lại mờ ----
var sel=null,hover=null;
function neighbors(id){{var s={{}};s[id]=1;adj.forEach(function(e){{if(e.from===id)s[e.to]=1;if(e.to===id)s[e.from]=1;}});return s;}}
function nodeTipHtml(n){{
  var base='<b>'+n.id+'</b><br>'+n.wiki+'/'+n.path;
  if(sel&&sel!==n){{                          // đang chọn 1 node → nói rõ quan hệ giữa 2 cái
    var rels=[];
    adj.forEach(function(e){{
      if(e.from===sel.id&&e.to===n.id)rels.push((D.relVi[e.rel]||e.rel)+' → (chiều: '+sel.id+' trỏ tới đây)');
      if(e.to===sel.id&&e.from===n.id)rels.push((D.relVi[e.rel]||e.rel)+' ← (chiều: đây trỏ tới '+sel.id+')');}});
    base += rels.length
      ? '<br><span style="color:#7fc0ff">với <b>'+sel.id+'</b>: '+rels.join('; ')+'</span>'
      : '<br><span style="opacity:.7">không nối trực tiếp với '+sel.id+'</span>';
  }}
  return base;
}}
function baseVisible(n){{return showOther.checked || n.wiki===PRIMARY;}}
var relFilter={{}};                            // lọc theo loại quan hệ (tick trong legend)
function relActive(){{for(var k in relFilter)if(relFilter[k])return true;return false;}}
function refresh(){{
  var focus=sel||hover, s=focus?neighbors(focus.id):null, active=relActive(), lit={{}};
  // dây: quyết định hiện/ẩn rồi thu node được "thắp sáng"
  paths.forEach(function(e){{
    var soft=(e.rel==='wikilink');
    var show = active ? !!relFilter[e.rel] : (showSoft.checked||!soft);   // có lọc → chỉ loại được tick
    if(focus) show = show && (e.from===focus.id||e.to===focus.id);
    else if(!active) show = show && (baseVisible(byId[e.from])&&baseVisible(byId[e.to]));  // lọc thì bỏ ràng buộc wiki chính/phụ
    e._p.style.display=show?'':'none'; if(show){{edgePath(e);lit[e.from]=1;lit[e.to]=1;}}
  }});
  // node: mờ nếu không nằm trong tiêu điểm / không dính dây nào đang hiện
  D.nodes.forEach(function(n){{if(!n._el)return;
    var dim = focus ? !s[n.id] : (active ? !lit[n.id] : !baseVisible(n));
    n._el.classList.toggle('dim', dim);
    n._el.classList.toggle('hot', !!focus && n.id===focus.id);
  }});
}}
function pullSatellites(n){{
  // hút các node quan hệ quây quanh n theo vòng tròn, node chính đứng yên
  var nb=Object.keys(neighbors(n.id)).filter(function(id){{return id!==n.id&&byId[id];}}).map(function(id){{return byId[id];}});
  var R=Math.max(150,nb.length*20), cx=n.x, cy=n.y;
  nb.forEach(function(m,i){{var a=(i/nb.length)*Math.PI*2 - Math.PI/2;
    place(m, cx+Math.cos(a)*R, cy+Math.sin(a)*R);}});
  redraw();
  setTimeout(function(){{fit([n].concat(nb));}},60);  // đợi transition khởi động rồi fit vào cụm (có padding)
}}
function restoreHome(){{D.nodes.forEach(function(m){{if(m._el)place(m,m.hx,m.hy);}});redraw();}}
var pulled=false;
function showDetail(n){{
  var out=adj.filter(function(e){{return e.from===n.id;}}),inn=adj.filter(function(e){{return e.to===n.id;}});
  var ev=D.ledger.filter(function(l){{return l.target===n.path&&l.wiki===n.wiki;}}).slice(0,4);
  var st=D.stale[n.wiki+'/'+n.path];
  var h='<b>'+(n.label||n.id)+'</b> <code>'+n.wiki+'/'+n.path+'</code> · '+n.type+'  <span style="opacity:.6">(double-click để hút vệ tinh + zoom)</span>';
  if(st)h+=' · <b style="color:#f08c00">STALE</b> (do <code>'+st.by+'</code> '+st.action+')';
  if(n.commit)h+='<br><span style="opacity:.75">commit:</span> <code>'+n.commit+'</code>';
  if(n.symbols&&n.symbols.length)h+='<br><span style="opacity:.75">symbols ('+n.symbols.length+'):</span> '+n.symbols.map(function(s){{return '<code>'+s+'</code>';}}).join(' ');
  h+='<br>→ trỏ đi: '+(out.map(function(e){{return e.rel+' <code>'+e.to+'</code>';}}).join(' · ')||'(không)');
  h+='<br>← được trỏ tới: '+(inn.map(function(e){{return '<code>'+e.from+'</code> '+e.rel;}}).join(' · ')||'(không)');
  if(ev.length)h+='<br>ledger: '+ev.map(function(l){{return l.ts+' '+l.action;}}).join(' · ');
  detail.innerHTML=h;detail.classList.add('on');
}}
function clearSel(){{sel=null;detail.classList.remove('on');
  if(pulled){{restoreHome();pulled=false;refresh();setTimeout(fitPrimary,60);}}else refresh();}}
function onClick(n){{                       // click nhẹ: chỉ sáng + panel, KHÔNG zoom
  if(sel===n&&!pulled){{clearSel();return;}}
  if(pulled){{restoreHome();pulled=false;}}
  sel=n; showDetail(n); refresh();
}}
function onDbl(n){{                          // double-click: hút vệ tinh + fit
  if(pulled&&sel===n){{clearSel();return;}}
  if(pulled)restoreHome();
  sel=n; showDetail(n); refresh(); pullSatellites(n); pulled=true;
}}
function select(n){{onClick(n);}}  // giữ tương thích search (Enter chọn)
// ---- search ----
var q=document.getElementById('q'),ac=document.getElementById('ac'),acItems=[],acIdx=-1;
function positionAc(){{var r=q.getBoundingClientRect();ac.style.left=r.left+'px';ac.style.top=(r.bottom+4)+'px';ac.style.minWidth=r.width+'px';}}
function pick(nd){{ac.classList.remove('on');q.value=nd.id;onDbl(nd);}}
function renderAc(){{
  ac.innerHTML=acItems.map(function(nd,i){{
    return '<div class="it'+(i===acIdx?' sel':'')+'" data-i="'+i+'"><b>'+nd.id+'</b> <span class="p">'+nd.wiki+'/'+nd.path+'</span><span class="w">'+nd.wiki+'</span></div>';}}).join('');
  [].slice.call(ac.querySelectorAll('.it')).forEach(function(el){{
    el.addEventListener('mousedown',function(ev){{ev.preventDefault();pick(acItems[+el.dataset.i]);}});}});
  positionAc(); ac.classList.toggle('on', acItems.length>0);
}}
q.addEventListener('input',function(){{var s=q.value.trim().toLowerCase(),n=0;
  D.nodes.forEach(function(nd){{if(!nd._el)return;
    var hit=!s||nd.id.toLowerCase().indexOf(s)>=0||(nd.title||'').toLowerCase().indexOf(s)>=0;
    nd._el.classList.toggle('match',!!s&&hit); if(s&&hit)n++;}});
  hint.textContent=s?(n+' khớp'):'';
  acItems = s ? D.nodes.filter(function(nd){{return nd.id.toLowerCase().indexOf(s)>=0||(nd.title||'').toLowerCase().indexOf(s)>=0;}}).slice(0,10) : [];
  acIdx = acItems.length?0:-1; renderAc();}});
q.addEventListener('keydown',function(e){{
  if(!acItems.length)return;
  if(e.key==='ArrowDown'){{e.preventDefault();acIdx=(acIdx+1)%acItems.length;renderAc();}}
  else if(e.key==='ArrowUp'){{e.preventDefault();acIdx=(acIdx-1+acItems.length)%acItems.length;renderAc();}}
  else if(e.key==='Enter'){{e.preventDefault();if(acIdx>=0)pick(acItems[acIdx]);}}
  else if(e.key==='Escape'){{ac.classList.remove('on');}}}});
q.addEventListener('blur',function(){{setTimeout(function(){{ac.classList.remove('on');}},150);}});
q.addEventListener('focus',function(){{if(acItems.length){{positionAc();ac.classList.add('on');}}}});
window.addEventListener('scroll',function(){{if(ac.classList.contains('on'))positionAc();}},true);
showOther.addEventListener('change',function(){{refresh();fitPrimary();}});
showSoft.addEventListener('change',refresh);
// legend = bộ lọc: tick loại quan hệ → chỉ hiện dây loại đó + sáng node liên quan
[].slice.call(document.querySelectorAll('.legend .lg input')).forEach(function(cb){{
  cb.addEventListener('change',function(){{var rel=cb.parentNode.dataset.rel;
    if(cb.checked)relFilter[rel]=1;else delete relFilter[rel];
    refresh();
    if(relActive()){{var vis=D.nodes.filter(function(n){{return n._el&&!n._el.classList.contains('dim');}});
      if(vis.length)fit(vis);}} else fitPrimary();
  }});
}});
document.getElementById('fit').addEventListener('click',fitPrimary);
function fitPrimary(){{fit(showOther.checked?D.nodes:D.nodes.filter(function(n){{return n.wiki===PRIMARY;}}));}}
// ---- init: mặc định chỉ sáng wiki chính, fit đúng cụm đó vào màn hình ----
refresh(); fitPrimary();
window.addEventListener('resize',function(){{clearTimeout(window.__t);window.__t=setTimeout(fitPrimary,150);}});
}})();
</script></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("primary", help="wiki dir chính (mặc định sáng)")
    ap.add_argument("--also", nargs="*", default=[], help="wiki dir phụ (hiện mờ)")
    ap.add_argument("--static", action="store_true", help="xuất HTML/CSS thuần (0 JavaScript)")
    ap.add_argument("--code-root", help="seed node code từ thư mục này → dựng import-graph đầy đủ (opt-in)")
    ap.add_argument("--json", help="dump nodes/edges/cycles ra JSON (cho eval/scoring)")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    t0 = time.perf_counter()
    prim = Path(a.primary).resolve()
    if not prim.is_dir():
        sys.exit(f"khong thay wiki dir: {prim}")
    ptag = prim.parent.name if prim.name == "wiki" else prim.name
    nodes, edges, ledger, stale = [], [], [], {}
    # repo_root để suy `touches` sống: gốc git nếu có, không thì thư mục cha của wiki.
    _rr = Path(a.code_root).resolve() if a.code_root else None
    if _rr is None:
        _rr = prim.parent.parent if prim.name == "wiki" else prim.parent
    scan(prim, ptag, nodes, edges, ledger, stale, _rr)
    for other in a.also:
        o = Path(other).resolve()
        if o.is_dir():
            scan(o, o.parent.name if o.name == "wiki" else o.name,
                 nodes, edges, ledger, stale, _rr)
    add_code_nodes(nodes, edges)   # node lá cho touches → cạnh wiki→code hiện ra
    # --code-root: seed node code từ thư mục code (opt-in) → dựng import-graph đầy đủ.
    # Default OFF → graph framework không đổi (chỉ code vào qua touches như cũ).
    if a.code_root and code_imports:
        croot = Path(a.code_root).resolve()
        ids = {n["id"] for n in nodes}
        for p in sorted(croot.rglob("*")):
            rel = p.relative_to(croot).as_posix()
            if (p.is_file() and p.suffix.lower() in code_imports.SUPPORTED_EXTS
                    and not any(s in rel for s in (".git/", "node_modules/", "ground-truth/"))
                    and rel not in ids):
                nodes.append(_mk_code_node(rel)); ids.add(rel)
        enrich_root = croot
    else:
        # repo root = cha của primary wiki (…/wiki → repo). Tìm .git đi lên.
        enrich_root = prim
        while enrich_root.parent != enrich_root and not (enrich_root / ".git").exists():
            enrich_root = enrich_root.parent
    enrich_code(nodes, edges, enrich_root)  # imports (đa ngôn ngữ) + symbols
    default_name = "wiki-graph-static.html" if a.static else "wiki-graph.html"
    out = Path(a.out).resolve() if a.out else Path("llmwiki/html").resolve() / default_name
    out.parent.mkdir(parents=True, exist_ok=True)
    render = build_static if a.static else build_html
    out.write_text(render(ptag, str(out), nodes, edges, ledger, stale), encoding="utf-8")
    if a.json:                     # dump nodes/edges thô cho eval/scoring (cùng dữ liệu graph vừa vẽ)
        Path(a.json).resolve().write_text(
            json.dumps({"nodes": nodes, "edges": edges,
                        "cycles": detect_cycles(nodes, edges)}, ensure_ascii=False, indent=1),
            encoding="utf-8")
    dt = (time.perf_counter() - t0) * 1000
    kind = "HTML thuần" if a.static else "JS"
    print(f"✓ {out} — {len(nodes)} node, {len(edges)} canh, primary={ptag}, {kind} ({dt:.0f} ms)")


if __name__ == "__main__":
    main()
