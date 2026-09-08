#!/usr/bin/env python3
"""Sinh llmwiki/html/290726-pdf-gap-overstack.html — overstack còn thiếu gì theo PDF
"Graph Engineering: The Karpathy Loop, Improved 1000x by Itself — The Anthropic Playbook" (11 trang).
Tái dùng design shell của build_source_map.py."""
import os, re, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "."]
import build_source_map as S

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.join(ROOT, "llmwiki/html/290726-pdf-gap-overstack.html")
E = html.escape

V = {
    "full": ("✅", "Có đủ", "#28a745", "v-full"),
    "part": ("🟡", "Một phần", "#c26a00", "v-part"),
    "gap":  ("🔴", "Thiếu", "#e0264b", "v-gap"),
    "na":   ("—", "Không áp", "#5856d6", "v-diff"),
}
def badge(k):
    ic, lb, _, cls = V[k]
    return '<span class="vb %s">%s %s</span>' % (cls, ic, E(lb))

SECTIONS = [
    ("Tóm tắt", "PDF nói gì, overstack đứng đâu"),
    ("Năm cơ chế", "Mỗi kiến trúc externalize một bottleneck"),
    ("Bốn gốc thiếu", "Bằng chứng file thật, không suy đoán"),
    ("Runtime-graph", "TABLE I — graph trong từng workflow pattern"),
    ("Checklist sản xuất", "TABLE VI + 14 bước chuẩn"),
    ("World model", "Mặt overstack mạnh nhất theo PDF"),
    ("Build path & phanh", "Đứng đâu trên timeline, khi nào ĐỪNG"),
]

# ── S1: năm cơ chế ───────────────────────────────────────────────────────────
MECHS = [
    ("Loop", "iteration + evaluation", "part",
     "<code>harness/scripts/loop-runner.py</code> — đủ guard tất định (max_iter, wall-clock, no-progress "
     "state-hash, escalate) + reflexion. Nhưng VERIFY là exit-code pass/fail, KHÔNG phải metric cải thiện — "
     "chưa phải ratchet."),
    ("Chain", "task order", "full",
     "<code>/propose → /plan → dispatch → /verify-before-commit</code> — chuỗi cố định, cổng người ở giữa, "
     "R7/R18 gác chất lượng từng khâu."),
    ("Swarm", "parallel search + role specialization", "part",
     "Orca dispatch song song + <code>council.py</code> (3 giai đoạn Karpathy, ẩn danh + anchor-guard). "
     "Nhưng primitive spawn/gather mượn runtime vendor, không sở hữu."),
    ("DAG", "experiment lineage", "gap",
     "git một nhánh <code>orca</code> tuyến tính + <code>provenance-log.py</code> (hash-chain sự kiện). "
     "Không có <code>children / leaves / lineage / diff</code> — không giữ nhiều nhánh thí nghiệm sống."),
    ("Knowledge graph", "shared facts + provenance + cross-session memory", "part",
     "wiki + <code>wiki-graph.py</code> (2 chiều, 0 token) + <code>build-wiki-graph.py</code> (thêm node code). "
     "Là DOCS-graph: phục vụ xem/lint, không workflow nào đọc-ghi lúc chạy."),
]

def diagram_progression():
    s = ['<svg viewBox="0 0 900 210" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Tiến trình PDF: vibe coding sang agentic engineering sang graph engineering; overstack đứng ở '
         'agentic engineering đã chín, graph engineering mới chớm</title>', S.defs()]
    s.append(S.node(20, 30, 190, 52, "1 · Vibe coding", "#9aa4b2", "người nói ý, model viết"))
    s.append(S.node(280, 30, 240, 52, "2 · Agentic engineering", "#0a84ff", "người spec + orchestrate + verify"))
    s.append(S.node(590, 30, 290, 52, "3 · Graph engineering", "#5856d6", "agent chia state qua graph typed"))
    s.append(S.line(210, 56, 278, 56, "#0a84ff", "ar0"))
    s.append(S.line(520, 56, 588, 56, "#5856d6", "ar2"))
    s.append(S.node(280, 130, 240, 46, "overstack Ở ĐÂY", "#34c759", "propose·gate·dispatch·harness"))
    s.append(S.node(590, 130, 290, 46, "mới chớm", "#ff9500", "wiki-graph docs-only, chưa runtime"))
    s.append(S.line(400, 128, 400, 84, "#34c759", "ar3"))
    s.append(S.line(735, 128, 735, 84, "#ff9500", "ar4"))
    s.append("</svg>")
    return "".join(s)

# ── S2: bốn gốc ──────────────────────────────────────────────────────────────
ROOTS = [
    ("Gốc 1 — Ratchet theo điểm số", "§II ratchet_loop",
     "PDF cho pseudocode nguyên vẹn: <code>score = evaluate()</code> → <code>if better(score, current): "
     "keep(commit)</code> else <code>revert(commit)</code>, mỗi vòng ghi một <code>Trial(commit, change, score, "
     "status)</code>, crash thì revert bằng git. Bốn tiền đề: verifiable · reversible · short horizon · bounded.",
     "<code>loop-runner.py</code> dừng ĐÚNG LÚC (5 guard, exit code phân biệt lý do) nhưng không giữ-tốt-vứt-tệ: "
     "<code>grep -nE 'git reset|revert|score|Trial'</code> trên file này trả về <b>0 kết quả</b>. "
     "Không metric, không chiều cải thiện, không lịch sử Trial.",
     "Nâng cấp tại chỗ: thêm <code>--metric-cmd</code> + <code>--direction</code> vào loop-runner, revert bằng "
     "<code>git reset</code>, ghi Trial vào run-log JSON sẵn có."),
    ("Gốc 2 — Edge ID để trích dẫn", "§V multi-hop querying",
     "“The answer can cite edge identifiers. If a statement is unsupported, the evaluator can identify the "
     "missing or contradictory edge.” Truy vấn = resolve entity → đi 1–2 hop → serialize trong budget → "
     "trả lời KÈM edge ID. Cấm dump cả graph vào context.",
     "Cạnh của overstack là <code>[[wikilink]]</code> — vô danh, không type, không ID. <code>/query</code> trả lời "
     "từ wiki nhưng không trích được “cạnh nào chống lưng câu này”. Nguyên tắc cấm-dump thì ĐÃ tuân thủ "
     "(orient chỉ bơm bản đồ, wiki-room có budget, mem-rank trả top-k).",
     "Đánh số cạnh ổn định trong <code>wiki-graph.py</code> (hash source→target→type) rồi bắt /query đính kèm."),
    ("Gốc 3 — Commit-DAG giữ lineage", "§III AgentHub",
     "“GitHub is for humans. AgentHub is for agents.” Thao tác chính không còn là merge-vào-main mà là "
     "<b>traverse the search graph</b>: <code>children</code> (đã thử gì trên kết quả này), <code>leaves</code> "
     "(biên chưa khám phá), <code>lineage</code> (đường sinh ra kết quả). Thí nghiệm bỏ đi vẫn là bằng chứng.",
     "overstack làm việc tuyến tính trên MỘT nhánh <code>orca</code>. <code>provenance-log.py</code> ghi sự kiện "
     "hash-chain theo writer nhưng không trả lời được ba truy vấn trên. Không message board — agent không đọc "
     "được giả thuyết đã bỏ của agent khác.",
     "Chỉ đáng xây khi thật sự chạy nhiều nhánh thí nghiệm song song — hiện chưa thấy đau (xem mục 07)."),
    ("Gốc 4 — Graph tham gia RUNTIME", "§IV TABLE I + §V",
     "Graph không phải tài liệu — nó là bộ nhớ dùng chung LÚC CHẠY: worker ghi <code>GraphUpdate</code>, "
     "validator kiểm provenance trong transaction, evaluator ground claim vào cạnh, orchestrator giữ context sạch. "
     "“The agent forgets, the graph does not.”",
     "wiki-graph của overstack sinh ra để NGƯỜI xem (HTML render) và để /lint. Không workflow nào query nó làm "
     "gate/routing/grounding. Thứ gần nhất: <code>claim-receipts.py</code> ground trích dẫn vào FILESYSTEM "
     "(đường dẫn có resolve không) — đúng tinh thần, sai tầng.",
     "Bước nhỏ nhất có nghĩa: cho evaluator (/qc-code, council) query wiki-graph để kiểm claim, trả feedback "
     "theo schema <code>{decision, claim, reason, required_evidence[]}</code> — format PDF cho sẵn."),
]

# ── S3: TABLE I ──────────────────────────────────────────────────────────────
TABLE1 = [
    ("Augmented LLM", "Retrieval source — traverse graph cho câu hỏi multi-hop", "part",
     "<code>/query</code> + <code>mem-rank</code> truy hồi từ wiki, nhưng theo trang, không theo đường cạnh"),
    ("Prompt Chaining", "Gate signal — kiểm entity vs graph hiện tại giữa các khâu", "gap", "—"),
    ("Routing", "Classifier input — type + degree của entity định tuyến truy vấn", "gap",
     "routing hiện theo BM25 <code>skills.search.json</code>, không theo graph"),
    ("Parallelization", "Shared surface — worker publish finding không giẫm nhau", "gap",
     "worker ghi file/draft riêng; không có bề mặt graph chung"),
    ("Orchestrator-Workers", "Shared memory — worker đọc/ghi graph, orchestrator giữ context sạch", "gap", "—"),
    ("Evaluator-Optimizer", "Grounding layer — evaluator kiểm claim vs cạnh graph", "part",
     "<code>claim-receipts.py</code> ground vào filesystem; <code>wikieval</code> kiểm vs golden — chưa vs cạnh"),
]

def diagram_runtime():
    s = ['<svg viewBox="0 0 900 260" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Trái: overstack hiện tại — graph một chiều từ code và wiki ra HTML cho người xem. '
         'Phải: PDF đòi graph hai chiều giữa worker, evaluator và orchestrator lúc chạy</title>', S.defs()]
    s.append('<text x="215" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#c26a00">overstack — DOCS-graph (một chiều)</text>')
    s.append(S.node(30, 40, 130, 40, "code + wiki", "#0a84ff"))
    s.append(S.node(30, 110, 170, 40, "build-wiki-graph.py", "#30b0c7", "0 token"))
    s.append(S.node(30, 180, 150, 40, "HTML render", "#9aa4b2", "mắt người xem"))
    s.append(S.line(95, 82, 95, 108, "#30b0c7", "ar1"))
    s.append(S.line(95, 152, 95, 178, "#9aa4b2", "ar1"))
    s.append('<text x="660" y="20" text-anchor="middle" font-size="11" font-weight="700" fill="#28a745">PDF — RUNTIME-graph (hai chiều)</text>')
    s.append(S.node(470, 105, 130, 44, "workers", "#0a84ff", "GraphUpdate"))
    s.append(S.node(640, 40, 150, 44, "GRAPH + validator", "#5856d6", "provenance, tx"))
    s.append(S.node(640, 170, 150, 44, "evaluator", "#34c759", "required_evidence[]"))
    s.append(S.node(470, 40, 130, 44, "orchestrator", "#30b0c7", "context sạch"))
    s.append(S.line(602, 118, 660, 88, "#0a84ff", "ar0"))
    s.append(S.line(660, 100, 602, 130, "#5856d6", "ar2"))
    s.append(S.line(715, 88, 715, 168, "#34c759", "ar3"))
    s.append(S.line(680, 168, 680, 88, "#5856d6", "ar2"))
    s.append(S.line(602, 62, 638, 62, "#30b0c7", "ar1"))
    s.append("</svg>")
    return "".join(s)

# ── S4: TABLE VI + 14 bước ──────────────────────────────────────────────────
TABLE6 = [
    ("Objective", "Task có test được không?", "Agent tối ưu sai mục tiêu", "full",
     "<code>/propose</code> + R7 ép SPEC đủ chất trước khi chạy"),
    ("Metric", "Phân biệt được cải thiện không?", "Hoạt động mà không tiến bộ", "part",
     "Eval suite có baseline; vòng loop thì KHÔNG có metric"),
    ("Reversibility", "Update có undo được không?", "Thí nghiệm hỏng phá state", "part",
     "git có; loop không tự revert; wiki xoá vật lý được"),
    ("Tool schema", "Tham số có type không?", "Gọi sai lặng lẽ, lỗi im", "gap",
     "Skill = markdown; từ chối tham số sai phụ thuộc vendor"),
    ("Artifact contract", "Worker phải trả về gì?", "Văn xuôi bất nhất", "gap",
     "Bàn giao = markdown; “nhìn ổn” vẫn hợp lệ với máy"),
    ("Provenance", "Mọi claim có nguồn không?", "Output không audit được", "full",
     "R2 <code>## Origin</code> chặn lúc Write + pre-commit — MẠNH hơn PDF (PDF kiểm lúc ghi graph)"),
    ("Resolution policy", "Quyết định gộp đảo ngược được không?", "False merge nhiễm graph", "na",
     "Không có tầng resolution — đúng khuyến cáo when-NOT-to của chính PDF"),
    ("Budget", "Hạn mức khai tường minh chưa?", "Tài nguyên không trần", "part",
     "<code>token-budget.py</code> cap token/tiền theo session; thiếu model-calls, sub-agents, workers, graph-writes"),
    ("Monitoring", "Metric theo dõi theo XU HƯỚNG chưa?", "Regression vô hình", "full",
     "<code>wiki-health.csv</code> + medic gương-soi mỗi phiên qua hook Stop"),
    ("Recovery", "Resume từ state được không?", "Mỗi gián đoạn là làm lại", "part",
     "run-log + <code>/orca-handover</code>; không auto-resume"),
]
STEPS14 = [
    (1, "Receive objective and constraints", "full"), (2, "Resolve task entities against the graph", "gap"),
    (3, "Retrieve bounded subgraph with provenance", "gap"), (4, "Create typed plan, validate dependencies", "part"),
    (5, "Assign independent steps to isolated workers", "full"), (6, "Require structured artifacts and evidence", "part"),
    (7, "Publish candidate graph updates", "gap"), (8, "Validate schemas, permissions, provenance", "part"),
    (9, "Run deterministic tests", "full"), (10, "Run evaluator agents against rubrics", "part"),
    (11, "Resolve conflicts or escalate uncertainty", "part"), (12, "Publish versioned final artifact", "part"),
    (13, "Link to sources, graph paths, runs, evaluations", "gap"), (14, "Record cost, latency, failures, open questions", "part"),
]

# ── S5: world model ─────────────────────────────────────────────────────────
WM = [
    ("Long-running investigations", "full", "problem-tree R17 — vấn đề xuyên phiên phải được flush ra cây"),
    ("Cross-session planning", "full", "<code>/orca-handover</code> — file bàn giao phiên khác làm tiếp được ngay"),
    ("Incremental document ingestion", "full", "<code>/ingest</code> — raw/ read-only, distill thành trang wiki có Origin"),
    ("Contradiction tracking", "part", "<code>/lint</code> rà thủ công; không có cạnh CONTRADICTS"),
    ("Temporal facts", "gap", "wiki không có valid-time — sự thật cũ bị ghi đè, không bị đóng dấu thời gian"),
    ("Versioned decisions", "full", "ADR + R13 + decision-anchoring liveness LIVE/STALE/ORPHAN/UNAVAILABLE"),
    ("Audit trails", "full", "audit.jsonl + <code>provenance-log.jsonl</code> hash-chain theo writer"),
    ("Handoff between models", "full", "AGENT.md ↔ CLAUDE.md parity (validator riêng) + skill mirror"),
    ("Recovery after failed run", "part", "run-log loop-runner; resume là việc tay"),
]

# ── S6: build path ──────────────────────────────────────────────────────────
PATH = [
    ("Day 1", "Reflective loop", "Measured quality improvement", "part",
     "loop có, guard có — thiếu “measured”: không điểm số"),
    ("Day 2", "Tool use", "Tool reduces known error class", "full",
     "84 skill; failure-flywheel gom lớp lỗi → sinh rule, đúng tinh thần “tool cho failure class đo được”"),
    ("Week 1", "Planning", "Variable tasks complete", "part",
     "propose/plan/R18 — markdown, không JSON, không validator DAG"),
    ("Week 2", "Multi-agent", "Role split beats single agent", "full",
     "Orca worktree + council + qc-code + trace-grader — CHƯA đo “beats” trên eval set"),
    ("Month 1", "Persistent graph", "Cross-session queries work", "part",
     "persistence QUA WIKI hoạt động thật; “cited edges” thì chưa — không edge ID"),
    ("Month 2", "Swarm workflow", "Wall-clock gain, no quality loss", "part",
     "mượn engine vendor; chưa tự đo wall-clock gain"),
]

# ═══════════════ render ═══════════════
def sec_open(i):
    t, sub = SECTIONS[i]
    return ('<section id="sec-%d" class="section-bg s-bg%d"><div class="section-header">'
            '<span class="tag">%02d · %s</span><h2>%s</h2><p>%s</p></div>'
            % (i, i, i + 1, E(t.upper()), E(t), E(sub)))

def card(title, body):
    return '<div class="card"><h4>%s</h4>%s</div>' % (title, body)

def ul(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)

def dbox(svg):
    return '<div class="diagram-box">%s</div>' % svg

MM = [
    ("PDF nói gì", "3 nguồn, 1 tiến trình", ["autoresearch — 700 exp / 2 ngày", "AgentHub — GitHub for agents",
     "Anthropic — 5 pattern + KG cookbook", "vibe → agentic → graph engineering"]),
    ("5 cơ chế", "externalize bottleneck", ["loop → iteration+eval", "chain → task order",
     "swarm → parallel search", "DAG → lineage", "KG → shared memory"]),
    ("4 gốc thiếu", "theo bằng chứng", ["ratchet điểm số (grep=0)", "edge ID trích dẫn",
     "commit-DAG lineage", "graph chưa runtime"]),
    ("Checklist", "TABLE VI: 3✅ 4🟡 2🔴", ["tool schema 🔴", "artifact contract 🔴",
     "provenance ✅ mạnh hơn PDF", "monitoring ✅ trends"]),
    ("World model", "6✅ 2🟡 1🔴", ["ADR liveness ✅", "handover ✅", "hash-chain ✅",
     "temporal facts 🔴"]),
    ("Phanh của PDF", "khi nào ĐỪNG", ["quan hệ đơn giản → đừng KG", "việc mạch liền → đừng fan-out",
     "budget trước worker"]),
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
            '<div class="node root has-children"><span class="nm">PDF ↔ overstack</span>'
            '<span class="ds">Graph Engineering, 11 trang</span><span class="ct">%d</span></div>'
            '<div class="children">%s</div></div></div></div></div>' % (len(MM), "".join(ch)))

# S0
s0 = sec_open(0) + """
<div class="card" style="margin-bottom:14px">
<p>PDF tổng hợp ba nguồn: <b>autoresearch</b> của Karpathy (agent tự chạy ~700 thí nghiệm ML trong 2 ngày,
giữ ~20 tối ưu, lõi ~630 dòng), <b>AgentHub</b> (nền cộng tác agent-first: bare git + SQLite + message board),
và <b>hạ tầng Anthropic</b> (5 workflow pattern · Dynamic Workflows spawn/gather tới 1 000 sub-agent ·
Knowledge Graph Cookbook 4 tầng). Thông điệp trung tâm: <i>“bottleneck thường không phải model call kế
tiếp — mà là CHỖ ĐẶT memory và evaluation”</i>, và mỗi kiến trúc tồn tại để externalize đúng một bottleneck
ra khỏi context window.</p>
<p style="margin-top:10px"><b style="color:var(--ink)">Đứng đâu:</b> overstack đã làm xong tầng
<b>agentic engineering</b> (người spec, cổng duyệt, guardrail tất định, eval có sàn) và đứng ở
<b>ngưỡng graph engineering</b>: có graph nhưng là DOCS-graph — sinh ra để xem và lint, chưa phải bộ nhớ
dùng chung mà worker/evaluator đọc-ghi lúc chạy. Bốn gốc thiếu bên dưới đều là hệ quả của ngưỡng này.</p></div>
<div class="grid g4" style="margin-bottom:14px">
<div class="card stat"><b style="color:#e0264b">4</b><span>gốc thiếu (mục 03)</span></div>
<div class="card stat"><b style="color:#c26a00">4/6</b><span>vai trò runtime của graph chưa có (TABLE I)</span></div>
<div class="card stat"><b style="color:#28a745">6/9</b><span>world model có đủ (mục 06)</span></div>
<div class="card stat"><b style="color:#0a84ff">~Week 2</b><span>vị trí trên build path (mục 07)</span></div>
</div>
<h3 style="font-size:14px;margin:18px 0 2px">Bản đồ trang</h3>
<p style="font-size:12px;color:var(--ink2)">Bấm nhánh để xổ.</p>""" + mindmap() + "</section>"

# S1
s1 = sec_open(1) + """
<div class="card"><p>Khung xương của PDF (§I): <i>mỗi kiến trúc externalize một bottleneck</i>. Đặt overstack
vào từng dòng thì thấy ngay hình dạng của cái thiếu — hai dòng cuối chính là gốc 3 và gốc 4.</p></div>
""" + dbox(diagram_progression()) + """
<div class="table-wrap"><table><thead><tr><th>Cơ chế</th><th>Externalize cái gì (PDF)</th>
<th>Phán quyết</th><th>overstack</th></tr></thead><tbody>""" + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (E(n), E(b), badge(v), o)
    for n, b, v, o in MECHS) + """</tbody></table></div>
<div class="card" style="margin-top:14px"><h4>Câu chốt §X của PDF, áp vào overstack</h4>
<p>“A loop can remember the current code and a local experiment log. A swarm can create many independent
contexts. A commit DAG remembers which work descends from which experiment. A knowledge graph remembers which
claims connect to which entities and sources.” — overstack nhớ bằng <b>wiki + git + JSONL</b>: đủ cho
hai vế đầu, chưa có hai vế sau.</p></div></section>"""

# S2
s2 = sec_open(2) + '<div class="grid g2">' + "".join(
    '<div class="card"><h4>%s <span style="font-weight:400;font-size:10.5px;color:var(--ink2)">· %s</span></h4>'
    '<p style="margin-bottom:8px"><b style="color:#5856d6">PDF đòi:</b> %s</p>'
    '<p style="margin-bottom:8px"><b style="color:#c26a00">overstack:</b> %s</p>'
    '<p><b style="color:#28a745">Bước kế:</b> %s</p></div>' % (E(t), E(ref), spec, cur, nxt)
    for t, ref, spec, cur, nxt in ROOTS) + "</div></section>"

# S3
s3 = sec_open(3) + """
<div class="card"><p>TABLE I của PDF là bảng “lật kèo”: graph không đứng cạnh workflow mà đứng
<b>bên trong</b> từng pattern, mỗi pattern dùng nó một kiểu. Đây là ranh giới DOCS-graph / RUNTIME-graph —
và là gốc thiếu thứ 4.</p></div>
""" + dbox(diagram_runtime()) + """
<div class="table-wrap"><table><thead><tr><th>Pattern</th><th>Vai trò graph (PDF TABLE I)</th>
<th>Phán quyết</th><th>overstack</th></tr></thead><tbody>""" + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (E(p), E(r), badge(v), o)
    for p, r, v, o in TABLE1) + """</tbody></table></div>
<div class="grid g2" style="margin-top:14px">""" + card("Grounding feedback — format PDF cho sẵn", """
<p>Evaluator ground một claim vào cạnh graph; thiếu cạnh thì trả về CÓ CẤU TRÚC, không phải văn xuôi:</p>
<div class="code-wrap"><pre class="code-block">{
  "decision": "revise",
  "claim": "Vendor_X_supplied_the_component_in_Y",
  "reason": "No_supported_path_from_Vendor_X_to_Y",
  "required_evidence": [
    "A_source-backed_supplied_relation",
    "A_source-backed_involved_in_relation"
  ]
}</pre></div>
<p style="margin-top:8px">Áp được ngay cho <code>/qc-code</code> và <code>council.py</code> mà không cần
dựng KG mới — ground vào wiki-graph hiện có.</p>""") + card("Ba vai trò graph (§V) — overstack chấm", ul([
    "<b>Shared memory</b> — worker ghi GraphUpdate: 🔴 worker overstack ghi file, không ghi graph",
    "<b>Grounding layer</b> — kiểm claim vs cạnh: 🟡 <code>claim-receipts.py</code> ground vào filesystem — đúng tinh thần, sai tầng",
    "<b>Persistent world model</b> — “agent forgets, graph does not”: ✅ overstack làm bằng wiki — xem mục 06",
])) + "</div></section>"

# S4
s4 = sec_open(4) + """
<div class="card"><p>TABLE VI của PDF — 10 câu hỏi, mỗi câu kèm “thiếu thì hỏng kiểu gì”.
Hai hàng đỏ của overstack nằm cạnh nhau và cùng một nguyên nhân: mọi hợp đồng đang là markdown cho người đọc,
chưa là schema cho máy từ chối.</p></div>
<div class="table-wrap"><table><thead><tr><th>Element</th><th>Câu hỏi</th><th>Thiếu thì…</th>
<th>Phán quyết</th><th>overstack</th></tr></thead><tbody>""" + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
    % (E(el), E(q), E(f), badge(v), o) for el, q, f, v, o in TABLE6) + """</tbody></table></div>
<h4 style="font-size:12px;margin:20px 0 6px">14 bước chuẩn cho một graph-grounded task (Appendix) — thiếu đúng 5 bước graph</h4>
<div class="table-wrap"><table><thead><tr><th style="width:36px">#</th><th>Bước</th><th>Phán quyết</th></tr></thead><tbody>""" + "".join(
    '<tr><td class="num"><b>%d</b></td><td>%s</td><td>%s</td></tr>' % (n, E(t), badge(v))
    for n, t, v in STEPS14) + """</tbody></table></div>
<p style="font-size:11.5px;color:var(--ink2);margin-top:8px">Bước 2, 3, 7, 8 (nửa graph), 13 — đều đòi graph
có thật lúc runtime. 9 bước còn lại overstack có tương đương qua propose/dispatch/verify.</p></section>"""

# S5
s5 = sec_open(5) + """
<div class="card"><p>§V của PDF: “<b>the agent forgets, the graph does not</b>” — chín năng lực mà
persistence mở ra. Đây là mặt overstack khớp PDF nhất, chỉ khác vật liệu: <i>the agent forgets,
the WIKI does not</i>. 6/9 có đủ bằng cơ chế đã chạy thật.</p></div>
""" + '<div class="table-wrap"><table><thead><tr><th>Năng lực (PDF §V)</th><th>Phán quyết</th><th>overstack</th></tr></thead><tbody>' + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (E(n), badge(v), o) for n, v, o in WM) + """
</tbody></table></div>
<div class="grid g2" style="margin-top:14px">""" + card("Hai lỗ còn lại", ul([
    "<b>Temporal facts</b> — trang wiki bị sửa là sự thật cũ biến mất; không valid-time, không lịch sử claim "
    "(git giữ diff nhưng không query được theo nghĩa)",
    "<b>Contradiction tracking</b> — <code>/lint</code> rà tay; không cạnh CONTRADICTS nên hai trang mâu thuẫn "
    "vẫn cùng tồn tại êm ái",
])) + card("Vì sao mặt này mạnh", ul([
    "R2/R4 làm persistence thành <b>luật</b>, không phải thói quen — quên là bị chặn",
    "provenance-log hash-chain THEO writer — giả mạo lịch sử là phát hiện được",
    "decision-anchoring nối quyết định vào symbol code thật, có 4 trạng thái sống/chết",
    "Đúng câu §X: “place memory outside the context window” — overstack đã đặt đúng chỗ từ đầu",
])) + "</div></section>"

# S6
s6 = sec_open(6) + """
<div class="card"><p>TABLE II của PDF — sáu chặng, mỗi chặng một exit criterion. overstack qua hẳn 2 chặng,
5 chặng còn “một phần” đều vì cùng lý do: chưa có phần <i>đo</i> (điểm số, cited edges, wall-clock gain).</p></div>
<div class="table-wrap"><table><thead><tr><th>Chặng</th><th>Deliverable</th><th>Exit criterion (PDF)</th>
<th>Phán quyết</th><th>overstack</th></tr></thead><tbody>""" + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
    % (E(d), E(dl), E(x), badge(v), o) for d, dl, x, v, o in PATH) + """</tbody></table></div>
<div class="grid g2" style="margin-top:14px">""" + card("Phanh của chính PDF — ba chỗ nói ĐỪNG", ul([
    "<b>§VIII.C:</b> đừng dựng KG khi task độc lập, không cần state xuyên phiên, quan hệ cố định/đơn giản, một "
    "bảng quan hệ trả lời được mọi query, hay sai số extraction vượt giá trị traversal — <i>đồ thị wikilink "
    "0-token của overstack có thể đã là mức đúng</i>",
    "<b>§IX.E:</b> việc cần mạch liền (kiến trúc, viết dài, refactor xoắn) GIẢM chất lượng khi fan-out — "
    "overstack chưa có luật cấm loại fan-out này",
    "<b>§IX.D:</b> 1 000 sub-agent = hàng chục đô một lần chạy; worker song song sinh lỗi TƯƠNG QUAN — sóng kiểm "
    "chứng phải khác prompt/bằng chứng/vai",
])) + card("Thứ tự việc đáng làm (rút từ cả PDF lẫn spec)", ul([
    "<b>1.</b> Ratchet điểm số cho loop-runner — metric + direction + git reset + Trial (nâng cấp tại chỗ)",
    "<b>2.</b> Edge ID + type cho cạnh wiki-graph; /query trích edge ID",
    "<b>3.</b> Grounding feedback schema <code>required_evidence[]</code> cho /qc-code + council",
    "<b>4.</b> 4 hạn mức còn thiếu vào token-budget (model calls · sub-agents · workers · graph writes)",
    "<b>5.</b> Commit-DAG hub — CHỜ tới khi thật sự chạy nhiều lineage song song",
])) + """</div>
<div class="card" style="margin-top:14px"><h4>Thước đo cuối (§X)</h4>
<p>“<i>Every important output can be traced to an objective, a plan, an artifact, a source, a graph path,
an evaluator decision, and a bounded execution record.</i>” Khi câu này còn sai, thêm agent chỉ thêm mờ đục.
overstack hiện đúng 5/7 mắt xích — đứt ở <b>graph path</b> (không edge ID) và một nửa <b>evaluator decision</b>
(rubric theo suite, chưa theo từng output).</p></div></section>"""

navlinks = "".join(
    '<a href="#sec-%d"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>%s</a>'
    % (i, S.IC[i % len(S.IC)], E(SECTIONS[i][0])) for i in range(len(SECTIONS)))

EXTRA_CSS = """
.vb{display:inline-block;font-size:10px;font-weight:700;padding:1.5px 8px;border-radius:999px;white-space:nowrap}
.v-full{background:rgba(52,199,89,.14);color:#28a745}
.v-part{background:rgba(255,149,0,.15);color:#c26a00}
.v-gap{background:rgba(255,45,85,.12);color:#e0264b}
.v-diff{background:rgba(88,86,214,.12);color:#5856d6}
"""

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>overstack ↔ Graph Engineering PDF — còn thiếu gì</title>
<meta name="description" content="Đối chiếu overstack với PDF Graph Engineering (Karpathy loop → AgentHub → Anthropic playbook): 4 gốc thiếu, TABLE I runtime-graph, checklist sản xuất, world model, build path.">
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23ff9500'/%3E%3C/svg%3E">
<script>(function(){try{var t=localStorage.getItem("osrcmap-theme");
if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}})();</script>
<style>__CSS__</style>
</head>
<body>
<a class="skip-link" href="#main">Bỏ qua điều hướng</a>
<nav>
  <div class="brand"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">__BRAND__</svg></span>
    <span><span class="logo-t">pdf-gap</span><br><span class="logo-s">overstack ↔ Graph Engineering</span></span></div>
  __NAV__
</nav>
<main id="main">
<div class="hero">
  <span class="eyebrow">Graph Engineering · The Karpathy Loop × Anthropic Playbook · 11 trang · July 2026</span>
  <h1>overstack còn thiếu gì theo PDF</h1>
  <p class="lead">PDF vẽ tiến trình <b>vibe coding → agentic engineering → graph engineering</b>: mỗi kiến trúc
  externalize một bottleneck ra khỏi context window. overstack đã làm xong tầng agentic (cổng duyệt, guardrail
  0 token, eval có sàn) và đứng ở ngưỡng tầng graph — có graph nhưng là DOCS-graph, chưa phải bộ nhớ runtime.
  Bốn gốc thiếu, mỗi gốc kèm bằng chứng file thật.</p>
  <div class="meta"><span>4 gốc thiếu</span><span>TABLE I: 4/6 vai trò graph chưa có</span>
  <span>TABLE VI: 3✅ 4🟡 2🔴</span><span>world model 6/9 ✅</span><span>build path ~Week 2</span>
  <span>trace §X: 5/7 mắt xích</span></div>
</div>
__SECS__
<footer>
  <p>Nguồn PDF: <code>~/Downloads/Graph-Engineering-Athropic-Karpathy-Loop.pdf</code> (11 trang, independently
  compiled July 2026 — not affiliated with Karpathy/Anthropic). Hệ đối chiếu: overstack tại commit
  <code>9032ae4</code>, nhánh <code>orca</code> — mọi tên file đã kiểm tồn tại trên đĩa.</p>
  <p style="margin-top:6px">File này: <code>/Users/thoaidd/Documents/Development/harness/setup/llmwiki/html/290726-pdf-gap-overstack.html</code></p>
  <p style="margin-top:6px">Trang liên quan: <code>290726-spec-vs-overstack.html</code> (đối chiếu spec dẫn xuất, 67 mục)
  · <code>290726-overstack-source-map.html</code> (bản đồ mã nguồn) · <code>onboarding-setup.html</code> (guided tour).</p>
</footer>
</main>
<script>__JS__</script>
</body>
</html>"""

out = (HTML.replace("__CSS__", S.CSS_BASE + S.section_css() + S.dark_css() + EXTRA_CSS)
           .replace("__BRAND__", S.BRAND)
           .replace("__NAV__", navlinks)
           .replace("__SECS__", s0 + s1 + s2 + s3 + s4 + s5 + s6)
           .replace("__JS__", S.JS))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(out)
for tok in ("__CSS__", "__NAV__", "__SECS__", "__JS__", "__BRAND__"):
    assert tok not in out, "token còn sót: " + tok
ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', out)
print("✅", OUT, len(out), "bytes")
print("external refs:", ext or "none ✅", "| sections:", out.count('<section id="sec-'))
