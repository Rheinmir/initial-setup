#!/usr/bin/env python3
"""build-overstack-docs — sinh TÀI LIỆU USER cho framework **overstack** thành MỘT file HTML
self-contained (glass docs-site-macos), luôn-mới.

Vì sao bằng code: số skill/rule và bảng tham chiếu phải khớp đĩa, không drift. Prose (giải
thích từng phần) là chuỗi tay trong file này; bảng skill/rule + số đếm thì PULL LIVE từ đĩa.

Travel: trang sinh ra ở llmwiki/html/overstack.html — được un-gitignore + nằm trong template
manifest + install-harness copy xuống dự án downstream, nên user nào cài overstack cũng có docs.

CLI:
  build-overstack-docs.py            # ghi llmwiki/html/overstack.html từ đĩa
  build-overstack-docs.py --check    # exit 2 nếu file cũ so với bản sinh (giữ docs luôn-mới)
"""
import re
import sys
from pathlib import Path


def detect_root() -> Path:
    repo = Path(__file__).resolve().parents[2]
    if (repo / "llmwiki").is_dir():
        return repo
    return Path.cwd()


ROOT = detect_root()
OUT = ROOT / "llmwiki" / "html" / "overstack.html"

# ── live data (đếm từ đĩa) ────────────────────────────────────────────────────────────────
def _fm_desc(p: Path) -> str:
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if not m:
        return ""
    fm = m.group(1)
    dm = re.search(r"^description:\s*(.*)$", fm, re.M)
    if not dm:
        return ""
    val = dm.group(1).strip()
    if val in (">", ">-", "|", "|-"):  # YAML folded/literal → gom dòng thụt sau
        body = []
        for ln in fm[dm.end():].splitlines():
            if ln.strip() and (ln.startswith(" ") or ln.startswith("\t")):
                body.append(ln.strip())
            elif ln.strip():
                break
        val = " ".join(body)
    val = val.strip().strip('"').strip("'")
    return re.split(r"(?<=[.!?。])\s|—| - |\. |\. ", val, 1)[0].strip()


def load_loops(root: Path) -> dict:
    try:
        t = (root / "harness" / "scripts" / "sync-skills.py").read_text(encoding="utf-8")
        m = re.search(r"LOOP_MAP\s*=\s*\{(.*?)\}", t, re.S)
        return dict(re.findall(r'"([a-z0-9-]+)"\s*:\s*"([a-z-]+)"', m.group(1))) if m else {}
    except Exception:
        return {}


def skills_by_loop(root: Path):
    loops = load_loops(root)
    sk_dir = root / "skills"
    if not (sk_dir.is_dir() and any(sk_dir.glob("*/SKILL.md"))):
        sk_dir = Path.home() / ".claude" / "skills"
    by = {}
    n = 0
    for d in sorted(sk_dir.glob("*/")):
        sk = d / "SKILL.md"
        if not sk.is_file():
            continue
        n += 1
        loop = loops.get(d.name, "utils")
        by.setdefault(loop, []).append((d.name, _fm_desc(sk)))
    return by, n


def rules(root: Path):
    pol = next((p for p in (root / "harness" / "poc-vendor-neutral" / "policy.yaml",
                            root / "harness" / "policy.yaml") if p.is_file()), None)
    if not pol:
        return []
    out = []
    try:
        import yaml
        rd = (yaml.safe_load(pol.read_text(encoding="utf-8")) or {}).get("rules", {})
        for r in (rd.values() if isinstance(rd, dict) else rd):
            if isinstance(r, dict) and r.get("id"):
                out.append((r["id"], str(r.get("name", "")).strip(), str(r.get("statement", "")).strip()))
    except Exception:
        for rid, name in re.findall(r"id:\s*(R\d+).*?name:\s*([^\n]+)", pol.read_text(encoding="utf-8"), re.S):
            out.append((rid, name.strip().strip('"'), ""))
    return sorted(set(out), key=lambda r: int(r[0][1:]))


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_personas(root: Path):
    """18 persona-lens + cases từ harness/council.personas.yaml (nguồn chân lý). Fail-safe → {}."""
    p = root / "harness" / "council.personas.yaml"
    if not p.is_file():
        return {}, {}
    try:
        import yaml
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return d.get("personas", {}), d.get("cases", {})
    except Exception:
        return {}, {}


# ── style + script (glass docs-site-macos, đã chứng minh ở master-wiki) ───────────────────
ACCENTS = [("#0a84ff", "10,132,255"), ("#30b0c7", "48,176,199"), ("#5856d6", "88,86,214"),
           ("#28a745", "52,199,89"), ("#f08c00", "255,149,0"), ("#e0264b", "255,45,85")]

# Loop nào >~8 skill → chia nhánh con theo CHỨC NĂNG (data nguồn-sự-thật, dùng cho cả mind map
# LẪN bảng tham chiếu). Mỗi loop: ([(key, nhãn) theo thứ tự], {skill→key}). Nhóm nhận màu g0,g1,…
LOOP_GROUPS = {
    "dev-loop": (
        [("edit", "✏️ sửa code an toàn"), ("build", "🏗️ dựng & onboard"), ("eval", "📊 eval & vòng lặp")],
        {"propose": "edit", "plan": "edit", "qc-code": "edit", "teach-me": "edit", "impact-check": "edit", "safe-change": "edit", "verify-before-commit": "edit",
         "build-now-adapt-later": "edit",
         "new-project-setup": "build", "onboard-codebase": "build", "new-skill": "build",
         "skill-provenance": "build", "doyourmagic": "build",
         "wikieval": "eval", "ship": "eval", "loop-runner": "eval", "failure-flywheel": "eval"}),
    "orchestrate": (
        [("dispatch", "🐳 điều phối"), ("eval", "📊 đánh giá"), ("ops", "🚀 vận hành & deploy")],
        {"orca-workflow": "dispatch", "orca-onboard": "dispatch", "orchestration": "dispatch",
         "orca-cli": "dispatch", "orca-dispatch-reference": "dispatch", "wayfinder": "dispatch",
         "orca-handover": "dispatch",
         "council": "eval", "trace-grader": "eval", "orca-eval": "eval",
         "orca-sec-scans": "ops", "jenkins-agent-l3-deploy": "ops", "orca-issue": "ops"}),
    "utils": (
        [("docs", "📄 tài liệu & render"), ("taste", "🎨 thiết kế & style"), ("imagegen", "🖼️ image→code/gen"),
         ("caveman", "🦴 caveman"), ("fdk", "🛠️ framework-dev"), ("utility", "🔧 tiện ích khác")],
        {"docs-site-macos": "docs", "extract-site": "docs", "md-to-html": "docs",
         "web-crawl": "docs", "web-clone": "docs",
         "tour-guide": "taste", "tour-guide-supademo": "taste",
         "brandkit": "taste", "hallmark": "taste", "design-taste-frontend": "taste", "design-taste-frontend-v1": "taste",
         "gpt-taste": "taste", "high-end-visual-design": "taste", "stitch-design-taste": "taste",
         "minimalist-ui": "taste", "industrial-brutalist-ui": "taste", "redesign-existing-projects": "taste",
         "cursor-animated-sites": "docs",
         "image-to-code": "imagegen", "imagegen-frontend-mobile": "imagegen",
         "imagegen-frontend-web": "imagegen",
         "cavecrew": "caveman", "caveman": "caveman", "caveman-commit": "caveman", "caveman-compress": "caveman",
         "caveman-help": "caveman", "caveman-review": "caveman", "caveman-stats": "caveman",
         "fdk": "fdk", "fdk-uat": "fdk", "medic": "fdk", "harness-tour": "fdk", "harness-update": "fdk", "health-check": "fdk",
         "snapshot-push": "fdk", "sync-template": "fdk", "docs-curate": "fdk",
         "agent-reach": "utility",
         "check-approve": "utility", "computer-use": "utility", "find-skills": "utility",
         "full-output-enforcement": "utility", "join-project": "utility", "last30days": "utility",
         "raise-issue": "utility", "ovs-notes": "utility", "frontier-scan": "utility",
         "uat-nonit-testcase": "utility", "fable5": "utility", "graph-mode": "utility", "i-have-adhd": "utility"}),
}


UNCLASSIFIED = []   # (loop, skill) chưa khai trong LOOP_GROUPS — main() cảnh báo để phân loại 1 lần


def group_key(loop, name):
    """key nhóm chức năng của skill; 'uncat' nếu loop chia nhóm mà skill chưa khai; None nếu loop không chia."""
    cfg = LOOP_GROUPS.get(loop)
    if not cfg:
        return None
    order, gmap = cfg
    return gmap.get(name, "uncat")

CSS_BASE = r"""
:root{--font:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,sans-serif;
--mono:'SF Mono',ui-monospace,Menlo,monospace;--glass2:rgba(255,255,255,.7);--glass3:rgba(255,255,255,.88);
--edge:inset 0 1px 0 rgba(255,255,255,.85);--border:rgba(30,90,170,.14);--t1:#0f0f12;--t2:#4a4a55;}
*{box-sizing:border-box}html{background:#e9f0fb;scrollbar-width:thin;scrollbar-color:transparent transparent}
html.scrolling{scrollbar-color:rgba(10,132,255,.32) transparent}
body{margin:0;padding-left:232px;font-family:var(--font);color:var(--t1);line-height:1.62;background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.1),transparent 60%),radial-gradient(700px 420px at 95% 12%,rgba(88,86,214,.08),transparent 55%),linear-gradient(180deg,#f7fbff,#eaf2fd);transition:padding-left .28s}
body::before{content:'';position:fixed;inset:-10%;z-index:-1;pointer-events:none;background:radial-gradient(640px 440px at 10% 14%,rgba(10,132,255,.2),transparent 65%),radial-gradient(380px 460px at 4% 52%,rgba(48,176,199,.16),transparent 65%),radial-gradient(540px 400px at 88% 10%,rgba(88,86,214,.12),transparent 60%),radial-gradient(480px 380px at 16% 86%,rgba(52,199,89,.1),transparent 60%);animation:orb 46s ease-in-out infinite alternate}
@keyframes orb{100%{transform:translate(2%,1.5%) scale(1.04)}}
body::after{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;background-image:radial-gradient(rgba(30,90,170,.1) 1px,transparent 1.3px);background-size:22px 22px;mask-image:linear-gradient(180deg,rgba(0,0,0,.55),rgba(0,0,0,.22))}
@media(prefers-reduced-motion:reduce){body::before{animation:none}}
::-webkit-scrollbar{width:11px;height:11px;background:transparent}::-webkit-scrollbar-thumb{background:transparent;border-radius:8px;border:3px solid transparent;background-clip:content-box;transition:background-color .25s}html.scrolling::-webkit-scrollbar-thumb,::-webkit-scrollbar-thumb:hover{background-color:rgba(10,132,255,.32)}
/* sidebar: stack KHÔNG bị nén (feedback 2026-07-07) — thiếu chỗ thì CUỘN, scrollbar ẩn hoàn toàn */
nav>*{flex-shrink:0}
nav{scrollbar-width:none;-ms-overflow-style:none}
nav::-webkit-scrollbar{width:0;height:0;display:none}
nav{position:fixed;top:0;left:0;bottom:0;width:232px;z-index:100;overflow-y:auto;display:flex;flex-direction:column;gap:1px;padding:18px 12px;background:linear-gradient(165deg,rgba(255,255,255,.30),rgba(255,255,255,.20) 48%,rgba(240,248,255,.32));backdrop-filter:blur(24px) saturate(1.7);-webkit-backdrop-filter:blur(24px) saturate(1.7);border-right:1px solid rgba(30,90,170,.12);box-shadow:inset -1px 0 0 rgba(30,90,170,.10),4px 0 24px rgba(30,90,170,.08);transition:transform .28s}
nav::before{content:'';position:absolute;inset:0;pointer-events:none;background:radial-gradient(220px 160px at 18% 4%,rgba(255,255,255,.34),transparent 70%)}nav>*{position:relative}
nav
.logo{margin:0 0 8px;padding:6px 10px;font-weight:800;font-size:16px;letter-spacing:-.03em;color:#0a84ff}
nav .logo small{display:block;font-size:10px;font-weight:600;color:var(--t2);-webkit-text-fill-color:var(--t2);letter-spacing:0}
nav a{position:relative;overflow:hidden;padding:5px 11px;border-radius:9px;font-size:12px;color:var(--t2);text-decoration:none;transition:background .15s,color .15s}nav a:hover{background:rgba(10,132,255,.06);color:#0a84ff}nav a.active{color:#0a84ff;background:rgba(10,132,255,.08);font-weight:600}
nav a .ic{display:inline-block;width:17px;margin-right:6px;text-align:center;opacity:.95}
nav .grp{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#9aa4b2;margin:12px 12px 2px}
.nav-close{position:absolute;top:10px;right:10px;width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--t2);cursor:pointer;background:rgba(0,0,0,.05);border:none;overflow:hidden}.nav-close:hover{color:#0a84ff;background:rgba(10,132,255,.1)}
.nav-toggle{position:fixed;top:12px;left:12px;z-index:120;width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:14px;color:var(--t2);cursor:pointer;background:linear-gradient(165deg,rgba(255,255,255,.5),rgba(255,255,255,.24));backdrop-filter:blur(24px) saturate(1.7);-webkit-backdrop-filter:blur(24px) saturate(1.7);border:1px solid transparent;box-shadow:inset 0 1px 0 rgba(255,255,255,.75),0 0 0 1px rgba(30,90,170,.08),0 2px 10px rgba(30,90,170,.12);transition:opacity .2s;overflow:hidden}body:not(.nav-collapsed) .nav-toggle{opacity:0;pointer-events:none}body.nav-collapsed nav{transform:translateX(-100%)}body.nav-collapsed{padding-left:0}@media(max-width:640px){body{padding-left:0}}
.ripple-ink{position:absolute;border-radius:50%;pointer-events:none;background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.7) 0%,rgba(255,255,255,.28) 38%,rgba(10,132,255,.2) 72%,transparent 100%);box-shadow:inset 0 1px 0 rgba(255,255,255,.9),inset 0 -10px 20px rgba(10,132,255,.12),0 0 14px rgba(10,132,255,.1);backdrop-filter:blur(2px) saturate(1.25);-webkit-backdrop-filter:blur(2px) saturate(1.25);transform:scale(0);opacity:1;animation:rippleGrow .6s cubic-bezier(.25,.46,.45,.94) forwards}
@keyframes rippleGrow{55%{transform:scale(1);opacity:.75}100%{transform:scale(1.04);opacity:0}}
.ripple{position:absolute;border-radius:50%;pointer-events:none;transform:scale(0);opacity:.9;background:radial-gradient(circle,rgba(255,255,255,.6) 0%,rgba(10,132,255,.22) 35%,transparent 70%);box-shadow:0 0 0 1px rgba(255,255,255,.45);animation:rippleWave .65s cubic-bezier(.2,.6,.3,1) forwards}
@keyframes rippleWave{to{transform:scale(2.8);opacity:0}}
.hero{max-width:1080px;margin:0 auto;padding:74px 24px 8px}.hero .eyebrow{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#5856d6;background:rgba(88,86,214,.1);padding:4px 12px;border-radius:999px;margin-bottom:14px}
.hero h1{font-size:clamp(26px,4vw,40px);line-height:1.06;letter-spacing:-.03em;margin:0 0 12px;color:#0a2540}
.hero p{font-size:13.5px;color:var(--t2);max-width:780px;margin:0}
section{position:relative}.sec::before{content:'';position:absolute;top:0;bottom:0;left:50%;width:100vw;transform:translateX(-50%);pointer-events:none}
.inner{position:relative;max-width:1080px;margin:0 auto;padding:40px 24px 44px}
.tag{display:inline-block;font-size:12px;font-weight:700;padding:4px 12px;border-radius:999px;margin-bottom:10px}
h2{font-size:21px;letter-spacing:-.02em;color:#1d1d1f;margin:0 0 6px}.lead{font-size:14px;color:var(--t2);max-width:840px;margin:0 0 8px}
h3{font-size:14px;margin:20px 0 6px;color:#1d1d1f}
p{margin:10px 0;max-width:860px;font-size:13.5px}
.card{background:var(--glass2);backdrop-filter:blur(8px) saturate(1.1);-webkit-backdrop-filter:blur(8px) saturate(1.1);border:1px solid var(--border);border-radius:16px;box-shadow:var(--edge),0 4px 20px rgba(0,0,0,.06);padding:18px 20px;margin-top:14px}
.card h4{margin:0 0 9px;font-size:13.5px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.grid3{grid-template-columns:1fr 1fr 1fr}@media(max-width:780px){.grid,.grid3{grid-template-columns:1fr}}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;margin-top:12px}
.pcard{display:flex;gap:10px;align-items:flex-start;background:var(--glass2);border:1px solid var(--border);border-radius:12px;padding:10px 11px}
.pcard .pav{width:36px;height:36px;flex-shrink:0}.pcard .pn{font-size:12px;font-weight:700;color:var(--t1)}
.pcard .pl{font-size:10px;font-weight:600}.pcard .ps{font-size:10px;color:var(--t2);margin-top:2px;line-height:1.35}
code{font-family:var(--mono);font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0;font-size:.85em;background:rgba(10,132,255,.08);padding:1px 5px;border-radius:5px;color:#0a5ec7}
.code-wrap{position:relative;margin:12px 0}
pre{background:rgba(13,24,40,.92);color:#e6edf6;border-radius:12px;padding:14px 46px 14px 16px;white-space:pre-wrap;word-break:break-word;overflow-wrap:anywhere;font-family:var(--mono);font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0;font-size:12.5px;line-height:1.55;margin:0;box-shadow:var(--edge),0 4px 20px rgba(0,0,0,.12)}pre code{background:none;color:inherit;padding:0;white-space:inherit}
.code-copy{position:absolute;top:7px;right:7px;z-index:2;width:28px;height:26px;display:inline-flex;align-items:center;justify-content:center;background:rgba(255,255,255,.12);color:#cbd5e1;border:1px solid rgba(255,255,255,.18);border-radius:7px;cursor:pointer;opacity:0;transition:opacity .15s,background .15s,color .15s}.code-copy svg{width:14px;height:14px;display:block}
.code-wrap:hover .code-copy{opacity:1}.code-copy:hover{background:rgba(255,255,255,.22);color:#fff}.code-copy.copied{background:rgba(16,185,129,.28);color:#6ee7b7;border-color:rgba(16,185,129,.5);opacity:1}
@media(max-width:640px){.code-copy{opacity:1}}
ul.s{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:6px}ul.s li{position:relative;padding-left:18px;font-size:12.5px;color:var(--t2)}ul.s li::before{content:'›';position:absolute;left:2px;font-weight:700;color:#5856d6}
ul.s li b{color:var(--t1)}
.kpi{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}.kpi .b{flex:1;min-width:92px;background:var(--glass2);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:14px;box-shadow:var(--edge),0 4px 18px rgba(0,0,0,.05);padding:13px 15px}
.kpi .n{font-size:22px;font-weight:800;letter-spacing:-.02em;line-height:1}.kpi .l{font-size:10.5px;color:var(--t2);margin-top:4px}
.chip{display:inline-block;font-size:11px;font-weight:600;font-family:var(--mono);background:rgba(10,132,255,.08);color:#0a5ec7;padding:2px 8px;border-radius:6px;margin:3px 4px 0 0}
ol.ck{margin:12px 0 0;padding-left:20px}ol.ck li{font-size:12.5px;color:var(--t2);margin:6px 0}ol.ck li b{color:var(--t1)}
.skip{position:fixed;top:-60px;left:12px;z-index:200;padding:8px 14px;background:#0a84ff;color:#fff;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;transition:top .18s}.skip:focus{top:12px}
.table-wrap{overflow-x:auto;margin:14px 0;-webkit-overflow-scrolling:touch}.table-wrap table{margin:0}
table{width:100%;border-collapse:collapse;margin:14px 0;background:var(--glass3);backdrop-filter:blur(4px);border:1px solid var(--border);border-radius:12px;overflow:hidden;font-size:12.5px;box-shadow:var(--edge),0 4px 18px rgba(0,0,0,.05)}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:top}th{font-size:10.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--t2);background:rgba(10,132,255,.05)}tr:last-child td{border-bottom:none}td code{white-space:nowrap}
.note{background:rgba(255,149,0,.08);border:1px solid rgba(255,149,0,.25);border-radius:14px;padding:16px 18px;margin-top:14px}
.note h4{margin:0 0 8px;color:#b46a00}
footer{max-width:1080px;margin:0 auto;padding:26px 24px 60px;font-size:12px;color:var(--t2);border-top:1px solid var(--border)}
/* mind map — distilled từ skills-cheatsheet (node chip glass + chevron + collapse, default close) */
.mm{overflow-x:auto;padding:14px 4px 6px}
.mm .tree,.mm .children{display:flex;flex-direction:column;gap:9px;justify-content:center}
.mm .row{display:flex;align-items:center;gap:48px;position:relative}
.mm .children{position:relative}
.mm .children.collapsed{display:none}
.mm .node{position:relative;display:inline-flex;flex-direction:column;gap:1px;padding:7px 13px;border-radius:13px;cursor:default;white-space:nowrap;background:var(--glass2);backdrop-filter:blur(7px) saturate(1.1);-webkit-backdrop-filter:blur(7px) saturate(1.1);border:1px solid var(--border);box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 3px 14px rgba(20,40,90,.07);transition:transform .12s,box-shadow .12s}
.mm .node.has-children{cursor:pointer}
.mm .node:hover{transform:translateY(-1px);box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 6px 20px rgba(20,40,90,.12)}
.mm .node .nm{font-size:13px;font-weight:700;letter-spacing:-.01em}
.mm .node .ds{font-size:10.5px;color:var(--t2);font-weight:500}
.mm .node .ct{font-size:10px;color:#fff;font-weight:700;padding:1px 7px;border-radius:999px;position:absolute;top:-8px;right:-8px;background:#0a84ff}
.mm .node.has-children::after{content:'';position:absolute;right:-7px;top:50%;width:6px;height:6px;border-right:2px solid var(--t2);border-bottom:2px solid var(--t2);transform:translateY(-50%) rotate(-45deg);opacity:.5}
.mm .node.collapsed-parent::after{transform:translateY(-50%) rotate(45deg)}
.mm .node.root{background:linear-gradient(135deg,rgba(10,132,255,.16),rgba(88,86,214,.14));border-color:rgba(10,132,255,.4)}
.mm .node.root .nm{font-size:15px}
.mm-canvas{position:relative;width:max-content}
.mm-links{position:absolute;top:0;left:0;pointer-events:none;overflow:visible;z-index:0}
.mm-links path{fill:none;stroke-width:2.2;opacity:.55;stroke-linecap:round}
.mm .tree{position:relative;z-index:1}
.mm .b-wiki .nm{color:#1f8a9c}.mm .b-wiki .ct{background:#30b0c7}.mm .b-wiki.node{border-color:rgba(48,176,199,.4)}
.mm .b-dev .nm{color:#5856d6}.mm .b-dev .ct{background:#5856d6}.mm .b-dev.node{border-color:rgba(88,86,214,.4)}
.mm .b-orch .nm{color:#e07b00}.mm .b-orch .ct{background:#ff9500}.mm .b-orch.node{border-color:rgba(255,149,0,.42)}
.mm .b-utils .nm{color:#1e8e3e}.mm .b-utils .ct{background:#34c759}.mm .b-utils.node{border-color:rgba(52,199,89,.4)}
.mm .b-rule .nm{color:#e0264b}.mm .b-rule .ct{background:#ff2d55}.mm .b-rule.node{border-color:rgba(255,45,85,.4)}
.mm .g0 .nm{color:#0a5ec7}.mm .g0 .ct{background:#0a84ff}.mm .g0.node{border-color:rgba(10,132,255,.4)}
.mm .g1 .nm{color:#1f8a9c}.mm .g1 .ct{background:#30b0c7}.mm .g1.node{border-color:rgba(48,176,199,.4)}
.mm .g2 .nm{color:#5856d6}.mm .g2 .ct{background:#5856d6}.mm .g2.node{border-color:rgba(88,86,214,.4)}
.mm .g3 .nm{color:#1e8e3e}.mm .g3 .ct{background:#34c759}.mm .g3.node{border-color:rgba(52,199,89,.4)}
.mm .g4 .nm{color:#c77f00}.mm .g4 .ct{background:#ff9500}.mm .g4.node{border-color:rgba(255,149,0,.42)}
.mm .g5 .nm{color:#c81e4a}.mm .g5 .ct{background:#ff2d55}.mm .g5.node{border-color:rgba(255,45,85,.4)}
/* ── redesign upgrades (a11y focus · orphan-fix · smooth-scroll · tabular số) ── */
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
h1,h2,h3,.hero h1{text-wrap:balance}p,.lead,.hero p{text-wrap:pretty}
.kpi .n,.mm .node .ct,th,td code{font-variant-numeric:tabular-nums}
/* focus-visible: keyboard-only ring, không ăn vào hover chuột */
a:focus-visible,button:focus-visible,nav a:focus-visible,.code-copy:focus-visible,.node:focus-visible{outline:2px solid #0a84ff;outline-offset:2px;border-radius:8px}
:focus:not(:focus-visible){outline:none}
/* active/pressed feedback nhất quán vật lý */
nav a:active{transform:translateY(.5px)}
.code-copy:active,.nav-toggle:active,.nav-close:active{transform:scale(.94)}

/* theme-switch — NÚT GẠT sáng/tối, hàng footer dính ĐÁY sidebar (feedback 2026-07-06: đừng rải 2 góc, đừng chen dưới logo) */
.theme-row{position:sticky;bottom:-18px;margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:8px;margin-left:-12px;margin-right:-12px;margin-bottom:-18px;padding:11px 16px;border-top:1px solid rgba(30,90,170,.14);background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(240,248,255,.65));backdrop-filter:blur(14px) saturate(1.4);-webkit-backdrop-filter:blur(14px) saturate(1.4)}
.theme-row .lbl{font-size:10.5px;font-weight:600;letter-spacing:.02em;color:var(--t2)}
.theme-switch{display:inline-flex;align-items:center;cursor:pointer;-webkit-tap-highlight-color:transparent}
.theme-switch .track{position:relative;width:50px;height:26px;border-radius:999px;background:linear-gradient(165deg,rgba(255,255,255,.6),rgba(255,255,255,.3));border:1px solid rgba(30,90,170,.2);box-shadow:inset 0 1px 3px rgba(30,90,170,.14);transition:background .2s,border-color .2s}
.theme-switch .track::before{content:'☀️';position:absolute;left:6px;top:50%;transform:translateY(-50%);font-size:11px}
.theme-switch .track::after{content:'🌙';position:absolute;right:6px;top:50%;transform:translateY(-50%);font-size:11px}
.theme-switch .knob{position:absolute;z-index:1;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 4px rgba(20,40,90,.3);transition:left .18s ease}
.theme-switch.on .knob{left:26px}
.theme-switch.on .track{background:linear-gradient(165deg,#2b3040,#191d27);border-color:rgba(120,160,220,.3)}
.theme-switch:active .knob{transform:scale(.92)}"""

# ── Dark mode (issue #14) + toggle sáng/tối (feedback 2026-07-06) ──────────────
# MỘT nguồn _DARK_RULES sinh RA HAI khối CSS (chống drift giữa 2 bản):
#   (a) @media prefers-color-scheme — mặc định theo hệ, CHỈ khi user chưa chọn light
#   (b) html[data-theme=dark]      — user bấm toggle chọn dark tường minh (localStorage)
# Selector dùng "&" làm placeholder cho <html>; light = base CSS nên không cần khối riêng.
_DARK_RULES = [
    ("&", "--glass2:rgba(30,34,44,.72);--glass3:rgba(36,40,52,.9);"
          "--edge:inset 0 1px 0 rgba(255,255,255,.06);--border:rgba(120,160,220,.18);"
          "--t1:#e7e9ee;--t2:#9aa2b1;background:#0c0f16;scrollbar-color:transparent transparent"),
    ("& body", "color:var(--t1);background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.14),transparent 60%),"
               "radial-gradient(700px 420px at 95% 12%,rgba(88,86,214,.12),transparent 55%),"
               "linear-gradient(180deg,#0d1017,#0a0d13)"),
    ("& h1,& h2,& h3,& h4", "color:#f2f4f8"),
    ("& nav", "background:rgba(18,21,28,.82)"),
    ("& table th,& table td", "border-color:var(--border)"),
    ("& table th", "background:rgba(255,255,255,.04)"),
    ("& .card,& .note,& .kpi .b,& .mm .node,& .diagram-box", "background:var(--glass2)"),
    ("& a", "color:#5fa8ff"),
    ("& .theme-row", "border-top-color:var(--border);background:linear-gradient(180deg,rgba(24,28,38,.7),rgba(16,20,28,.85))"),
]


def _theme_css() -> str:
    def block(prefix):
        return "\n".join(sel.replace("&", prefix) + "{" + body + "}" for sel, body in _DARK_RULES)
    return ("\n@media (prefers-color-scheme: dark){\n" + block("html:not([data-theme=light])") + "\n}\n"
            + block("html[data-theme=dark]") + "\n")


CSS_BASE += _theme_css()

JS = r"""
(function(){var K='overstack-theme',d=document.documentElement,nav=document.querySelector('nav');if(!nav)return;function isDark(){var t=d.getAttribute('data-theme');return t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
var sw=document.createElement('div');sw.className='theme-switch';sw.id='theme-toggle';sw.dataset.noRipple='1';sw.setAttribute('role','switch');sw.setAttribute('tabindex','0');sw.innerHTML='<span class="track"><span class="knob"></span></span>';
var row=document.createElement('div');row.className='theme-row';var lb=document.createElement('span');lb.className='lbl';lb.textContent='Giao diện';row.appendChild(lb);row.appendChild(sw);nav.appendChild(row);
function paint(){var dk=isDark();sw.classList.toggle('on',dk);sw.setAttribute('aria-checked',dk?'true':'false');sw.setAttribute('aria-label',dk?'Nút gạt giao diện: đang tối — gạt sang sáng':'Nút gạt giao diện: đang sáng — gạt sang tối');sw.title=sw.getAttribute('aria-label')}
function flip(){var next=isDark()?'light':'dark';d.setAttribute('data-theme',next);try{localStorage.setItem(K,next)}catch(e){}paint()}
sw.addEventListener('click',flip);sw.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '||e.key==='Spacebar'){e.preventDefault();flip()}});
try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',paint)}catch(e){}paint()})();
(function(){const n=document.querySelector('nav');if(!n)return;const o=document.createElement('button');o.className='nav-toggle';o.textContent='☰';o.setAttribute('aria-label','Mở menu điều hướng');document.body.appendChild(o);const c=document.createElement('button');c.className='nav-close';c.textContent='✕';c.setAttribute('aria-label','Đóng menu điều hướng');n.appendChild(c);o.onclick=function(){document.body.classList.remove('nav-collapsed')};c.onclick=function(){document.body.classList.add('nav-collapsed')};if(matchMedia('(max-width:640px)').matches)document.body.classList.add('nav-collapsed')})();
(function(){var ls=[].slice.call(document.querySelectorAll('nav a')),ss=[].slice.call(document.querySelectorAll('section[id]'));var ob=new IntersectionObserver(function(es){var a='';es.forEach(function(e){if(e.isIntersecting)a=e.target.id});if(a)ls.forEach(function(l){l.classList.toggle('active',l.getAttribute('href')==='#'+a)})},{rootMargin:'-40% 0px -55% 0px'});ss.forEach(function(s){ob.observe(s)})})();
(function(){var t;addEventListener('scroll',function(){document.documentElement.classList.add('scrolling');clearTimeout(t);t=setTimeout(function(){document.documentElement.classList.remove('scrolling')},900)},{passive:true})})();
(function(){var mm=document.querySelector('.mm');if(!mm)return;var NS='http://www.w3.org/2000/svg';function colorOf(n){return n.classList.contains('b-wiki')?'#30b0c7':n.classList.contains('b-dev')?'#5856d6':n.classList.contains('b-orch')?'#ff9500':n.classList.contains('b-utils')?'#34c759':n.classList.contains('b-rule')?'#ff2d55':n.classList.contains('g0')?'#0a84ff':n.classList.contains('g1')?'#30b0c7':n.classList.contains('g2')?'#5856d6':n.classList.contains('g3')?'#34c759':n.classList.contains('g4')?'#ff9500':n.classList.contains('g5')?'#ff2d55':'#9aa4b2';}function draw(){var canvas=mm.querySelector('.mm-canvas'),svg=mm.querySelector('.mm-links');if(!canvas||!svg)return;var w=canvas.offsetWidth,h=canvas.offsetHeight;svg.setAttribute('width',w);svg.setAttribute('height',h);svg.setAttribute('viewBox','0 0 '+w+' '+h);while(svg.firstChild)svg.removeChild(svg.firstChild);var cR=canvas.getBoundingClientRect();[].slice.call(canvas.querySelectorAll('.node.has-children')).forEach(function(p){var row=p.parentElement,kids=null,ch=row.children;for(var i=0;i<ch.length;i++){if(ch[i].classList.contains('children'))kids=ch[i];}if(!kids||kids.classList.contains('collapsed'))return;var pr=p.getBoundingClientRect(),px=pr.right-cR.left,py=pr.top+pr.height/2-cR.top;[].slice.call(kids.children).forEach(function(crow){var cn=crow.querySelector(':scope > .node');if(!cn)return;var rr=cn.getBoundingClientRect(),cx=rr.left-cR.left,cy=rr.top+rr.height/2-cR.top,dx=Math.max(22,(cx-px)*0.55);var pa=document.createElementNS(NS,'path');pa.setAttribute('d','M'+px+' '+py+' C'+(px+dx)+' '+py+' '+(cx-dx)+' '+cy+' '+cx+' '+cy);pa.setAttribute('stroke',colorOf(cn));svg.appendChild(pa);});});}[].slice.call(mm.querySelectorAll('.node.has-children')).forEach(function(n){var row=n.parentElement,kids=null,c=row.children;for(var i=0;i<c.length;i++){if(c[i].classList.contains('children'))kids=c[i];}if(!kids)return;if(n.classList.contains('cat')){kids.classList.add('collapsed');n.classList.add('collapsed-parent');}n.setAttribute('tabindex','0');n.setAttribute('role','button');n.setAttribute('aria-expanded',String(!kids.classList.contains('collapsed')));var _tog=function(e){e.stopPropagation();if(e.preventDefault)e.preventDefault();var collapsed=kids.classList.toggle('collapsed');n.classList.toggle('collapsed-parent',collapsed);n.setAttribute('aria-expanded',String(!collapsed));draw();};n.addEventListener('click',_tog);n.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '||e.key==='Spacebar')_tog(e);});});draw();addEventListener('load',function(){setTimeout(draw,60);});addEventListener('resize',function(){clearTimeout(window.__mmt);window.__mmt=setTimeout(draw,120);},{passive:true});})();
(function(){var C='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',K='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';document.querySelectorAll('pre.code-block').forEach(function(pre){if(pre.dataset.copy)return;pre.dataset.copy='1';var code=pre.textContent;var w=document.createElement('div');w.className='code-wrap';pre.parentNode.insertBefore(w,pre);w.appendChild(pre);var b=document.createElement('button');b.className='code-copy';b.title='Copy';b.setAttribute('aria-label','Copy');b.innerHTML=C;w.appendChild(b);b.addEventListener('click',function(){var done=function(){b.innerHTML=K;b.classList.add('copied');setTimeout(function(){b.innerHTML=C;b.classList.remove('copied');},1500);};if(navigator.clipboard){navigator.clipboard.writeText(code).then(done,done);}else{var ta=document.createElement('textarea');ta.value=code;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}ta.remove();done();}});});})();
(function(){function attach(el){el.addEventListener('pointerdown',function(e){var r=el.getBoundingClientRect();var x=e.clientX-r.left,y=e.clientY-r.top;var rad=Math.hypot(Math.max(x,r.width-x),Math.max(y,r.height-y));var ink=document.createElement('span');ink.className='ripple-ink';ink.style.width=ink.style.height=rad*2+'px';ink.style.left=(x-rad)+'px';ink.style.top=(y-rad)+'px';el.appendChild(ink);ink.addEventListener('animationend',function(){ink.remove()});});}document.querySelectorAll('nav a, .nav-toggle, .nav-close').forEach(function(el){el.dataset.noRipple='1';attach(el);});})();
(function(){document.addEventListener('pointerdown',function(e){var el=e.target.closest('button, .nav-link, .collapse-toggle, .checklist label');if(!el||el.dataset.noRipple)return;var r=el.getBoundingClientRect();var d=Math.max(r.width,r.height)*1.2;var s=document.createElement('span');s.className='ripple';s.style.cssText='width:'+d+'px;height:'+d+'px;left:'+(e.clientX-r.left-d/2)+'px;top:'+(e.clientY-r.top-d/2)+'px';if(getComputedStyle(el).position==='static')el.style.position='relative';el.style.overflow='hidden';el.appendChild(s);s.addEventListener('animationend',function(){s.remove()});});})();
"""


def accent_css(n: int) -> str:
    out = []
    for i in range(n):
        hexc, rgb = ACCENTS[i % len(ACCENTS)]
        out.append(f"#s{i} .tag{{background:rgba({rgb},.12);color:{hexc}}}"
                   f"#s{i} .card h4{{color:{hexc}}}#s{i} .card li::before{{color:{hexc}}}"
                   f".s{i}::before{{background:linear-gradient(180deg,rgba({rgb},.05),transparent 55%)}}")
    return "\n".join(out)


# ── sections (prose tay; bảng live tiêm vào) ──────────────────────────────────────────────
# Cơ chế runtime + tự-gác (KHÔNG phải rule) — DERIVE từ harness/mechanisms.yaml (ADR-001,
# council-025): trước đây là hằng-số CHÉP TAY ở đây → drift âm thầm mà "khớp đĩa ✓" không bắt.
# Giờ là DATA: overstack.html sinh từ manifest, và medic probe `narrative` cắn khi cơ-chế LIVE
# vắng khỏi trang. KHÔNG chép tay lại ở đây nữa (đó là gốc-rễ bệnh đã chữa).
def load_mechanisms(root: Path):
    """Đọc harness/mechanisms.yaml → list dict {id,name,kind,desc,surface,live_probe}.
    Manifest lỗi/thiếu → [] + cảnh báo stderr (thà trống-thấy-được còn hơn sai-âm-thầm —
    Taleb default-unknown; đừng chép tay lại để 'lành' giả)."""
    p = root / "harness" / "mechanisms.yaml"
    try:
        import yaml
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return data.get("mechanisms", []) or []
    except Exception as e:
        sys.stderr.write(f"[build-overstack-docs] KHÔNG đọc được {p}: {e} — mục cơ-chế sẽ TRỐNG\n")
        return []


def load_foundation(root: Path):
    """Đọc harness/foundation.yaml → dict {problem, why-exists, tech-choices[...]}.
    Manifest lỗi/thiếu → {} + cảnh báo stderr (thà trống-thấy-được còn hơn sai-âm-thầm —
    council-026/GH#6; mục Nền tảng DERIVE từ đây, không chép tay)."""
    p = root / "harness" / "foundation.yaml"
    try:
        import yaml
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return data.get("foundation", {}) or {}
    except Exception as e:
        sys.stderr.write(f"[build-overstack-docs] KHÔNG đọc được {p}: {e} — mục Nền tảng sẽ TRỐNG\n")
        return {}


def sections(root: Path):
    by_loop, n_sk = skills_by_loop(root)
    mechs = load_mechanisms(root)   # cơ-chế = DATA từ manifest (council-025), không chép tay
    fnd = load_foundation(root)     # Nền tảng = DATA từ foundation.yaml (GH#6), không chép tay
    rs = rules(root)
    n_rules = len(rs)
    n_scripts = len(list((root / "harness" / "scripts").glob("*.py"))) if (root / "harness" / "scripts").is_dir() else 0

    loop_order = ["wiki-loop", "dev-loop", "orchestrate", "utils"]
    skill_rows = []
    for loop in loop_order + [l for l in by_loop if l not in loop_order]:
        for name, desc in sorted(by_loop.get(loop, [])):
            gk = group_key(loop, name)
            lp = (loop + " / " + gk) if gk else loop
            skill_rows.append(f"<tr><td><code>/{esc(name)}</code></td><td>{esc(lp)}</td><td>{esc(desc)}</td></tr>")
    skills_table = ("<div class=\"table-wrap\"><table><tr><th>Skill</th><th>Loop</th><th>Dùng khi</th></tr>"
                    + "".join(skill_rows) + "</table></div>")
    rule_rows = "".join(f"<tr><td><code>{rid}</code></td><td><b>{esc(name)}</b>{(' — ' + esc(stmt)) if stmt else ''}</td></tr>" for rid, name, stmt in rs)
    rules_table = f"<div class=\"table-wrap\"><table><tr><th>Rule</th><th>Chặn / đảm bảo điều gì</th></tr>{rule_rows}</table></div>"

    # ── mind map (cheatsheet bezier; loop >~8 skill chia nhánh con theo CHỨC NĂNG) ──
    loop_cls = {"wiki-loop": "b-wiki", "dev-loop": "b-dev", "orchestrate": "b-orch", "utils": "b-utils"}
    loop_ds = {"wiki-loop": "vòng tri thức", "dev-loop": "chia theo chức năng",
               "orchestrate": "chia theo chức năng", "utils": "chia theo chức năng"}

    def _node(cls, nm, ds="", ct=None):
        dsh = '<span class="ds">%s</span>' % esc(ds) if ds else ''
        cth = '<span class="ct">%s</span>' % ct if ct is not None else ''
        return '<div class="node %s"><span class="nm">%s</span>%s%s</div>' % (cls, esc(nm), dsh, cth)

    def _row(inner):
        return '<div class="row">%s</div>' % inner

    def _leaf(cls, name, desc):
        return _row(_node(cls + " leaf", "/" + name, (desc[:52] + "…") if len(desc) > 54 else desc))

    def _subtree(cls, nm, ds, child_rows, count=None):
        cnt = count if count is not None else len(child_rows)
        return _row(_node(cls + " cat has-children", nm, ds, cnt)
                    + '<div class="children">%s</div>' % "".join(child_rows))

    branches = []
    for loop in loop_order + [l for l in by_loop if l not in loop_order]:
        items = sorted(by_loop.get(loop, []))
        if not items:
            continue
        parent_cls = loop_cls.get(loop, "b-utils")
        if loop in LOOP_GROUPS:   # loop dài → chia nhánh con theo chức năng
            order, gmap = LOOP_GROUPS[loop]
            groups = {}
            for n, d in items:
                gk = gmap.get(n)
                if gk is None:                      # skill MỚI chưa phân nhóm → KHÔNG âm thầm nhét nhóm cuối
                    gk = "__uncat__"
                    UNCLASSIFIED.append((loop, n))
                groups.setdefault(gk, []).append((n, d))
            subs = []
            for gi, (gk, glabel) in enumerate(order):
                g = sorted(groups.get(gk, []))
                if not g:
                    continue
                gcls = "g%d" % (gi % 6)
                subs.append(_subtree(gcls, glabel, "", [_leaf(gcls, n, d) for n, d in g]))
            unc = sorted(groups.get("__uncat__", []))
            if unc:   # nhóm hiện-rõ để dev phân loại 1 lần (đừng giấu trong nhóm khác)
                subs.append(_subtree("g5", "❓ chưa phân loại", "thêm vào LOOP_GROUPS",
                                     [_leaf("g5", n, d) for n, d in unc]))
            branches.append(_subtree(parent_cls, loop, loop_ds.get(loop, ""), subs, count=len(items)))
        else:
            branches.append(_subtree(parent_cls, loop, loop_ds.get(loop, ""), [_leaf(parent_cls, n, d) for n, d in items]))
    branches.append(_subtree("b-rule", "rules", "harness gác (rule enforce bởi validator + hook)",
                             [_row(_node("b-rule leaf", rid,
                                         (stmt[:74] + "…") if len(stmt) > 76 else (stmt or name)))
                              for rid, name, stmt in rs]))
    # cơ chế runtime + tự-gác (KHÔNG phải rule) — DERIVE từ manifest mechanisms.yaml (council-025)
    branches.append(_subtree("b-rule", "cơ chế", "hook runtime + harness tự-gác",
                             [_row(_node("b-rule leaf", _x["name"], _x["desc"])) for _x in mechs]))

    # 5 trend 2026 → 5 chức năng qua build-now-adapt-later (core tất định now, adapter verified:false)
    # BNAL — AUTO từ harness/*.config.yaml (mỗi config = 1 adapter). KHÔNG hardcode → không drift (ADR-012/013/015).
    import glob as _glob
    _BDESC = {
        "success-flywheel": "gom trace THẮNG → playbook tái dùng (gương dương của failure-flywheel)",
        "egress-guard": "chặn egress/MCP độc: allow-list domain + cờ injection mô tả tool",
        "trace-otel": "audit phẳng → span OTel-GenAI + truy nhân-quả (lỗi step 10 ⇒ tool step 3)",
        "spec-gate": "spec→plan→tasks nguồn-sự-thật + conformance (chống drift; cf Spec Kit)",
        "scoped-hooks": "skill tự khai guard ở frontmatter, chỉ chạy khi skill active",
        "mem-rank": "memory agent: ADD/UPDATE/DELETE/NOOP + retrieve ranked (Jaccard)",
        "token-budget": "governor token+$ per session/task (FinOps gap); warn→block",
        "inject-scan": "quét OUTPUT tool tìm injection gián tiếp (egress lo mô tả)",
        "claim-receipts": "cổng hallucination: trích reference → verify tồn tại (Tool Receipts)",
        "prospect-critic": "reflection TRƯỚC chạy: soi plan vs taxonomy failure-flywheel",
        "web-crawl": "crawl URL → markdown (builtin urllib; adapter Firecrawl/Crawl4AI)",
        "web-clone": "clone site: snapshot 1-file HOẶC reconstruct→Next.js (ai-website-cloner)",
        "sweep-gate": "nhịp Sweeper: đếm accretion → nhắc gọt (Boris Cherny)",
        "archetypes": "5 persona Boris (proto/build/sweep/grow/maintain): dispatch + phase-map",
        "pattern-library": "R14 kho pattern bảo vệ (chỉ sửa khi unlock env)",
        "failure-flywheel": "gom lỗi lặp → draft rule stub (Hamel flywheel)",
        "council": "hội đồng N model blind peer-rank + chairman",
        "trace-grader": "chấm ĐƯỜNG ĐI agent (tool/thứ tự/pass^k)",
        "loop-runner": "vòng lặp guardrail propose→verify→revise + termination",
        "wikieval": "eval hồi quy từ wiki goldens + baseline (CI gate)",
    }
    _broot = Path(__file__).resolve().parents[2]
    _bf, _bt = [], []
    for _cf in sorted(_glob.glob(str(_broot / "harness" / "*.config.yaml"))):
        _nm = Path(_cf).name[:-len(".config.yaml")]
        try:
            _ver = re.search(r"^\s*verified\s*:\s*true\b", Path(_cf).read_text(encoding="utf-8"), re.M) is not None
        except Exception:
            _ver = False
        _leafrow = _row(_node("b-rule leaf", _nm, _BDESC.get(_nm, "BNAL adapter (1 config quarantine)")))
        (_bt if _ver else _bf).append(_leafrow)
    branches.append(_subtree("b-rule", "BNAL", f"build-now-adapt-later: {len(_bf) + len(_bt)} adapter = {len(_bf)} chờ hiệu chỉnh (verified:false) + {len(_bt)} đã chốt (verified:true). AUTO từ harness/*.config.yaml — ADR-012/013/015",
        [_subtree("b-rule", "verified:false — chờ hiệu chỉnh", "guess best-effort; finalize = sửa 1 config", _bf, count=len(_bf)),
         _subtree("b-rule", "verified:true — đã chốt", "đã verify; self-test giữ trung thực", _bt, count=len(_bt))],
        count=len(_bf) + len(_bt)))

    mindmap_html = ('<div class="mm"><div class="mm-canvas"><svg class="mm-links"></svg>'
                    '<div class="tree"><div class="row">'
                    + _node("root has-children", "overstack", "gõ /<tên> để gọi · %d rule" % n_rules, n_sk)
                    + '<div class="children">' + "".join(branches) + '</div></div></div></div></div>')

    S = []
    S.append(("quickstart", "Quickstart", "00 · Bắt đầu", "Quickstart — chạy được trong 2 phút", [
        "<p class=\"lead\">Bạn chỉ cần nhớ ba thứ: <b>cài</b>, <b>để agent làm việc</b>, và <b>khi muốn tính năng mới thì /propose trước</b>. Phần còn lại overstack lo (rào chắn tất định chặn agent làm bậy, 0 token).</p>",
        "<h3>1. Cài vào dự án của bạn (một dòng)</h3>",
        "<p>Dán cho <b>Agent</b> (nó tự cài rồi tự kiểm mọi thứ đã đúng chỗ) — hoặc chạy thẳng trong <b>terminal</b>. Cùng một lệnh:</p>"
        "<pre class='code-block'><code>curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash</code></pre>",
        "<p>Lệnh này kéo cả <b>3 nền tảng</b> — <b>harness</b> (rào chắn), <b>skills</b> (kỹ năng), <b>llmwiki</b> (nền tri thức) — và bật guardrail ngay. Dự án cũ đã có wiki? Gọi <code>/harness-update</code> để migrate + tự trả nợ.</p>",
        "<h3>2. Cứ làm việc bình thường với agent</h3>",
        "<p>Agent (Claude Code, Cursor, opencode…) giờ bị overstack gác: không ghi bậy vào <code>raw/</code>, mọi trang wiki buộc có nguồn gốc (<code>## Origin</code>), index/log tự cập-nhật-bằng-code. Bạn không phải nhớ luật — hàng rào tự cắn.</p>",
        "<h3>3. Muốn một tính năng/đổi thay? gọi <code>/orca-workflow</code></h3>",
        "<p>Đây là lệnh bạn dùng nhiều nhất. <code>/orca-workflow</code> tự chạy trọn vòng <b>propose → gate → dispatch → verify</b>: vẽ kế hoạch (file ảnh hưởng, cái gì có thể vỡ, sequence diagram) + DỪNG chờ bạn duyệt, rồi giao việc cho các agent chạy song song, rồi đối chiếu kết quả. Các skill con (<code>propose</code>, <code>safe-change</code>, <code>verify-before-commit</code>…) do nó <b>điều phối</b> — bạn hiếm khi gọi tay từng cái.</p>",
        "<div class=\"note\"><h4>Lệnh bạn gọi TRỰC TIẾP nhiều nhất</h4><ul class=\"s\">"
        "<li><code>/orca-workflow</code> — dựng/đổi một tính năng (điều phối cả propose→gate→dispatch→verify).</li>"
        "<li><code>/orca-onboard</code> — onboard codebase (một hay nhiều) song song vào wiki.</li>"
        "<li><code>/harness-update</code> — tự bảo trì: cập nhật overstack + trả nợ wiki + health-check.</li>"
        "<li><code>find-skills \"&lt;việc&gt;\"</code> — không chắc có sẵn kỹ năng gì? hỏi nó.</li></ul></div>",
        "<p style=\"margin-top:14px\">Cần hiểu sâu từng phần? Các tab bên trái đi từ <b>tổng quan</b> → <b>cài đặt</b> → <b>ba trụ</b> → <b>workflow</b> → <b>tự bảo trì</b> → <b>tham chiếu đầy đủ</b>.</p>",
    ]))

    S.append(("what", "overstack là gì", "01 · Tổng quan", "overstack là gì", [
        "<p class=\"lead\">overstack <b>không phải một app</b> — nó là <b>một lớp bạn đặt lên dự án</b> để biến AI agent thành một <b>kỹ sư có kỷ luật</b>: có <b>trí nhớ</b> (wiki), <b>luật không phá được</b> (harness), <b>kỹ năng đóng sẵn</b> (skills), biết <b>điều phối nhiều agent</b> (Orca) — và tự <b>đo &amp; kiểm</b> việc agent làm khi chạy (chi phí, chất lượng, dấu vết). <i>Giới chuyên môn (2026) gọi cả lớp này là <b>agent harness engineering</b> / <b>AI control plane</b>; từng mảng có tên riêng — <b>context engineering</b> (trí nhớ) · <b>guardrails / policy-as-code</b> (luật) · <b>agent orchestration</b> (điều phối) · <b>AgentOps + evals</b> (đo &amp; kiểm). Nhánh nghề rộng hơn: <b>agentic engineering</b>. Bản chất vẫn chỉ là: agent làm việc có kỷ luật, đo được, kiểm được.</i></p>",
        f"<div class=\"kpi\"><div class=\"b\"><div class=\"n\" style=\"color:#0a84ff\">{n_sk}</div><div class=\"l\">skills (/…)</div></div>"
        f"<div class=\"b\"><div class=\"n\" style=\"color:#e0264b\">{n_rules}</div><div class=\"l\">rules tất định</div></div>"
        f"<div class=\"b\"><div class=\"n\" style=\"color:#5856d6\">{n_scripts}</div><div class=\"l\">harness scripts</div></div>"
        "<div class=\"b\"><div class=\"n\" style=\"color:#28a745\">0</div><div class=\"l\">token/lần gác</div></div>"
        "<div class=\"b\"><div class=\"n\" style=\"color:#30b0c7\">3</div><div class=\"l\">nền tảng + Orca</div></div></div>",
        "<div class=\"grid\"><div class=\"card\"><h4>3 nền tảng + lớp điều phối</h4><ul class=\"s\">"
        "<li><b>Nền 1 · Wiki (tri thức)</b> — nơi dự án nhớ: concept, entity, nguồn, ADR, draft; mỗi trang truy được nguồn.</li>"
        "<li><b>Wiki-graph (đồ thị tri thức + code)</b> — engine tất định (không RAG) tự dựng <code>wiki-graph.html</code>: node = trang wiki + file code, cạnh = quan hệ (wikilink, import code→code đa ngôn ngữ). Tự tươi cuối phiên khi wiki/code đổi. Nay <b>ship xuống downstream</b> (opt-in <code>OVERSTACK_WIKIGRAPH=1</code>, fail-open) nên dự án của bạn tự vẽ được đồ thị của chính nó, không chỉ repo framework.</li>"
        "<li><b>Nền 2 · Harness (rào chắn)</b> — luật tất định bằng code chặn agent làm bậy, không tốn token, không bypass được khi merge.</li>"
        "<li><b>Nền 3 · Skills (kỹ năng)</b> — quy trình đóng gói, gọi bằng <code>/tên</code>, cài global dùng mọi dự án.</li>"
        "<li><b>Orca (điều phối)</b> — KHÔNG phải nền tảng mà là LỚP chạy nhiều agent trên 3 nền đó: propose → gate → dispatch → verify. (Lưu ý: \"5 trụ runtime\" lại là khái niệm khác — đo lường &amp; gác LÚC CHẠY.)</li></ul></div>"
        "<div class=\"card\"><h4>Triết lý</h4><ul class=\"s\">"
        "<li><b>Đừng tin agent nhớ</b> — luật, log, bản đồ năng lực đều do CODE đảm bảo, không trông chờ trí nhớ LLM.</li>"
        "<li><b>Tất định &gt; xác suất</b> — rào chắn là code chạy 0-token; phần cần LLM bị nhốt sau adapter.</li>"
        "<li><b>Build-now-adapt-later</b> — dựng phần chắc chắn ngay, nhốt ẩn số sau MỘT adapter để chỉnh sau.</li>"
        "<li><b>Travel-with-project</b> — cái gì phục vụ dự án thì đi theo khi cài; đồ nghề dev framework ở lại.</li></ul></div></div>",
    ]))

    # ── Nền tảng — DERIVE từ harness/foundation.yaml (GH#6), KHÔNG chép tay ─────────
    def _evi(item):
        s = str(item).strip()
        if s.startswith("[[") and s.endswith("]]"):   # wikilink → nguyên văn (R-validator wiki lo)
            return esc(s)
        return "<code>%s</code>" % esc(s)              # path repo-relative → code

    _tc = fnd.get("tech-choices") or []
    if not fnd or not (fnd.get("problem") or _tc):
        _fnd_blocks = ["<p class=\"lead\">Mục Nền tảng chưa điền. Tạo/điền <code>harness/foundation.yaml</code> "
                       "rồi chạy <code>python3 fdk/tools/build-overstack-docs.py</code> để trang này derive tự động.</p>"]
    else:
        _fnd_blocks = [
            "<p class=\"lead\">Ba câu gốc mà người mới (và agent) đọc <b>đầu tiên</b>: dự án giải quyết "
            "<b>bài toán gì</b>, <b>vì sao nó tồn tại</b>, và <b>vì sao chọn các công nghệ này</b>. "
            "Toàn bộ mục này <b>derive</b> từ <code>harness/foundation.yaml</code> — sửa nguồn rồi regen, "
            "không chép tay (chống drift, ADR-001).</p>",
            "<div class=\"grid\">"
            "<div class=\"card\"><h4>Bài toán</h4><p style=\"margin:0\">%s</p></div>"
            "<div class=\"card\"><h4>Vì sao tồn tại</h4><p style=\"margin:0\">%s</p></div></div>"
            % (esc(str(fnd.get("problem", "—")).strip()), esc(str(fnd.get("why-exists", "—")).strip())),
        ]
        if _tc:
            _rows = []
            for _c in _tc:
                _alts = _c.get("alternatives-rejected") or []
                _alt_html = "".join(
                    "<li><b>%s</b> — %s</li>" % (esc(str(_a.get("alt", "")).strip()), esc(str(_a.get("reason", "")).strip()))
                    for _a in _alts) or "<li>—</li>"
                _evis = _c.get("evidence-link") or []
                _evi_html = " ".join(_evi(_e) for _e in _evis) or "—"
                _rows.append(
                    "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td><ul class=\"s\" style=\"margin:0;padding-left:16px\">%s</ul></td><td>%s</td></tr>"
                    % (esc(str(_c.get("tech", "")).strip()), esc(str(_c.get("role", "")).strip()),
                       esc(str(_c.get("why", "")).strip()), _alt_html, _evi_html))
            _fnd_blocks.append(
                "<h3>Vì sao chọn các công nghệ này</h3>"
                "<table><tr><th>Công nghệ</th><th>Vai trò</th><th>Vì sao</th>"
                "<th>Đã loại (vì sao)</th><th>Bằng chứng</th></tr>" + "".join(_rows) + "</table>")
    S.append(("foundation", "Nền tảng", "01 · Nền tảng",
              "Nền tảng — bài toán · vì sao tồn tại · vì sao chọn công nghệ", _fnd_blocks))

    S.append(("install", "Cài đặt", "02 · Cài đặt", "Cài đặt — global vs per-project", [
        "<p class=\"lead\">overstack cài bằng một dòng bootstrap. Có hai chế độ, dùng cả hai là tốt nhất.</p>",
        "<h3>Bootstrap (mặc định — cả 3 nền tảng)</h3>",
        "<p>Dán cho <b>Agent</b> (nó tự cài rồi tự kiểm mọi thứ đã đúng chỗ) — hoặc chạy thẳng trong <b>terminal</b>. Cùng một lệnh:</p>"
        "<pre class='code-block'><code>curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash</code></pre>",
        "<p>Kéo harness + skills + llmwiki và bật chặn ngay. Opt-out: <code>--harness-only</code>.</p>",
        "<div class=\"note\"><h4>Dự án MỚI từ đầu (chưa có code)?</h4><p style=\"margin:0\">Không cần cài tay rồi feed từng file — chỉ <b>dán nội dung <code>00-New-Project.md</code></b> cho agent. Nó tự cài overstack → kickoff (hỏi 3 câu) → dựng knowledge base → scaffold MVP, dừng hỏi đúng lúc. Chi tiết: <code>setup.md</code>.</p></div>",
        "<div class=\"grid\"><div class=\"card\"><h4>Per-project (cho team)</h4><ul class=\"s\">"
        "<li>harness/ + .claude/settings.json được <b>commit vào repo</b> → đồng đội clone về là được bảo vệ.</li>"
        "<li>Có pre-commit (L2) + baseline audit cho dự án cũ.</li>"
        "<li>Đây là cách DUY NHẤT bảo vệ cả team (global chỉ bảo vệ máy bạn).</li></ul></div>"
        "<div class=\"card\"><h4>Global (cho máy bạn)</h4><ul class=\"s\">"
        "<li><code>install-harness.sh --global</code> → hooks + validators vào <code>~/.claude/harness/</code>.</li>"
        "<li>Mọi dự án có <code>llmwiki/</code> trên máy được gác; dự án khác chỉ tốn ~1ms/tool-call.</li>"
        "<li>Kèm <b>code-logger</b> + <b>build-capabilities</b> (ADR-005) → log + bản đồ năng lực xuống cùng dự án.</li></ul></div></div>",
        "<div class=\"note\"><h4>Sau khi cài</h4><ul class=\"s\">"
        "<li>Mở <b>session mới</b> thì hooks mới nạp.</li>"
        "<li>Chưa có <code>pre-commit</code>? cài <code>pipx install pre-commit</code> để bật chặn ở lớp L2.</li>"
        "<li>Tự bảo trì về sau: <code>/harness-update</code> (cập nhật + trả nợ + refresh bản đồ năng lực).</li></ul></div>",
    ]))

    S.append(("wiki", "Wiki", "03 · Tri thức", "Nền tảng 1 — Wiki (tri thức)", [
        "<p class=\"lead\">Wiki là bộ nhớ dài hạn của dự án. overstack ép nó luôn truy được nguồn, không bao giờ lệch index, và — từ 07/2026 — tự phát hiện khi code đã đổi mà wiki chưa theo kịp. Tất cả bằng rào chắn tất định (code chạy ở hook/CI, không tốn token), không bằng kỷ luật con người.</p>",
        "<div class=\"grid\"><div class=\"card\"><h4>Luật vàng của wiki</h4><ul class=\"s\">"
        "<li>Mọi trang phải có <code>## Origin</code> — luôn truy được nguồn gốc (R2).</li>"
        "<li>Thêm/xoá trang phải cập nhật <code>wiki/index.md</code> (R3) — overstack có <code>--fix</code> tự thêm.</li>"
        "<li>Mỗi thao tác append <code>wiki/log.md</code> — nay do <b>code-logger</b> ghi bằng code, không chờ agent.</li>"
        "<li>Không bao giờ ghi vào <code>raw/</code> — đó là inbox của con người, agent chỉ đọc (R1).</li></ul></div>"
        "<div class=\"card\"><h4>Cấu trúc thư mục</h4><ul class=\"s\">"
        "<li><code>concepts/</code> — khái niệm; <code>entities/</code> — thực thể; <code>sources/</code> — nguồn + ADR + draft.</li>"
        "<li><code>architecture/</code>, <code>tours/</code> — kiến trúc & tour. File wiki KHÔNG nằm ở gốc <code>wiki/</code> (R5).</li>"
        "<li>Frontmatter OKF v0.1 (<code>type:</code>…) — máy đọc được (R9).</li>"
        "<li>Liên kết chéo bằng <code>[[wikilink]]</code>; trang chỉ tạo SAU khi code đã commit.</li></ul></div></div>",
        "<div class=\"grid\"><div class=\"card\"><h4>Tự phát hiện lệch (staleness) — HAI chiều</h4><ul class=\"s\">"
        "<li><b>Wiki→wiki</b>: mỗi lần ghi trang, hook <b>wiki_ledger</b> append sự kiện vào <code>ledger.jsonl</code> "
        "(khoá <code>flock</code> — nhiều phiên ghi song song không giẫm dòng nhau) và lan cờ stale (lệch thời) "
        "<i>đúng 1 bước</i> sang các trang trỏ tới nó (<code>stale.json</code> — cap 1 bước nên miễn nhiễm bão-stale/chu trình).</li>"
        "<li><b>Code→wiki</b> <i>(mới 07/2026)</i>: <b>wiki-sync</b> giữ một "
        "NEO <code>.last-sync.json</code> (commit + content-hash của wiki lần rà cuối). <code>--check</code> là "
        "<b>cổng no-op tất định 0 token</b>: code không đổi kể từ neo → trả lời \"wiki current\" mà không cần gọi LLM; "
        "có đổi → tự map file-code-đổi → trang wiki nhắc tới file đó và cờ <code>code-drift</code>.</li>"
        "<li>Đầu mỗi phiên, <b>session_start</b> nhắc 1 dòng nếu code đã đổi N commit kể từ neo — realtime, không chờ cron.</li>"
        "<li><i>Giới hạn thật</i>: map code→trang là heuristic nhắc-tên-file (thiên về bắt-thừa); <code>/lint</code> "
        "vẫn là người phán xử cuối trước khi sửa.</li></ul></div>"
        "<div class=\"card\"><h4>Vận hành không người trông</h4><ul class=\"s\">"
        "<li>CI cron <code>wiki-refresh.yml</code> (sinh từ policy bằng gen-converters): mỗi ngày chạy cổng no-op "
        "trước — <b>không drift thì kết thúc miễn phí</b> (0 token).</li>"
        "<li>Có drift + có <code>ANTHROPIC_API_KEY</code>: LLM chạy <code>/lint</code> sửa <i>surgical</i> rồi chốt neo; "
        "mở PR <b>chỉ diff wiki</b> cho người review.</li>"
        "<li>Không có key: vẫn mở PR mang cờ <code>code-drift</code> tất định để phiên làm việc kế rà — degrade tử tế, "
        "không im lặng bỏ qua.</li>"
        "<li>Neo chỉ được ghi khi nội dung wiki <i>thực sự</i> đổi (content-hash) — cron chạy lại không tự sinh diff rác.</li></ul></div></div>",
        "<div class=\"grid\"><div class=\"card\"><h4>Kỷ luật cập nhật surgical (phẫu thuật — chạm đúng chỗ)</h4><ul class=\"s\">"
        "<li><b>Docs-impact-plan</b> trước khi sửa: <code>code đổi → trang → sửa gì → vì sao</code>; trang không truy được về một thay đổi cụ thể thì không đụng.</li>"
        "<li><b>Soft diff budget</b>: ít file code đổi thì chỉ sửa 1–2 trang; muốn sửa rộng hơn phải tự vấn trước.</li>"
        "<li><b>Cấm formatting-only edit</b> — diff nhiễu là nợ cho người review; <b>canonical home</b> — mỗi concept một trang chính chủ, nơi khác chỉ <code>[[wikilink]]</code>.</li>"
        "<li><b>No-op hợp lệ</b>: \"wiki đã current, không sửa gì\" là kết quả tốt — không sửa lấy có.</li></ul></div>"
        "<div class=\"card\"><h4>Truy hồi &amp; trí nhớ nhiều tầng</h4><ul class=\"s\">"
        "<li><b>wiki-graph</b> — đồ thị tri thức + code sinh tất định (không RAG), truy wiki↔code hai chiều.</li>"
        "<li><b>mem-rank / record-episode</b> — tầng nhớ episodic (theo phiên): phiên sau hỏi \"phiên trước làm gì\" theo nghĩa.</li>"
        "<li><b>wiki-room</b> — context phiên chính mục rữa thì mở room 1 tầng nạp chi tiết wiki với budget cứng.</li>"
        "<li><b>retrieval-eval</b> chạy trong CI — chất lượng truy hồi không được tụt dưới sàn (tất định, không LLM).</li></ul></div></div>",
    ]))

    _flow = [("agent định ghi", "#9aa4b2", ""), ("L0 · hook", "#0a84ff", "PreToolUse"),
             ("L2 · pre-commit", "#5856d6", "fdk-gate"), ("L4 · CI", "#ff9500", "harness.yml (merge)"),
             ("✓ vào main", "#34c759", "")]
    _hsvg = ['<svg viewBox="0 0 900 165" xmlns="http://www.w3.org/2000/svg">'
             '<defs><marker id="arrH" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
             '<path d="M0,0 L9,4.5 L0,9 Z" fill="#9aa4b2"/></marker></defs>']
    for _i, (_nm, _c, _sub) in enumerate(_flow):
        _x = 16 + _i * 180
        _hsvg.append(f'<rect x="{_x}" y="46" width="152" height="52" rx="8" fill="rgba(255,255,255,.7)" stroke="{_c}" stroke-width="1.6"/>')
        _hsvg.append(f'<text x="{_x + 76}" y="{68 if _sub else 76}" text-anchor="middle" font-size="11.5" font-weight="700" fill="#0f0f12">{_nm}</text>')
        if _sub:
            _hsvg.append(f'<text x="{_x + 76}" y="86" text-anchor="middle" font-size="8.5" fill="#4a4a55">{_sub}</text>')
        if _i < 4:
            _hsvg.append(f'<line class="flow" x1="{_x + 152}" y1="72" x2="{_x + 184}" y2="72" stroke="#9aa4b2" stroke-width="2" marker-end="url(#arrH)"/>')
        if 1 <= _i <= 3:  # mỗi lớp gác có nhánh CHẶN
            _hsvg.append(f'<text x="{_x + 76}" y="124" text-anchor="middle" font-size="9" font-weight="600" fill="#ff2d55">✗ exit 2 → chặn</text>')
    _hsvg.append('</svg>')
    S.append(("harness", "Harness", "04 · Rào chắn", "Nền tảng 2 — Harness (rào chắn tất định)", [
        "<p class=\"lead\">Harness là phần làm overstack khác mọi \"prompt pack\": luật là CODE chạy ở hook/CI, chặn được agent kể cả khi nó cố tình lờ. 0 token, không bypass được khi merge. Một thay đổi phải qua <b>3 lớp gác</b> mới vào main — vi phạm ở lớp nào thì <b>exit 2</b> chặn ngay lớp đó:</p>",
        '<div class="diagram-box">' + "".join(_hsvg) + '<div class="diagram-hint">✥ kéo từng ô · cuộn để zoom</div></div>',
        f"<p>Hiện có <b>{n_rules} rule</b> (R1–R{n_rules}), mỗi rule enforce bởi validator tất định + hook (một số rule chặn qua hook, không có file validator riêng — nên số validator ít hơn số rule); vi phạm bị chặn ở write-time (hook), commit (pre-commit), và merge (CI) — ba lớp. Bảng dưới giải thích <b>từng rule</b>. Các <b>cơ chế runtime + tự-gác</b> (auto-index, force-query, orientation, code-index, harness-lint…) là một nhánh <i>“cơ chế”</i> riêng — chia & giải thích từng cái trong <b>mind map</b> (mục Tham chiếu cuối trang).</p>",
        rules_table,
        "<div class=\"grid\"><div class=\"card\"><h4>Ba lớp CHẶN (hook · pre-commit · CI)</h4><ul class=\"s\">"
        "<li><b>L0 hook</b> — chặn ngay lúc agent định ghi (PreToolUse).</li>"
        "<li><b>L1 settings</b> — wiring policy→agent (thuộc lớp hook, không phải điểm chặn riêng).</li>"
        "<li><b>L2 pre-commit</b> — chặn lúc commit (content-validator theo file-đổi; xem issue #18).</li>"
        "<li><b>L4 CI</b> — chặn lúc merge, nơi không agent nào bypass được (SÀN THẬT).</li></ul>"
        "<p class=\"s\" style=\"margin:6px 0 0;color:var(--t2)\">Nhãn nhảy L0/L1/L2→L4: <b>L3 để trống có chủ đích</b> (không có lớp giữa pre-commit và CI). Ba <i>điểm chặn</i> thật = hook · pre-commit · CI (concept harness-enforcement-floor).</p></div>"
        "<div class=\"card\"><h4>Harness tự gác chính nó</h4><ul class=\"s\">"
        "<li><b>harness-lint</b> — bắt hằng-số-lệch giữa các script.</li>"
        "<li><b>harness-doctor</b> — chạy fixture sai/đúng qua từng validator, chứng minh rào còn cắn.</li>"
        "<li><b>fdk-gate</b> — định-nghĩa-hoàn-thành: 14 bước phải xanh mới cho push.</li></ul></div></div>",
    ]))

    S.append(("skills", "Skills", "05 · Kỹ năng", "Nền tảng 3 — Skills (kỹ năng đóng gói)", [
        f"<p class=\"lead\">Skill là một quy trình đóng gói thành file <code>SKILL.md</code>, gọi bằng <code>/tên</code>. Hiện có <b>{n_sk}</b> skill, chia theo \"loop\" (vòng công việc). Cài global qua <code>npx skills add</code> → dùng ở mọi dự án. &nbsp;<a href=\"skill-whiteboard.html\">🗺️ Xem bản đồ quan hệ skill đầy đủ →</a></p>",
        "<div class=\"grid\"><div class=\"card\"><h4>wiki-loop</h4><ul class=\"s\"><li>nuôi tri thức: <code>/ingest</code>, <code>/query</code>, <code>/lint</code>.</li></ul></div>"
        "<div class=\"card\"><h4>dev-loop</h4><ul class=\"s\"><li>vòng phát triển: <code>/propose</code>, <code>/impact-check</code>, <code>/safe-change</code>, <code>/verify-before-commit</code>…</li></ul></div>"
        "<div class=\"card\"><h4>orchestrate (entry chính)</h4><ul class=\"s\"><li><b><code>/orca-workflow</code></b> · <b><code>/orca-onboard</code></b> — lệnh bạn gọi trực tiếp; chúng điều phối các skill dev-loop. Cùng nhóm: <code>/council</code>, <code>/trace-grader</code>.</li></ul></div>"
        "<div class=\"card\"><h4>utils</h4><ul class=\"s\"><li>tiện ích: <code>/fdk</code>, <code>/harness-update</code>, <code>/docs-site-macos</code>…</li></ul></div></div>",
        "<p>Bảng đầy đủ luôn-mới ở tab <a href=\"@reference\">Tham chiếu</a>. Không chắc dùng skill nào? <code>find-skills \"&lt;việc&gt;\"</code>.</p>",
    ]))

    _wf = [("propose", "#0a84ff", "draft + DỪNG duyệt", "proposed"),
           ("gate", "#5856d6", "R7 đủ cặp .md+.html", "approved"),
           ("dispatch", "#30b0c7", "agent + CLI rẻ", "dispatched"),
           ("verify", "#34c759", "dispatch-verify + trace-grader", "done")]
    _wsvg = ['<svg viewBox="0 0 900 150" xmlns="http://www.w3.org/2000/svg">'
             '<defs><marker id="arrW" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
             '<path d="M0,0 L9,4.5 L0,9 Z" fill="#9aa4b2"/></marker></defs>']
    for _i, (_nm, _c, _mech, _state) in enumerate(_wf):
        _x = 22 + _i * 220
        _wsvg.append(f'<rect x="{_x}" y="42" width="186" height="56" rx="8" fill="rgba(255,255,255,.7)" stroke="{_c}" stroke-width="1.6"/>')
        _wsvg.append(f'<text x="{_x + 93}" y="66" text-anchor="middle" font-size="13" font-weight="700" fill="#0f0f12">{_nm}</text>')
        _wsvg.append(f'<text x="{_x + 93}" y="84" text-anchor="middle" font-size="8.5" fill="#4a4a55">{_mech}</text>')
        _wsvg.append(f'<text x="{_x + 93}" y="120" text-anchor="middle" font-size="9" font-weight="600" fill="{_c}">task: {_state}</text>')
        if _i < 3:
            _wsvg.append(f'<line class="flow" x1="{_x + 186}" y1="70" x2="{_x + 218}" y2="70" stroke="#9aa4b2" stroke-width="2" marker-end="url(#arrW)"/>')
    _wsvg.append('</svg>')
    S.append(("workflow", "Workflow dev", "06 · Quy trình", "Workflow — gọi /orca-workflow, nó lo 4 bước", [
        "<p class=\"lead\">Cách bạn làm việc thực tế: gọi <b><code>/orca-workflow</code></b> cho một tính năng — nó tự chạy trọn <b>vòng lặp</b> 4 bước dưới (cộng đồng gọi việc thiết kế vòng này là <i>loop engineering / agentic loop</i>). Các skill dev-loop là <b>bước con</b> do nó điều phối, bạn không gọi tay từng cái. Mỗi bước khớp một trạng thái <b>task-lifecycle</b> (Trụ 3) — gate validator chặn nếu đi sai. Cần vòng lặp tự-sửa CÓ chốt dừng bắt buộc (max-iter/budget/no-progress)? → <b><code>/loop-runner</code></b>.</p>",
        '<div class="diagram-box">' + "".join(_wsvg) + '<div class="diagram-hint">✥ kéo từng ô · cuộn để zoom</div></div>',
        "<ol class=\"ck\">"
        "<li><b>propose</b> — restate yêu cầu, liệt kê file ảnh hưởng + cái có thể vỡ, vẽ sequence diagram, viết draft. DỪNG chờ bạn duyệt.</li>"
        "<li><b>gate</b> — validator R7 chặn proposal thiếu (đủ cặp <code>.md</code> + <code>.html</code> một-diagram-mỗi-task).</li>"
        "<li><b>dispatch</b> — giao việc cho các agent (chọn CLI theo bảng chi phí); chạy song song.</li>"
        "<li><b>verify</b> — <code>dispatch-verify</code> đối chiếu \"khai done\" với file thật; <code>/trace-grader</code> chấm cả ĐƯỜNG ĐI.</li></ol>",
        "<div class=\"note\"><h4>Hai lệnh điều phối bạn gọi trực tiếp</h4><p style=\"margin:0\"><code>/orca-workflow</code> (một tính năng) và <code>/orca-onboard</code> (onboard nhiều codebase song song). Các skill dev-loop (<code>propose</code> · <code>impact-check</code> · <code>safe-change</code> · <code>verify-before-commit</code>) là bước CON trong các flow này — gọi tay chỉ khi muốn chạy lẻ một bước.</p></div>",
    ]))

    _agents = [("claude", "#0a84ff"), ("opencode", "#30b0c7"), ("agy/kiro", "#ff9500")]
    _osvg = ['<svg viewBox="0 0 900 200" xmlns="http://www.w3.org/2000/svg">'
             '<defs><marker id="arrO" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
             '<path d="M0,0 L9,4.5 L0,9 Z" fill="#9aa4b2"/></marker></defs>'
             '<rect x="18" y="76" width="150" height="48" rx="8" fill="rgba(255,255,255,.7)" stroke="#5856d6" stroke-width="1.6"/>'
             '<text x="93" y="104" text-anchor="middle" font-size="12" font-weight="700" fill="#0f0f12">coordinator</text>'
             '<rect x="556" y="76" width="150" height="48" rx="8" fill="rgba(255,255,255,.7)" stroke="#30b0c7" stroke-width="1.6"/>'
             '<text x="631" y="98" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">worker_done</text>'
             '<text x="631" y="113" text-anchor="middle" font-size="8.5" fill="#4a4a55">gom kết quả</text>'
             '<rect x="730" y="76" width="150" height="48" rx="8" fill="rgba(255,255,255,.7)" stroke="#34c759" stroke-width="1.6"/>'
             '<text x="805" y="98" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">verify</text>'
             '<text x="805" y="113" text-anchor="middle" font-size="8.5" fill="#4a4a55">dispatch-verify</text>'
             '<line class="flow" x1="706" y1="100" x2="726" y2="100" stroke="#9aa4b2" stroke-width="2" marker-end="url(#arrO)"/>']
    for _i, (_nm, _c) in enumerate(_agents):
        _y = 18 + _i * 64
        _cy = _y + 23
        _osvg.append(f'<rect x="318" y="{_y}" width="170" height="46" rx="7" fill="rgba(255,255,255,.7)" stroke="{_c}" stroke-width="1.5"/>')
        _osvg.append(f'<text x="403" y="{_cy + 4}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0f0f12">agent · {_nm}</text>')
        _osvg.append(f'<line class="flow" x1="168" y1="100" x2="314" y2="{_cy}" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrO)"/>')
        _osvg.append(f'<line class="flow" x1="488" y1="{_cy}" x2="552" y2="100" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrO)"/>')
    _osvg.append('</svg>')
    S.append(("orca", "Orca (đa-agent)", "07 · Điều phối", "Orca — điều phối đa-agent", [
        "<p class=\"lead\">Orca là lớp điều phối: thay vì một agent làm tuần tự, nhiều agent chạy song song theo một flow có kiểm soát — coordinator <b>fan-out</b> việc cho N agent (chọn CLI theo cost), gom <code>worker_done</code>, rồi verify.</p>",
        '<div class="diagram-box">' + "".join(_osvg) + '<div class="diagram-hint">✥ kéo từng ô · cuộn để zoom</div></div>',
        "<div class=\"grid\"><div class=\"card\"><h4>Khi nào dùng</h4><ul class=\"s\">"
        "<li><code>/orca-workflow</code> — vòng propose→gate→dispatch hằng ngày cho một tính năng.</li>"
        "<li><code>/orca-onboard</code> — onboard nhiều codebase song song (phân tích đồng thời).</li></ul></div>"
        "<div class=\"card\"><h4>An toàn</h4><ul class=\"s\">"
        "<li>orca_guard hook canh hành vi đa-agent.</li>"
        "<li>dispatch-verify bắt \"khai done nhưng file vắng\".</li>"
        "<li>trace-grader chấm tool/thứ tự/pass^k — không chỉ kết quả.</li></ul></div></div>",
    ]))

    _bsvg = ('<svg viewBox="0 0 900 190" xmlns="http://www.w3.org/2000/svg">'
             '<defs><marker id="arrB" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
             '<path d="M0,0 L9,4.5 L0,9 Z" fill="#9aa4b2"/></marker></defs>'
             '<rect x="16" y="68" width="140" height="52" rx="8" fill="rgba(255,255,255,.7)" stroke="#ff9500" stroke-width="1.6"/>'
             '<text x="86" y="90" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">Ẩn số ⚠️</text>'
             '<text x="86" y="105" text-anchor="middle" font-size="8.5" fill="#4a4a55">model/API/ngưỡng</text>'
             '<rect x="222" y="20" width="196" height="48" rx="7" fill="rgba(255,255,255,.7)" stroke="#34c759" stroke-width="1.5"/>'
             '<text x="320" y="40" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">Contract — build now</text>'
             '<text x="320" y="55" text-anchor="middle" font-size="8.5" fill="#4a4a55">UI/logic/safety (test đủ)</text>'
             '<rect x="222" y="120" width="196" height="48" rx="7" fill="rgba(255,255,255,.7)" stroke="#ff2d55" stroke-width="1.5"/>'
             '<text x="320" y="140" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">Adapter — quarantine</text>'
             '<text x="320" y="155" text-anchor="middle" font-size="8.5" fill="#4a4a55">verified:false (1 file)</text>'
             '<rect x="486" y="68" width="150" height="52" rx="8" fill="rgba(255,255,255,.7)" stroke="#0a84ff" stroke-width="1.6"/>'
             '<text x="561" y="90" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">Mock → E2E</text>'
             '<text x="561" y="105" text-anchor="middle" font-size="8.5" fill="#4a4a55">chạy được NGAY</text>'
             '<rect x="704" y="68" width="180" height="52" rx="8" fill="rgba(255,255,255,.7)" stroke="#30b0c7" stroke-width="1.6"/>'
             '<text x="794" y="90" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0f0f12">Adapt-checklist</text>'
             '<text x="794" y="105" text-anchor="middle" font-size="8.5" fill="#4a4a55">→ verified:true (1 chỗ)</text>'
             '<line class="flow" x1="156" y1="84" x2="218" y2="46" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrB)"/>'
             '<line class="flow" x1="156" y1="106" x2="218" y2="144" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrB)"/>'
             '<line class="flow" x1="418" y1="44" x2="482" y2="86" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrB)"/>'
             '<line class="flow" x1="418" y1="144" x2="482" y2="104" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrB)"/>'
             '<line class="flow" x1="636" y1="94" x2="700" y2="94" stroke="#9aa4b2" stroke-width="2" marker-end="url(#arrB)"/>'
             '</svg>')
    S.append(("bnal", "Build-now-adapt-later", "08 · Mẫu BNAL", "Build-now-adapt-later — thêm tính năng có ẩn số, không liều", [
        "<p class=\"lead\">Skill <b><code>/build-now-adapt-later</code></b> cho BẠN khi thêm vào <b>dự án của bạn</b> một tính năng còn phần chưa chắc (dùng model/API/lib nào, ngưỡng bao nhiêu, dịch vụ ngoài nào). Thay vì chờ chắc-chắn-mới-làm hay liều-đoán-rồi-khoá-mình, nó dựng phần CHẮC CHẮN ngay và nhốt phần CHƯA CHẮC sau MỘT adapter + config <code>verified:false</code> + một ADAPT-CHECKLIST — ship sớm, chỉnh sau ở đúng một chỗ.</p>",
        '<div class="diagram-box">' + _bsvg + '<div class="diagram-hint">✥ kéo từng ô · cuộn để zoom</div></div>',
        "<div class=\"grid\"><div class=\"card\"><h4>Build now</h4><ul class=\"s\">"
        "<li>Lõi tất định (cái bạn CHẮC) build + test ngay, không phụ thuộc ẩn số.</li>"
        "<li>Mọi ẩn số (model nào, ngưỡng bao nhiêu) sống ở ĐÚNG MỘT file config.</li>"
        "<li><code>verified:false</code> = đoán chưa xác nhận; phần gọi LLM/dịch vụ ngoài mặc định <code>enabled:false</code> (fail-safe).</li>"
        "<li><b>adapt-registry</b> gác: ẩn số không rò ra ngoài adapter (Step-7 leak-gate).</li></ul></div>"
        "<div class=\"card\"><h4>Adapt later</h4><ul class=\"s\">"
        "<li>Khi đã có dữ liệu / đã chốt lựa chọn: lõi pass self-test → <code>verified:true</code> hợp lệ.</li>"
        "<li>Phần ngoài (model/API): nối adapter + bật <code>enabled:true</code> sau khi kiểm chứng riêng.</li>"
        "<li>Chỉ sửa MỘT file adapter — không phải lục lại khắp codebase.</li></ul></div></div>",
        "<div class=\"note\"><h4>overstack tự ăn dog food</h4><p style=\"margin:0\">5 tính năng nâng cao của chính overstack (council · loop-runner · wikieval · trace-grader · failure-flywheel) đều dựng bằng BNAL — nên pattern này đã chứng minh trên thực tế, không phải lý thuyết.</p></div>",
    ]))

    _pers, _ = load_personas(root)
    _pcards = []
    for _i, (_pid, _pv) in enumerate(_pers.items()):
        _nm = _pv.get("name", _pid)
        _ini = esc("".join(w[0] for w in _nm.split()[:2]).upper())
        _col = ACCENTS[_i % len(ACCENTS)][0]
        _av = (f'<svg viewBox="0 0 36 36" class="pav"><circle cx="18" cy="18" r="17" fill="{_col}22" '
               f'stroke="{_col}" stroke-width="1.4"/><text x="18" y="23" text-anchor="middle" '
               f'font-size="13" font-weight="700" fill="{_col}">{_ini}</text></svg>')
        _pcards.append(f'<div class="pcard">{_av}<div><div class="pn">{esc(_nm)}</div>'
                       f'<div class="pl" style="color:{_col}">{esc(_pv.get("lens", ""))}</div>'
                       f'<div class="ps">{esc(_pv.get("sig", ""))}</div></div></div>')
    _pblock = ('<h3 class="sub">18 persona-lens (council) — góc nhìn "vĩ nhân"</h3>'
               '<p class="lead">Council bốc 3-5 lens theo VIỆC: <code>council.py roster --case risk</code> '
               '(8 case design/strategy/debug/risk/product/decision/simplify/ml-ai), luôn ép ≥1 cặp đối-trọng. '
               'Avatar tự sinh từ chữ-cái-đầu (self-contained, không ảnh ngoài); nguồn '
               '<code>harness/council.personas.yaml</code>.</p>'
               '<div class="pgrid">' + "".join(_pcards) + '</div>') if _pcards else ""
    S.append(("advanced", "Đánh giá (Evaluation)", "09 · Đánh giá", "Evaluation — đánh giá chất lượng &amp; quyết định khó (council · wikieval · trace-grader · loop-runner · failure-flywheel)", [
        "<p class=\"lead\">Năm skill <b>evaluation</b> BẠN gọi khi dev dự án của mình (mỗi cái lõi tất định, phần LLM nhốt sau adapter). Dùng khi cần đánh giá chất lượng, quyết một vấn đề khó, hay chạy một vòng lặp tự-sửa an toàn. Đây là trục PHÁN-XỬ; cổng tất định không-LLM nằm ở Trụ 4 (xem tab 5 trụ runtime).</p>",
        "<div class=\"grid\"><div class=\"card\"><h4>Đánh giá chất lượng</h4><ul class=\"s\">"
        "<li><b><code>/wikieval</code></b> — bộ eval hồi quy cho wiki dự án bạn (cascade assert tất định + baseline chặn merge khi tụt).</li>"
        "<li><b><code>/trace-grader</code></b> — chấm ĐƯỜNG ĐI agent đã đi (tool/thứ tự/pass^k), bắt \"đúng kết quả nhưng đi đường tệ\".</li></ul></div>"
        "<div class=\"card\"><h4>Quyết định khó & vòng lặp</h4><ul class=\"s\">"
        "<li><b><code>/council</code></b> — nhiều model trả lời độc lập → chấm chéo ẩn danh → tổng hợp, cho một vấn đề khó (Karpathy 3-stage).</li>"
        "<li><b><code>/loop-runner</code></b> — chạy vòng lặp agent CÓ chốt dừng bắt buộc (max-iter/budget/no-progress) — không sợ loop hoang.</li>"
        "<li><b><code>/failure-flywheel</code></b> — gom lỗi lặp trong dự án bạn → đề xuất rule/skill mới vào luồng /propose.</li></ul></div></div>",
        _pblock,
    ]))

    S.append(("awareness", "Năng lực & Truy vết", "10 · Truy vết", "Capabilities &amp; Traceability — bản đồ năng lực + logger (agent biết mình CÓ GÌ &amp; ĐÃ LÀM GÌ, bằng code)", [
        "<p class=\"lead\">Hai cơ chế: <b>capabilities</b> (bản đồ năng lực — agent biết mình có gì) + <b>traceability / logger</b> (ghi lại mọi việc đã làm) — bằng code, không bằng trí nhớ LLM (ADR-005). Logger này chính là nguồn nuôi 5 trụ runtime ở tab kế.</p>",
        "<div class=\"grid\"><div class=\"card\"><h4>Bản đồ năng lực</h4><ul class=\"s\">"
        "<li><code>build-capabilities</code> sinh <code>CAPABILITIES.md</code> từ đĩa: mọi skill + rule.</li>"
        "<li>Xuống cùng dự án: downstream đọc <b>global skills + rule đã cài</b> → \"đồ nghề bạn có Ở DỰ ÁN NÀY\".</li>"
        "<li>Đủ = skill ＋ rule (harness chặn gì) ＋ state (đã làm gì).</li></ul></div>"
        "<div class=\"card\"><h4>Logger bằng code</h4><ul class=\"s\">"
        "<li><b>code-logger</b> để hook ghi <code>log.md</code> bằng CODE mỗi Write/Stop.</li>"
        "<li>Không trông chờ agent \"nhớ append log\" — máy ghi.</li>"
        "<li>Xuống cùng dự án (deploy cạnh hooks) → log wiki của chính dự án đó.</li></ul></div></div>",
    ]))

    # 5 trụ runtime (AgentOps) — sơ đồ luồng tương tác: 1 sổ-cái nuôi 5 trụ, gác ở gate.
    _pillars = [
        ("1 · Cost", "#0a84ff", "code-logger --run-cost", "STRONG", "ok"),
        ("2 · Knowledge", "#30b0c7", "llmwiki + CAPABILITIES", "STRONG", "ok"),
        ("3 · Task", "#5856d6", "task_lifecycle (T-ID)", "STRONG", "ok"),
        ("4 · Quality", "#34c759", "code-health + fdk-gate", "STRONG", "ok"),
        ("5 · Audit", "#ff9500", "--audit hash-chain", "STRONG", "ok"),
    ]
    _svg = ['<svg viewBox="0 0 900 280" xmlns="http://www.w3.org/2000/svg">'
            '<defs><marker id="arrR" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
            '<path d="M0,0 L9,4.5 L0,9 Z" fill="#9aa4b2"/></marker></defs>'
            '<rect x="22" y="118" width="150" height="46" rx="8" fill="rgba(255,255,255,.7)" stroke="#5856d6" stroke-width="1.6"/>'
            '<text x="97" y="139" text-anchor="middle" font-size="12" font-weight="700" fill="#0f0f12">Mỗi action agent</text>'
            '<text x="97" y="154" text-anchor="middle" font-size="9" fill="#4a4a55">record(event,…)</text>'
            '<rect x="222" y="113" width="160" height="56" rx="8" fill="rgba(255,255,255,.7)" stroke="#0a84ff" stroke-width="1.6"/>'
            '<text x="302" y="135" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">events.jsonl</text>'
            '<text x="302" y="151" text-anchor="middle" font-size="8.5" fill="#4a4a55">append-only + hash-chain</text>'
            '<rect x="716" y="118" width="160" height="46" rx="8" fill="rgba(255,255,255,.7)" stroke="#1d1d1f" stroke-width="1.6"/>'
            '<text x="796" y="139" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">fdk-gate + CI</text>'
            '<text x="796" y="154" text-anchor="middle" font-size="8.5" fill="#4a4a55">vi phạm → đỏ</text>']
    for _i, (_nm, _col, _mech, _st, _) in enumerate(_pillars):
        _y = 16 + _i * 51
        _cy = _y + 20
        _svg.append(f'<rect x="438" y="{_y}" width="174" height="40" rx="7" fill="rgba(255,255,255,.7)" stroke="{_col}" stroke-width="1.5"/>')
        _svg.append(f'<text x="525" y="{_cy - 2}" text-anchor="middle" font-size="11" font-weight="700" fill="#0f0f12">{_nm}</text>')
        _svg.append(f'<text x="525" y="{_cy + 12}" text-anchor="middle" font-size="8.5" fill="#4a4a55">{_mech}</text>')
        _svg.append(f'<line class="flow" x1="382" y1="141" x2="434" y2="{_cy}" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrR)"/>')
        _svg.append(f'<line class="flow" x1="612" y1="{_cy}" x2="712" y2="141" stroke="#9aa4b2" stroke-width="1.5" marker-end="url(#arrR)"/>')
    _svg.append('</svg>')
    _rows = "".join(
        f'<tr><td><b>{_nm}</b></td><td>{_mech}</td><td><span class="pill {_p}">{_st}</span></td></tr>'
        for (_nm, _c, _mech, _st, _p) in _pillars)
    _pdetail = [
        ("1 · Cost Attribution", "#0a84ff", "Đo TIỀN: tokens + chi phí mỗi run, ghi ledger từ Stop hook (<code>code-logger --run-cost</code>). Trả lời: tiền chảy đi đâu, run nào đắt bất thường."),
        ("2 · Knowledge Flow", "#30b0c7", "Tri thức ĐÚNG tới agent: <code>CLAUDE.md</code>/CAPABILITIES top-down + promote bottom-up (propose→gate, failure-flywheel). Trả lời: agent có đúng ngữ cảnh không."),
        ("3 · Task Tracking", "#5856d6", "Mỗi việc một mã bền <code>T-YYMMDD-NN</code> đi proposed→approved→dispatched→done; validator <code>task_lifecycle</code> chặn nếu đi sai. Trả lời: draft này → commit nào, đã duyệt chưa."),
        ("4 · Quality Gates", "#34c759", "Cổng TẤT ĐỊNH không-LLM: <code>code_health</code> (mọi .py compile) + self-test, chạy ở fdk-gate + CI. Trả lời: code có hồi quy không — chặn cả khi LLM bị lừa."),
        ("5 · Audit &amp; Analytics", "#ff9500", "Sổ-cái <code>events.jsonl</code> append-only + hash-chain; <code>--audit --check</code> verify ở gate; <code>--reconcile</code> quy actor agent/người. Trả lời: ai sửa gì, log có bị giả mạo không."),
    ]
    _pdet_html = ('<h3 class="sub">Chi tiết từng trụ</h3><div class="pgrid">' + "".join(
        f'<div class="pcard"><div><div class="pn" style="color:{_c}">{_nm}</div><div class="ps">{_d}</div></div></div>'
        for (_nm, _c, _d) in _pdetail) + '</div>')
    S.append(("runtime", "AgentOps · 5 trụ", "11 · AgentOps", "AgentOps — 5 trụ runtime (Cost · Knowledge · Task · Quality · Audit)", [
        "<p class=\"lead\">Đây chính là tầng <b>AgentOps</b> của overstack — <i>\"DevOps cho AI agent\"</i>: <b>đo &amp; gác việc agent làm LÚC CHẠY</b> (chi phí · evals · observability · audit), không phải kỷ luật lúc-code. Năm trụ là một hệ: mọi action agent ghi vào một sổ-cái <code>events.jsonl</code> (append-only + hash-chain), từ đó nuôi 5 trụ, rồi <b>gác ở <code>fdk-gate</code> + CI</b>. Đánh giá đầy đủ + bằng chứng: <a href=\"300626-outer-harness-evaluation.html\">outer-harness-evaluation</a>.</p>",
        '<div class="diagram-box">' + "".join(_svg) + '<div class="diagram-hint">✥ kéo từng ô · cuộn để zoom · kéo mép dưới để mở rộng</div></div>',
        '<div class="table-wrap"><table><thead><tr><th>Trụ</th><th>Cơ chế (bằng CODE, không-LLM)</th><th>Trạng thái</th></tr></thead><tbody>'
        + _rows + '</tbody></table></div>',
        _pdet_html,
        "<p class=\"lead\" style=\"margin-top:10px\">Mấu chốt: trục <b>phán-xử</b> (tab Đánh giá: council/wikieval) và trục <b>tất định</b> (Trụ 4 code-health, Trụ 5 audit-chain) tách bạch — cổng tất định chặn cả khi LLM bị lừa.</p>",
    ]))

    _maint = [m for m in mechs if "maintain" in (m.get("surface") or [])]
    _maint_html = ('<ul class="s">' + "".join(
        f'<li><b>{esc(m["name"])}</b> — {esc(m["desc"])} <span style="color:#94a3b8">'
        f'(<code>{esc(m["live_probe"])}</code>)</span></li>' for m in _maint) + '</ul>'
    ) if _maint else '<p style="color:#b46a00">(manifest cơ-chế trống — xem <code>harness/mechanisms.yaml</code>)</p>'
    S.append(("maintain", "Tự bảo trì", "11 · Bảo trì", "Tự bảo trì overstack trên máy bạn", [
        "<p class=\"lead\">Sức khoẻ overstack được gác bởi <b>một tuyến phòng thủ cuối</b> — <code>/medic</code>: một lệnh chứng minh hệ còn khoẻ (luật còn cắn · validator không lệch bản · docs khớp đĩa · code compile · eval không tụt). Xanh = yên tâm; đỏ = in đúng chỗ hở + lệnh sửa.</p>",
        "<pre class='code-block'><code>python3 fdk/tools/medic.py --ci   # cổng sức-khoẻ tổng (chìa vạn năng)\n/harness-update                   # cập nhật bản mới + trả nợ wiki (self-heal)</code></pre>",
        "<p class=\"lead\" style=\"margin-top:14px\">Các tuyến bảo trì hiện có (<b>derive từ <code>harness/mechanisms.yaml</code></b> — không chép tay; medic probe <code>narrative</code> cắn nếu một tuyến LIVE vắng khỏi trang này):</p>",
        _maint_html,
        "<ol class=\"ck\">"
        "<li><b>medic gương-soi</b> — phiên đụng framework tự chạy <code>medic --ci</code> cuối lượt; dark-rail/docs-lệch lộ SỚM, không đợi commit-gate.</li>"
        "<li><b>Update + self-heal</b> — <code>/harness-update</code> cài bản mới, tự backfill nợ (Origin/index/OKF) trong một process.</li>"
        "<li><b>Refresh bản đồ năng lực</b> — <code>build-capabilities --root .</code> để agent thấy đúng đồ nghề sau update.</li></ol>",
        "<p>Đọc kết quả medic theo verdict: <b>KHOẺ</b> (xanh) · <b>KHOẺ có cảnh báo</b> (vàng — nợ đã biết) · <b>FAIL</b> (đỏ — có rail đen/docs lệch/code vỡ, đừng push). <code>/harness-update</code> theo exit code: <code>0</code> sạch · <code>3</code> còn nợ xử tay một lần · khác = lỗi hạ tầng.</p>",
    ]))

    # ── code-state self-narration (Phase 2, hợp đồng cứng council-advisory 030726) ──
    _n_val = len(list((root / "harness" / "validators").glob("*.py"))) if (root / "harness" / "validators").is_dir() else 0
    _n_hook = len(list((root / "llmwiki" / ".claude" / "hooks").glob("*.py"))) if (root / "llmwiki" / ".claude" / "hooks").is_dir() else 0
    _facts = [  # CHỈ FACT ỔN ĐỊNH (đổi thì regen cùng commit → docs-probe xanh); mỗi dòng có nguồn + lệnh
        ("skill", n_sk, "đĩa", "ls skills/*/SKILL.md | wc -l"),
        ("rule", n_rules, "policy", "grep -c 'id: R' harness/poc-vendor-neutral/policy.yaml"),
        ("validator", _n_val, "đĩa", "ls harness/validators/*.py | wc -l"),
        ("hook", _n_hook, "đĩa", "ls llmwiki/.claude/hooks/*.py | wc -l"),
        ("cơ-chế phòng thủ", len(mechs), "manifest", "grep -c '- id:' harness/mechanisms.yaml"),
        ("harness script", n_scripts, "đĩa", "ls harness/scripts/*.py | wc -l"),
    ]
    _fact_rows = "".join(
        f'<tr><td><b>{esc(l)}</b></td><td><b>{v}</b></td>'
        f'<td><span class="tag">{esc(s)}</span></td><td><code>{esc(c)}</code></td></tr>'
        for l, v, s, c in _facts)
    S.append(("codestate", "Trạng thái hiện thời", "12 · Trạng thái", "Trạng thái code hiện thời — tự tường thuật (FACT có nguồn)", [
        "<p class=\"lead\">overstack <b>tự tường thuật</b> trạng thái của chính nó theo một hợp đồng cứng (council-advisory): <b>một dòng FACT = một nguồn máy-đọc = một lệnh tái tạo được</b>. Không có \"prose mồ côi\"; mọi con số dưới đây bạn tự chạy lệnh sẽ ra y hệt.</p>",
        "<h3 class=\"sub\">FACT ổn định (đếm từ đĩa — bake trong trang này, gác bởi docs-probe + probe narrative)</h3>",
        f"<div class=\"table-wrap\"><table class=\"tbl\"><thead><tr><th>chỉ số</th><th>giá trị</th><th>nguồn</th><th>lệnh tái tạo</th></tr></thead><tbody>{_fact_rows}</tbody></table></div>",
        "<div class=\"note\"><h4>FACT động (git HEAD · dirty · bộ nhớ · code-graph · verdict medic) — xem LIVE, KHÔNG bake</h4>"
        "<p style=\"margin:0 0 8px\">Các chỉ số ĐỘNG (đổi mỗi commit) cố tình KHÔNG bake vào trang tĩnh này — bake cứng thì docs-probe sẽ đỏ vĩnh viễn sau mỗi commit (chicken-egg). Chạy lệnh để lấy trạng thái <b>hiện tại, luôn đúng</b>:</p>"
        "<pre class='code-block'><code>python3 fdk/tools/code-state.py          # bảng FACT trạng thái code (LIVE)\npython3 fdk/tools/code-state.py --check  # chứng minh tái tạo được (render 2 lần, diff)</code></pre></div>",
        "<div class=\"note\" style=\"border-color:#c9a227;background:rgba(255,193,7,.07)\"><h4>⚠ Ranh giới FACT ↔ OPINION</h4>"
        "<p style=\"margin:0\">Bảng trên chỉ chứa <b>SỰ KIỆN đo được</b> (có nguồn + lệnh). Mọi câu <i>diễn giải</i> — \"code sạch\", \"kiến trúc tốt\", \"đã ổn định\" — là <b>Ý KIẾN của người</b>, không thuộc lớp FACT và không xuất hiện ở đây (Feynman: cái tái tạo-được-bởi-người-lạ mới là dữ liệu). Verdict sức khoẻ khách quan duy nhất: <code>python3 fdk/tools/medic.py</code>.</p></div>",
    ]))

    S.append(("fdk", "FDK · dev overstack", "12 · Mở rộng", "FDK — phát triển chính overstack", [
        "<p style=\"font-size:12.5px;color:#b46a00;background:rgba(255,149,0,.1);border-radius:8px;padding:6px 12px;display:inline-block;margin:0 0 6px\">👷 Hai tab này (FDK + Dev cái mới) dành cho người <b>PHÁT TRIỂN chính overstack</b> — bỏ qua nếu bạn chỉ DÙNG overstack cho dự án của mình.</p>",
        "<p class=\"lead\">Khi bạn muốn sửa CHÍNH overstack (thêm skill/rule/validator/hook), gọi <code>/fdk</code> — front-door on-demand. KHÔNG auto-bơm mọi phiên (phần lớn phiên là dùng overstack cho DỰ ÁN KHÁC — ADR-004).</p>",
        "<div class=\"grid\"><div class=\"card\"><h4>/fdk lo gì</h4><ul class=\"s\">"
        "<li>Pre-flight: pull trước khi sửa · biết luật · đừng dẫm module cũ · propose trước.</li>"
        "<li>Inventory live (đếm skill/validator/rule từ đĩa, không hardcode).</li>"
        "<li>Self-contained: chạy được ở bất kỳ project nào.</li></ul></div>"
        "<div class=\"card\"><h4>Ranh giới (travel)</h4><ul class=\"s\">"
        "<li>Đồ nghề DEV (fdk-gate, meta-guards) ở LẠI repo overstack.</li>"
        "<li>Cái phục vụ dự án (skills, harness, code-logger, capability-map) thì TRAVEL xuống.</li></ul></div></div>",
        "<div class=\"note\"><h4>Dev framework TỪ một dự án khác → tự mở PR</h4><p style=\"margin:0\">Đang dở dự án khác mà cần chưng cất một skill vào overstack? Vì <code>fdk-gate</code>/<code>fdk/tools</code> không travel (ADR-004), <code>/fdk</code> dùng <code>fdk-kit.sh</code>: <b>pull</b> kit về sandbox <code>.overstack-kit/</code> → distill + <b>check</b> (fdk-gate) → <b>submit</b> = push branch + <code>gh pr create</code> tự mở PR vào <code>orca</code>. Một lệnh kéo về, một lệnh đẩy lên.</p></div>",
    ]))

    S.append(("newfeature", "Dev cái mới cần update gì", "13 · Checklist", "Dev một cái mới — cần update gì cho HỢP LỆ", [
        "<p class=\"lead\">👷 <i>(cho người phát triển overstack)</i> Khi thêm một tính năng/skill/rule mới cho overstack, đây là những chỗ phải đồng bộ để nó <b>hợp lệ</b> (bản máy-đọc = <code>fdk-gate</code>).</p>",
        "<ol class=\"ck\">"
        "<li><b>Code + test</b> — viết lõi tất định + self-test; ẩn số → nhốt sau MỘT adapter (<code>verified:false</code>).</li>"
        "<li><b>Rule mới?</b> → thêm vào <code>policy.yaml</code> + validator + wiring (đừng hardcode rời rạc).</li>"
        "<li><b>Skill mới?</b> → <code>skills/&lt;tên&gt;/SKILL.md</code> (canonical) + sync sang <code>llmwiki/skills/</code> (mirror) + LOOP_MAP + bảng skill trong AGENT.md ＋ CLAUDE.md (giữ parity) + CAPABILITIES.</li>"
        "<li><b>Cổng mới?</b> → cắm vào pre-commit + CI + một bước trong <code>fdk-gate</code>.</li>"
        "<li><b>Wiki \"vì sao\"</b> — viết concept giải thích lý do tồn tại (như feature-catalog).</li>"
        "<li><b>Docs người-đọc</b> — cập nhật trang này (regenerate) + README nếu đổi cách dùng.</li>"
        "<li><b>fdk-gate GREEN</b> — chạy <code>python3 harness/scripts/fdk-gate.py</code>, đủ bước mới push.</li></ol>",
        "<div class=\"note\"><h4>Vì sao cần checklist này</h4><p style=\"margin:0\">overstack lớn → thêm một thứ mà quên đồng bộ một chỗ = drift âm thầm. fdk-gate biến \"hợp lệ\" thành 14 bước máy-kiểm, không phụ thuộc trí nhớ.</p></div>",
    ]))

    _loop_meta = {
        "wiki-loop": ("#30b0c7", "Vòng tri thức", "Nạp → hỏi → dọn wiki của dự án. Dùng khi có tài liệu mới, cần tổng hợp câu trả lời từ wiki, hay wiki phình cần dọn."),
        "dev-loop": ("#5856d6", "Vòng phát triển", "Luồng làm tính năng: propose → gate → verify, cộng onboard codebase và eval (kiểm hồi quy, vòng lặp có guardrail)."),
        "orchestrate": ("#ff9500", "Điều phối đa-agent", "Chạy nhiều agent song song có kiểm soát: propose→gate→dispatch→verify, đánh giá (council/trace-grader), và deploy."),
        "utils": ("#34c759", "Tiện ích", "Đồ nghề rời: render tài liệu, thiết kế/style, image→code, caveman (nén token), dev-framework, và tiện ích khác."),
    }

    def _skitems(lp):
        return '<ul class="s">' + "".join(
            f'<li><b><code>/{esc(n)}</code></b> — {esc((d[:64] + "…") if len(d) > 66 else d)}</li>'
            for n, d in sorted(by_loop.get(lp, []))) + '</ul>'
    _secs = []
    for _lp in ("wiki-loop", "dev-loop", "orchestrate", "utils"):
        _c, _t, _intro = _loop_meta[_lp]
        _secs.append(f'<div class="card"><h4 style="color:{_c}">{_lp} — {_t}</h4><p>{_intro}</p>{_skitems(_lp)}</div>')
    _secs.append(f'<div class="card"><h4 style="color:#e0264b">rules — luật harness</h4>'
                 f'<p>{n_rules} rule (R1–R{n_rules}), enforce bởi validator tất định + hook, gác 3 lớp: <b>hook</b> (write-time) · <b>pre-commit</b> · <b>CI</b> (merge — không bypass được). Bảng đầy đủ từng rule ở tab <b>Nền 2 · Harness</b>.</p></div>')
    _secs.append('<div class="card"><h4 style="color:#ff2d55">cơ chế — runtime tự-gác (không phải rule)</h4>'
                 '<p>Các hook + cơ chế chạy nền để harness tự vận hành và tự kiểm chính nó — không nhờ agent nhớ:</p><ul class="s">'
                 + "".join(f'<li><b>{esc(_x["name"])}</b> — {esc(_x["desc"])}</li>' for _x in mechs) + '</ul></div>')
    _secs.append('<div class="card"><h4 style="color:#0a84ff">BNAL — build-now-adapt-later</h4>'
                 '<p>Thêm tính năng còn ẩn số mà không liều: dựng phần chắc chắn now, nhốt ẩn số sau MỘT config adapter (verified:false → true), auto từ harness/*.config.yaml. Chi tiết + sơ đồ ở tab <b>An toàn khi mở rộng</b>.</p></div>')
    _b7html = '<h3 class="sub">7 nhánh mind map — giải thích chi tiết từng nhánh</h3>' + "".join(_secs)
    S.append(("reference", "Tham chiếu (mind map)", "14 · Tham chiếu", "Tham chiếu — mind map skill & rule (đếm từ đĩa)", [
        f"<p class=\"lead\">Bản đồ tư duy (cheatsheet) toàn bộ đồ nghề: <b>{n_sk} skill</b> theo loop · <b>{n_rules} rule</b> · <b>{len(mechs)} cơ-chế</b> — <b>số liệu đếm từ đĩa</b>, còn <b>danh sách cơ-chế derive từ <code>harness/mechanisms.yaml</code> và gác bằng medic probe <code>narrative</code></b> (không chép tay). Mind map chia <b>7 nhánh</b> (4 loop skill + rules + cơ chế + BNAL) — xem bản đồ trước, giải thích từng nhánh ngay dưới. Mỗi nhánh <b>mặc định đóng — click để mở/đóng</b> (mũi tên ▸).</p>",
        mindmap_html,
        _b7html,
        "<h3 style=\"margin-top:26px\">Bảng chi tiết (mô tả đầy đủ)</h3>"
        "<p class=\"s\" style=\"color:var(--t2)\">Để tránh lặp (mỗi bảng render MỘT lần — chống drift): "
        "bảng <b>từng rule</b> ở tab <a href=\"@harness\">Nền 2 · Harness</a>; bảng <b>từng skill</b> ở tab "
        "<a href=\"@skills\">Skill</a>. Mind map trên là bản tra cứu nhanh; bảng đầy đủ nằm đúng tab chủ đề.</p>",
    ]))
    # ── Graph nhúng: đường DUY NHẤT để memory-map (#4) và skill-whiteboard (#5) xuống
    # được máy user. Hai artifact đó KHÔNG travel (generator là framework_only), nhưng
    # overstack.html thì "output travel" — nên nhúng vào đây là chúng đi theo.
    # Dùng iframe srcdoc thay vì tách fragment renderer: iframe cô lập JS/id, nên KHÔNG
    # phải mổ template 350 dòng của build-wiki-graph.py — engine đó đang travel, mổ nó
    # để lấy một khung nhìn là đổi rủi ro lấy tiện.
    # TỰ SINH hai graph trước khi nhúng — KHÔNG dựa vào thứ tự hook.
    # Bug đã dính ngay lần đầu: stop.py chạy build-overstack-docs ở block (A), còn
    # wiki-graph ở block (B) và memory-map ở secondary_memory() — đều SAU. Nên overstack
    # nhúng bản cũ và medic báo docs stale ở mọi phiên. Root không phải "sai thứ tự" mà là
    # "overstack phụ thuộc artifact có trigger sinh KHÁC nó". Tự sinh thì hết cả lớp lỗi,
    # không phải sắp lại thứ tự rồi mong nó đứng yên.
    import subprocess as _sp
    for _gen in ("memory-map.py", "whiteboard-skill-map.py"):
        _g = root / "fdk" / "tools" / _gen
        if _g.is_file():
            try:
                _sp.run([sys.executable, str(_g)], cwd=str(root), capture_output=True, timeout=60)
            except Exception:
                pass   # fail-open: thiếu/hỏng generator thì nhúng bản đang có

    emb = []
    for fname, title, why in (
            ("memory-map.html", "Bản đồ trí nhớ",
             "phiên nào chạm file nào — cạnh <code>elaborates</code>, sinh lại cuối mỗi phiên"),
            ("skill-whiteboard.html", "Bản đồ skill",
             "loop chứa skill nào — cạnh <code>contains</code> / <code>orchestrates</code>")):
        f = root / "llmwiki" / "html" / fname
        if not f.is_file():
            continue
        doc = f.read_text(encoding="utf-8").replace("&", "&amp;").replace('"', "&quot;")
        emb.append(f'<h3>{title}</h3><p class="lead">{why}</p>'
                   f'<iframe title="{title}" style="width:100%;height:640px;border:1px solid '
                   f'var(--line,#d8e2f0);border-radius:12px;background:#fff" '
                   f'sandbox="allow-scripts" srcdoc="{doc}"></iframe>')
    if emb:
        S.append(("graphs", "Bản đồ quan hệ", "· BẢN ĐỒ", "Bản đồ quan hệ (graph)", [
            '<p class="lead">Các đồ thị này nhúng thẳng vào trang, nên chúng đi cùng '
            '<code>overstack.html</code> xuống máy bạn — không cần cài thêm gì.</p>'] + emb))

    return S


def render(root: Path) -> str:
    UNCLASSIFIED.clear()
    S = sections(root)
    by_loop, n_sk = skills_by_loop(root)
    n_rules = len(rules(root))
    nav = ['<div class="logo">overstack<small>tài liệu chính thức · sinh từ đĩa</small></div>',
           '<div class="grp">Bắt đầu</div>']
    # Gom nhóm theo HÀNH TRÌNH người mới (feedback 2026-07-07), không theo kiến trúc nội bộ:
    # người zero-context nghĩ theo câu hỏi "là gì / cài sao / dùng hằng ngày / đo kiểm / tra cứu".
    grouped = [("Mới bắt đầu", ["quickstart", "what", "install"]),
               ("3 nền tảng", ["wiki", "harness", "skills"]),
               ("Dùng hằng ngày", ["workflow", "orca", "bnal"]),
               ("Đo & kiểm khi chạy", ["advanced", "runtime", "awareness", "codestate"]),
               ("Tra cứu", ["reference", "graphs"]),
               ("Vận hành", ["maintain"]),
               ("👷 Cho người phát triển overstack", ["fdk", "newfeature"])]
    # Thứ tự thân bài = thứ tự phẳng của `grouped` (nav ↔ thân luôn khớp, chống lệch khi chèn/di tab)
    _flat = [sid for _g, ids in grouped for sid in ids]
    S = sorted(S, key=lambda t: _flat.index(t[0]) if t[0] in _flat else len(_flat))
    id2nav = {sid: navlabel for sid, navlabel, *_ in S}
    idx = {sid: i for i, (sid, *_rest) in enumerate(S)}
    ICON = {"quickstart": "🚀", "what": "📖", "install": "📦", "wiki": "📚", "harness": "🛡️",
            "skills": "🧰", "workflow": "🔄", "orca": "🐳", "advanced": "⚖️", "awareness": "🧭",
            "runtime": "📡", "bnal": "🧩", "maintain": "🔧", "reference": "🗺️", "fdk": "👷",
            "newfeature": "✅", "codestate": "📊"}
    # Nhãn sidebar tiếng-Việt-trước, jargon-trong-ngoặc (feedback 2026-07-07 — người mới không đọc
    # được FDK/BNAL/AgentOps trần). CHỈ đổi text sidebar; H2 + nội dung section giữ nguyên.
    NAV_OVERRIDE = {"quickstart": "Chạy thử 2 phút", "wiki": "Wiki (trí nhớ)",
                    "harness": "Harness (luật)", "skills": "Skills (kỹ năng)",
                    "workflow": "Quy trình làm việc", "orca": "Chạy nhiều agent (Orca)",
                    "bnal": "Thêm tính năng có ẩn số", "advanced": "Đánh giá chất lượng",
                    "runtime": "5 trụ vận hành (AgentOps)", "awareness": "Năng lực & dấu vết",
                    "reference": "Mind map skill & rule"}
    nav = ['<div class="logo">overstack<small>tài liệu chính thức · sinh từ đĩa</small></div>']
    for grp, ids in grouped:
        nav.append(f'<div class="grp">{grp}</div>')
        for sid in ids:
            nav.append(f'<a href="#s{idx[sid]}"><span class="ic">{ICON.get(sid, "•")}</span>{NAV_OVERRIDE.get(sid, id2nav[sid])}</a>')
    body = []
    for i, (sid, navlabel, tag, title, blocks) in enumerate(S):
        tag = re.sub(r'^\s*\d+\s*·\s*', f'{i:02d} · ', tag)   # auto-số eyebrow theo thứ tự (chống trùng khi chèn tab)
        inner = [f'<span class="tag">{tag}</span>', f"<h2>{title}</h2>"]
        inner.extend(blocks)
        body.append(f'<section id="s{i}" class="sec s{i}"><div class="inner">{"".join(inner)}</div></section>')
    html = [
        '<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">',
        # chống FOUC: áp theme user đã chọn TRƯỚC khi CSS render (đọc localStorage ngay trong head)
        '<script>(function(){try{var t=localStorage.getItem("overstack-theme");'
        'if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}})();</script>',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>overstack — tài liệu chính thức</title>",
        "<style>", CSS_BASE, accent_css(len(S)), "</style></head><body>",
        '<a class="skip" href="#s0">Bỏ qua tới nội dung chính</a>',
        "<nav>", "".join(nav), "</nav>",
        '<header class="hero"><span class="eyebrow">Tài liệu chính thức · cho người đọc</span>',
        "<h1>overstack</h1>",
        f"<p>overstack là <b>một lớp bạn đặt lên dự án</b> (<i>agent harness · AI control plane</i>) để AI agent làm việc như một <b>kỹ sư có kỷ luật</b>: có <b>trí nhớ</b> (wiki — <i>context engineering</i>), có <b>luật không phá được</b> (harness — <i>guardrails / policy-as-code</i>, {n_rules} rule · 0 token), có <b>kỹ năng đóng sẵn</b> ({n_sk} skill), biết <b>điều phối nhiều agent</b> (Orca — <i>agent orchestration</i>) — và tự <b>đo + kiểm</b> khi chạy (<i>AgentOps: evals + observability</i>). "
        f"Bắt đầu ở Quickstart; các tab sau đi sâu từng phần.</p></header>",
        "".join(body),
        '<footer>overstack · tài liệu sinh bằng <code>fdk/tools/build-overstack-docs.py</code> (số liệu live từ đĩa) · '
        "self-contained, offline-proof · travel cùng install.</footer>",
        "<script>", JS, "</script></body></html>",
    ]
    out = "".join(html)
    # Resolve link nội bộ dạng @<sid> (vd @reference) → #s{idx} thật, chống gãy khi đổi thứ tự tab.
    # Dùng sentinel '@' (không phải '#') để KHÔNG bao giờ đè nhầm href="#..." trong ví dụ HTML ở <pre>/<code>.
    out = re.sub(r'href="@([a-z][a-z0-9-]*)"',
                 lambda m: f'href="#s{idx[m.group(1)]}"' if m.group(1) in idx else m.group(0), out)
    return out


def main():
    content = render(ROOT)
    if UNCLASSIFIED:   # hỏi-1-lần: nhắc dev khai nhóm cho skill mới (rồi nó tự vào mind map)
        skills = ", ".join(f"{n} ({lp})" for lp, n in sorted(UNCLASSIFIED))
        print(f"[build-overstack-docs] ⚠ {len(UNCLASSIFIED)} skill chưa phân nhóm mind map "
              f"(đang ở '❓ chưa phân loại'): {skills}\n  → thêm vào LOOP_GROUPS trong "
              f"fdk/tools/build-overstack-docs.py (1 lần), rồi auto-vào nhóm.", file=sys.stderr)
    if "--check" in sys.argv[1:]:
        cur = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if cur.strip() != content.strip():
            print("[build-overstack-docs] overstack.html CŨ so với đĩa — chạy lại để cập nhật.", file=sys.stderr)
            sys.exit(2)
        print("overstack.html khớp đĩa ✓")
        sys.exit(0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"✓ wrote {OUT.relative_to(ROOT)} ({len(content)} bytes, {content.count(chr(10)) + 1} dòng)")


if __name__ == "__main__":
    main()
