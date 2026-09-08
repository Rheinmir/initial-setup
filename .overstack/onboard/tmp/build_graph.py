#!/usr/bin/env python3
"""Assign layers (ordered prefix rules, first match wins), attach tour, validate, save."""
import json, os, sys, subprocess, datetime
from collections import Counter, defaultdict

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
T = os.path.join(ROOT, ".overstack", "onboard", "tmp")
OUT = os.path.join(ROOT, ".overstack", "graph")
os.makedirs(OUT, exist_ok=True)

g = json.load(open(os.path.join(T, "assembled-graph.json")))
nodes, edges = g["nodes"], g["edges"]
byid = {n["id"]: n for n in nodes}

# ---- LAYERS: ordered (prefix-predicate, id, name, description) — FIRST MATCH WINS ----
LAYERS = [
    ("layer:harness-core", "Harness Core (vendor-neutral)",
     "Lõi CLI đọc policy.yaml và thực thi luật, cộng installer 1-dòng (bootstrap/install/uninstall). "
     "Logic chặn nằm ở đây, không nhúng vào vendor nào — mỗi vendor chỉ là caller mỏng.",
     lambda p: p.startswith("harness/poc-vendor-neutral/")),

    ("layer:harness-validators", "Harness Validators",
     "15 validator tất định (0 token) hiện thực R1–R18: no_write_raw, origin_required, index_sync, "
     "folder_structure, okf_frontmatter, decision_adr, patterns_guard…",
     lambda p: p.startswith("harness/validators/")),

    ("layer:harness-scripts", "Harness Scripts",
     "63 script vận hành harness: cài đặt, fdk-gate, sync-skills, council, loop-runner, eval, "
     "code-logger, decision-anchoring, egress-guard, medic phụ trợ.",
     lambda p: p.startswith("harness/scripts/")),

    ("layer:harness-quality", "Harness Quality & Telemetry",
     "Test/eval/metrics của chính harness: harness/tests (fire-drill luật còn cắn), evals (promptfoo), "
     "metrics JSONL (provenance-log, scratch-log, baseline).",
     lambda p: p.startswith(("harness/tests/", "harness/evals/", "harness/metrics/"))),

    ("layer:harness-policy", "Harness Policy & Config",
     "Khai báo bất biến: policy.yaml (18 rule), foundation.yaml, mechanisms.yaml, các *.config.yaml "
     "(council, egress-guard, mem-rank, failure-flywheel…) và tài liệu kiến trúc harness.",
     lambda p: p.startswith("harness/") or p.startswith("harness-local/")),

    ("layer:skills", "Skills (canonical)",
     "84 skill dạng SKILL.md, gọi bằng /<tên>. Đây là bản canonical; mirror sang llmwiki/skills/ "
     "và cài global vào ~/.claude/skills.",
     lambda p: p.startswith("skills/")),

    ("layer:vendor-adapter", "Vendor Adapter (hooks)",
     "Dây cắm mỏng cho từng vendor: hook Claude Code (PreToolUse/PostToolUse/Stop/SessionStart/"
     "SessionEnd) + settings.json permissions.deny. Fail-open để lỗi hạ tầng không phá phiên.",
     lambda p: p.startswith((".claude/", "llmwiki/.claude/", ".claude-plugin/"))),

    ("layer:knowledge-base", "Knowledge Base (llmwiki/wiki)",
     "Trụ tri thức per-project: concepts/entities/sources/adr/draft + index.md (R3) và log.md (R4). "
     "Là bộ nhớ dài hạn agent đọc trước khi hành động.",
     lambda p: p.startswith(("llmwiki/wiki/", "llmwiki/raw/", "llmwiki/patterns/", "llmwiki/personas/"))),

    ("layer:skills-mirror", "Skills Mirror (llmwiki/skills)",
     "Bản mirror của skills đi kèm khuôn llmwiki khi deploy xuống dự án; sync bằng "
     "harness/scripts/sync-skills.py, lệch bản là drift phải sửa.",
     lambda p: p.startswith("llmwiki/skills/")),

    ("layer:docs-html", "Generated Docs (HTML)",
     "Tài liệu self-contained sinh BẰNG CODE từ đĩa: overstack.html, wiki-graph.html, "
     "fdk-problem-tree.html — nên bảng skill/rule luôn khớp thực tế.",
     lambda p: p.startswith(("llmwiki/html/", "fdk/docs/"))),

    ("layer:fdk", "FDK — Framework Dev Kit",
     "Đồ nghề phát triển CHÍNH overstack: 19 tool sinh CAPABILITIES/cheatsheet/skill-search/"
     "wiki-graph, medic (cổng sức khoẻ), artifacts, new-skill. Không travel xuống dự án con (ADR-004/008).",
     lambda p: p.startswith("fdk/") and not p.startswith("fdk/wiki/")),

    ("layer:fdk-wiki", "FDK Wiki (framework's own knowledge)",
     "Wiki RIÊNG của framework (ADR-008): ADR-001..010, concepts harness/fdk, decisions, sources. "
     "Tách khỏi llmwiki/wiki để tri thức framework không lẫn tri thức dự án.",
     lambda p: p.startswith("fdk/wiki/")),

    ("layer:llmwiki-rules", "llmwiki Rules & Template",
     "Rule file agent nạp mỗi phiên (CLAUDE.md/AGENT.md) và phần còn lại của khuôn llmwiki "
     "đi theo dự án khi cài.",
     lambda p: p.startswith("llmwiki/")),

    ("layer:ci-gate", "CI & Repo Gate",
     "Sàn vendor-neutral: GitHub Actions harness.yml chạy validator + self-test mỗi PR, "
     ".pre-commit-config.yaml gate mọi commit, .template-manifest.json theo dõi drift template.",
     lambda p: p.startswith(".github/") or p in (".pre-commit-config.yaml", ".template-manifest.json",
                                                 ".gitignore", ".gitattributes")),

    ("layer:dot-artifacts", ".overstack/ — artifacts (sinh ra / kéo về)",
     "Quy ước: mọi artifact sinh/kéo về gom một gốc .overstack/ — .overstack/doyourmagic (bundle skill tool ngoài, "
     "đồng bộ với rheinmir/dym), .overstack/onboard + .overstack/graph (đầu ra phase 1 /orca-onboard, "
     "chính là đồ nghề vẽ graph này), .overstack/kit. Không phải lõi, không lẫn vào skills canonical.",
     lambda p: p.startswith(".overstack/")),

    ("layer:project-bootstrap", "Project Bootstrap & Docs",
     "Prompt dựng dự án mới (00→03 + setup.md) và tài liệu gốc repo: README, CLAUDE.md, RELEASE-*.",
     lambda p: True),  # catch-all
]

assign = {}
for n in nodes:
    p = n["filePath"]
    for lid, lname, ldesc, pred in LAYERS:
        if pred(p):
            assign[n["id"]] = lid
            break

layers = []
for lid, lname, ldesc, _ in LAYERS:
    ids = [nid for nid, l in assign.items() if l == lid]
    if ids:
        layers.append({"id": lid, "name": lname, "description": ldesc, "nodeIds": sorted(ids)})
for n in nodes:
    n["layer"] = assign[n["id"]]

# ---- TOUR (authored: Claude main thread reasoning) ----
def N(p):
    for pref in ("file:", "config:", "document:"):
        if pref + p in byid: return pref + p
    return None

TOUR_SPEC = [
    (1, "Ba trụ của overstack — bắt đầu ở README",
     "overstack là lớp khung đặt LÊN TRÊN dự án, biến AI agent thành cộng sự tự-kỷ-luật bằng ba trụ: "
     "llmwiki/ (trí nhớ), harness/ (guardrail tất định 0 token), skills/ (tay nghề đóng gói). "
     "README mô tả cả ba và một-dòng cài đặt duy nhất.",
     ["README.md", "CLAUDE.md", "llmwiki/AGENT.md"]),

    (2, "Một dòng cài — bootstrap kéo cả ba trụ",
     "bootstrap.sh là cửa vào thật: curl | bash trong thư mục dự án là cài/update cả 3 trụ, in bảng "
     "trạng thái cuối. install.sh làm phần harness (mặc định harness-only khi chạy từ repo đã clone), "
     "uninstall.sh gỡ sạch. Đây là hợp đồng downstream — đổi ở đây là đổi trải nghiệm người mới.",
     ["harness/poc-vendor-neutral/bootstrap.sh", "harness/poc-vendor-neutral/install.sh",
      "harness/poc-vendor-neutral/uninstall.sh", "harness/downstream-contract.yaml"]),

    (3, "policy.yaml — luật là dữ liệu, không phải code",
     "18 rule (R1..R18) khai báo trong YAML, vendor-free: no-write-raw, origin-required, index-sync, "
     "log-append, folder-structure, verify-before-commit, proposal-complete, decision-to-adr… "
     "Thêm luật = thêm entry ở đây rồi nối validator, không sửa rải rác trong hook.",
     ["harness/policy.yaml", "harness/poc-vendor-neutral/policy.yaml", "harness/foundation.yaml",
      "harness/mechanisms.yaml"]),

    (4, "Lõi thực thi — llmwiki-validate.py đọc policy rồi phán",
     "Lõi CLI vendor-neutral: nhận payload từ bất kỳ vendor nào, đọc policy.yaml, trả verdict "
     "allow/deny. Vì lõi tách khỏi vendor, cùng một luật cắn được ở Claude Code, opencode, CI.",
     ["harness/poc-vendor-neutral/bin/llmwiki-validate.py",
      "harness/poc-vendor-neutral/bin/harness-events.py",
      "harness/poc-vendor-neutral/gen-converters.py"]),

    (5, "15 validator — mỗi luật một file, chạy 0 token",
     "Mỗi rule có một validator python thuần: no_write_raw chặn ghi llmwiki/raw/, origin_required ép "
     "mọi trang wiki có '## Origin', index_sync bắt index.md khớp đĩa, folder_structure chặn tạo thư "
     "mục lạ, decision_adr ép quyết định kiến trúc phải trỏ ADR. Không LLM nào được quyền phủ quyết.",
     ["harness/validators/no_write_raw.py", "harness/validators/origin_required.py",
      "harness/validators/index_sync.py", "harness/validators/folder_structure.py",
      "harness/validators/decision_adr.py", "harness/validators/okf_frontmatter.py"]),

    (6, "Dây cắm vendor — hook Claude Code, fail-open",
     "Adapter mỏng: PreToolUse chặn TRƯỚC khi Write/Edit/Bash xảy ra, PostToolUse ghi audit.jsonl và "
     "sinh log.md, Stop chặn kết thúc lượt nếu index.md lệch, SessionStart in trạng thái + drift. "
     "Mọi hook fail-open — hạ tầng lỗi thì exit 0, không phá phiên người dùng.",
     ["llmwiki/.claude/hooks/pre_tool_use.py", "llmwiki/.claude/hooks/post_tool_use.py",
      "llmwiki/.claude/hooks/stop.py", "llmwiki/.claude/hooks/session_start.py",
      ".claude/settings.json"]),

    (7, "Trụ tri thức — llmwiki/wiki là bộ nhớ dài hạn",
     "Wiki dự án: concepts/ (khái niệm), entities/ (thực thể), sources/ (nguồn + ADR + draft). "
     "index.md là mục lục bắt buộc khớp đĩa (R3), log.md là nhật ký append-only (R4). Agent QUERY "
     "wiki trước khi grep code — đó là lý do context không rot qua nhiều phiên.",
     ["llmwiki/wiki/index.md", "llmwiki/wiki/log.md", "llmwiki/CLAUDE.md", "llmwiki/AGENT.md"]),

    (8, "Trụ kỹ năng — SKILL.md canonical rồi mirror",
     "Mỗi skill là một SKILL.md gọi bằng /<tên>. Bản canonical ở skills/, mirror sang llmwiki/skills/ "
     "để đi kèm khuôn wiki, và cài global qua npx skills add. sync-skills.py giữ hai cây khỏi lệch — "
     "lệch bản là drift, medic sẽ báo.",
     ["skills/orca-workflow/SKILL.md", "skills/propose/SKILL.md", "skills/verify-before-commit/SKILL.md",
      "harness/scripts/sync-skills.py", "fdk/tools/sync-skill.sh"]),

    (9, "Vòng làm việc hằng ngày — propose → gate → dispatch",
     "Luồng chuẩn: /propose viết draft vào wiki rồi DỪNG chờ duyệt, người gật thì /plan mở thành brief "
     "thi hành được, dispatch cho agent, cuối cùng /verify-before-commit promote draft thành wiki thật "
     "và mở cổng commit (R6). Human-in-the-loop nằm ở cổng, không nằm ở lời nhắc.",
     ["skills/propose/SKILL.md", "skills/plan/SKILL.md", "skills/verify-before-commit/SKILL.md",
      "skills/orca-workflow/SKILL.md", "skills/ship/SKILL.md"]),

    (10, "FDK — đồ nghề phát triển CHÍNH framework",
     "fdk/ là bộ dev-kit của người làm framework, không travel xuống dự án con (ADR-004/008): "
     "build-capabilities.py đếm skill/rule/tool từ đĩa sinh CAPABILITIES.md, build-skill-search.py "
     "cho find-skill, new-skill.py scaffold skill vào cả hai cây, fdk-gate.py là definition-of-done.",
     ["fdk/CAPABILITIES.md", "fdk/tools/build-capabilities.py", "fdk/tools/build-skill-search.py",
      "fdk/tools/new-skill.py", "harness/scripts/fdk-gate.py"]),

    (11, "Tài liệu sinh bằng code — không bao giờ lệch đĩa",
     "build-overstack-docs.py đọc thẳng skills/, policy.yaml, fdk/tools/ rồi sinh overstack.html "
     "self-contained; build-wiki-graph.py vẽ vector quan hệ concept↔code. Vì sinh từ đĩa, tài liệu "
     "không thể nói dối về những gì đang thật sự có.",
     ["fdk/tools/build-overstack-docs.py", "fdk/tools/build-wiki-graph.py",
      "llmwiki/html/overstack.html", "llmwiki/html/wiki-graph.html"]),

    (12, "Cổng sức khoẻ cuối — medic, pre-commit, CI",
     "medic.py chứng minh trong MỘT lệnh rằng luật còn cắn (fire-drill), validator không lệch bản, "
     "docs khớp đĩa, eval không regress. .pre-commit-config.yaml là backstop vendor-neutral, "
     "harness.yml chạy validator + self-test mỗi PR. Ba tầng để một tầng hỏng vẫn còn chặn.",
     ["fdk/tools/medic.py", ".pre-commit-config.yaml", ".github/workflows/harness.yml",
      "harness/scripts/harness-doctor.py"]),

    (13, "Dựng dự án mới — dán một prompt là xong",
     "00-New-Project.md là prompt một-lần: agent tự cài overstack, kickoff hỏi 3 câu, dựng knowledge "
     "base, scaffold MVP, dừng đúng chỗ cần người quyết. 01/02/03 là bản tách pha khi muốn đi chậm.",
     ["00-New-Project.md", "01-Project-Kickoff.md", "02-Setup-Knowledge-Base.md",
      "03-Scaffold-Application.md", "setup.md"]),
]

tour = []
missing_tour = []
for order, title, desc, paths in TOUR_SPEC:
    ids = []
    for p in paths:
        i = N(p)
        if i: ids.append(i)
        else: missing_tour.append(p)
    tour.append({"order": order, "title": title, "description": desc, "nodeIds": ids})

# ---- VALIDATE ----
warn = []
seen = set()
for n in nodes:
    if n["id"] in seen: warn.append(f"duplicate node id: {n['id']}")
    seen.add(n["id"])
edges = [e for e in edges if e["source"] in seen and e["target"] in seen]
lay_count = Counter()
for l in layers:
    for i in l["nodeIds"]: lay_count[i] += 1
for i, c in lay_count.items():
    if c != 1: warn.append(f"node in {c} layers: {i}")
unlayered = [n["id"] for n in nodes if n["id"] not in lay_count]
if unlayered: warn.append(f"{len(unlayered)} nodes without layer")
if missing_tour: warn.append("tour paths not found: " + ", ".join(missing_tour))
deg = Counter()
for e in edges:
    deg[e["source"]] += 1; deg[e["target"]] += 1
orphans = [n["id"] for n in nodes if deg[n["id"]] == 0]

TODAY = datetime.date.today().isoformat()
commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
graph = {
    "version": "1.0",
    "project": {
        "name": "overstack (rheinmir/setup)",
        "languages": ["Markdown", "Python", "Shell", "YAML", "HTML"],
        "frameworks": ["Claude Code hooks", "pre-commit", "GitHub Actions", "promptfoo", "Orca"],
        "description": "Lớp khung self-disciplined cho AI agent: trí nhớ (llmwiki) + guardrail tất định "
                       "(harness) + tay nghề đóng gói (skills), cài bằng một dòng curl.",
        "analyzedAt": TODAY,
        "gitCommitHash": commit,
    },
    "nodes": nodes, "edges": edges, "layers": layers, "tour": tour,
}
json.dump(graph, open(os.path.join(OUT, "knowledge-graph.json"), "w"), ensure_ascii=False, indent=1)
json.dump({"lastAnalyzedAt": TODAY, "gitCommitHash": commit, "analyzedFiles": len(nodes)},
          open(os.path.join(OUT, "meta.json"), "w"), indent=1)

print(f"nodes={len(nodes)} edges={len(edges)} layers={len(layers)} tour={len(tour)} orphans={len(orphans)}")
for l in layers:
    print(f"  {l['id']:<28} {len(l['nodeIds']):>4} nodes")
print("WARNINGS:" if warn else "no warnings")
for w in warn: print("  ⚠", w)
