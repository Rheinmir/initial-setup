#!/usr/bin/env python3
"""Gợi ý layer: fact|mental-model cho node wiki chưa phân loại — REPORT-ONLY, không tự ghi.

Nối tiếp GH#93 (llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md): field
`layer:` là opt-in thuần tuý, dự án cũ có wiki lớn không có cách nào biết node nào NÊN gắn
layer gì mà không đọc tay từng file. Khác `touches`/`operationalizes` (suy CHẮC CHẮN — path
tồn tại trên đĩa hay không), fact vs mental-model là PHÁN ĐOÁN NGỮ NGHĨA — sai một heuristic
không được phép âm thầm ghi cứng vào frontmatter (xem 030826-wiki-layer-suggest.md § Non-goals).

Script này CHỈ in gợi ý ra report. Người/agent đọc report, tự quyết định chấp nhận dòng nào,
rồi TỰ TAY dán snippet 3 dòng (layer/layer_source/layer_date) vào file — không có đường nào
để script tự ghi file wiki.

Dùng:
  wiki-layer-suggest.py [--wiki-dir llmwiki/wiki] [--out report.txt]
  wiki-layer-suggest.py --self-test
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

SKIP_BASENAMES = {"README.md", "_template.md"}
_DEFAULT_CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)
_LAYER_RE = re.compile(r"^layer[ \t]*:", re.MULTILINE)
_TYPE_RE = re.compile(r"^type[ \t]*:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
_ANALYSIS_SECTION_RE = re.compile(r"^##\s*(Approaches|Trade-?off|Non-goals)", re.MULTILINE | re.IGNORECASE)


def _content_dirs() -> tuple:
    """Mirror wiki-graph.py::_content_dirs() — nguồn chung harness/wikidirs.py, fail-open."""
    harness_dir = Path(__file__).resolve().parent.parent
    if str(harness_dir) not in sys.path:
        sys.path.insert(0, str(harness_dir))
    try:
        import wikidirs
        dirs = tuple(getattr(wikidirs, "CONTENT_DIRS", ()))
        return dirs or _DEFAULT_CONTENT_DIRS
    except Exception:
        return _DEFAULT_CONTENT_DIRS


CONTENT_DIRS = _content_dirs()


def suggest_layer(frontmatter_type: str, body: str) -> tuple:
    """Heuristic thuần (0-token) → (layer_gợi_ý, confidence, lý_do) hoặc (None, None, None)
    nếu không luật nào khớp — KHÔNG ép đoán khi không chắc."""
    t = (frontmatter_type or "").strip()
    if t == "source":
        return "fact", "medium", "type: source — thường là auto-distill/ghi lại sự kiện đã xảy ra"
    if t in ("concept", "draft", "architecture") and _ANALYSIS_SECTION_RE.search(body or ""):
        return ("mental-model", "medium",
                f"type: {t} + có section phân tích (Approaches/Trade-off/Non-goals)")
    return None, None, None


def scan_wiki(wiki: Path) -> list:
    """Quét CONTENT_DIRS, trả về list gợi ý cho node CHƯA có layer: — không đọc/ghi gì khác."""
    out = []
    for d in CONTENT_DIRS:
        base = wiki / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name in SKIP_BASENAMES:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            m = FRONTMATTER_RE.match(text)
            fm = m.group(1) if m else ""
            if _LAYER_RE.search(fm):
                continue  # đã có layer: (người hoặc lần chạy trước) — không đè
            tm = _TYPE_RE.search(fm)
            ftype = tm.group(1) if tm else ""
            body = text[m.end():] if m else text
            layer, confidence, reason = suggest_layer(ftype, body)
            if layer is None:
                continue
            out.append({
                "path": p.relative_to(wiki).as_posix(),
                "type": ftype or "?",
                "layer": layer,
                "confidence": confidence,
                "reason": reason,
            })
    return out


def render_report(suggestions: list, run_date: str) -> str:
    if not suggestions:
        return "Không có gợi ý nào — mọi node đã có layer: hoặc không khớp heuristic nào.\n"
    lines = [f"wiki-layer-suggest — {len(suggestions)} gợi ý (report-only, KHÔNG tự ghi file)", ""]
    for s in suggestions:
        lines.append(f"  {s['path']}  (type: {s['type']})")
        lines.append(f"    → gợi ý: layer: {s['layer']}  [confidence={s['confidence']}]  — {s['reason']}")
        lines.append("    Dán vào frontmatter nếu đồng ý (3 dòng, không thiếu dòng nào):")
        lines.append(f"      layer: {s['layer']}")
        lines.append("      layer_source: heuristic")
        lines.append(f"      layer_date: {run_date}")
        lines.append("")
    return "\n".join(lines)


def self_test() -> int:
    """3 case: type:source→fact, type:concept+Approaches→mental-model, node mơ hồ→không gợi ý.
    Đồng thời chứng minh KHÔNG file nào bị ghi trong quá trình chạy."""
    import tempfile

    checks = []
    with tempfile.TemporaryDirectory() as td:
        wiki = Path(td) / "wiki"
        (wiki / "sources").mkdir(parents=True)
        (wiki / "concepts").mkdir(parents=True)
        f_source = wiki / "sources" / "a.md"
        f_source.write_text("---\ntype: source\n---\n\n# A\n\nGhi lại sự kiện.\n", encoding="utf-8")
        f_concept = wiki / "concepts" / "b.md"
        f_concept.write_text(
            "---\ntype: concept\n---\n\n# B\n\n## Approaches\n\nPhương án A vs B.\n", encoding="utf-8")
        f_vague = wiki / "concepts" / "c.md"
        f_vague.write_text("---\ntype: concept\n---\n\n# C\n\nMột đoạn văn bình thường.\n", encoding="utf-8")
        before = {p: p.read_bytes() for p in (f_source, f_concept, f_vague)}

        suggestions = scan_wiki(wiki)
        by_path = {s["path"]: s for s in suggestions}

        checks.append(("type:source -> gợi ý fact",
                       by_path.get("sources/a.md", {}).get("layer") == "fact"))
        checks.append(("type:concept + Approaches -> gợi ý mental-model",
                       by_path.get("concepts/b.md", {}).get("layer") == "mental-model"))
        checks.append(("node mơ hồ -> KHÔNG có gợi ý (không ép đoán)",
                       "concepts/c.md" not in by_path))
        checks.append(("đúng 2 gợi ý, không thừa không thiếu", len(suggestions) == 2))

        after = {p: p.read_bytes() for p in (f_source, f_concept, f_vague)}
        checks.append(("report-only thật — 0 byte file nào bị đổi", before == after))

        # node đã có layer: từ trước -> không đè, không xuất hiện lại trong report
        f_has_layer = wiki / "sources" / "d.md"
        f_has_layer.write_text("---\ntype: source\nlayer: fact\n---\n\n# D\n", encoding="utf-8")
        suggestions2 = scan_wiki(wiki)
        checks.append(("node đã có layer: -> không xuất hiện lại trong report",
                       "sources/d.md" not in {s["path"] for s in suggestions2}))

    buf = io.StringIO()
    with redirect_stdout(buf):
        print(render_report([{"path": "x.md", "type": "source", "layer": "fact",
                              "confidence": "medium", "reason": "test"}], "2026-08-03"))
    rendered = buf.getvalue()
    checks.append(("report chứa đủ 3 dòng snippet copy-paste",
                   "layer: fact" in rendered and "layer_source: heuristic" in rendered
                   and "layer_date: 2026-08-03" in rendered))

    for name, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    bad = [n for n, ok in checks if not ok]
    print("wiki-layer-suggest self-test:", "PASS" if not bad else f"FAIL ({len(bad)})")
    return 0 if not bad else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-dir", default="llmwiki/wiki")
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    import datetime
    wiki = Path(a.wiki_dir).resolve()
    if not wiki.is_dir():
        sys.exit(f"khong thay wiki dir: {wiki}")
    suggestions = scan_wiki(wiki)
    run_date = datetime.date.today().isoformat()
    report = render_report(suggestions, run_date)
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
        print(f"wrote {a.out} ({len(suggestions)} gợi ý)")
    else:
        print(report)


if __name__ == "__main__":
    main()
