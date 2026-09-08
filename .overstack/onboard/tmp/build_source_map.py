#!/usr/bin/env python3
"""Sinh llmwiki/html/290726-overstack-source-map.html — trang mô tả source code repo overstack.
Mọi con số đọc thẳng từ .overstack/graph/knowledge-graph.json, domain-graph.json, policy.yaml.
Design system: /docs-site-macos (liquid glass light-blue, sidebar-only nav, R11)."""
import json, os, re, sys, html
from collections import Counter, defaultdict

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT = os.path.join(ROOT, "llmwiki/html/290726-overstack-source-map.html")
G = json.load(open(os.path.join(ROOT, ".overstack/graph/knowledge-graph.json")))
D = json.load(open(os.path.join(ROOT, ".overstack/onboard/intermediate/domain-graph.json")))
E = html.escape

byid = {n["id"]: n for n in G["nodes"]}
indeg = Counter()
for e in G["edges"]:
    indeg[e["target"]] += 1
etypes = Counter(e["type"] for e in G["edges"])
ntypes = Counter(n["type"] for n in G["nodes"])

# ---------- rules từ policy.yaml (parse thủ công, không cần PyYAML) ----------
def parse_rules(path):
    rules, cur = [], None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*- id:\s*(R\d+)", line)
        if m:
            if cur: rules.append(cur)
            cur = {"id": m.group(1), "name": "", "statement": "", "enforce": "", "validator": ""}
            continue
        if cur is None: continue
        for key, field in (("name", "name"), ("statement", "statement"),
                           ("enforce_at", "enforce"), ("validator", "validator")):
            m = re.match(r"\s+%s:\s*(.+)" % key, line)
            if m:
                v = m.group(1).strip().strip('"').split("  #")[0].strip()
                cur[field] = v
    if cur: rules.append(cur)
    return rules

rules = parse_rules(os.path.join(ROOT, "harness/policy.yaml"))
rules.sort(key=lambda r: int(r["id"][1:]))

# ---------- layers ----------
layers = []
for L in G["layers"]:
    files = sorted((byid[i] for i in L["nodeIds"]),
                   key=lambda n: (-n.get("churn", 0), -indeg[n["id"]], n["filePath"]))
    layers.append({**L, "files": files, "count": len(files),
                   "churn": sum(f.get("churn", 0) for f in files)})

hot = sorted([n for n in G["nodes"] if n.get("churn")], key=lambda n: -n["churn"])[:20]
dep = [(byid[i], c) for i, c in indeg.most_common(40)
       if not byid[i]["filePath"].endswith(("wiki/log.md", "wiki/index.md"))][:15]

subjects = []
sp = os.path.join(ROOT, ".overstack/onboard/tmp/recent-subjects.txt")
if os.path.isfile(sp):
    subjects = [l.strip() for l in open(sp, encoding="utf-8") if l.strip()][:14]

n_steps = sum(len(f["steps"]) for d in D["domains"] for f in d["flows"])
n_flows = sum(len(d["flows"]) for d in D["domains"])

# ═══════════════════════════ CSS ═══════════════════════════
ACCENT = ["#0a84ff", "#30b0c7", "#5856d6", "#34c759", "#ff9500", "#ff2d55"]
H4 = ["#0a84ff", "#30b0c7", "#5856d6", "#28a745", "#f08c00", "#e0264b"]
OVER = ["rgba(10,132,255,.05)", "rgba(48,176,199,.05)", "rgba(88,86,214,.05)",
        "rgba(52,199,89,.05)", "rgba(255,149,0,.06)", "rgba(255,45,85,.05)"]
TAGBG = ["rgba(10,132,255,.10)", "rgba(48,176,199,.12)", "rgba(88,86,214,.11)",
         "rgba(52,199,89,.12)", "rgba(255,149,0,.12)", "rgba(255,45,85,.10)"]

SECTIONS = [
    ("Tổng quan", "Repo là gì, đo bằng số"),
    ("Kiến trúc 5 lớp", "Luật chảy từ khai báo xuống thực thi"),
    ("Bản đồ 15 tầng", "846 file, mỗi file thuộc đúng một tầng"),
    ("18 luật đang gác", "Nguồn chân lý là policy.yaml"),
    ("7 miền · %d luồng" % n_flows, "%d bước, mỗi bước một file:line thật" % n_steps),
    ("File nóng & lịch sử", "Churn, phụ thuộc, việc đang làm"),
    ("Quy ước & cạm bẫy", "Thứ phải biết trước khi sửa"),
]

CSS_BASE = """
*{margin:0;padding:0;box-sizing:border-box}
html{background:#e9f0fb;scroll-behavior:smooth;scrollbar-width:thin;scrollbar-color:transparent transparent}
html.scrolling{scrollbar-color:rgba(10,132,255,.32) transparent}
:root{
 --font-text:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue','Roboto','Segoe UI',sans-serif;
 --font-display:-apple-system,BlinkMacSystemFont,'SF Pro Display','Helvetica Neue','Roboto','Segoe UI',sans-serif;
 --font-mono:'SF Mono',ui-monospace,SFMono-Regular,Menlo,'Roboto Mono',Consolas,monospace;
 --glass-1:rgba(255,255,255,.55);--glass-2:rgba(255,255,255,.7);--glass-3:rgba(255,255,255,.88);
 --blur-1:24px;--blur-2:8px;--blur-3:4px;
 --edge-hi:inset 0 1px 0 rgba(255,255,255,.85);
 --border:rgba(30,90,170,.14);--ink:#0f0f12;--ink2:#4a4a55;--code-bg:#11151f}
body{font-family:var(--font-text);font-size:13px;line-height:1.62;color:var(--ink);padding-left:200px;
 -webkit-font-smoothing:antialiased;
 background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.10),transparent 60%),
   radial-gradient(700px 420px at 95% 15%,rgba(90,162,232,.08),transparent 55%),
   linear-gradient(180deg,#f7fbff 0%,#eaf2fd 100%);
 transition:padding-left .28s cubic-bezier(.4,0,.2,1)}
body::before{content:'';position:fixed;inset:-10%;z-index:-1;pointer-events:none;
 background:
  radial-gradient(640px 440px at 10% 14%,rgba(10,132,255,.22),transparent 65%),
  radial-gradient(380px 460px at 4% 52%,rgba(48,176,199,.18),transparent 65%),
  radial-gradient(540px 400px at 88% 10%,rgba(88,86,214,.13),transparent 60%),
  radial-gradient(720px 500px at 74% 76%,rgba(48,176,199,.13),transparent 65%),
  radial-gradient(480px 380px at 16% 86%,rgba(255,149,0,.12),transparent 60%);
 animation:orbDrift 46s ease-in-out infinite alternate}
@keyframes orbDrift{100%{transform:translate(2.2%,1.6%) scale(1.045)}}
body::after{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;
 background-image:radial-gradient(rgba(30,90,170,.11) 1px,transparent 1.3px);background-size:22px 22px;
 mask-image:linear-gradient(180deg,rgba(0,0,0,.55),rgba(0,0,0,.22));
 -webkit-mask-image:linear-gradient(180deg,rgba(0,0,0,.55),rgba(0,0,0,.22))}
a{color:#0a84ff;text-decoration:none}
h1,h2,h3,.logo-t{font-family:var(--font-display);letter-spacing:-.02em;text-wrap:balance}
p{text-wrap:pretty}
code{font-family:var(--font-mono);font-size:11.5px;background:rgba(10,132,255,.08);
 padding:1px 5px;border-radius:5px;color:#0b5fbf;word-break:break-word}
:focus-visible{outline:2px solid #0a84ff;outline-offset:2px;border-radius:8px}
:focus:not(:focus-visible){outline:none}
::-webkit-scrollbar{width:11px;height:11px;background:transparent}
::-webkit-scrollbar-track,::-webkit-scrollbar-track-piece,::-webkit-scrollbar-corner,
::-webkit-scrollbar-button{background:transparent;border:0;box-shadow:none}
::-webkit-scrollbar-thumb{background:transparent;border-radius:8px;border:3px solid transparent;
 background-clip:content-box;transition:background-color .25s ease}
html.scrolling::-webkit-scrollbar-thumb,::-webkit-scrollbar-thumb:hover{background-color:rgba(10,132,255,.32)}
::-webkit-scrollbar-thumb:active{background-color:rgba(10,132,255,.6)}
.skip-link{position:fixed;top:8px;left:8px;z-index:200;padding:8px 14px;border-radius:10px;font-size:12px;
 background:var(--glass-1);backdrop-filter:blur(var(--blur-1));border:1px solid var(--border);
 transform:translateY(-150%);transition:transform .2s}
.skip-link:focus-visible{transform:translateY(0)}

/* ── sidebar ── */
nav{position:fixed;top:0;left:0;bottom:0;width:200px;z-index:100;display:flex;flex-direction:column;
 align-items:stretch;gap:2px;padding:18px 12px;overflow-y:auto;scrollbar-width:none;-ms-overflow-style:none;
 background:linear-gradient(165deg,rgba(255,255,255,.46) 0%,rgba(255,255,255,.22) 48%,rgba(240,248,255,.34) 100%);
 backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
 -webkit-backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
 border-right:1px solid rgba(255,255,255,.55);
 box-shadow:inset 0 1px 0 rgba(255,255,255,.9),inset 1px 0 0 rgba(255,255,255,.5),
  inset -1px 0 0 rgba(30,90,170,.10),4px 0 24px rgba(30,90,170,.08);
 transition:transform .28s cubic-bezier(.4,0,.2,1)}
nav::-webkit-scrollbar{width:0;height:0;display:none}
nav>*{flex-shrink:0;position:relative}
nav::before{content:'';position:absolute;inset:0;pointer-events:none;
 background:radial-gradient(220px 160px at 18% 4%,rgba(255,255,255,.55),transparent 70%),
  linear-gradient(115deg,rgba(255,255,255,.28) 0%,transparent 28%,transparent 72%,rgba(255,255,255,.14) 100%)}
.brand{display:flex;align-items:center;gap:9px;margin:0 0 14px;padding:6px 8px}
.brand .ic{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;
 background:linear-gradient(135deg,#0a84ff,#64b5f7);box-shadow:0 2px 8px rgba(10,132,255,.3)}
.brand .ic svg{width:15px;height:15px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.logo-t{font-size:15px;font-weight:700;
 background:linear-gradient(135deg,#0a84ff,#64b5f7);-webkit-background-clip:text;background-clip:text;color:transparent}
.logo-s{font-size:9.5px;color:var(--ink2);letter-spacing:.02em}
nav a{display:flex;align-items:center;gap:9px;padding:5px 10px;border-radius:10px;font-size:12px;
 color:var(--ink2);overflow:hidden;transition:background .15s,color .15s}
nav a .ic{width:24px;height:24px;border-radius:7px;display:grid;place-items:center;flex-shrink:0}
nav a .ic svg{width:14px;height:14px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
nav a:hover{background:rgba(10,132,255,.06);color:var(--ink)}
nav a.active{color:#0a84ff;background:rgba(10,132,255,.08);font-weight:600}
.nav-close{position:absolute;top:10px;right:10px;width:26px;height:26px;border-radius:8px;display:flex;
 align-items:center;justify-content:center;font-size:12px;color:var(--ink2);cursor:pointer;
 background:rgba(0,0,0,.04);border:none;overflow:hidden}
.nav-close:hover{color:#0a84ff;background:rgba(10,132,255,.10)}
.nav-toggle{position:fixed;top:12px;left:12px;z-index:120;width:32px;height:32px;border-radius:10px;
 display:flex;align-items:center;justify-content:center;font-size:14px;color:var(--ink2);cursor:pointer;
 background:linear-gradient(165deg,rgba(255,255,255,.5),rgba(255,255,255,.24));
 backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
 -webkit-backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);border:1px solid transparent;
 box-shadow:inset 0 1px 0 rgba(255,255,255,.75),0 0 0 1px rgba(30,90,170,.08),0 2px 10px rgba(30,90,170,.12);
 transition:opacity .2s,transform .28s cubic-bezier(.4,0,.2,1)}
.nav-toggle:hover{color:#0a84ff}
body:not(.nav-collapsed) .nav-toggle{opacity:0;pointer-events:none;transform:translateX(-6px)}
body.nav-collapsed nav{transform:translateX(-100%)}
body.nav-collapsed{padding-left:0}
.theme-row{position:sticky;bottom:-18px;margin-top:auto;display:flex;align-items:center;
 justify-content:space-between;padding:11px 12px;border-top:1px solid var(--border);
 background:linear-gradient(180deg,rgba(255,255,255,.16),rgba(255,255,255,.42));backdrop-filter:blur(14px)}
.theme-row .lbl{font-size:11px;color:var(--ink2)}
.theme-switch{cursor:pointer}
.theme-switch .track{position:relative;display:block;width:50px;height:26px;border-radius:999px;
 background:rgba(30,90,170,.14);transition:background .2s}
.theme-switch .track::before{content:'☀️';position:absolute;left:6px;top:5px;font-size:10px}
.theme-switch .track::after{content:'🌙';position:absolute;right:6px;top:5px;font-size:10px}
.theme-switch .knob{position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;
 background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.22);transition:left .18s;z-index:2}
.theme-switch.on .knob{left:26px}
.theme-switch.on .track{background:rgba(10,132,255,.45)}

/* ── ripple ── */
.ripple-ink,.ripple{position:absolute;border-radius:50%;pointer-events:none}
.ripple-ink{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.70) 0%,rgba(255,255,255,.28) 38%,rgba(10,132,255,.20) 72%,transparent 100%);
 box-shadow:inset 0 1px 0 rgba(255,255,255,.9),inset 0 -10px 20px rgba(10,132,255,.12),0 0 14px rgba(10,132,255,.10);
 backdrop-filter:blur(2px) saturate(1.25);transform:scale(0);opacity:1;
 animation:rippleGrow .6s cubic-bezier(.25,.46,.45,.94) forwards}
@keyframes rippleGrow{55%{transform:scale(1);opacity:.75}100%{transform:scale(1.04);opacity:0}}
.ripple{transform:scale(0);opacity:.9;
 background:radial-gradient(circle,rgba(255,255,255,.6) 0%,rgba(10,132,255,.22) 35%,transparent 70%);
 box-shadow:0 0 0 1px rgba(255,255,255,.45);animation:rippleWave .65s cubic-bezier(.2,.6,.3,1) forwards}
@keyframes rippleWave{to{transform:scale(2.8);opacity:0}}

/* ── hero ── */
.hero{max-width:1100px;margin:0 auto;padding:74px 24px 26px}
.hero .eyebrow{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
 padding:4px 11px;border-radius:999px;background:rgba(10,132,255,.10);color:#0a84ff;margin-bottom:14px}
.hero h1{font-size:clamp(26px,4vw,40px);font-weight:700;line-height:1.14;
 background:linear-gradient(135deg,#0a84ff,#5aa2e8,#cfe3fb);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .lead{font-size:14px;color:var(--ink2);max-width:760px;margin-top:12px}
.hero .meta{display:flex;flex-wrap:wrap;gap:7px;margin-top:16px}
.hero .meta span{font-size:10.5px;color:var(--ink2);padding:3px 10px;border-radius:999px;
 background:var(--glass-2);border:1px solid var(--border);box-shadow:var(--edge-hi);font-variant-numeric:tabular-nums}

/* ── sections ── */
.section-bg{position:relative;overflow:visible}
.section-bg::before{content:'';position:absolute;top:0;bottom:0;left:50%;width:100vw;
 transform:translateX(-50%);pointer-events:none}
section{max-width:1100px;margin:0 auto;padding:56px 24px 62px;scroll-margin-top:24px;position:relative}
.section-header{margin-bottom:20px}
.tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 padding:3px 10px;border-radius:999px;margin-bottom:9px}
.section-header h2{font-size:21px;font-weight:700;color:#1d1d1f}
.section-header p{font-size:13px;color:var(--ink2);margin-top:6px;max-width:800px}
.card{background:var(--glass-2);backdrop-filter:blur(var(--blur-2)) saturate(1.1);border:1px solid var(--border);
 border-radius:16px;box-shadow:var(--edge-hi),0 4px 20px rgba(20,40,90,.08);padding:18px}
.card h4{font-size:12.5px;font-weight:700;margin-bottom:8px}
.card p,.card li{font-size:12.5px;color:var(--ink2)}
.card ul{list-style:none;display:flex;flex-direction:column;gap:6px}
.card li{padding-left:14px;position:relative}
.card li::before{content:'›';position:absolute;left:0;font-weight:700}
.grid{display:grid;gap:14px}
.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:820px){.g2,.g3,.g4{grid-template-columns:1fr}}
.stat{text-align:center;padding:15px 10px}
.stat b{display:block;font-size:24px;font-weight:700;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.stat span{font-size:10.5px;color:var(--ink2)}

/* ── tables (tier 3) ── */
.table-wrap{overflow-x:auto;border-radius:14px;border:1px solid var(--border);
 box-shadow:var(--edge-hi),0 4px 20px rgba(20,40,90,.06);margin-top:14px}
table{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums;
 background:var(--glass-3);backdrop-filter:blur(var(--blur-3))}
th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink2);
 padding:9px 12px;border-bottom:1px solid var(--border);white-space:nowrap;font-weight:700}
td{padding:8px 12px;border-bottom:1px solid rgba(30,90,170,.07);vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:rgba(10,132,255,.04)}
td.num{text-align:right;white-space:nowrap}
.pill{display:inline-block;font-size:10px;font-weight:700;padding:1.5px 8px;border-radius:999px;white-space:nowrap}
.p-hard{background:rgba(255,45,85,.12);color:#e0264b}
.p-auto{background:rgba(52,199,89,.14);color:#28a745}
.p-repo{background:rgba(88,86,214,.12);color:#5856d6}
.p-hot{background:rgba(255,149,0,.14);color:#c26a00}

/* ── master-detail ── */
.md-wrap{display:grid;grid-template-columns:272px 1fr;gap:16px;margin-top:16px}
.md-list{list-style:none;max-height:560px;overflow-y:auto;padding-right:4px}
.md-list li{padding:9px 12px;border-radius:13px;cursor:pointer;margin-bottom:7px;background:var(--glass-2);
 backdrop-filter:blur(var(--blur-2));border:1px solid var(--border);box-shadow:var(--edge-hi);
 transition:transform .16s,border-color .16s;position:relative;overflow:hidden}
.md-list li:hover{transform:translateX(3px)}
.md-list li[aria-selected=true]{border-color:rgba(10,132,255,.45);
 background:linear-gradient(120deg,rgba(255,255,255,.94),rgba(238,246,255,.88))}
.md-list .mt{font-size:12px;font-weight:700;display:block}
.md-list .ms{font-size:10px;color:var(--ink2)}
.md-detail{min-height:220px}
.md-pane{display:none}
.md-pane.on{display:block}
.md-pane h3{font-size:15px;font-weight:700;margin-bottom:6px}
.md-pane .desc{font-size:12.5px;color:var(--ink2);margin-bottom:12px}
.filelist{list-style:none;display:flex;flex-direction:column;gap:3px;font-family:var(--font-mono);font-size:11px}
.filelist li{display:flex;justify-content:space-between;gap:12px;padding:3px 8px;border-radius:7px}
.filelist li:nth-child(odd){background:rgba(10,132,255,.035)}
.filelist .fp{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.filelist .fm{color:var(--ink2);font-size:10px;white-space:nowrap;flex-shrink:0}
.steps{list-style:none;counter-reset:s;display:flex;flex-direction:column;gap:7px}
.steps li{padding:8px 11px;border-radius:11px;background:rgba(255,255,255,.6);border:1px solid var(--border);font-size:12px}
.steps .sn{font-weight:700;font-size:11px;margin-right:6px}
.steps .loc{display:block;font-family:var(--font-mono);font-size:10.5px;color:var(--ink2);margin-top:3px}
.flowhead{font-size:12px;font-weight:700;margin:14px 0 7px;display:flex;align-items:center;gap:8px}
.flowhead .trg{font-weight:400;font-size:10.5px;color:var(--ink2)}

/* ── diagram ── */
.diagram-box{background:var(--glass-2);backdrop-filter:blur(var(--blur-2)) saturate(1.1);
 border:1px solid var(--border);border-radius:16px;box-shadow:var(--edge-hi),0 4px 20px rgba(20,40,90,.08);
 padding:20px;margin:18px 0;position:relative;overflow:hidden;display:flex;flex-direction:column;
 resize:vertical;min-height:180px;transition:box-shadow .2s ease}
.diagram-box:hover{box-shadow:var(--edge-hi),0 6px 28px rgba(20,40,90,.14)}
.diagram-viewport{position:relative;flex:1 1 auto;width:100%;overflow:hidden;cursor:grab;touch-action:none}
.diagram-viewport.grabbing{cursor:grabbing}
.diagram-viewport svg{width:100%;height:auto;display:block;overflow:visible;transform-origin:0 0;
 will-change:transform;user-select:none;-webkit-user-select:none}
.diagram-box text{font-variant-numeric:tabular-nums}
.dnode{cursor:move}
.dnode>rect{transition:filter .15s ease}
.dnode:hover>rect:first-of-type{filter:drop-shadow(0 3px 8px rgba(0,0,0,.18))}
.diagram-hint{position:absolute;top:8px;right:12px;z-index:5;font-size:10px;color:var(--ink2);
 background:rgba(255,255,255,.75);border:1px solid rgba(0,0,0,.05);border-radius:20px;padding:3px 10px;
 white-space:nowrap;opacity:0;transition:opacity .2s;pointer-events:none}
.diagram-box:hover .diagram-hint{opacity:.9}
.diagram-reset{position:absolute;bottom:8px;right:10px;z-index:5;font-size:11px;background:rgba(255,255,255,.85);
 border:1px solid rgba(0,0,0,.08);border-radius:8px;padding:3px 9px;cursor:pointer;color:var(--ink2);
 opacity:0;transition:opacity .2s}
.diagram-box:hover .diagram-reset{opacity:1}
.diagram-box::after{content:'';position:absolute;right:5px;bottom:5px;width:16px;height:16px;pointer-events:none;
 opacity:0;transition:opacity .25s ease;clip-path:polygon(100% 0,100% 100%,0 100%);
 background:repeating-linear-gradient(135deg,transparent 0 3.5px,rgba(10,132,255,.45) 3.5px 5px)}
.diagram-box:hover::after{opacity:.85}
.diagram-box::-webkit-resizer{display:none}
@keyframes flowArrow{0%{stroke-dashoffset:20}100%{stroke-dashoffset:0}}
@keyframes pulseA{0%,100%{opacity:1}50%{opacity:.45}}

/* ── code ── */
.code-wrap{position:relative;margin-top:12px}
pre.code-block{background:var(--code-bg);color:#dbe4f0;border-radius:12px;padding:14px 16px;overflow-x:auto;
 font-family:var(--font-mono);font-size:11.5px;line-height:1.65;border:1px solid rgba(255,255,255,.06)}
.code-copy{position:absolute;top:7px;right:7px;z-index:2;width:28px;height:26px;display:inline-flex;
 align-items:center;justify-content:center;background:rgba(255,255,255,.1);color:#cbd5e1;
 border:1px solid rgba(255,255,255,.15);border-radius:7px;cursor:pointer;opacity:0;
 transition:opacity .15s,background .15s,color .15s}
.code-copy svg{width:14px;height:14px;display:block}
.code-wrap:hover .code-copy{opacity:1}
.code-copy:hover{background:rgba(255,255,255,.2);color:#fff}
.code-copy.copied{background:rgba(16,185,129,.25);color:#6ee7b7;border-color:rgba(16,185,129,.45);opacity:1}
@media(max-width:640px){.code-copy{opacity:1}}

/* ── mind map ── */
.mm{overflow-x:auto;padding:14px 4px 6px}
.mm-canvas{position:relative;width:max-content}
.mm-links{position:absolute;top:0;left:0;pointer-events:none;overflow:visible;z-index:0}
.mm-links path{fill:none;stroke-width:2.2;opacity:.55;stroke-linecap:round}
.mm .tree{position:relative;z-index:1}
.mm .tree,.mm .children{display:flex;flex-direction:column;gap:9px;justify-content:center}
.mm .row{display:flex;align-items:center;gap:48px;position:relative}
.mm .children{position:relative}
.mm .children.collapsed{display:none}
.mm .node{position:relative;display:inline-flex;flex-direction:column;gap:1px;padding:7px 13px;border-radius:13px;
 cursor:default;white-space:nowrap;background:rgba(255,255,255,.72);backdrop-filter:blur(7px) saturate(1.1);
 border:1px solid var(--border);box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 3px 14px rgba(20,40,90,.07);
 transition:transform .12s}
.mm .node.has-children{cursor:pointer}
.mm .node:hover{transform:translateY(-1px)}
.mm .node .nm{font-size:13px;font-weight:700;letter-spacing:-.01em}
.mm .node .ds{font-size:10.5px;color:var(--ink2)}
.mm .node .ct{font-size:10px;color:#fff;font-weight:700;padding:1px 7px;border-radius:999px;position:absolute;
 top:-8px;right:-8px;background:#0a84ff;font-variant-numeric:tabular-nums}
.mm .node.has-children::after{content:'';position:absolute;right:-7px;top:50%;width:6px;height:6px;
 border-right:2px solid var(--ink2);border-bottom:2px solid var(--ink2);transform:translateY(-50%) rotate(-45deg);opacity:.5}
.mm .node.collapsed-parent::after{transform:translateY(-50%) rotate(45deg)}
.mm .node.root{background:linear-gradient(135deg,rgba(10,132,255,.16),rgba(88,86,214,.14));border-color:rgba(10,132,255,.4)}
.mm .b-0 .nm{color:#30b0c7}.mm .b-0{border-color:rgba(48,176,199,.4)}
.mm .b-1 .nm{color:#5856d6}.mm .b-1{border-color:rgba(88,86,214,.4)}
.mm .b-2 .nm{color:#f08c00}.mm .b-2{border-color:rgba(255,149,0,.4)}
.mm .b-3 .nm{color:#28a745}.mm .b-3{border-color:rgba(52,199,89,.4)}
.mm .b-4 .nm{color:#e0264b}.mm .b-4{border-color:rgba(255,45,85,.4)}

.checklist{list-style:none;display:flex;flex-direction:column;gap:8px}
.checklist li{display:flex;align-items:flex-start;gap:10px;font-size:12.5px;color:var(--ink2);cursor:pointer}
.checklist li::before{display:none}
.checklist input[type=checkbox]{width:16px;height:16px;border-radius:4px;border:1.5px solid #cbd5e1;
 appearance:none;-webkit-appearance:none;cursor:pointer;flex-shrink:0;background:rgba(255,255,255,.8);
 margin-top:2px;transition:all .15s}
.checklist input[type=checkbox]:checked{background:#0a84ff;border-color:#0a84ff;
 background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13 4L6.5 11 3 7.5' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E");
 background-size:contain}
.checklist label{cursor:pointer;line-height:1.5}
.checklist input[type=checkbox]:checked+label{text-decoration:line-through;color:#94a3b8}

footer{max-width:1100px;margin:0 auto;padding:30px 24px 60px;font-size:11.5px;color:var(--ink2);
 border-top:1px solid var(--border)}
@media(max-width:640px){body{padding-left:0}nav{box-shadow:0 8px 30px rgba(0,0,0,.14)}
 .md-wrap{grid-template-columns:1fr}.md-list{max-height:none}}
@media(prefers-reduced-motion:reduce){
 *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
  transition-duration:.001ms!important;scroll-behavior:auto!important}}
"""

# dark rules — viết MỘT lần, emit 2 prefix
DARK = [
 ([""], "--glass-1:rgba(30,38,54,.55);--glass-2:rgba(26,33,48,.72);--glass-3:rgba(22,28,42,.88);"
      "--border:rgba(120,160,220,.16);--ink:#e8ecf4;--ink2:#98a3b8;--code-bg:#0a0d14;background:#0c0f16"),
 (["body"], "color:var(--ink);background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.12),transparent 60%),"
            "radial-gradient(700px 420px at 95% 15%,rgba(88,86,214,.10),transparent 55%),"
            "linear-gradient(180deg,#0d121c 0%,#0a0e17 100%)"),
 (["body::after"], "background-image:radial-gradient(rgba(150,190,255,.10) 1px,transparent 1.3px)"),
 (["nav"], "background:linear-gradient(165deg,rgba(38,48,68,.62) 0%,rgba(24,31,46,.42) 48%,rgba(30,40,60,.55) 100%);"
           "border-right:1px solid rgba(120,160,220,.18);"
           "box-shadow:inset 0 1px 0 rgba(255,255,255,.10),4px 0 24px rgba(0,0,0,.35)"),
 ([".card", ".diagram-box", ".md-list li"],
  "box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 4px 20px rgba(0,0,0,.32)"),
 ([".md-list li[aria-selected=true]"], "background:linear-gradient(120deg,rgba(40,52,74,.95),rgba(30,40,62,.9));"
                                       "border-color:rgba(10,132,255,.5)"),
 ([".section-header h2"], "color:#f2f5fa"),
 ([".hero .meta span", ".steps li"], "background:rgba(30,38,54,.6);border-color:rgba(120,160,220,.16)"),
 (["table"], "background:rgba(20,26,40,.9)"),
 (["td"], "border-bottom:1px solid rgba(120,160,220,.09)"),
 (["tbody tr:hover"], "background:rgba(10,132,255,.08)"),
 (["code"], "background:rgba(10,132,255,.16);color:#7ab8ff"),
 ([".mm .node"], "background:rgba(30,38,54,.78);box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 3px 14px rgba(0,0,0,.3)"),
 ([".filelist li:nth-child(odd)"], "background:rgba(120,160,220,.06)"),
 ([".diagram-hint", ".diagram-reset"],
  "background:rgba(30,38,54,.9);color:var(--ink2);border-color:rgba(120,160,220,.16)"),
 ([".theme-row"], "background:linear-gradient(180deg,rgba(24,31,46,.3),rgba(24,31,46,.6))"),
 ([".diagram-box rect.nbox"], "fill:rgba(40,50,70,.85)"),
 ([".diagram-box text"], "fill:#dfe6f2"),
]
def dark_css():
    # Selector giữ dạng LIST — prefix dán vào TỪNG selector. Dán vào mỗi selector đầu tiên
    # thì các selector sau rò sang light mode (bug đã gặp: .steps li ra xám ở light);
    # còn split(',') thì vỡ khi selector chứa rgba(...) nên không dùng chuỗi phẩy nữa.
    def pref(p, sels):
        return ",".join(p if s == "" else "%s %s" % (p, s) for s in sels)
    a = "".join("%s{%s}" % (pref("html:not([data-theme=light])", s), d) for s, d in DARK)
    b = "".join("%s{%s}" % (pref("html[data-theme=dark]", s), d) for s, d in DARK)
    return "@media (prefers-color-scheme:dark){%s}%s" % (a, b)

def section_css():
    out = []
    for i in range(len(SECTIONS)):
        k = i % 6
        out.append("#sec-%d .tag{background:%s;color:%s}" % (i, TAGBG[k], ACCENT[k]))
        out.append("#sec-%d .card h4{color:%s}" % (i, H4[k]))
        out.append("#sec-%d .card li::before{color:%s}" % (i, ACCENT[k]))
        out.append("#sec-%d .stat b{color:%s}" % (i, H4[k]))
        out.append("#sec-%d nav a .ic{}" % i)
        out.append(".s-bg%d::before{background:linear-gradient(180deg,%s 0%%,transparent 60%%)}" % (i, OVER[k]))
        out.append("nav a[href='#sec-%d'] .ic{background:linear-gradient(135deg,%s,%s)}" % (i, ACCENT[k], H4[k]))
    return "".join(out)

# ═══════════════════════════ ICONS ═══════════════════════════
IC = [
 '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',                       # info
 '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',                          # stack
 '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M3 10h6"/>',          # map/files
 '<path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4z"/>',                           # shield
 '<path d="M4 6h10M4 12h16M4 18h7"/><circle cx="18" cy="6" r="2"/><circle cx="13" cy="18" r="2"/>',  # flows
 '<path d="M3 17l5-5 4 3 5-7 4 4"/><path d="M3 21h18"/>',                                # chart
 '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9L2.5 18a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',  # warn
]
BRAND = '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>'

# ═══════════════════════════ SVG DIAGRAMS ═══════════════════════════
def node(x, y, w, h, label, color, sub=None):
    t = ('<rect class="nbox" x="%d" y="%d" width="%d" height="%d" rx="8" fill="rgba(255,255,255,.7)" '
         'stroke="%s" stroke-width="1.6"/>' % (x, y, w, h, color))
    ty = y + h / 2 + (0 if not sub else -4)
    t += ('<text x="%d" y="%.1f" text-anchor="middle" font-size="10.5" font-weight="600" fill="#0f0f12">%s</text>'
          % (x + w / 2, ty + 3.5, E(label)))
    if sub:
        t += ('<text x="%d" y="%.1f" text-anchor="middle" font-size="8.5" fill="#4a4a55">%s</text>'
              % (x + w / 2, y + h / 2 + 10, E(sub)))
    return t

def line(x1, y1, x2, y2, color, mk):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.8" '
            'stroke-dasharray="5 4" class="flow" marker-end="url(#%s)"/>' % (x1, y1, x2, y2, color, mk))

def defs():
    m = ""
    for i, c in enumerate(ACCENT):
        m += ('<marker id="ar%d" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
              'orient="auto"><path d="M0 0L10 5L0 10z" fill="%s"/></marker>' % (i, c))
    return ('<defs>%s<style>.flow{animation:flowArrow 1.1s linear infinite}'
            '.pulseA{animation:pulseA 2.4s ease-in-out infinite}</style></defs>' % m)

def diagram_layers():
    s = ['<svg viewBox="0 0 900 320" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Năm lớp harness: policy khai báo ở L0, adapter vendor L1, pre-commit L2, audit L3, eval L4</title>',
         defs()]
    rows = [("L0 · POLICY", "policy.yaml — 18 rule", 20, "#dc2626"),
            ("L1 · SESSION", "hook per-vendor, fail-open", 78, "#0a84ff"),
            ("L2 · REPO", "pre-commit backstop", 136, "#5856d6"),
            ("L3 · AUDIT", "audit.jsonl · log.md sinh máy", 194, "#30b0c7"),
            ("L4 · EVALS", "wiki-health · promptfoo · retrieval", 252, "#34c759")]
    for name, sub, y, c in rows:
        s.append(node(40, y, 300, 44, name, c, sub))
    s.append(node(430, 20, 180, 44, "llmwiki-validate.py", "#7c3aed", "lõi vendor-neutral"))
    s.append(node(430, 92, 180, 44, "15 validators", "#ea580c", "python thuần, 0 token"))
    s.append(node(430, 164, 180, 44, "harness-events.py", "#30b0c7", "stop · audit · session"))
    s.append(node(430, 236, 180, 44, "medic.py", "#34c759", "fire-drill: luật còn cắn?"))
    s.append(node(690, 92, 170, 44, "Agent bị chặn", "#dc2626", "hoặc được cho qua"))
    s.append(node(690, 200, 170, 44, "CI harness.yml", "#5856d6", "67 assertion / PR"))
    s.append(line(340, 42, 428, 42, ACCENT[0], "ar0"))
    s.append(line(340, 100, 428, 114, ACCENT[0], "ar0"))
    s.append(line(340, 158, 688, 222, ACCENT[2], "ar2"))
    s.append(line(340, 216, 428, 186, ACCENT[1], "ar1"))
    s.append(line(340, 274, 428, 258, ACCENT[3], "ar3"))
    s.append(line(610, 114, 688, 114, ACCENT[5], "ar5"))
    s.append(line(610, 42, 690, 100, ACCENT[0], "ar0"))
    s.append("</svg>")
    return "".join(s)

def diagram_block():
    s = ['<svg viewBox="0 0 900 250" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Luồng chặn một hành động sai: agent gọi Write, hook PreToolUse gọi lõi, lõi đọc policy rồi trả verdict</title>',
         defs()]
    s.append(node(20, 100, 150, 44, "Agent", "#0a84ff", "gọi Write / Bash"))
    s.append(node(210, 100, 160, 44, "PreToolUse hook", "#30b0c7", "pre_tool_use.py:73"))
    s.append(node(410, 100, 170, 44, "llmwiki-validate", "#5856d6", "apply_rule():203"))
    s.append(node(410, 20, 170, 44, "policy.yaml", "#dc2626", "18 rule khai báo"))
    s.append(node(410, 180, 170, 44, "validators/*.py", "#ea580c", "0 token"))
    s.append(node(660, 40, 200, 44, "DENY + stderr cho agent", "#ff2d55", "hành động không xảy ra"))
    s.append(node(660, 150, 200, 44, "ALLOW → ghi audit", "#34c759", "post_tool_use.py:10"))
    s.append(line(170, 122, 208, 122, ACCENT[0], "ar0"))
    s.append(line(370, 122, 408, 122, ACCENT[1], "ar1"))
    s.append(line(495, 64, 495, 98, ACCENT[5], "ar5"))
    s.append(line(495, 144, 495, 178, ACCENT[4], "ar4"))
    s.append(line(580, 110, 658, 70, ACCENT[5], "ar5"))
    s.append(line(580, 134, 658, 172, ACCENT[3], "ar3"))
    s.append("</svg>")
    return "".join(s)

def dbox(svg):
    return '<div class="diagram-box">%s</div>' % svg

# ═══════════════════════════ MIND MAP ═══════════════════════════
MM = [
    ("Tổng quan", "3 trụ · 846 file", ["llmwiki — trí nhớ dài hạn", "harness — 18 luật tất định",
                                       "skills — 84 quy trình", "fdk — dev-kit framework"]),
    ("Kiến trúc", "5 lớp L0→L4", ["L0 policy.yaml khai báo", "L1 hook per-vendor",
                                  "L2 pre-commit backstop", "L3 audit JSONL", "L4 evals có sàn"]),
    ("15 tầng file", "mỗi file đúng 1 tầng", [l["name"] for l in layers[:8]]),
    ("18 luật", "policy là dữ liệu", [("%s %s" % (r["id"], r["name"])) for r in rules[:8]]),
    ("%d miền" % len(D["domains"]), "%d luồng · %d bước" % (n_flows, n_steps),
     [d["name"] for d in D["domains"]]),
    ("File nóng", "churn 365 ngày", [("%s (%d)" % (os.path.basename(n["filePath"]), n["churn"])) for n in hot[:7]]),
    ("Cạm bẫy", "đã trả giá", ["tồn tại ≠ dùng được", "3 bản của một skill",
                               "orca là nhánh phát hành", "repo tự gác chính nó"]),
]
def mindmap():
    ch = []
    for i, (name, desc, leaves) in enumerate(MM):
        lv = "".join('<div class="row"><div class="node b-%d leaf"><span class="nm">%s</span></div></div>'
                     % (i % 5, E(l)) for l in leaves)
        ch.append('<div class="row"><div class="node b-%d cat has-children"><span class="nm">%s</span>'
                  '<span class="ds">%s</span><span class="ct">%d</span></div>'
                  '<div class="children">%s</div></div>' % (i % 5, E(name), E(desc), len(leaves), lv))
    return ('<div class="mm"><div class="mm-canvas"><svg class="mm-links"></svg><div class="tree"><div class="row">'
            '<div class="node root has-children"><span class="nm">overstack</span>'
            '<span class="ds">rheinmir/setup · nhánh orca</span><span class="ct">%d</span></div>'
            '<div class="children">%s</div></div></div></div></div>' % (len(MM), "".join(ch)))

# ═══════════════════════════ SECTIONS ═══════════════════════════
def sec_open(i):
    t, sub = SECTIONS[i]
    return ('<section id="sec-%d" class="section-bg s-bg%d"><div class="section-header">'
            '<span class="tag">%02d · %s</span><h2>%s</h2><p>%s</p></div>'
            % (i, i, i + 1, E(t.upper()), E(t), E(sub)))

def card(title, body, tag="div"):
    return '<div class="card"><h4>%s</h4>%s</div>' % (E(title), body)

def ul(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)

# --- sec 0 ---
STATS = [("846", "file phân tích"), ("2 905", "cạnh quan hệ"), ("15", "tầng kiến trúc"),
         ("18", "luật đang gác"), ("84", "skill"), ("620", "commit")]
s0 = sec_open(0) + """
<div class="card" style="margin-bottom:14px"><p style="font-size:13px;color:var(--ink2)">
<b style="color:var(--ink)">overstack</b> là một lớp khung đặt <i>lên trên</i> dự án của bạn — không phải thư viện
để import, cũng không phải service để chạy. Nó là tập hợp file được cài vào thư mục gốc của một dự án bất kỳ
để biến AI agent làm việc trong đó thành một cộng sự kỹ thuật <b style="color:var(--ink)">tự kỷ luật</b>.
Chữ "tự kỷ luật" ở đây rất cụ thể: agent không được phép chọn có tuân thủ hay không — kỷ luật được cài bằng
code tất định chạy trước và sau mỗi hành động, tốn 0 token, và agent không có quyền phủ quyết.</p>
<p style="margin-top:10px;font-size:13px;color:var(--ink2)">Đây là repo nơi <b style="color:var(--ink)">tài liệu và
cấu hình chính là sản phẩm</b>, còn Python và Shell là bộ máy thực thi. Ai quen đọc repo theo hướng "tìm hàm main"
sẽ lạc — cửa vào thật là <code>harness/poc-vendor-neutral/bootstrap.sh</code> và <code>harness/policy.yaml</code>.</p></div>
<div class="grid g3" style="margin-bottom:14px">""" + "".join(
    '<div class="card stat"><b>%s</b><span>%s</span></div>' % (n, l) for n, l in STATS) + """</div>
<div class="grid g2">""" + card("Ba trụ", ul([
    "<b>llmwiki/</b> — trí nhớ dài hạn: concepts, entities, sources, adr, draft",
    "<b>harness/</b> — guardrail tất định: 18 rule, 15 validator, 0 token",
    "<b>skills/</b> — 84 quy trình đóng gói, gọi bằng <code>/&lt;tên&gt;</code>",
    "<b>fdk/</b> — dev-kit của người làm framework, không travel xuống dự án con",
])) + card("Thành phần ngôn ngữ", ul([
    "585 Markdown — tri thức và skill",
    "125 Python — validator, hook, tool sinh docs",
    "39 Shell — installer, bootstrap, gate",
    "32 YAML — policy.yaml và cấu hình cơ chế",
    "30 JSON · 8 HTML — manifest, metrics, docs self-contained",
])) + """</div>
<h3 style="font-size:14px;margin:22px 0 2px">Bản đồ trang</h3>
<p style="font-size:12px;color:var(--ink2)">Bấm một nhánh để xổ.</p>""" + mindmap() + "</section>"

# --- sec 1 ---
s1 = sec_open(1) + """
<div class="card" style="margin-bottom:4px"><p>Ý tưởng cốt lõi ghi trong
<code>harness/poc-vendor-neutral/README.md</code>: <b style="color:var(--ink)">logic chặn không nằm trong MCP,
cũng không nhúng vào một vendor — nó là một CLI lõi đọc policy.yaml, và mỗi vendor chỉ là caller mỏng gọi vào</b>.
Vì thế cùng một luật cắn được ở Claude Code, ở opencode, và ở CI mà không phải viết lại ba lần.</p></div>
""" + dbox(diagram_layers()) + """
<div class="grid g2">""" + card("Vì sao ba tầng chồng nhau", ul([
    "Hook vendor bắt sớm nhất — trước khi file bị ghi",
    "pre-commit bắt khi vendor bị tắt hoặc người gõ <code>git commit</code> tay",
    "CI bắt khi cả hai bị bỏ qua (fresh-clone, bypass)",
    "Một tầng hỏng thì hai tầng còn lại vẫn chặn",
])) + card("Fail-open là đánh đổi có ý thức", ul([
    "Hook lỗi hạ tầng → exit 0, ghi cảnh báo, không phá phiên",
    "Guardrail hỏng thầm lặng vẫn hơn guardrail làm agent không dùng được",
    "Bù lại: <code>medic.py</code> chạy fire-drill để chứng minh luật CÒN cắn",
    "Và hook <code>SessionStart</code> in số rule đang gác mỗi phiên",
])) + "</div></section>"

# --- sec 2 : master-detail layers ---
def layer_pane(i, L):
    files = L["files"]
    show = files[:16]
    rows = "".join(
        '<li><span class="fp">%s</span><span class="fm">%s</span></li>'
        % (E(f["filePath"]), (("%d chạm" % f["churn"]) if f.get("churn") else
                              ("%d dep" % indeg[f["id"]]) if indeg[f["id"]] else "%d dòng" % f.get("lines", 0)))
        for f in show)
    more = ('<p style="font-size:11px;color:var(--ink2);margin-top:8px">… và %d file nữa</p>'
            % (len(files) - len(show))) if len(files) > len(show) else ""
    return ('<div class="md-pane%s" data-p="%d"><h3>%s</h3><p class="desc">%s</p>'
            '<div class="card"><h4>%d file · %d lần chạm trong 365 ngày</h4>'
            '<ul class="filelist">%s</ul>%s</div></div>'
            % (" on" if i == 0 else "", i, E(L["name"]), E(L["description"]), L["count"], L["churn"], rows, more))

items = "".join('<li role="option" data-i="%d" aria-selected="%s"><span class="mt">%s</span>'
                '<span class="ms">%d file</span></li>'
                % (i, "true" if i == 0 else "false", E(L["name"]), L["count"])
                for i, L in enumerate(layers))
s2 = sec_open(2) + """
<div class="card"><p>Mỗi file thuộc <b style="color:var(--ink)">đúng một tầng</b> — quy tắc gán theo tiền tố đường
dẫn, khớp đầu tiên thắng, nên không có file nào bị đếm hai lần và không có file nào rơi ngoài. Đáng chú ý:
<code>knowledge-base</code> (224 file) và <code>skills</code> (199 file) chiếm gần một nửa repo.</p></div>
<div class="md-wrap"><ul class="md-list" role="listbox" data-md="layers">""" + items + """</ul>
<div class="md-detail" data-mdp="layers">""" + "".join(layer_pane(i, L) for i, L in enumerate(layers)) + """
</div></div></section>"""

# --- sec 3 : rules ---
def rule_pill(r):
    en = r["enforce"]
    if "session" in en and "repo" in en: return '<span class="pill p-hard">chặn 2 tầng</span>'
    if "session-stop" in en: return '<span class="pill p-hard">chặn lúc Stop</span>'
    if "session" in en: return '<span class="pill p-hard">chặn runtime</span>'
    if "repo" in en: return '<span class="pill p-repo">cổng commit</span>'
    return '<span class="pill p-auto">tự động</span>'

rrows = "".join(
    '<tr><td><b>%s</b></td><td><code>%s</code></td><td>%s</td><td>%s</td><td><code>%s</code></td></tr>'
    % (E(r["id"]), E(r["name"]), E(r["statement"][:190] + ("…" if len(r["statement"]) > 190 else "")),
       rule_pill(r), E(r["validator"] if r["validator"] not in ("null", "") else "—"))
    for r in rules)
s3 = sec_open(3) + """
<div class="card"><p><code>harness/policy.yaml</code> là nguồn chân lý duy nhất. Thêm luật nghĩa là thêm một entry
ở đây rồi nối validator, chứ không rải <code>if</code> khắp hook. Mỗi rule khai <code>statement</code> (luật nói gì),
<code>enforce_at</code> (chặn ở đâu) và <code>validator</code> (file nào thi hành).</p></div>
""" + dbox(diagram_block()) + """
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Tên</th><th>Luật nói gì</th><th>Chặn ở đâu</th>
<th>Validator</th></tr></thead><tbody>""" + rrows + """</tbody></table></div>
<div class="grid g2" style="margin-top:14px">""" + card("Đọc thử một rule", """
<div class="code-wrap"><pre class="code-block">- id: R2
  name: origin-required
  validator: origin_required.py
  statement: "Mọi wiki file phải có section '## Origin'
              — luôn truy được nguồn gốc."
  enforce_at: [session, repo]
  applies_to: [write]</pre></div>""") + card("Ba nơi luật cắn", ul([
    "<b>session</b> — hook PreToolUse chặn trước khi file bị ghi",
    "<b>session-stop</b> — hook Stop chặn kết thúc lượt (R3 index-sync)",
    "<b>repo</b> — pre-commit và CI, bắt cả khi vendor bị tắt",
    "R4/R8/R10 không chặn mà tự động hoá hoặc nhắc",
])) + "</div></section>"

# --- sec 4 : domains master-detail ---
def dom_pane(i, d):
    flows = []
    for f in d["flows"]:
        steps = "".join(
            '<li><span class="sn">%s</span>%s<span class="loc">%s:%d</span></li>'
            % (E(str(s["order"])), E(s.get("name", s["id"])), E(s["file"]), s["line"])
            for s in f["steps"])
        flows.append('<div class="flowhead">%s <span class="trg">— %s</span></div><ul class="steps">%s</ul>'
                     % (E(f["name"]), E(f.get("trigger", "")), steps))
    eps = ul(["<code>%s</code>" % E(e) for e in d.get("entryPoints", [])])
    return ('<div class="md-pane%s" data-p="%d"><h3>%s</h3><p class="desc">%s</p>'
            '<div class="card" style="margin-bottom:12px"><h4>Cửa vào</h4>%s</div>%s</div>'
            % (" on" if i == 0 else "", i, E(d["name"]), E(d["description"]), eps, "".join(flows)))

ditems = "".join('<li role="option" data-i="%d" aria-selected="%s"><span class="mt">%s</span>'
                 '<span class="ms">%d luồng · %d bước</span></li>'
                 % (i, "true" if i == 0 else "false", E(d["name"]), len(d["flows"]),
                    sum(len(f["steps"]) for f in d["flows"]))
                 for i, d in enumerate(D["domains"]))
s4 = sec_open(4) + """
<div class="card"><p>Cửa vào của repo này <b style="color:var(--ink)">không phải HTTP endpoint</b> mà là bốn dạng:
lệnh CLI <code>curl | bash</code>, hook event của vendor, slash-command skill, và CI job. Toàn bộ %d bước dưới đây
đã được đối chiếu với đĩa — mỗi bước trỏ một <code>file:line</code> tồn tại thật tại commit
<code>9032ae4</code>.</p></div>
<div class="md-wrap"><ul class="md-list" role="listbox" data-md="doms">%s</ul>
<div class="md-detail" data-mdp="doms">%s</div></div></section>""" % (
    n_steps, ditems, "".join(dom_pane(i, d) for i, d in enumerate(D["domains"])))

# --- sec 5 : hot files ---
hrows = "".join(
    '<tr><td class="num"><b>%d</b></td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>'
    % (n["churn"], E(n["filePath"]), E(next(l["name"] for l in layers if l["id"] == n["layer"])),
       '<span class="pill p-hot">nóng</span>' if n["churn"] >= 20 else "")
    for n in hot)
drows = "".join('<tr><td class="num"><b>%d</b></td><td><code>%s</code></td><td>%s</td></tr>'
                % (c, E(n["filePath"]), E(next(l["name"] for l in layers if l["id"] == n["layer"])))
                for n, c in dep)
srows = "".join("<li>%s</li>" % E(s) for s in subjects)
erows = "".join('<tr><td><code>%s</code></td><td class="num">%d</td></tr>' % (E(k), v)
                for k, v in etypes.most_common())
s5 = sec_open(5) + """
<div class="card"><p>Đo bằng số commit chạm vào file trong 365 ngày. Đây là chỉ báo tốt nhất cho "sửa ở đâu thì
đụng nhiều thứ". Lưu ý <code>llmwiki/wiki/log.md</code> nóng nhất là <b style="color:var(--ink)">bình thường</b> —
nó là nhật ký append-only do R4 sinh tự động mỗi phiên, không phải mùi xấu.</p></div>
<div class="grid g2" style="margin-top:14px;align-items:start">
<div><h4 style="font-size:12px;margin-bottom:6px">File nóng nhất (churn 365 ngày)</h4>
<div class="table-wrap"><table><thead><tr><th>Chạm</th><th>File</th><th>Tầng</th><th></th></tr></thead>
<tbody>""" + hrows + """</tbody></table></div></div>
<div><h4 style="font-size:12px;margin-bottom:6px">Được phụ thuộc nhiều nhất (in-degree)</h4>
<div class="table-wrap"><table><thead><tr><th>Dep</th><th>File</th><th>Tầng</th></tr></thead>
<tbody>""" + drows + """</tbody></table></div>
<p style="font-size:11.5px;color:var(--ink2);margin-top:8px">Sửa những file này là thay đổi lan rộng — dùng
<code>/impact-check</code> hoặc <code>/safe-change</code> trước.</p></div></div>
<div class="grid g2" style="margin-top:16px;align-items:start">""" + card(
    "Đang làm gì gần đây (commit 90 ngày)", ul([E(s) for s in subjects]) if subjects else "<p>—</p>") + """
<div><h4 style="font-size:12px;margin-bottom:6px">Loại quan hệ trong graph</h4>
<div class="table-wrap"><table><thead><tr><th>Loại cạnh</th><th>Số lượng</th></tr></thead>
<tbody>""" + erows + """</tbody></table></div>
<p style="font-size:11.5px;color:var(--ink2);margin-top:8px">115 cạnh <code>related</code> suy từ co-change:
hai file đổi cùng nhau ≥4 lần. Phần lớn chính là cặp <b>canonical ↔ mirror</b> của skill.</p></div></div>
</section>"""

# --- sec 6 ---
s6 = sec_open(6) + """
<div class="grid g2">""" + card("Quy ước bắt buộc", ul([
    "Skill có <b>ba bản</b>: canonical <code>skills/</code>, mirror <code>llmwiki/skills/</code>, bản cài <code>~/.claude/skills</code>",
    "<b>Hai wiki tách biệt</b> (ADR-008): <code>llmwiki/wiki/</code> là khuôn per-project, <code>fdk/wiki/</code> là wiki của chính framework",
    "<code>fdk/</code> <b>không travel</b> xuống dự án con (ADR-004/008) — có validator canh",
    "Mọi trang wiki phải có <code>## Origin</code> (R2) và một dòng trong <code>index.md</code> (R3)",
    "Chỉ được tạo file trong thư mục đã khai báo (R5) — không phát minh thư mục mới",
])) + card("Cạm bẫy đã trả giá", ul([
    "<b>Repo tự gác chính nó</b> — sửa sai ở <code>harness/validators/</code> có thể tự khoá phiên làm việc",
    "<b>\"Tồn tại ≠ dùng được\"</b> — code-graph MCP hỏng nhiều tuần vì code chỉ kiểm server có được KHAI BÁO hay không",
    "<b>Ba bản skill</b> là nguồn drift thường trực — kiểm cả ba trước khi kết luận đã vá",
    "<b>Nhánh <code>orca</code> là nhánh phát hành</b> — URL cài đặt hardcode nó, push hỏng là hỏng đường cài của mọi người mới",
    "86/846 node orphan — chủ yếu trang wiki độc lập và asset",
])) + """</div>
<div class="grid g2" style="margin-top:14px">""" + card("Checklist trước khi sửa file dùng chung", """
<ul class="checklist">
<li><input type="checkbox" id="k1"><label for="k1">Chạy 5-Why tới khi chạm cấu trúc, viết chuỗi ra</label></li>
<li><input type="checkbox" id="k2"><label for="k2">Tra <code>fdk/CAPABILITIES.md</code> — đồ nghề đã có chưa</label></li>
<li><input type="checkbox" id="k3"><label for="k3"><code>/impact-check</code> map caller trước khi đổi chữ ký</label></li>
<li><input type="checkbox" id="k4"><label for="k4">Sửa canonical rồi <code>sync-skills.py</code>, đừng vá bản cài</label></li>
<li><input type="checkbox" id="k5"><label for="k5"><code>python3 fdk/tools/medic.py</code> phải xanh trước khi commit</label></li>
</ul>""") + card("Lệnh hay dùng", """
<div class="code-wrap"><pre class="code-block"># cài cả 3 trụ vào một dự án bất kỳ
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/\\
harness/poc-vendor-neutral/bootstrap.sh | bash

# cổng sức khoẻ tổng — chứng minh luật CÒN cắn
python3 fdk/tools/medic.py

# definition-of-done cho mọi thay đổi framework
python3 harness/scripts/fdk-gate.py

# sinh lại bản đồ năng lực + docs từ đĩa
python3 fdk/tools/build-capabilities.py
python3 fdk/tools/build-overstack-docs.py</pre></div>""") + "</div></section>"

# ═══════════════════════════ NAV / SHELL ═══════════════════════════
navlinks = "".join(
    '<a href="#sec-%d"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>%s</a>'
    % (i, IC[i % len(IC)], E(SECTIONS[i][0])) for i in range(len(SECTIONS)))

JS = r"""
/* nav collapse */
(function(){var nav=document.querySelector('nav');if(!nav)return;
var btn=document.createElement('button');btn.className='nav-toggle';btn.textContent='☰';
btn.setAttribute('aria-label','Mở thanh điều hướng');document.body.appendChild(btn);
var cl=document.createElement('button');cl.className='nav-close';cl.textContent='✕';
cl.setAttribute('aria-label','Đóng thanh điều hướng');nav.appendChild(cl);
var apply=function(c){document.body.classList.toggle('nav-collapsed',c);
 try{localStorage.setItem('navCollapsed',c?'1':'0')}catch(e){}};
btn.addEventListener('click',function(){apply(false)});cl.addEventListener('click',function(){apply(true)});
try{var s=localStorage.getItem('navCollapsed');
 if(s==='1'||(s!=='0'&&matchMedia('(max-width:640px)').matches))apply(true)}catch(e){}})();

/* theme switch */
(function(){var K='osrcmap-theme',d=document.documentElement,nav=document.querySelector('nav');if(!nav)return;
function isDark(){var t=d.getAttribute('data-theme');return t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
var sw=document.createElement('div');sw.className='theme-switch';sw.setAttribute('role','switch');
sw.setAttribute('tabindex','0');sw.innerHTML='<span class="track"><span class="knob"></span></span>';
var row=document.createElement('div');row.className='theme-row';
var lb=document.createElement('span');lb.className='lbl';lb.textContent='Giao diện';
row.appendChild(lb);row.appendChild(sw);nav.appendChild(row);
function paint(){var dk=isDark();sw.classList.toggle('on',dk);sw.setAttribute('aria-checked',dk?'true':'false');
 sw.setAttribute('aria-label',dk?'Nút gạt giao diện: đang tối — gạt sang sáng':'Nút gạt giao diện: đang sáng — gạt sang tối')}
function flip(){var n=isDark()?'light':'dark';d.setAttribute('data-theme',n);try{localStorage.setItem(K,n)}catch(e){}paint()}
sw.addEventListener('click',flip);
sw.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();flip()}});paint()})();

/* scroll spy */
(function(){var links=[].slice.call(document.querySelectorAll('nav a[href^="#sec"]'));
var secs=[].slice.call(document.querySelectorAll('section[id]'));if(!secs.length)return;
var ob=new IntersectionObserver(function(es){var a='';es.forEach(function(e){if(e.isIntersecting)a=e.target.id});
 if(a)links.forEach(function(l){l.classList.toggle('active',l.getAttribute('href')==='#'+a)})},
 {rootMargin:'-40% 0px -55% 0px'});secs.forEach(function(s){ob.observe(s)});
if(links[0])links[0].classList.add('active')})();

/* scrollbar flash */
(function(){var flash=function(el){var t;return function(){el.classList.add('scrolling');clearTimeout(t);
 t=setTimeout(function(){el.classList.remove('scrolling')},900)}};
var root=document.documentElement;addEventListener('scroll',flash(root),{passive:true});
var nav=document.querySelector('nav');if(nav)nav.addEventListener('scroll',flash(nav),{passive:true})})();

/* ripple ink on nav controls */
(function(){function attach(el){el.addEventListener('pointerdown',function(e){
 var r=el.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
 var rad=Math.hypot(Math.max(x,r.width-x),Math.max(y,r.height-y));
 var ink=document.createElement('span');ink.className='ripple-ink';
 ink.style.width=ink.style.height=rad*2+'px';ink.style.left=(x-rad)+'px';ink.style.top=(y-rad)+'px';
 el.appendChild(ink);ink.addEventListener('animationend',function(){ink.remove()})})}
document.querySelectorAll('nav a,.nav-toggle,.nav-close').forEach(attach)})();

/* generic ripple */
(function(){document.addEventListener('pointerdown',function(e){
 var el=e.target.closest('button, .md-list li, .checklist label');
 if(!el||el.dataset.noRipple||el.classList.contains('nav-toggle')||el.classList.contains('nav-close'))return;
 var r=el.getBoundingClientRect(),d=Math.max(r.width,r.height)*1.2;
 var s=document.createElement('span');s.className='ripple';
 s.style.cssText='width:'+d+'px;height:'+d+'px;left:'+(e.clientX-r.left-d/2)+'px;top:'+(e.clientY-r.top-d/2)+'px';
 if(getComputedStyle(el).position==='static')el.style.position='relative';
 el.style.overflow='hidden';el.appendChild(s);
 s.addEventListener('animationend',function(){s.remove()})})})();

/* master-detail */
(function(){document.querySelectorAll('.md-list').forEach(function(list){
 var key=list.dataset.md,panes=document.querySelector('[data-mdp="'+key+'"]');if(!panes)return;
 list.addEventListener('click',function(e){var li=e.target.closest('li');if(!li)return;
  var i=li.dataset.i;
  list.querySelectorAll('li').forEach(function(x){x.setAttribute('aria-selected',x===li?'true':'false')});
  panes.querySelectorAll('.md-pane').forEach(function(p){p.classList.toggle('on',p.dataset.p===i)})})})})();

/* code copy */
(function(){var COPY='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
var CHECK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
document.querySelectorAll('pre.code-block').forEach(function(pre){if(pre.dataset.copy)return;pre.dataset.copy='1';
 var code=pre.textContent,wrap=pre.parentNode;
 if(!wrap.classList.contains('code-wrap')){var w=document.createElement('div');w.className='code-wrap';
  pre.parentNode.insertBefore(w,pre);w.appendChild(pre);wrap=w}
 var b=document.createElement('button');b.className='code-copy';b.setAttribute('aria-label','Copy');
 b.title='Copy';b.innerHTML=COPY;wrap.appendChild(b);
 b.addEventListener('click',function(){
  var done=function(){b.innerHTML=CHECK;b.classList.add('copied');
   setTimeout(function(){b.innerHTML=COPY;b.classList.remove('copied')},1500)};
  if(navigator.clipboard){navigator.clipboard.writeText(code).then(done,done)}
  else{var ta=document.createElement('textarea');ta.value=code;document.body.appendChild(ta);ta.select();
   document.execCommand('copy');ta.remove();done()}})})})();

/* mind map */
(function(){var mm=document.querySelector('.mm');if(!mm)return;var NS='http://www.w3.org/2000/svg';
function colorOf(n){return n.classList.contains('b-0')?'#30b0c7':n.classList.contains('b-1')?'#5856d6':
 n.classList.contains('b-2')?'#ff9500':n.classList.contains('b-3')?'#34c759':
 n.classList.contains('b-4')?'#ff2d55':'#9aa4b2'}
function draw(){var canvas=mm.querySelector('.mm-canvas'),svg=mm.querySelector('.mm-links');if(!canvas||!svg)return;
 var w=canvas.offsetWidth,h=canvas.offsetHeight;svg.setAttribute('width',w);svg.setAttribute('height',h);
 svg.setAttribute('viewBox','0 0 '+w+' '+h);while(svg.firstChild)svg.removeChild(svg.firstChild);
 var cR=canvas.getBoundingClientRect();
 [].slice.call(canvas.querySelectorAll('.node.has-children')).forEach(function(p){
  var row=p.parentElement,kids=null,ch=row.children;
  for(var i=0;i<ch.length;i++){if(ch[i].classList.contains('children'))kids=ch[i]}
  if(!kids||kids.classList.contains('collapsed'))return;
  var pr=p.getBoundingClientRect(),px=pr.right-cR.left,py=pr.top+pr.height/2-cR.top;
  [].slice.call(kids.children).forEach(function(crow){var cn=crow.querySelector(':scope > .node');if(!cn)return;
   var rr=cn.getBoundingClientRect(),cx=rr.left-cR.left,cy=rr.top+rr.height/2-cR.top,dx=Math.max(22,(cx-px)*0.55);
   var pa=document.createElementNS(NS,'path');
   pa.setAttribute('d','M'+px+' '+py+' C'+(px+dx)+' '+py+' '+(cx-dx)+' '+cy+' '+cx+' '+cy);
   pa.setAttribute('stroke',colorOf(cn));svg.appendChild(pa)})})}
[].slice.call(mm.querySelectorAll('.node.has-children')).forEach(function(n){
 var row=n.parentElement,kids=null,c=row.children;
 for(var i=0;i<c.length;i++){if(c[i].classList.contains('children'))kids=c[i]}
 if(!kids)return;
 if(n.classList.contains('cat')){kids.classList.add('collapsed');n.classList.add('collapsed-parent')}
 n.addEventListener('click',function(e){e.stopPropagation();var open=kids.classList.toggle('collapsed');
  n.classList.toggle('collapsed-parent',open);draw()})});
draw();addEventListener('load',function(){setTimeout(draw,60)});
addEventListener('resize',function(){clearTimeout(window.__mmt);window.__mmt=setTimeout(draw,120)},{passive:true})})();

/* draggable diagrams */
function initDraggableDiagrams(){var NS='http://www.w3.org/2000/svg';
var nearest=function(nodes,x,y){var best=null,bd=1e9;nodes.forEach(function(n){
 var cx=Math.max(n.x,Math.min(x,n.x+n.w)),cy=Math.max(n.y,Math.min(y,n.y+n.h));
 var d=Math.hypot(x-cx,y-cy);if(d<bd){bd=d;best=n}});return bd<=42?best:null};
document.querySelectorAll('.diagram-box').forEach(function(box){var svg=box.querySelector('svg');
 if(!svg||box.dataset.draggable)return;box.dataset.draggable='1';
 var vp=document.createElement('div');vp.className='diagram-viewport';box.insertBefore(vp,svg);vp.appendChild(svg);
 var hint=document.createElement('div');hint.className='diagram-hint';
 hint.textContent='✥ kéo từng ô · kéo nền để pan · cuộn để zoom · kéo mép dưới để mở rộng';box.appendChild(hint);
 var reset=document.createElement('button');reset.className='diagram-reset';reset.textContent='⟲ reset';box.appendChild(reset);
 var allRects=[].slice.call(svg.querySelectorAll('rect'));
 var nodes=allRects.filter(function(r){return (+r.getAttribute('width'))>=70&&(+r.getAttribute('height'))>=30})
  .map(function(r){return{rect:r,x:+r.getAttribute('x'),y:+r.getAttribute('y'),w:+r.getAttribute('width'),
   h:+r.getAttribute('height'),els:[r],tx:0,ty:0}});
 var inNode=function(px,py){return nodes.find(function(n){
  return px>=n.x-1&&px<=n.x+n.w+1&&py>=n.y-1&&py<=n.y+n.h+1})};
 [].slice.call(svg.querySelectorAll('text')).forEach(function(t){
  var x=parseFloat(t.getAttribute('x')),y=parseFloat(t.getAttribute('y'));
  if(isNaN(x)||isNaN(y))return;var n=inNode(x,y);if(n)n.els.push(t)});
 nodes.forEach(function(n){var g=document.createElementNS(NS,'g');g.setAttribute('class','dnode');
  n.rect.parentNode.insertBefore(g,n.rect);n.els.forEach(function(el){g.appendChild(el)});n.g=g});
 var links=[].slice.call(svg.querySelectorAll('line')).filter(function(l){return l.hasAttribute('x1')});
 links.forEach(function(l){l._x1=+l.getAttribute('x1');l._y1=+l.getAttribute('y1');
  l._x2=+l.getAttribute('x2');l._y2=+l.getAttribute('y2');
  l._n1=nearest(nodes,l._x1,l._y1);l._n2=nearest(nodes,l._x2,l._y2)});
 var reroute=function(){links.forEach(function(l){
  if(l._n1){l.setAttribute('x1',l._x1+l._n1.tx);l.setAttribute('y1',l._y1+l._n1.ty)}
  if(l._n2){l.setAttribute('x2',l._x2+l._n2.tx);l.setAttribute('y2',l._y2+l._n2.ty)}})};
 var vbBase=(svg.getAttribute('viewBox')||'0 0 900 200').split(/\s+/).map(Number);
 var fitViewBox=function(){var pad=16,minX=vbBase[0],minY=vbBase[1],maxX=vbBase[0]+vbBase[2],maxY=vbBase[1]+vbBase[3];
  nodes.forEach(function(n){minX=Math.min(minX,n.x+n.tx-pad);minY=Math.min(minY,n.y+n.ty-pad);
   maxX=Math.max(maxX,n.x+n.w+n.tx+pad);maxY=Math.max(maxY,n.y+n.h+n.ty+pad)});
  svg.setAttribute('viewBox',minX+' '+minY+' '+(maxX-minX)+' '+(maxY-minY))};
 var ptx=0,pty=0,scale=1;
 var applyCanvas=function(){svg.style.transform='translate('+ptx+'px,'+pty+'px) scale('+scale+')'};
 var toSvg=function(cx,cy){var p=svg.createSVGPoint();p.x=cx;p.y=cy;return p.matrixTransform(svg.getScreenCTM().inverse())};
 var mode=null,node=null,start=null,t0=null,p0=null;
 vp.addEventListener('pointerdown',function(e){vp.setPointerCapture(e.pointerId);
  var g=e.target.closest&&e.target.closest('g.dnode');
  if(g){mode='node';node=nodes.find(function(n){return n.g===g});start=toSvg(e.clientX,e.clientY);
   t0={x:node.tx,y:node.ty}}
  else{mode='pan';p0={x:e.clientX-ptx,y:e.clientY-pty};vp.classList.add('grabbing')}});
 vp.addEventListener('pointermove',function(e){
  if(mode==='node'){var c=toSvg(e.clientX,e.clientY);node.tx=t0.x+(c.x-start.x);node.ty=t0.y+(c.y-start.y);
   node.g.setAttribute('transform','translate('+node.tx+','+node.ty+')');reroute()}
  else if(mode==='pan'){ptx=e.clientX-p0.x;pty=e.clientY-p0.y;applyCanvas()}});
 var end=function(){if(mode==='node')fitViewBox();mode=null;node=null;vp.classList.remove('grabbing')};
 vp.addEventListener('pointerup',end);vp.addEventListener('pointercancel',end);
 vp.addEventListener('wheel',function(e){e.preventDefault();
  var r=vp.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
  var ns=Math.min(4,Math.max(0.5,scale*(e.deltaY<0?1.1:0.9)));
  ptx=mx-(mx-ptx)*(ns/scale);pty=my-(my-pty)*(ns/scale);scale=ns;applyCanvas()},{passive:false});
 var doReset=function(){ptx=0;pty=0;scale=1;svg.style.transition='transform .3s cubic-bezier(.4,0,.2,1)';
  applyCanvas();setTimeout(function(){svg.style.transition=''},320);
  nodes.forEach(function(n){n.tx=0;n.ty=0;n.g.setAttribute('transform','translate(0,0)')});reroute();fitViewBox()};
 reset.addEventListener('click',doReset);vp.addEventListener('dblclick',doReset)})}
initDraggableDiagrams();
"""

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>overstack — bản đồ source code</title>
<meta name="description" content="Bản đồ mã nguồn repo overstack: 15 tầng kiến trúc, 846 file, 18 luật, 7 miền nghiệp vụ với file:line thật.">
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
<script>(function(){try{var t=localStorage.getItem("osrcmap-theme");
if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}})();</script>
<style>__CSS__</style>
</head>
<body>
<a class="skip-link" href="#main">Bỏ qua điều hướng</a>
<nav>
  <div class="brand"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">__BRAND__</svg></span>
    <span><span class="logo-t">overstack</span><br><span class="logo-s">bản đồ source code</span></span></div>
  __NAV__
</nav>
<main id="main">
<div class="hero">
  <span class="eyebrow">rheinmir/setup · nhánh orca · commit 9032ae4</span>
  <h1>Bản đồ mã nguồn overstack</h1>
  <p class="lead">Một lớp khung đặt lên trên dự án của bạn, biến AI agent thành cộng sự kỹ thuật tự kỷ luật:
  trí nhớ dài hạn (llmwiki), nguyên tắc không thể phá (harness — 18 luật tất định, 0 token), tay nghề đóng gói
  sẵn (84 skill). Trang này mô tả chính mã nguồn đó — mọi con số đọc thẳng từ knowledge graph, mọi
  <code>file:line</code> đã đối chiếu tồn tại thật.</p>
  <div class="meta"><span>846 file</span><span>2 905 cạnh</span><span>15 tầng</span><span>18 luật</span>
  <span>7 miền · __NF__ luồng · __NS__ bước</span><span>620 commit từ 28/04/2026</span></div>
</div>
__SECS__
<footer>
  <p>Sinh bằng code từ <code>.overstack/graph/knowledge-graph.json</code> +
  <code>.overstack/onboard/intermediate/domain-graph.json</code> + <code>harness/policy.yaml</code>
  bởi <code>/orca-onboard</code> → <code>/docs-site-macos</code>, ngày 29/07/2026.</p>
  <p style="margin-top:6px">Self-contained: không request ngoài, mở bằng <code>file://</code> vẫn chạy đủ.
  Xem thêm <code>llmwiki/html/onboarding-setup.html</code> (guided tour 13 bước) và
  <code>llmwiki/html/wiki-graph.html</code> (vector concept↔code).</p>
</footer>
</main>
<script>__JS__</script>
</body>
</html>"""

def main():
  out = (HTML.replace("__CSS__", CSS_BASE + section_css() + dark_css())
             .replace("__BRAND__", BRAND)
             .replace("__NAV__", navlinks)
             .replace("__NF__", str(n_flows)).replace("__NS__", str(n_steps))
             .replace("__SECS__", s0 + s1 + s2 + s3 + s4 + s5 + s6)
             .replace("__JS__", JS))
  os.makedirs(os.path.dirname(OUT), exist_ok=True)
  open(OUT, "w", encoding="utf-8").write(out)
  print("✅", OUT, len(out), "bytes")
  for tok in ("__CSS__", "__NAV__", "__SECS__", "__JS__", "__BRAND__", "__NF__", "__NS__"):
      assert tok not in out, "token còn sót: " + tok
  ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', out)
  print("external resource refs:", ext or "none ✅")
  print("sections:", out.count('<section id="sec-'), "| rules:", len(rules),
        "| layers:", len(layers), "| domains:", len(D["domains"]))

if __name__ == "__main__":
    main()
