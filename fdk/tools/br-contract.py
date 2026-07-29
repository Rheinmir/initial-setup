#!/usr/bin/env python3
"""br-contract — sinh UI CONTRACT (md + html) từ frames + ui-layout.yaml (GH#15).

Một CONTRACT chốt thực hiện: đọc MỌI frame (làm gì · ui_role · scope · acceptance) +
`br/ui-layout.yaml` (frame nào chung màn · route thật) → một bảng tổng cấu-trúc-cố-định
dùng cho MỌI dự án, xuất song song:
  • `br/UI-CONTRACT.md`  — canonical, máy đọc + diff được (nguồn chân lý contract)
  • `br/UI-CONTRACT.html` — bản người review (self-contained, neumorphic, theme toggle)

Trục CODE (frame, frame-lint gác) và trục HIỂN THỊ (screen/route, file này) TÁCH nhau:
sửa layout gom lại màn KHÔNG đụng frame. Tool này join 2 trục + validate lệch.

DETERMINISTIC (build + selftest): parse frame/layout, join frame→screen→route, đếm
frame/screen/route, phát hiện lệch (screen trỏ frame không tồn tại · ui_screen frame
lệch layout), render md + html. Không gọi model.

Usage:
  br-contract.py build <frames-dir> [--layout br/ui-layout.yaml] [--root .]
                       [--out-md br/UI-CONTRACT.md] [--out-html br/UI-CONTRACT.html]
  br-contract.py selftest
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

_fl = importlib.util.spec_from_file_location("_framelint", Path(__file__).with_name("frame-lint.py"))
_m = importlib.util.module_from_spec(_fl)
_fl.loader.exec_module(_m)
parse_frontmatter = _m.parse_frontmatter

ROLE_ORDER = ["screen", "form", "panel", "widget", "action", "none"]


# ── core (pure, testable) ───────────────────────────────────────────────────
def _load_frames(frames_dir):
    out = {}
    for f in sorted(Path(frames_dir).glob("*.md")):
        if f.name == "index.md":
            continue
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        fid = fm.get("frame_id") or f.stem
        out[fid] = {
            "muc_tieu": (fm.get("muc_tieu") or "").strip(),
            "ui_role": (fm.get("ui_role") or "none"),
            "ui_screen": fm.get("ui_screen") or "",
            "clause_ids": fm.get("clause_ids") or [],
            "scope_code": fm.get("scope_code") or [],
            "acceptance_test": fm.get("acceptance_test") or "",
            "run_log_ref": fm.get("run_log_ref") or "",
            "_path": f,
        }
    return out


def _status_of(frame, root):
    ref = frame.get("run_log_ref")
    if not ref:
        return "chưa chạy"
    p = Path(root) / ref
    if not p.exists():
        return "chưa chạy"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return "?"
    v = str(data.get("verdict") or data.get("status") or "").lower()
    if v in ("pass", "green", "done", "ok", "success"):
        return "xong"
    if v in ("fail", "red", "failed"):
        return "đỏ"
    return v or "chưa chạy"


def build_contract(frames_dir, layout_path, root="."):
    frames = _load_frames(frames_dir)
    layout = {}
    lp = Path(layout_path)
    if lp.exists() and yaml is not None:
        layout = yaml.safe_load(lp.read_text(encoding="utf-8")) or {}
    nav_style = layout.get("nav_style") or "—"
    screens = layout.get("screens") or []

    frame_screen = {}          # fid -> (screen_id, title, route)
    warnings = []
    for sc in screens:
        sid, title, route = sc.get("id"), sc.get("title", ""), sc.get("route", "")
        for fid in sc.get("frames") or []:
            if fid not in frames:
                warnings.append(f"screen `{sid}` trỏ frame `{fid}` KHÔNG tồn tại")
                continue
            if fid in frame_screen:
                warnings.append(f"frame `{fid}` bị gán ≥2 màn ({frame_screen[fid][0]} & {sid})")
            frame_screen[fid] = (sid, title, route)

    rows = []
    for fid in sorted(frames):
        fr = frames[fid]
        sid, title, route = frame_screen.get(fid, ("", "", ""))
        # consistency: frame khai ui_screen phải khớp layout
        if fr["ui_screen"] and fr["ui_screen"] != sid:
            warnings.append(f"frame `{fid}` khai ui_screen=`{fr['ui_screen']}` nhưng layout xếp vào `{sid or '—'}`")
        if fr["ui_role"] != "none" and not sid:
            warnings.append(f"frame `{fid}` có ui_role=`{fr['ui_role']}` nhưng CHƯA nằm màn nào (thêm vào ui-layout.yaml)")
        rows.append({
            "fid": fid, "muc_tieu": fr["muc_tieu"], "ui_role": fr["ui_role"],
            "screen": title or sid, "route": route,
            "clause_ids": fr["clause_ids"], "scope_code": fr["scope_code"],
            "acceptance": fr["acceptance_test"], "status": _status_of(fr, root),
            "assigned": bool(sid),
        })

    routes = sorted({sc.get("route") for sc in screens if sc.get("route")})
    unassigned = [r["fid"] for r in rows if not r["assigned"] and r["ui_role"] == "none"]
    unassigned_ui = [r["fid"] for r in rows if not r["assigned"] and r["ui_role"] != "none"]
    return {
        "nav_style": nav_style, "screens": screens, "rows": rows,
        "counts": {"frames": len(rows), "screens": len(screens), "routes": len(routes)},
        "routes": routes, "unassigned_logic": unassigned, "unassigned_ui": unassigned_ui,
        "warnings": warnings,
    }


# ── render markdown ─────────────────────────────────────────────────────────
def render_md(c, project=""):
    L = []
    L.append(f"# UI CONTRACT{(' — ' + project) if project else ''}")
    L.append("")
    L.append("> Contract chốt thực hiện — sinh tự động từ frames + `br/ui-layout.yaml` "
             "(`br-contract.py`). Trục code (frame) và trục hiển thị (screen/route) tách nhau.")
    L.append("")
    cc = c["counts"]
    L.append(f"**Tổng:** {cc['frames']} frame · {cc['screens']} màn hình · {cc['routes']} route thật "
             f"· nav_style `{c['nav_style']}`")
    L.append("")
    if c["warnings"]:
        L.append("## ⚠️ Lệch cần xử lý")
        for w in c["warnings"]:
            L.append(f"- {w}")
        L.append("")
    L.append("## Bảng contract")
    L.append("")
    L.append("| frame | làm gì | ui_role | màn hình | route | clause | acceptance (điều kiện chốt) | trạng thái |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in c["rows"]:
        mt = (r["muc_tieu"][:60] + "…") if len(r["muc_tieu"]) > 61 else r["muc_tieu"]
        L.append(f"| `{r['fid']}` | {mt} | {r['ui_role']} | {r['screen'] or '—'} | "
                 f"`{r['route'] or '—'}` | {', '.join(r['clause_ids']) or '—'} | "
                 f"`{r['acceptance'] or '—'}` | {r['status']} |")
    L.append("")
    L.append("## Màn hình → frame")
    for sc in c["screens"]:
        L.append(f"- **{sc.get('title', sc.get('id'))}** (`{sc.get('route','—')}`): "
                 f"{', '.join('`'+f+'`' for f in (sc.get('frames') or [])) or '—'}")
    if c["unassigned_ui"]:
        L.append("")
        L.append(f"**⚠️ Có UI nhưng chưa gán màn:** {', '.join('`'+f+'`' for f in c['unassigned_ui'])}")
    if c["unassigned_logic"]:
        L.append(f"**Logic thuần (không UI):** {', '.join('`'+f+'`' for f in c['unassigned_logic'])}")
    L.append("")
    return "\n".join(L)


# ── render html (self-contained, neumorphic, R16 absolute path) ─────────────
def render_html(c, project, abs_path):
    cc = c["counts"]
    rows_html = "\n".join(
        f'<tr><td><code>{r["fid"]}</code></td><td>{_esc(r["muc_tieu"])}</td>'
        f'<td><span class="role r-{r["ui_role"]}">{r["ui_role"]}</span></td>'
        f'<td>{_esc(r["screen"]) or "—"}</td><td><code>{r["route"] or "—"}</code></td>'
        f'<td>{", ".join(r["clause_ids"]) or "—"}</td>'
        f'<td><code>{_esc(r["acceptance"]) or "—"}</code></td>'
        f'<td><span class="st s-{_stkey(r["status"])}">{r["status"]}</span></td></tr>'
        for r in c["rows"])
    warn_html = ""
    if c["warnings"]:
        items = "".join(f"<li>{_esc(w)}</li>" for w in c["warnings"])
        warn_html = f'<div class="warn"><b>⚠️ Lệch cần xử lý ({len(c["warnings"])})</b><ul>{items}</ul></div>'
    screens_html = "".join(
        f'<div class="screen"><h3>{_esc(sc.get("title", sc.get("id")))} '
        f'<code>{sc.get("route","—")}</code></h3>'
        f'<div class="chips">{"".join("<span class=chip>"+_esc(f)+"</span>" for f in (sc.get("frames") or [])) or "—"}</div></div>'
        for sc in c["screens"])
    return _HTML.format(project=_esc(project), navstyle=_esc(str(c["nav_style"])),
                        nf=cc["frames"], ns=cc["screens"], nr=cc["routes"],
                        rows=rows_html, warn=warn_html, screens=screens_html, abs_path=_esc(abs_path))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _stkey(s):
    return {"xong": "ok", "đỏ": "red"}.get(s, "pending")


_HTML = """<!doctype html><html lang=vi><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>UI Contract — {project}</title>
<script>(function(){{try{{var t=localStorage.getItem('uic-theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}}})();</script>
<style>
:root{{--bg:#e0e5ec;--ink:#3a4252;--ink2:#6b7280;--acc:#4a6cf7;--shl:rgba(255,255,255,.75);--shd:rgba(163,177,198,.55);--card:#e0e5ec}}
html[data-theme=dark]{{--bg:#2a2d32;--ink:#c8ccd4;--ink2:#8b93a1;--acc:#5d7bf9;--shl:rgba(255,255,255,.04);--shd:rgba(0,0,0,.55);--card:#2a2d32}}
*{{box-sizing:border-box}}
body{{margin:0;padding:32px 20px 80px;background:var(--bg);color:var(--ink);font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-size:24px;letter-spacing:-.02em;margin:0 0 4px}}
.sub{{color:var(--ink2);font-size:13px;margin-bottom:22px}}
.tiles{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:22px}}
.tile{{flex:1;min-width:130px;padding:16px 18px;border-radius:18px;background:var(--card);box-shadow:-6px -6px 12px var(--shl),6px 6px 12px var(--shd)}}
.tile .n{{font-size:26px;font-weight:800;color:var(--acc);font-variant-numeric:tabular-nums}}
.tile .l{{font-size:11.5px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}}
.card{{border-radius:20px;background:var(--card);box-shadow:-6px -6px 12px var(--shl),6px 6px 12px var(--shd);padding:8px;margin-bottom:22px;overflow:hidden}}
.card.pad{{padding:18px 22px}}
.tblwrap{{overflow-x:auto;border-radius:14px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid rgba(120,130,150,.16);vertical-align:top}}
th{{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2)}}
code{{font-family:'SF Mono',ui-monospace,Menlo,monospace;font-size:11px;background:rgba(120,130,160,.12);padding:1px 5px;border-radius:5px}}
.role{{font-size:10.5px;padding:2px 8px;border-radius:999px;font-weight:600}}
.r-none{{color:var(--ink2);background:rgba(120,130,150,.14)}}
.r-screen,.r-form,.r-panel,.r-widget,.r-action{{color:var(--acc);background:rgba(74,108,247,.14)}}
.st{{font-size:10.5px;padding:2px 8px;border-radius:999px;font-weight:600}}
.s-ok{{color:#1a7a44;background:rgba(52,199,89,.18)}}
.s-red{{color:#c0392b;background:rgba(255,59,48,.16)}}
.s-pending{{color:var(--ink2);background:rgba(120,130,150,.14)}}
.warn{{border-radius:16px;padding:14px 18px;margin-bottom:22px;background:var(--card);box-shadow:inset -4px -4px 8px var(--shl),inset 4px 4px 8px var(--shd);border-left:4px solid #ff9500}}
.warn ul{{margin:8px 0 0;padding-left:18px;font-size:12.5px}}
.screen{{padding:12px 6px;border-bottom:1px solid rgba(120,130,150,.14)}}
.screen:last-child{{border-bottom:none}}
.screen h3{{margin:0 0 8px;font-size:14px}}
.chips{{display:flex;gap:7px;flex-wrap:wrap}}
.chip{{font-size:11px;padding:3px 10px;border-radius:999px;background:var(--card);box-shadow:-3px -3px 6px var(--shl),3px 3px 6px var(--shd);color:var(--ink)}}
.tgl{{position:fixed;top:14px;right:16px;width:44px;height:26px;border-radius:999px;background:var(--card);box-shadow:inset -3px -3px 6px var(--shl),inset 3px 3px 6px var(--shd);cursor:pointer;border:none}}
.tgl::after{{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:var(--acc);transition:left .18s}}
html[data-theme=dark] .tgl::after{{left:21px}}
h2{{font-size:16px;margin:0 0 12px}}
.foot{{margin-top:30px;font-size:11px;color:var(--ink2)}}
</style></head><body>
<button class=tgl id=tgl aria-label="Đổi giao diện"></button>
<div class=wrap>
<h1>UI Contract — {project}</h1>
<div class=sub>Contract chốt thực hiện · sinh tự động từ frames + <code>br/ui-layout.yaml</code> · nav_style <code>{navstyle}</code></div>
<div class=tiles>
  <div class=tile><div class=n>{nf}</div><div class=l>frame</div></div>
  <div class=tile><div class=n>{ns}</div><div class=l>màn hình</div></div>
  <div class=tile><div class=n>{nr}</div><div class=l>route thật</div></div>
</div>
{warn}
<div class="card pad"><h2>Bảng contract</h2><div class=tblwrap><table>
<thead><tr><th>frame</th><th>làm gì</th><th>ui_role</th><th>màn hình</th><th>route</th><th>clause</th><th>acceptance (chốt)</th><th>trạng thái</th></tr></thead>
<tbody>{rows}</tbody></table></div></div>
<div class="card pad"><h2>Màn hình → frame</h2>{screens}</div>
<div class=foot>📄 File: <code>{abs_path}</code></div>
</div>
<script>
document.getElementById('tgl').addEventListener('click',function(){{var d=document.documentElement,n=d.getAttribute('data-theme')==='dark'?'light':'dark';d.setAttribute('data-theme',n);try{{localStorage.setItem('uic-theme',n)}}catch(e){{}}}});
</script></body></html>"""


def cmd_build(frames_dir, layout, root, out_md, out_html):
    if yaml is None:
        print("  [FAIL] cần PyYAML để đọc ui-layout.yaml", file=sys.stderr)
        return 2
    project = Path(root).resolve().name
    c = build_contract(frames_dir, layout, root)
    Path(out_md).write_text(render_md(c, project), encoding="utf-8")
    html_abs = str(Path(out_html).resolve())
    Path(out_html).write_text(render_html(c, project, html_abs), encoding="utf-8")
    cc = c["counts"]
    print(f"  contract: {cc['frames']} frame · {cc['screens']} màn · {cc['routes']} route "
          f"· {len(c['warnings'])} lệch")
    print(f"    md   → {out_md}")
    print(f"    html → {out_html}")
    if c["warnings"]:
        for w in c["warnings"][:6]:
            print(f"    ⚠️ {w}")
    return 0


# ── selftest ────────────────────────────────────────────────────────────────
def selftest():
    import tempfile
    ok = True

    def chk(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
            print("  [FAIL]", msg)

    FR = """---
schema_version: 0
frame_id: {fid}
created_by: slicer
parent_br: BR.md
clause_ids: [C1]
parent_br_hash: x
muc_tieu: "Frame {fid} làm việc nghiệp vụ cụ thể cho hệ thống"
scope_code: ["app/{fid}.py"]
scope_test: ["tests/{fid}.py"]
acceptance_test: "python3 -m tests.{fid}"
ui_role: {role}
ui_screen: {screen}
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
        d = Path(td); fd = d / "frames"; fd.mkdir()
        (fd / "a.md").write_text(FR.format(fid="frame-a", role="form", screen="s1"))
        (fd / "b.md").write_text(FR.format(fid="frame-b", role="panel", screen="s1"))
        (fd / "c.md").write_text(FR.format(fid="frame-c", role="none", screen=""))
        layout = d / "ui-layout.yaml"
        layout.write_text(
            "nav_style: tabs\nscreens:\n"
            "  - id: s1\n    title: Màn Một\n    route: /one\n    frames: [frame-a, frame-b]\n"
            "  - id: s2\n    title: Màn Hai\n    route: /two\n    frames: [frame-ghost]\n",
            encoding="utf-8")
        c = build_contract(fd, layout, td)
        chk(c["counts"]["frames"] == 3, f"frames count {c['counts']}")
        chk(c["counts"]["screens"] == 2, "screens count")
        chk(c["counts"]["routes"] == 2, f"routes count {c['routes']}")
        a = next(r for r in c["rows"] if r["fid"] == "frame-a")
        chk(a["screen"] == "Màn Một" and a["route"] == "/one", f"frame-a join sai: {a}")
        chk("frame-c" in c["unassigned_logic"], "frame-c logic thuần phải ở unassigned_logic")
        chk(any("frame-ghost" in w and "KHÔNG tồn tại" in w for w in c["warnings"]),
            f"phải cảnh báo ghost frame: {c['warnings']}")
        # mismatch ui_screen
        (fd / "e.md").write_text(FR.format(fid="frame-e", role="form", screen="s9"))
        layout.write_text(
            "nav_style: tabs\nscreens:\n  - id: s1\n    title: M1\n    route: /one\n    frames: [frame-e]\n",
            encoding="utf-8")
        c2 = build_contract(fd, layout, td)
        chk(any("frame-e" in w and "ui_screen" in w for w in c2["warnings"]), "phải cảnh báo ui_screen lệch")
        md = render_md(c, "proj")
        chk("frame-a" in md and "route thật" in md, "md thiếu nội dung")
        html = render_html(c, "proj", "/abs/x.html")
        chk("/abs/x.html" in html and "frame-a" in html, "html thiếu abs path / nội dung")
        chk("{" not in html.split("<body>")[1] or "}" not in html.split("<body>")[1].split("<script>")[0], "html còn placeholder chưa điền")

    print("br-contract self-test:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-contract.py", description="Sinh UI Contract (md+html) từ frames + ui-layout.")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="sinh UI-CONTRACT.md + .html")
    b.add_argument("frames_dir")
    b.add_argument("--layout", default="br/ui-layout.yaml")
    b.add_argument("--root", default=".")
    b.add_argument("--out-md", default="br/UI-CONTRACT.md")
    b.add_argument("--out-html", default="br/UI-CONTRACT.html")
    b.set_defaults(func=lambda a: cmd_build(a.frames_dir, a.layout, a.root, a.out_md, a.out_html))
    s = sub.add_parser("selftest", help="offline deterministic checks")
    s.set_defaults(func=lambda a: selftest())
    return p


if __name__ == "__main__":
    _args = build_parser().parse_args()
    sys.exit(_args.func(_args))
