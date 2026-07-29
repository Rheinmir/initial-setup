#!/usr/bin/env python3
"""build-line-status — the Ralph production-line MONITOR (GH#15, step 4 / #11 thin-slice).

A deterministic READ LAYER over data that already exists after steps 1-3. It does
NOT create a new ledger, run a daemon, or fire on its own (lesson p-17 — don't grow
a sink; Goodhart-safe = it only DISPLAYS + traces, never scores). Sources:

  • br/frames/*.md frontmatter  → per-frame status, frame↔clause↔scope map
  • br/frames/<id>.run.json      → the loop-runner run-log (verdict, iters, guard events)
  • br/BR.clauses.json           → clause provenance (raw|user|lens-assumed) from /br compile
  • (optional) git               → merged? (baseline_ref is ancestor of HEAD)

Emits `br/line-status.json` (machine) + `llmwiki/html/line-status.html` (human, offline,
dark-mode, R16 full-path). Status is derived by fixed rules — never by an LLM.

Usage:
  build-line-status.py build   [--root R] [--frames DIR] [--out-json P] [--out-html P]
  build-line-status.py --check [--root R] ...     # regen in memory, diff on-disk → exit 1 if drift
  build-line-status.py selftest                   # fixtures covering all 5 states + traceback

Exit: 0 ok / (--check) 0 in-sync · 1 drift · 2 usage.
"""
import argparse
import html as _html
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Reuse frame-lint's robust frontmatter parser (DRY — one parser for the pipeline).
_FL = Path(__file__).with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter

# Deterministic status vocabulary (derived, never guessed).
STATUS_ORDER = ["killed", "stalled", "pending", "green-pending-review", "merged"]
STATUS_LABEL = {
    "pending": "chưa chạy",
    "green-pending-review": "xanh — chờ người duyệt",
    "stalled": "kẹt",
    "killed": "bị dừng (kill)",
    "merged": "đã gộp",
}
STATUS_COLOR = {
    "pending": "#8a94a6", "green-pending-review": "#22c55e", "stalled": "#eab308",
    "killed": "#ef4444", "merged": "#3b82f6",
}
_STALL_VERDICTS = {"NO_PROGRESS", "TIMEOUT", "MAX_ITER", "ESCALATE"}


def derive_status(frame, runlog):
    """Fixed rules — the ONLY place a frame's state is decided. No model involved."""
    outcome = (frame.get("outcome") or "").strip().lower()
    if outcome in ("merged", "killed"):
        return outcome
    if outcome in ("discarded", "dropped"):
        return "killed"
    ref = frame.get("run_log_ref")
    if not ref or runlog is None:
        return "pending"
    v = runlog.get("verdict")
    if v == "SUCCESS":
        return "green-pending-review"
    if v == "PROTECT_VIOLATION":
        return "killed"        # test-tamper fail-closed → thrown away
    if v in _STALL_VERDICTS:
        return "stalled"
    return "pending"


def _load_runlog(root, frame):
    ref = frame.get("run_log_ref")
    if not ref:
        return None
    p = (root / ref) if not Path(ref).is_absolute() else Path(ref)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _load_clauses(root):
    p = root / "br" / "BR.clauses.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def collect(root, frames_dir):
    """Build the deterministic line-status model from the 4 sources."""
    root = Path(root).resolve()
    frames_dir = Path(frames_dir)
    clauses = _load_clauses(root)
    frames = []
    if frames_dir.is_dir():
        for f in sorted(frames_dir.glob("*.md")):
            if f.name == "index.md":
                continue
            try:
                fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            runlog = _load_runlog(root, fm)
            status = derive_status(fm, runlog)
            cids = fm.get("clause_ids") or []
            frames.append({
                "frame_id": fm.get("frame_id"),
                "file": f.name,
                "status": status,
                "clause_ids": cids,
                "depends_on": fm.get("depends_on") or [],
                "scope_code": fm.get("scope_code") or [],
                "muc_tieu": fm.get("muc_tieu") or "",
                "run": None if runlog is None else {
                    "verdict": runlog.get("verdict"),
                    "iterations_run": runlog.get("iterations_run"),
                    "reason": runlog.get("reason"),
                    "scope_reverted": any(i.get("scope_reverted") for i in runlog.get("iterations", [])),
                    "protect_violation": any(i.get("protect_violation") for i in runlog.get("iterations", [])),
                    "changed_files": runlog.get("changed_files") or [],
                    "commit": runlog.get("commit"),
                    "scope_clean": runlog.get("scope_clean"),
                    "out_of_scope_files": runlog.get("out_of_scope_files") or [],
                },
                "assumed_clauses": [c for c in cids
                                    if str(clauses.get(c, {}).get("provenance", "")).startswith("lens")],
            })
    # Which frames are WAITING on an upstream that isn't green yet (GH#75 / ATG). Derived,
    # like every other status here: a frame is waiting iff some frame it depends_on is not
    # done. This is what makes the line a graph on screen instead of a list.
    _done = {fr["frame_id"] for fr in frames if fr["status"] in ("merged", "green-pending-review")}
    for fr in frames:
        fr["waiting_on"] = [d for d in fr["depends_on"] if d not in _done]
    counts = {s: sum(1 for fr in frames if fr["status"] == s) for s in STATUS_ORDER}
    total_assumed = sum(1 for c, meta in clauses.items()
                        if str(meta.get("provenance", "")).startswith("lens"))
    return {
        "schema_version": 0,
        "frames": frames,
        "counts": counts,
        "total_frames": len(frames),
        "clauses": clauses,
        "assumed_clause_count": total_assumed,
        "waiting_frames": sum(1 for fr in frames if fr["waiting_on"]),
    }


# ── HTML render (offline, dark-mode, deterministic — same model → same bytes) ─
def _esc(s):
    return _html.escape(str(s if s is not None else ""))


# Stable per-frame colour (index-based, deterministic) for the folder tree.
_FRAME_COLORS = ["#0a84ff", "#30b0c7", "#5856d6", "#34c759", "#ff9500", "#ff2d55", "#8a5cf6", "#e0264b"]


def _frame_color(idx):
    return _FRAME_COLORS[idx % len(_FRAME_COLORS)]


def build_folder_tree(model):
    """Map every file to the frame(s) that own it, then nest into a folder tree.
    Uses the ACTUAL changed_files when a frame has run; falls back to the declared
    scope_code globs (marked 'dự định') for frames not yet run. Deterministic."""
    frame_idx = {fr["frame_id"]: i for i, fr in enumerate(model["frames"])}
    owners = {}          # concrete path -> [{frame, status, actual:True}]
    pending = []         # (frame_id, status, [scope globs]) for frames not run yet
    for fr in model["frames"]:
        changed = (fr["run"] or {}).get("changed_files") or []
        if changed:
            for path in changed:
                owners.setdefault(path, []).append(
                    {"frame": fr["frame_id"], "status": fr["status"], "actual": True})
        else:
            pending.append((fr["frame_id"], fr["status"], fr["scope_code"]))
    tree = {}
    for path in sorted(owners):
        parts = path.split("/")
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node.setdefault("__files__", []).append((parts[-1], path))
    return tree, owners, frame_idx, pending


def _render_tree(node, owners, frame_idx, depth=0):
    out = []
    pad = 18 * depth
    # folders first (keys that aren't __files__)
    for name in sorted(k for k in node if k != "__files__"):
        out.append(f'<div class="tnode" style="padding-left:{pad}px"><span class="tfold">📁 {_esc(name)}/</span></div>')
        out.append(_render_tree(node[name], owners, frame_idx, depth + 1))
    for fname, fullpath in node.get("__files__", []):
        badges = ""
        for o in owners.get(fullpath, []):
            col = _frame_color(frame_idx.get(o["frame"], 0))
            dim = "" if o["actual"] else ";opacity:.55"
            suffix = "" if o["actual"] else " (dự định)"
            badges += (f'<span class="fbadge" style="background:{col}22;color:{col}{dim}" '
                       f'title="{_esc(o["status"])}">{_esc(o["frame"])}{suffix}</span>')
        out.append(f'<div class="tnode" style="padding-left:{18*depth}px">'
                   f'<span class="tfile">📄 {_esc(fname)}</span> {badges}</div>')
    return "".join(out)


def render_html(model, out_html_path):
    rows = []
    for fr in model["frames"]:
        col = STATUS_COLOR[fr["status"]]
        run = fr["run"] or {}
        guard = []
        if run.get("scope_reverted"):
            guard.append("diff-jail cắn")
        if run.get("protect_violation"):
            guard.append("test-hash cắn")
        run_txt = ""
        if fr["run"]:
            run_txt = f'{_esc(run.get("verdict"))} · {_esc(run.get("iterations_run"))} vòng'
            if guard:
                run_txt += " · " + " · ".join(guard)
        assumed = ""
        if fr["assumed_clauses"]:
            assumed = f' <span class="assumed" title="điều khoản do lens điền — chưa kiểm chứng">⚠ {_esc(",".join(fr["assumed_clauses"]))}</span>'
        # ACTUAL frame→code footprint from the run-log (real files changed + commit sha),
        # falling back to the declared scope_code when the frame has not run yet.
        run = fr["run"] or {}
        changed = run.get("changed_files") or []
        commit = run.get("commit")
        clean = run.get("scope_clean")
        oos = run.get("out_of_scope_files") or []
        if changed or fr["run"]:
            files_txt = _esc(", ".join(changed)) if changed else '<span class="mut">(không đổi file)</span>'
            if commit:
                files_txt += f' <span class="mut" title="commit trong worktree branch">@{_esc(commit[:8])}</span>'
            if clean is True:
                files_txt += ' <span class="pill" style="background:rgba(34,197,94,.14);color:#15803d" title="mọi file đã đổi nằm TRONG scope_code — diff-jail bảo đảm">✓ trong scope</span>'
            elif clean is False:
                files_txt += f' <span class="pill" style="background:rgba(239,68,68,.14);color:#b91c1c" title="có file lọt ngoài scope!">⚠ lọt scope: {_esc(", ".join(oos))}</span>'
        else:
            files_txt = f'<span class="mut" title="chưa chạy — mới là phạm vi khai báo, chưa phải file thật đổi">{_esc(", ".join(fr["scope_code"]))} (dự định)</span>'
        # Dependency column: what this frame is built on top of, and whether it is still
        # WAITING (an upstream frame is not green yet, so running this one now is premature).
        if not fr["depends_on"]:
            dep_txt = '<span class="mut" title="không phụ thuộc frame nào — chạy được ngay">—</span>'
        elif fr["waiting_on"]:
            dep_txt = (f'<span class="pill" style="background:rgba(234,179,8,.16);color:#a16207" '
                       f'title="upstream chưa xanh — chạy frame này bây giờ là phí, sửa upstream trước">'
                       f'⏸ chờ: {_esc(", ".join(fr["waiting_on"]))}</span>')
        else:
            dep_txt = (f'<span class="mut" title="mọi frame nó dựa lên đều đã xanh — sẵn sàng chạy">'
                       f'✓ sau {_esc(", ".join(fr["depends_on"]))}</span>')
        rows.append(
            f'<tr><td><code>{_esc(fr["frame_id"])}</code></td>'
            f'<td><span class="pill" style="background:{col}22;color:{col}">{_esc(STATUS_LABEL[fr["status"]])}</span></td>'
            f'<td>{_esc(", ".join(fr["clause_ids"]))}{assumed}</td>'
            f'<td class="mut">{dep_txt}</td>'
            f'<td class="mut">{files_txt}</td>'
            f'<td class="mut">{run_txt}</td></tr>'
        )
    c = model["counts"]
    kpis = "".join(
        f'<div class="kpi"><b style="color:{STATUS_COLOR[s]}">{c[s]}</b><span>{_esc(STATUS_LABEL[s])}</span></div>'
        for s in STATUS_ORDER
    )
    trace = json.dumps(
        [{"frame": fr["frame_id"], "scope": fr["scope_code"],
          "changed": (fr["run"] or {}).get("changed_files") or [],
          "commit": (fr["run"] or {}).get("commit"),
          "scope_clean": (fr["run"] or {}).get("scope_clean"),
          "clauses": fr["clause_ids"], "assumed": fr["assumed_clauses"], "status": fr["status"]}
         for fr in model["frames"]],
        ensure_ascii=False,
    )
    tree, owners, frame_idx, pending = build_folder_tree(model)
    tree_html = _render_tree(tree, owners, frame_idx)
    for fid, status, globs in pending:
        col = _frame_color(frame_idx.get(fid, 0))
        tree_html += (f'<div class="tnode"><span class="tfile" style="opacity:.6">🔲 {_esc(", ".join(globs))}</span>'
                      f'<span class="fbadge" style="background:{col}22;color:{col};opacity:.6">{_esc(fid)} (dự định, chưa chạy)</span></div>')
    if not tree_html:
        tree_html = '<div class="mut">Chưa có file nào (chạy /br slice + run).</div>'
    legend = "".join(
        f'<span class="fbadge" style="background:{_frame_color(i)}22;color:{_frame_color(i)}">{_esc(fr["frame_id"])}</span>'
        for i, fr in enumerate(model["frames"]))
    abspath = str(Path(out_html_path).resolve())
    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Line status — dây chuyền Ralph</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
<style>
:root{{--bg:#eef4fb;--card:#fff;--ink:#1c2b3a;--sub:#5a6f88;--line:#c9d8ec;--acc:#2f6fdb}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0f1722;--card:#1b2534;--ink:#e5edf7;--sub:#94a8c0;--line:#2b3b52;--acc:#7aa7f7}}}}
/* toggle thắng hệ (feedback: không ép mode — user tự chọn, nhớ localStorage) */
:root[data-theme=light]{{--bg:#eef4fb;--card:#fff;--ink:#1c2b3a;--sub:#5a6f88;--line:#c9d8ec;--acc:#2f6fdb}}
:root[data-theme=dark]{{--bg:#0f1722;--card:#1b2534;--ink:#e5edf7;--sub:#94a8c0;--line:#2b3b52;--acc:#7aa7f7}}
.theme-toggle{{position:fixed;top:12px;right:14px;z-index:50;width:34px;height:34px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer;font-size:15px}}
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.6 -apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--ink);padding:28px 18px;max-width:1040px;margin:auto}}
h1{{font-size:1.4rem;margin:0 0 4px}}.sub{{color:var(--sub);margin:0 0 20px}}
.kpis{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0 24px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 18px;min-width:120px}}
.kpi b{{font-size:1.7rem;display:block}}.kpi span{{color:var(--sub);font-size:.82rem}}
table{{border-collapse:collapse;width:100%;background:var(--card);border-radius:12px;overflow:hidden;font-size:.9rem}}
th,td{{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}}
th{{background:rgba(47,111,219,.08)}}
.pill{{border-radius:99px;padding:2px 10px;font-size:.78rem;font-weight:600;white-space:nowrap}}
code{{background:rgba(47,111,219,.12);border-radius:5px;padding:1px 6px;font-size:.86em}}
.mut{{color:var(--sub);font-size:.85rem}}.assumed{{color:#f59e0b;font-weight:600}}
.trace{{margin:24px 0;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}}
.trace input{{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);margin:8px 0}}
.trace pre{{background:var(--bg);border-radius:8px;padding:12px;overflow-x:auto;font-size:.82rem;white-space:pre-wrap}}
.tree{{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:var(--card);font-family:var(--font-mono);font-size:12.5px;margin:8px 0 6px;overflow-x:auto}}
.tnode{{padding:2px 0;white-space:nowrap}}.tfold{{color:var(--sub);font-weight:600}}.tfile{{color:var(--ink)}}
.fbadge{{display:inline-block;border-radius:99px;padding:0 8px;font-size:10.5px;font-weight:700;margin-left:6px;font-family:-apple-system,'Segoe UI',sans-serif}}
.legend{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 2px;font-size:12px;color:var(--sub)}}
footer{{margin-top:32px;color:var(--sub);font-size:.78rem;border-top:1px solid var(--line);padding-top:12px}}
</style></head><body>
<script>/* chống FOUC: áp theme đã lưu TRƯỚC khi vẽ */
(function(){{try{{var t=localStorage.getItem('lsTheme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
<button class="theme-toggle" id="thBtn" title="Đổi sáng/tối" aria-label="Đổi giao diện sáng tối">◐</button>
<script>
document.getElementById('thBtn').addEventListener('click',function(){{
  var r=document.documentElement,cur=r.getAttribute('data-theme');
  var next=cur?(cur==='dark'?'light':'dark'):(matchMedia('(prefers-color-scheme: dark)').matches?'light':'dark');
  r.setAttribute('data-theme',next);try{{localStorage.setItem('lsTheme',next);}}catch(e){{}}
}});
</script>
<h1>📊 Line status — dây chuyền sản xuất Ralph</h1>
<p class="sub">Lớp ĐỌC tất định trên dữ liệu đã có (frame · run-log · BR). Không chấm điểm, chỉ hiển thị + truy ngược. Trạng thái suy bằng luật cố định, không dùng model.</p>
<div class="kpis">{kpis}<div class="kpi"><b style="color:#f59e0b">{model["assumed_clause_count"]}</b><span>điều khoản assumed còn gánh</span></div></div>
<table><thead><tr><th>Frame</th><th>Trạng thái</th><th>Điều khoản (clause)</th><th title="frame này dựa lên frame nào (depends_on) — ⏸ = upstream chưa xanh">Phụ thuộc</th><th>File code (thật đã đổi · scope-check)</th><th>Run gần nhất</th></tr></thead>
<tbody>{"".join(rows) or '<tr><td colspan="6" class="mut">Chưa có frame nào (chạy /br slice để sinh).</td></tr>'}</tbody></table>
<h2 style="font-size:1.05rem;margin:26px 0 6px">🗂️ Cây thư mục — file nào thuộc frame nào</h2>
<div class="legend"><span>Chú giải frame:</span>{legend}</div>
<div class="tree">{tree_html}</div>
<p class="mut" style="font-size:11.5px;margin:0 0 8px">Nhãn màu = frame sở hữu file (file THẬT đã đổi). Nhãn mờ "(dự định)" = frame chưa chạy, mới là phạm vi khai báo <code>scope_code</code>.</p>
<div class="trace"><b>Truy ngược (traceback):</b> gõ tên file hoặc frame_id → thấy chuỗi file → frame → điều khoản → assumed?
<input id="q" placeholder="vd: src/auth.py  hoặc  frame-001" oninput="tr()"/>
<pre id="out">— nhập để truy ngược —</pre></div>
<footer>📄 File này (sinh bởi <code>fdk/tools/build-line-status.py</code>, chống drift bằng <code>--check</code>): <code>{_esc(abspath)}</code><br>
Thuật ngữ: <b>frame</b> (khung việc nhỏ gắn code) · <b>clause</b> (điều khoản BR) · <b>assumed</b> (do lens chuyên gia điền, chưa kiểm chứng) · <b>diff-jail</b> (phanh chặn sửa ngoài scope) · <b>test-hash</b> (phanh chặn sửa bài test).</footer>
<script>
const DATA={trace};
function tr(){{const q=document.getElementById('q').value.trim().toLowerCase();const o=document.getElementById('out');if(!q){{o.textContent='— nhập để truy ngược —';return;}}
const hits=DATA.filter(f=>(f.frame||'').toLowerCase().includes(q)||(f.scope||[]).some(s=>s.toLowerCase().includes(q)||q.includes(s.replace(/\\*+/g,'').toLowerCase())));
if(!hits.length){{o.textContent='Không khớp frame nào cho: '+q;return;}}
o.textContent=hits.map(f=>`file/scope: ${{(f.scope||[]).join(', ')}}\\n  → frame: ${{f.frame}}  [${{f.status}}]\\n  → điều khoản: ${{(f.clauses||[]).join(', ')}}\\n  → assumed (chưa kiểm chứng): ${{(f.assumed||[]).join(', ')||'(không)'}}`).join('\\n\\n');}}
</script></body></html>
"""


# ── build / check / selftest ────────────────────────────────────────────────
def _default_paths(root):
    root = Path(root)
    return root / "br" / "line-status.json", root / "llmwiki" / "html" / "line-status.html"


def build(root, frames_dir=None, out_json=None, out_html=None, check=False):
    root = Path(root).resolve()
    frames_dir = Path(frames_dir) if frames_dir else root / "br" / "frames"
    dj, dh = _default_paths(root)
    out_json = Path(out_json) if out_json else dj
    out_html = Path(out_html) if out_html else dh
    model = collect(root, frames_dir)
    new_json = json.dumps(model, indent=2, ensure_ascii=False) + "\n"
    new_html = render_html(model, out_html)
    if check:
        drift = []
        for path, new in ((out_json, new_json), (out_html, new_html)):
            old = path.read_text(encoding="utf-8") if path.exists() else None
            if old != new:
                drift.append(str(path))
        if drift:
            print(f"[build-line-status] DRIFT (regenerate): {drift}", file=sys.stderr)
            return 1
        print("[build-line-status] in sync")
        return 0
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(new_json, encoding="utf-8")
    out_html.write_text(new_html, encoding="utf-8")
    print(f"[build-line-status] wrote {out_json}")
    print(f"[build-line-status] wrote {out_html}  ({model['total_frames']} frame, "
          f"{model['assumed_clause_count']} assumed clause)")
    return 0


def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fdir = root / "br" / "frames"
        fdir.mkdir(parents=True)
        (root / "br" / "BR.clauses.json").write_text(json.dumps({
            "S1.1": {"provenance": "user"},
            "S4.2": {"provenance": "lens:taleb"},   # an assumed clause
        }), encoding="utf-8")

        def frame(fid, clause, runref=None, outcome=None):
            lines = [
                "---", "schema_version: 0", f"frame_id: {fid}", "created_by: human",
                "parent_br: br/BR.md", f"clause_ids: [{clause}]", "parent_br_hash: x",
                f'muc_tieu: "muc tieu {fid}"', 'scope_code: ["src/**"]', 'scope_test: ["tests/**"]',
                "acceptance_test: \"true\"",
            ]
            if runref:
                lines.append(f"run_log_ref: {runref}")
            if outcome:
                lines.append(f"outcome: {outcome}")
            lines += ["---", f"# {fid}"]
            (fdir / f"{fid}.md").write_text("\n".join(lines), encoding="utf-8")

        def runlog(name, verdict, iters=1, scope=False, protect=False):
            it = [{"iter": 1}]
            if scope:
                it[0]["scope_reverted"] = ["out/x.py"]
            if protect:
                it[0]["protect_violation"] = ["tests/t.py"]
            (root / "br" / name).write_text(json.dumps({
                "verdict": verdict, "iterations_run": iters, "reason": "test", "iterations": it,
            }), encoding="utf-8")

        # 5 states
        frame("frame-pending", "S1.1")                                   # pending (no run)
        frame("frame-green", "S4.2", runref="br/g.run.json"); runlog("g.run.json", "SUCCESS")       # green (+assumed clause)
        frame("frame-stall", "S1.1", runref="br/s.run.json"); runlog("s.run.json", "NO_PROGRESS", scope=True)  # stalled
        frame("frame-kill", "S1.1", runref="br/k.run.json"); runlog("k.run.json", "PROTECT_VIOLATION", protect=True)  # killed
        frame("frame-merged", "S1.1", runref="br/g.run.json", outcome="merged")  # merged

        model = collect(root, fdir)
        got = {fr["frame_id"]: fr["status"] for fr in model["frames"]}
        expect = {
            "frame-pending": "pending", "frame-green": "green-pending-review",
            "frame-stall": "stalled", "frame-kill": "killed", "frame-merged": "merged",
        }
        for k, v in expect.items():
            good = got.get(k) == v
            ok = ok and good
            print(f"  [{'PASS' if good else 'FAIL'}] {k:<16} status={got.get(k)} (want {v})")
        # assumed clause surfaced on the green frame
        gf = next(f for f in model["frames"] if f["frame_id"] == "frame-green")
        a_ok = gf["assumed_clauses"] == ["S4.2"] and model["assumed_clause_count"] == 1
        ok = ok and a_ok
        print(f"  [{'PASS' if a_ok else 'FAIL'}] assumed-clause traceback  {gf['assumed_clauses']}")
        # guard events surfaced
        sf = next(f for f in model["frames"] if f["frame_id"] == "frame-stall")
        g_ok = sf["run"]["scope_reverted"] is True
        ok = ok and g_ok
        print(f"  [{'PASS' if g_ok else 'FAIL'}] guard-event surfaced (diff-jail on stalled)")
        # --check idempotency
        oj = root / "br" / "line-status.json"
        oh = root / "out.html"
        build(root, frames_dir=fdir, out_json=oj, out_html=oh)
        rc = build(root, frames_dir=fdir, out_json=oj, out_html=oh, check=True)
        c_ok = rc == 0
        ok = ok and c_ok
        print(f"  [{'PASS' if c_ok else 'FAIL'}] --check idempotent right after build (rc={rc})")

    print("-" * 60)
    print(f"  build-line-status self-test: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="build-line-status.py", description="Ralph line-status monitor (deterministic read layer).")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="generate line-status.json + line-status.html")
    b.add_argument("--root", default=".")
    b.add_argument("--frames", default=None)
    b.add_argument("--out-json", default=None)
    b.add_argument("--out-html", default=None)
    b.add_argument("--check", action="store_true", help="regen in memory, diff on-disk, exit 1 on drift")
    b.set_defaults(func=lambda a: build(a.root, a.frames, a.out_json, a.out_html, a.check))
    s = sub.add_parser("selftest", help="fixtures covering all 5 states + traceback + --check")
    s.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
