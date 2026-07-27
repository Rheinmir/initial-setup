#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""code-state — overstack TỰ TƯỜNG THUẬT trạng thái code hiện thời (self-narration, Phase 2).

Từ council-advisory 030726 (Rams·Taleb·Feynman). HỢP ĐỒNG CỨNG:
  1. Một dòng FACT = một PROBE = một lệnh tái tạo được (không có "prose mồ côi").
  2. Hai lớp TÁCH VẬT LÝ: FACT (có [nguồn] + lệnh, tái tạo byte-cho-byte trong cùng repo-state)
     vs OPINION (diễn giải người — KHÔNG in ở đây; đây chỉ có FACT + 1 disclaimer).
  3. Mặc định UNKNOWN, không "lành" giả: đo được thì in số, không thì ghi 'UNKNOWN'.
  4. CHỈ FACT nhị-phân/đếm-được từ nguồn máy-đọc — CẤM câu "code sạch/tốt/ổn định".

Vì sao LIVE (không bake vào overstack.html committed): git HEAD/dirty/medic-verdict ĐỘNG,
bake cứng → docs-probe đỏ vĩnh viễn sau mỗi commit (chicken-egg). Trang bake FACT ỔN ĐỊNH
(counts), còn FACT ĐỘNG lấy qua lệnh này → luôn hiện tại, staleness không tồn tại.

Dùng:
  code-state.py            # in bảng FACT trạng thái code (đọc bằng mắt)
  code-state.py --check    # render 2 lần, diff — chứng minh TÁI TẠO ĐƯỢC (Feynman). exit≠0 nếu lệch.
  code-state.py --json     # máy đọc
Self-contained stdlib. Fail-mềm: nguồn thiếu → UNKNOWN, không giết cả bảng.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sh(args, timeout=120):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception:
        return 127, "", ""


def _git(*a):
    rc, out, _ = sh(["git", *a])
    return out if rc == 0 else None


def _count(glob, base="."):
    d = ROOT / base
    return len(list(d.glob(glob))) if d.is_dir() else None


def _lines(path):
    p = ROOT / path
    if not p.is_file():
        return None
    try:
        return sum(1 for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip())
    except Exception:
        return None


def _medic_verdict():
    """Verdict LIVE của medic (KHÔNG đệ quy: code-state không bị generator gọi)."""
    m = ROOT / "fdk/tools/medic.py"
    if not m.is_file():
        return "UNKNOWN"
    rc, out, err = sh([sys.executable, str(m), "--ci"], timeout=180)
    blob = re.sub(r"\033\[[0-9;]*m", "", out + err)   # strip ANSI trước khi parse
    v = re.search(r"▉\s*([^—\n]+?)\s*—\s*(\d+ fail[^\n]*)", blob)
    if v:
        return f"{v.group(1).strip()} ({v.group(2).strip()})"
    return "FAIL" if rc != 0 else "KHOẺ"


def _graph_symbols():
    """code-graph index có DÙNG ĐƯỢC không — không phải "file có tồn tại không".

    Docstring cũ tự nhận "không suy diễn" trong khi đang suy diễn: `db.is_file()` rồi in
    `index có (NKB)`. DB 0 byte cho ra đúng chữ "index có (0KB)" — và dòng đó lên thẳng
    bảng FACT của overstack.html cho người đọc. Cùng lớp lỗi đã sửa ở dep-health.py, nên
    hỏi luôn câu đúng: mở được và có bảng thật không."""
    import sqlite3
    for db in (ROOT / ".graph-agent" / "index.db",):
        if not db.is_file():
            continue
        kb = db.stat().st_size // 1024
        try:
            # KHÔNG mode=ro: WAL thiếu -shm → ro báo hỏng trên DB lành.
            conn = sqlite3.connect(str(db))
            try:
                names = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                n = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0] \
                    if "symbols" in names else 0
            finally:
                conn.close()
        except sqlite3.Error:
            return f"index HỎNG ({kb}KB, không mở được) — dùng grep"
        if {"symbols", "files"} <= names:
            return f"index dùng được ({n} symbol, {kb}KB)"
        return f"index HỎNG ({kb}KB, thiếu bảng) — dùng grep"
    return "UNKNOWN (không có .graph-agent/index.db — dùng grep)"


def facts(include_medic=True):
    """Trả list FACT: (nhóm, nhãn, value, nguồn, lệnh). Deterministic trong cùng repo-state.
    include_medic=False: BỎ dòng verdict medic — dùng cho --check (reproducibility) để KHÔNG
    đệ quy medic↔code-state (medic p_selfstate gọi code-state --check) và cho nhanh."""
    head = _git("rev-parse", "--short", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    cdate = _git("show", "-s", "--format=%cI", "HEAD")
    porcelain = _git("status", "--porcelain")
    dirty = None if porcelain is None else len([l for l in porcelain.splitlines() if l.strip()])
    F = [
        ("git", "branch", branch or "UNKNOWN", "git", "git rev-parse --abbrev-ref HEAD"),
        ("git", "HEAD", head or "UNKNOWN", "git", "git rev-parse --short HEAD"),
        ("git", "commit cuối", cdate or "UNKNOWN", "git", "git show -s --format=%cI HEAD"),
        ("git", "file chưa commit", ("UNKNOWN" if dirty is None else str(dirty)), "git", "git status --porcelain | wc -l"),
        ("đồ nghề", "skill", _fmt(_count("*/SKILL.md", "skills")), "đĩa", "ls skills/*/SKILL.md | wc -l"),
        ("đồ nghề", "rule", _fmt(_rule_count()), "policy", "grep -c 'id: R' policy.yaml"),
        ("đồ nghề", "validator", _fmt(_count("*.py", "harness/validators")), "đĩa", "ls harness/validators/*.py | wc -l"),
        ("đồ nghề", "hook", _fmt(_count("*.py", "llmwiki/.claude/hooks")), "đĩa", "ls llmwiki/.claude/hooks/*.py | wc -l"),
        ("đồ nghề", "cơ-chế (manifest)", _fmt(_mech_count()), "manifest", "grep -c '- id:' harness/mechanisms.yaml"),
        ("đồ nghề", "script", _fmt(_count("*.py", "harness/scripts")), "đĩa", "ls harness/scripts/*.py | wc -l"),
        ("bộ nhớ", "scratch-log entry", _fmt(_lines("harness/metrics/scratch-log.jsonl")), "ledger", "wc -l harness/metrics/scratch-log.jsonl"),
        ("bộ nhớ", "wiki-ledger event", _fmt(_lines("llmwiki/wiki/ledger.jsonl")), "ledger", "wc -l llmwiki/wiki/ledger.jsonl"),
        ("code-graph", "index", _graph_symbols(), "graph", "ls -la .graph-agent/index.db"),
    ]
    if include_medic:
        F.append(("medic", "verdict LIVE", _medic_verdict(), "medic", "python3 fdk/tools/medic.py --ci"))
    return F


def _fmt(v):
    return "UNKNOWN" if v is None else str(v)


def _rule_count():
    p = ROOT / "harness/poc-vendor-neutral/policy.yaml"
    if not p.is_file():
        return None
    return len(re.findall(r"id:\s*R\d+", p.read_text(encoding="utf-8")))


def _mech_count():
    p = ROOT / "harness/mechanisms.yaml"
    if not p.is_file():
        return None
    return len(re.findall(r"^\s*-\s*id:", p.read_text(encoding="utf-8"), re.M))


def render_text(include_medic=True):
    out = ["TRẠNG THÁI CODE — self-narration (FACT · mỗi dòng có nguồn + lệnh tái tạo)"]
    grp = None
    for g, label, val, src, cmd in facts(include_medic):
        if g != grp:
            out.append(f"\n[{g}]")
            grp = g
        out.append(f"  {label:22} {val:38} ({src})  ← {cmd}")
    out.append("\n— OPINION (KHÔNG phải FACT): mọi diễn giải 'khoẻ/tốt/ổn định' là ý kiến người,")
    out.append("  không có ở bảng này. Verdict sức khoẻ khách quan: `python3 fdk/tools/medic.py`.")
    return "\n".join(out)


def render_html():
    """Fragment cho overstack.html — CHỈ FACT động (git/memory/graph/medic). Counts ổn định
    do generator tự bake nơi khác. Mỗi dòng có badge nguồn + lệnh (không prose mồ côi)."""
    rows = []
    for g, label, val, src, cmd in facts():
        rows.append(f'<tr><td>{g}</td><td>{label}</td><td><b>{val}</b></td>'
                    f'<td><span class="src">{src}</span></td><td><code>{cmd}</code></td></tr>')
    return ("<table class='cstate'><thead><tr><th>nhóm</th><th>chỉ số</th><th>giá trị</th>"
            "<th>nguồn</th><th>lệnh tái tạo</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def check_reproducible():
    """Feynman: render 2 lần trong cùng repo-state → phải BYTE-IDENTICAL (loại verdict medic +
    git-dirty vốn ổn định trong-state). Lệch = có nondeterminism trá hình dữ liệu → fail."""
    a = render_text(include_medic=False)   # loại verdict medic (live/ngoại + chống đệ quy)
    b = render_text(include_medic=False)
    if a == b:
        print("✓ code-state TÁI TẠO ĐƯỢC: 2 lần render byte-identical (cùng repo-state)")
        return 0
    print("✗ code-state KHÔNG tái tạo: 2 lần render lệch — có nondeterminism", file=sys.stderr)
    return 1


def main():
    if "--check" in sys.argv:
        return check_reproducible()
    if "--json" in sys.argv:
        print(json.dumps([{"group": g, "label": l, "value": v, "source": s, "cmd": c}
                          for g, l, v, s, c in facts()], ensure_ascii=False, indent=2))
        return 0
    if "--html" in sys.argv:
        print(render_html())
        return 0
    print(render_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
