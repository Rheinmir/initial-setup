#!/usr/bin/env python3
"""Sinh llmwiki/html/290726-spec-vs-overstack.html — đối chiếu overstack (hệ hiện tại)
với graph-engineering-implementation-spec.md v0.1.
Tái dùng design shell của build_source_map.py (một nguồn CSS/JS, không nhân bản)."""
import os, re, sys, html
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "."]
import build_source_map as S           # CSS_BASE, JS, ACCENT/H4, dark_css, section_css, node/line/defs, IC, BRAND

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.join(ROOT, "llmwiki/html/290726-spec-vs-overstack.html")
E = html.escape

# ── thang phán quyết ─────────────────────────────────────────────────────────
V = {
    "full": ("✅", "Có đủ", "#34c759", "v-full"),
    "part": ("🟡", "Một phần", "#ff9500", "v-part"),
    "gap":  ("🔴", "Thiếu", "#ff2d55", "v-gap"),
    "diff": ("◆",  "Khác thiết kế", "#5856d6", "v-diff"),
    "plus": ("★",  "Vượt spec", "#0a84ff", "v-plus"),
}
def badge(k):
    ic, lb, _, cls = V[k]
    return '<span class="vb %s">%s %s</span>' % (cls, ic, E(lb))

SECTIONS = [
    ("Tóm tắt", "Hai hệ giải cùng bài toán trên hai nền khác nhau"),
    ("Năm mặt phẳng", "§2 — mặt nào có, mặt nào là thứ khác"),
    ("Hai đồ thị & data model", "§2.1 · §3 — node, cạnh, bốn bất biến ghi"),
    ("Bảy thành phần", "§4.1–4.7 — từng cấu phần, bằng chứng file thật"),
    ("Budget · Rails · Eval", "§5 · §7 — hạn mức khai trước và bộ đo"),
    ("Khoảng trống & việc nên làm", "§10 acceptance + ưu tiên"),
    ("Chỗ overstack đi xa hơn", "Thứ spec không nói tới"),
]

# ── §2 năm mặt phẳng ─────────────────────────────────────────────────────────
PLANES = [
    ("Control", "Python service (FastAPI) nhận objective, lập plan, cấp budget, start/stop workflow",
     "Không có service. Điều phối bằng skill <code>/propose → /plan → dispatch</code> cộng "
     "<code>harness/scripts/orca-dispatch.py</code> và Orca CLI. Objective sống trong draft wiki, "
     "không trong một API.", "diff",
     "Cố ý: framework phải travel theo repo và cài bằng một dòng curl — thêm một service là thêm thứ "
     "người dùng phải vận hành."),
    ("Execution", "Container worker (Docker) + git worktree, cách ly",
     "git worktree qua Orca (<code>skills/orca-cli/SKILL.md</code>), chạy thẳng trên máy dev. "
     "Không container, không image pinning.", "part",
     "Cách ly nhánh có; cách ly môi trường chạy thì không — hai agent vẫn dùng chung Python/OS của máy."),
    ("Artifact", "Object store S3 + index quan hệ Postgres, immutable + versioned",
     "File trong chính repo git; <code>fdk/tools/artifacts.py</code> dựng manifest và bắt bốn lỗi vòng đời "
     "(slug trùng phân kỳ, orphan, row index trỏ file gitignored). Version = commit git.", "part",
     "Bất biến và version có (git), nhưng artifact HTML/draft bị gitignore nên trên bản clone mới là không tồn tại."),
    ("Graph", "Postgres → NetworkX cho traversal; Neo4j tuỳ chọn về sau",
     "<code>harness/scripts/wiki-graph.py</code> dựng đồ thị có hướng trong bộ nhớ từ "
     "<code>[[wikilink]]</code>, giữ cả chiều inbound; <code>fdk/tools/build-wiki-graph.py</code> thêm node "
     "code và suy cạnh <code>imports</code>. MCP code-graph (SQLite) hiện <b>absent</b> trên máy này.", "part",
     "Đồ thị có thật và 0 token, nhưng phi-thường-trú: dựng lại mỗi lần chạy, không có store để truy vấn nguội."),
    ("Evaluation", "Python harness + rubric store",
     "<code>harness/evals/promptfooconfig.yaml</code> (19 golden question), <code>wikieval.py</code> "
     "(cascade assert, chặn CI), <code>retrieval-eval.py</code> (30 golden, có sàn baseline), "
     "<code>trace-grader.py</code> (chấm ĐƯỜNG ĐI, không chỉ đáp án), <code>skill-resolve-eval.py</code>, "
     "baseline JSON trong <code>harness/metrics/</code>.", "full",
     "Mặt mạnh nhất. Có thứ spec không đòi: chấm quỹ đạo để bắt 'corrupt success' và flaky."),
]

# ── §3 node / edge ───────────────────────────────────────────────────────────
NODES = [
    ("Entity", "full", "<code>llmwiki/wiki/entities/*.md</code>, frontmatter <code>type</code> ép bởi R9"),
    ("Claim", "gap", "Không có node mệnh đề riêng — khẳng định nằm trong văn xuôi của trang, không địa chỉ hoá được"),
    ("Source", "full", "<code>wiki/sources/</code> + mục <code>## Origin</code> bắt buộc mọi trang (R2, chặn 2 tầng)"),
    ("Artifact", "part", "<code>fdk/MANIFEST.json</code> sinh bởi <code>artifacts.py</code>; không có trường version riêng"),
    ("AgentRun", "part", "<code>wiki/sources/*-session-provenance.md</code> + <code>scratch-log.jsonl</code> + <code>writer_id</code>"),
    ("Evaluation", "part", "<code>harness/metrics/eval-baseline.json</code> — theo bộ eval, không theo từng output"),
    ("Task", "part", "Ledger Orca + <code>wiki/sources/ISSUES.md</code>; <code>orca-reconcile.py</code> soát task treo"),
    ("Commit", "full", "git + trường <code>git_sha</code> trong mỗi sự kiện <code>provenance-log.jsonl</code>"),
    ("Metric", "full", "<code>harness/metrics/*.json|jsonl|csv</code> — baseline, cost-by-session, wiki-health"),
]
EDGES = [
    ("MENTIONS", "part", "<code>[[wikilink]]</code> — có cạnh nhưng KHÔNG có type"),
    ("SUPPORTS", "gap", "—"),
    ("CONTRADICTS", "gap", "— (mâu thuẫn phát hiện thủ công qua <code>/lint</code>)"),
    ("DERIVED_FROM", "part", "<code>derives-from</code> trong <code>build-wiki-graph.py</code> (dò chu trình)"),
    ("PRODUCED", "part", "<code>writer_id</code> + <code>topic</code> trong provenance-log"),
    ("EVALUATES", "gap", "—"),
    ("REVISES", "gap", "—"),
    ("SUPERSEDES", "part", "R13: ADR bị đè phải khai <code>Superseded by</code>"),
    ("DEPENDS_ON", "part", "<code>depends-on</code> (wiki) + cạnh <code>imports</code> (code)"),
    ("PARENT_OF", "part", "git parent — nhưng không đưa vào đồ thị tri thức"),
    ("RESOLVED_TO", "gap", "— không có tầng entity resolution"),
]
INVARIANTS = [
    ("1. Mọi claim có cạnh source hoặc đánh dấu <code>inference</code>", "full",
     "R2 <code>origin_required.py</code> chặn ngay lúc Write, lại chặn lần nữa ở pre-commit. "
     "Mạnh hơn spec: spec kiểm lúc ghi graph, overstack kiểm trước khi file kịp tồn tại."),
    ("2. Mọi artifact có run tạo ra nó và một version", "part",
     "Origin có ô Commit; provenance-log có <code>writer_id</code> + <code>git_sha</code>. "
     "Nhưng không trường version riêng, và ô Commit do <code>/verify-before-commit</code> điền — bỏ bước thì trống."),
    ("3. Mọi evaluation nêu rõ rubric", "part",
     "Assertion nằm trong chính golden page (<code>wikieval.py</code>); "
     "<code>harness/council.personas.yaml</code> là rubric cho hội đồng. Không bắt buộc rubric ID."),
    ("4. Mọi đối tượng bị đè vẫn địa chỉ hoá được (chỉ soft-delete)", "part",
     "R13 giữ ADR bị đè; decision-anchoring T8 khoá xoá-vật-lý theo id. "
     "Nhưng trang wiki thường vẫn xoá vật lý được — chỉ R3 index-sync phát hiện."),
]

# ── §4 bảy thành phần (master-detail) ────────────────────────────────────────
COMPONENTS = [
 ("4.1", "Ratchet Loop Engine", "part",
  "Vòng generate → evaluate → keep/revert, mỗi Trial ghi lại trước khi lặp tiếp, revert bằng "
  "<code>git reset</code> về commit giữ cuối, dừng theo budget / N lần không cải thiện / tín hiệu dừng. "
  "Bắt buộc có <code>program.md</code> khai file được sửa, metric và chiều, budget, lệnh chạy, chính sách crash "
  "và leo thang. Bốn tiền đề: verify được · đảo ngược được · chân trời ngắn · môi trường có biên.",
  [("Có thật", "<code>harness/scripts/loop-runner.py</code> — vòng điều khiển tất định + <b>toàn bộ</b> guard "
    "bắt buộc: <code>max_iter</code> 6, <code>budget_seconds</code> 900, <code>no_progress_k</code> 2 "
    "(băm state-hash để dò tiến triển), <code>escalate_after_iter</code> 4 → giao lại cho người. "
    "Exit code phân biệt SUCCESS/MAX_ITER/TIMEOUT/NO_PROGRESS/ESCALATE. "
    "Có run-log JSON và reflexion: mỗi vòng hỏng ghi một dòng bài học vào trang wiki episodic."),
   ("Tương đương <code>program.md</code>", "<code>harness/loop-runner.config.yaml</code> — đúng vai trò spec mô tả "
    "(vùng file được sửa, budget, lệnh verify, chính sách leo thang), lại theo /build-now-adapt-later: "
    "mọi giá trị chưa chắc đều gắn <code>#&nbsp;ASSUMPTION</code> và bước LLM-revise là stub no-op."),
   ("Thiếu", "<b>Không có ratchet theo điểm số.</b> VERIFY là exit-code pass/fail, không phải metric cải thiện; "
    "grep <code>git reset</code> trong <code>loop-runner.py</code> ra <b>0</b> kết quả — không có revert bằng git; "
    "không có bản ghi <code>Trial{commit, score, status}</code>. Nói cách khác: vòng lặp <i>dừng đúng lúc</i> "
    "nhưng chưa <i>giữ cái tốt hơn và vứt cái tệ hơn</i>.")]),

 ("4.2", "Tool Layer", "part",
  "Mỗi tool khai schema JSON có type cho tham số, phạm vi quyền, hợp đồng kết quả. Tham số sai bị từ chối "
  "TRƯỚC khi chạy, cấm ép kiểu ngầm. Chỉ thêm tool khi có một lớp lỗi ĐO ĐƯỢC, và ghi lại ID lớp lỗi đó.",
  [("Có thật", "84 skill dạng SKILL.md; quyền qua <code>.claude/settings.json → permissions.deny</code> và "
    "<code>egress-guard.py</code> nối vào PreToolUse cho Bash (chặn rò dữ liệu ra ngoài)."),
   ("Đúng tinh thần spec", "<code>harness/scripts/failure-flywheel.py</code> gom lỗi lặp thành lớp, quá ngưỡng thì "
    "scaffold rule/skill mới — chính là 'chỉ thêm tool khi có failure class đo được'."),
   ("Thiếu", "Skill là markdown, không schema JSON có type; việc từ chối tham số sai phụ thuộc tool của vendor "
    "chứ không phải hợp đồng của overstack.")]),

 ("4.3", "Planner", "part",
  "Plan là JSON <code>{objective, steps[{id, action, input, depends_on, success}]}</code>. Validator từ chối "
  "plan có phụ thuộc treo, có chu trình, hoặc bước không có tiêu chí thành công. Replan giữ artifact của bước "
  "đã xong; retry có trần theo bước và theo plan. Chỉ lập plan khi đường đi thay đổi.",
  [("Có thật", "<code>/propose</code> → R7 <code>proposal_complete.py</code> bắt bảng Agent Task Assignment, "
    "sequence diagram TỪNG task, cấm placeholder → <code>/plan</code> → R18 plan-executable → "
    "<code>spec-gate.py</code> (spec → plan → tasks, kiểm một thay đổi có trích spec không)."),
   ("Vượt spec", "<code>harness/scripts/dispatch-verify.py</code> — <b>hậu kiểm</b> lời hứa của proposal với thực tế "
    "trên đĩa. Spec chỉ chặn plan xấu trước khi chạy; overstack còn hỏi lại sau khi chạy xong 'file hứa có thật chưa'."),
   ("Thiếu", "Plan là markdown, không JSON. Không có validator DAG (phụ thuộc treo, chu trình) — R7/R18 kiểm "
    "<i>đủ mục</i> chứ không kiểm <i>đồ thị phụ thuộc</i>. Không có trần retry theo bước.")]),

 ("4.4", "Multi-Agent Roles", "part",
  "Vai: planner, implementer, test author, reviewer, security reviewer, synthesizer. Mọi bàn giao là hợp đồng "
  "artifact có schema, không bao giờ là văn xuôi tự do. Reviewer phải trả lỗi theo tiêu chí "
  "<code>{criterion_id, location, defect, severity}</code> — 'nhìn ổn' là schema-invalid. Agent code song song "
  "dùng git worktree. Bắt đầu bằng cặp tối thiểu generator + critic.",
  [("Có thật", "<code>harness/scripts/council.py</code> — ba giai đoạn của Karpathy, phần TẤT ĐỊNH tách hẳn khỏi model: "
    "ẩn danh tác giả (sắp theo sha256 ổn định), gộp mean-rank, nêu bất đồng, anchor-guard chống thiên vị vị trí "
    "bằng seed truyền vào (không RNG toàn cục), xuất transcript json + md."),
   ("Có thật", "Worktree isolation qua Orca; <code>/qc-code</code> review bốn mục có điểm và verdict; "
    "<code>trace-grader.py</code> chấm quỹ đạo để bắt 'đúng đáp án nhưng sai đường' và flaky."),
   ("Thiếu", "Bàn giao giữa các vai là file markdown (draft, PLAN, report) — không schema. Một reviewer trả "
    "'nhìn ổn' vẫn hợp lệ với máy; không có kiểu <code>{criterion_id, location, defect, severity}</code>.")]),

 ("4.5", "Knowledge Graph Pipeline", "part",
  "Bốn tầng test độc lập được: (1) extraction bằng model rẻ, schema-constrained; (2) resolution bằng model mạnh, "
  "blocking rẻ rồi model gom cụm canonical, kết quả cộng thêm (alias, rationale, confidence, run ID); "
  "(3) assembly vào MultiDiGraph, mọi write qua validator trong transaction; (4) query: giải entity → đi ≤2 hop "
  "→ serialize trong ngân sách token → trả lời kèm trích edge ID. <b>Cấm dump cả graph vào context.</b>",
  [("Có thật", "Đồ thị dựng <b>tất định, 0 token</b>: <code>wiki-graph.py</code> giữ cả hai chiều cạnh để trả lời "
    "'trang nào trỏ tới đây'; <code>build-wiki-graph.py</code> thêm node code, suy cạnh <code>imports</code> từ code "
    "thật, dò chu trình <code>derives-from</code>/<code>depends-on</code>, vẽ ra HTML."),
   ("Đồng ý với spec", "Nguyên tắc 'cấm dump cả graph' được thi hành thật: hook <code>orient</code> chỉ bơm bản đồ, "
    "<code>/wiki-room</code> nạp chi tiết trong budget cứng, <code>mem-rank.py</code> trả về vài memory liên quan "
    "thay vì đổ hết, <code>query-proxy.py</code> đo token của chiến lược đọc."),
   ("Thiếu", "Không có tầng extraction hay resolution bằng LLM; không có confidence trên cạnh; câu trả lời không "
    "trích edge ID; bảy điểm của 'context builder contract' chưa được gói thành một hàm dùng chung."),
   ("Lưu ý ngược", "Chính spec §8 khuyên <b>đừng</b> xây KG khi quan hệ cố định và đơn giản. Đồ thị wikilink "
    "0-token hiện tại có thể đã là điểm dừng đúng — xem mục 06.")]),

 ("4.6", "Commit DAG Service", "gap",
  "Hub kiểu AgentHub: bare git repo + index + HTTP API + CLI với <code>push · fetch · log · children · leaves · "
  "lineage · diff</code>. Node commit mang: parent, agent, giả thuyết, diff, metric, runtime, memory, môi trường, "
  "trạng thái giữ/bỏ. Không cần nhánh main, không merge queue. Kèm message board append-only nối được với commit và claim.",
  [("Có thật", "<code>harness/scripts/provenance-log.py</code> — sổ sự kiện artifact-level, git-tracked, "
    "<b>hash-chain theo từng writer_id</b>, <code>.gitattributes merge=union</code> để nhiều writer merge được qua git. "
    "Ba hàm <code>append_event/read_events/correlate</code> là adapter DUY NHẤT, chừa sẵn slot đổi sang broker thật."),
   ("Gần đúng", "<code>llmwiki/wiki/log.md</code> append-only ≈ message board; "
    "<code>wiki/sources/ISSUES.md</code> là ledger issue travel theo repo; <code>ledger-snapshot.py</code> chụp trạng thái."),
   ("Thiếu", "Không có hub và không có bốn truy vấn cốt lõi <code>children / leaves / lineage / diff</code>. "
    "Quan trọng hơn: <b>không giữ nhiều lineage thí nghiệm sống song song</b> — overstack vẫn là một dòng công việc "
    "tuyến tính trên nhánh <code>orca</code>. Commit không mang metric/runtime/memory.")]),

 ("4.7", "Swarm Workflow Engine", "part",
  "Script điều phối sinh ra với primitive <code>spawn(role, payload)</code> và <code>gather(tasks, {concurrency})</code>. "
  "Context tươi cho mỗi sub-agent; trạng thái trung gian nằm trong biến script và artifact, không nằm trong transcript chung. "
  "Mặc định concurrency 16, trần cứng 1 000 worker. <b>Phải khai reducer TRƯỚC khi fan-out</b> — engine từ chối chạy nếu "
  "chưa có bước tổng hợp và hợp đồng bằng chứng. Sóng kiểm chứng phải khác prompt/bằng chứng/vai so với sóng sinh.",
  [("Có thật", "<code>harness/scripts/orca-dispatch.py</code> — giao việc cho CLI bất kỳ và <b>biết chắc lúc nó xong</b>. "
    "Sinh ra từ một phép đo thật ngày 2026-07-20: trên 59 task orchestration chỉ 13 (22%) từng được dispatch, "
    "46 (78%) chưa bao giờ được giao. <code>orca-reconcile.py</code> soát task treo."),
   ("Gần đúng", "Yêu cầu 'khai reducer trước fan-out' được R7 phủ một phần: proposal phải khai ai làm task nào "
    "trước khi fan-out, và <code>dispatch-verify.py</code> hậu kiểm sau đó. Context tươi mỗi sub-agent: có sẵn."),
   ("Thiếu", "overstack không sở hữu primitive <code>spawn/gather</code> — đang mượn runtime điều phối của vendor. "
    "Không có trần concurrency/worker của riêng mình, không bắt buộc sóng kiểm chứng phải khác vai với sóng sinh "
    "(rủi ro lỗi tương quan mà spec §9 nêu).")]),
]

# ── §5 budgets ───────────────────────────────────────────────────────────────
BUDGETS = [
    ("max tokens · max cost", "full", "<code>harness/scripts/token-budget.py</code> — đếm token bằng code, quy ra tiền "
     "theo <code>harness/cost-rates.json</code>, cap theo session và theo task, chế độ <code>warn|block</code>, có self-test"),
    ("max wall-clock", "full", "<code>budget_seconds</code> trong loop-runner (mặc định 900s), exit code 3 = TIMEOUT"),
    ("max retries", "full", "<code>max_iter</code> + <code>escalate_after_iter</code>, exit 2/5"),
    ("max model calls", "gap", "—"),
    ("max sub-agents · max concurrent workers", "gap", "— trần nằm ở runtime vendor, không ở overstack"),
    ("max tool calls", "gap", "—"),
    ("max graph writes", "gap", "—"),
    ("minimum evidence required", "part", "<code>capproof</code> trong <code>build-capabilities.py</code>: mỗi năng lực "
     "quảng cáo phải có NEO bằng chứng nguồn (209/209 hiện có neo)"),
    ("Protected path do execution plane ép, không nhờ prompt", "full", "Hook chặn thật ở PreToolUse; "
     "R14 <code>patterns_guard.py</code> khoá <code>llmwiki/patterns/</code>; <code>egress-guard.py</code> chặn Bash rò ra ngoài"),
    ("Chính sách leo thang cho người là bắt buộc", "full", "<code>escalate_after_iter</code> trong config, exit 5 = ESCALATE"),
    ("Cạn budget thì trả artifact tốt nhất + lý do dừng", "full", "run-log JSON của loop-runner + exit code phân biệt lý do"),
    ("Mọi thao tác graph huỷ là soft-delete", "part", "R13 giữ ADR bị đè; khoá xoá-vật-lý per-id của decision-anchoring; "
     "trang wiki thường vẫn xoá vật lý được"),
    ("Chặn metric-gaming bằng ràng buộc đa chiều", "part", "medic dò nhiều mặt (rules/docs/code/eval/fresh-install); "
     "nhưng loop-runner chưa có ràng buộc đa chiều vì chưa có metric"),
]

# ── §7 eval ──────────────────────────────────────────────────────────────────
EVALS = [
    ("Meta-loop: ratchet trên chính artifact của pipeline", "part",
     "<code>flywheel.py</code>, <code>success-flywheel.py</code>, <code>failure-flywheel.py</code> gom lỗi và thành công "
     "thành lớp rồi đề xuất rule/skill — nhưng không phải vòng tự động 'đổi một thứ → đo → giữ hoặc trả lại'"),
    ("Gold set extraction ≥100 tài liệu gán nhãn tay", "gap", "Không có tầng extraction nên không có gold set này"),
    ("Gold set resolution có ca đối kháng (alias không trùng chữ nào)", "gap", "Không có tầng resolution"),
    ("Gold set query đa hop, kèm đường edge kỳ vọng", "part",
     "30 golden trong <code>llmwiki/wiki/sources/evals/retrieval</code> (<code>retrieval-baseline.json</code>: 30/30 hit) "
     "+ 19 golden question promptfoo. Nhưng chỉ kiểm đáp án, không kiểm ĐƯỜNG đi trong graph"),
    ("Metric tầng Extraction / Resolution", "gap", "Không áp dụng — không có hai tầng đó"),
    ("Metric tầng Graph (component, mật độ, node cô lập)", "part",
     "<code>wiki-health.py</code> có orphan và broken link; chưa theo dõi xu hướng số thành phần liên thông"),
    ("Metric tầng Query (độ chính xác, đường trích dẫn hợp lệ, cỡ subgraph)", "part",
     "<code>retrieval-eval.py</code> đo hit và token; không đo tính hợp lệ của đường trích dẫn"),
    ("Metric tầng Workflow (thành công, chi phí mỗi lần thành công, wall-clock)", "part",
     "<code>dispatch-proof.json</code>, <code>cost-by-session.json</code>"),
    ("Metric tầng Operations (recovery, correction, retry)", "part",
     "<code>trace-grader.py</code> chấm retry storm và flaky; chưa tổng hợp thành chỉ số vận hành"),
    ("Giám sát production theo XU HƯỚNG, không theo điểm đơn lẻ", "full",
     "<code>wiki-health.csv</code> ghi theo thời gian, <code>sync-log.jsonl</code>, <code>medic --ci</code> chạy mỗi phiên "
     "qua hook Stop — hệ tự soi gương liên tục chứ không đợi người nhớ"),
]

# ── §10 acceptance ───────────────────────────────────────────────────────────
ACCEPT = [
    ("Objective khởi nguồn", "part", "Draft SPEC trong <code>wiki/sources/draft/</code> — có, nhưng không phải output nào cũng gắn một objective ID"),
    ("Bước plan tương ứng", "part", "<code>*-PLAN.md</code> (R18) — markdown, không có step ID máy đọc"),
    ("Phiên bản artifact", "part", "Commit git + ô <code>Origin → Commit</code>; ô này do <code>/verify-before-commit</code> điền"),
    ("Nguồn hỗ trợ", "full", "R2 <code>## Origin</code> — chặn cứng ở cả hook lẫn pre-commit"),
    ("Đường trong graph kèm edge ID", "gap", "Đồ thị wiki không phát edge ID ổn định để trích dẫn"),
    ("Quyết định của evaluator kèm rubric", "part", "<code>eval-baseline.json</code> theo bộ eval, không theo từng output"),
    ("Bản ghi thực thi có biên (chi phí, độ trễ, retry)", "part", "<code>cost-by-session.json</code> + run-log loop-runner; chưa gắn vào từng output"),
    ("Không phụ thuộc transcript chat", "full", "Đúng thiết kế gốc: R4 sinh log bằng máy, provenance-log hash-chain, "
     "audit.jsonl — không chỗ nào cần đọc lại transcript"),
]

# ── §6 vượt spec ─────────────────────────────────────────────────────────────
BEYOND = [
    ("Chặn TRƯỚC hành động, 0 token, agent không phủ quyết được",
     "Spec kiểm tính hợp lệ chủ yếu ở lúc ghi graph. overstack chặn ở PreToolUse — file sai không kịp tồn tại. "
     "18 rule khai trong <code>policy.yaml</code>, 15 validator Python thuần."),
    ("Fire-drill: chứng minh cơ chế phòng thủ CÒN sống",
     "<code>fdk/tools/medic.py</code> cố tình vi phạm rồi xác nhận bị chặn. Spec không có khái niệm 'chứng minh "
     "guardrail chưa chết' — nó giả định validator đã cài là còn chạy."),
    ("Nguyên tắc 'tồn tại ≠ dùng được'",
     "<code>dep-health.py</code> mở DB và kiểm bảng <code>symbols</code> thay vì kiểm entry config. Sinh ra sau khi "
     "code-graph MCP hỏng nhiều tuần mà mọi phiên vẫn bị lùa vào dùng. Rủi ro này không có trong §9 của spec."),
    ("Chống drift nhiều bản của cùng một artifact",
     "Mỗi skill tồn tại ba nơi (canonical, mirror, bản cài); <code>sync-skills.py</code> + job CI bắt lệch. "
     "Spec chỉ nói immutable store, không nói tới bài toán nhiều bản."),
    ("Tài liệu sinh bằng code, có bằng chứng cho từng năng lực",
     "<code>build-capabilities.py</code> đếm từ đĩa; <code>capproof</code> đòi mỗi năng lực quảng cáo phải có neo nguồn. "
     "Bảng năng lực không thể nói dối."),
    ("Cổng chống ảo giác trích dẫn",
     "<code>claim-receipts.py</code> rút mọi đường dẫn agent CITE rồi kiểm có resolve thật trên đĩa không — "
     "biến lớp lỗi 'hallucination' từ hậu kiểm thành cổng trước commit."),
    ("Hạ tầng bằng không",
     "Spec v1 cần Postgres, S3, Docker, FastAPI. overstack cài bằng một dòng curl, chạy trên git + Python thuần + "
     "hook của vendor. Đổi lại: không có store thường trú, không cách ly môi trường chạy."),
]

# ── tally ────────────────────────────────────────────────────────────────────
allv = ([p[3] for p in PLANES] + [n[1] for n in NODES] + [e[1] for e in EDGES] +
        [i[1] for i in INVARIANTS] + [c[2] for c in COMPONENTS] +
        [b[1] for b in BUDGETS] + [e[1] for e in EVALS] + [a[1] for a in ACCEPT])
T = Counter(allv)
TOTAL = sum(T.values())
pct = lambda k: round(100.0 * T[k] / TOTAL)

# ═══════════════ render helpers ═══════════════
def sec_open(i):
    t, sub = SECTIONS[i]
    return ('<section id="sec-%d" class="section-bg s-bg%d"><div class="section-header">'
            '<span class="tag">%02d · %s</span><h2>%s</h2><p>%s</p></div>'
            % (i, i, i + 1, E(t.upper()), E(t), E(sub)))

def vtable(rows, headers, wide=2):
    th = "".join("<th>%s</th>" % E(h) for h in headers)
    tr = ""
    for r in rows:
        tds = "<td><b>%s</b></td><td>%s</td>" % (r[0], badge(r[1]))
        for extra in r[2:]:
            tds += "<td>%s</td>" % extra
        tr += "<tr>%s</tr>" % tds
    return '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, tr)

def card(title, body):
    return '<div class="card"><h4>%s</h4>%s</div>' % (title, body)

def ul(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)

# ═══════════════ diagram: hai nền ═══════════════
def diagram_stacks():
    s = ['<svg viewBox="0 0 900 300" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Spec dựng một platform năm mặt phẳng trên Postgres/S3/Docker; overstack dựng cùng năm trách nhiệm '
         'trên git, file và hook của vendor</title>', S.defs()]
    s.append('<text x="150" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="#5856d6">SPEC v0.1 — platform</text>')
    s.append('<text x="640" y="18" text-anchor="middle" font-size="11" font-weight="700" fill="#0a84ff">overstack — harness</text>')
    rows = [("Control · FastAPI", "Skill + Orca dispatch", "#5856d6"),
            ("Execution · Docker", "git worktree (không container)", "#30b0c7"),
            ("Artifact · S3 + Postgres", "file trong git + MANIFEST", "#ff9500"),
            ("Graph · Postgres/NetworkX", "wiki-graph in-memory, 0 token", "#34c759"),
            ("Evaluation · harness", "promptfoo · wikieval · trace-grader", "#0a84ff")]
    y = 36
    for left, right, c in rows:
        s.append(S.node(20, y, 260, 40, left, c))
        s.append(S.node(500, y, 280, 40, right, c))
        s.append(S.line(282, y + 20, 498, y + 20, c, "ar%d" % (rows.index((left, right, c)) % 6)))
        y += 50
    s.append(S.node(320, 120, 140, 44, "cùng 5 trách nhiệm", "#ff2d55", "khác nền tảng"))
    s.append("</svg>")
    return "".join(s)

def diagram_trace():
    s = ['<svg viewBox="0 0 900 220" xmlns="http://www.w3.org/2000/svg" role="img">',
         '<title>Chuỗi truy vết bắt buộc của spec §1.4 và chỗ overstack đứt: edge ID</title>', S.defs()]
    chain = [("objective", "draft SPEC", "#34c759"), ("plan", "PLAN.md", "#34c759"),
             ("artifact", "commit git", "#34c759"), ("source", "## Origin (R2)", "#34c759"),
             ("graph path", "KHÔNG có edge ID", "#ff2d55"), ("evaluation", "baseline theo suite", "#ff9500"),
             ("execution", "cost + run-log", "#ff9500")]
    x = 12
    for i, (a, b, c) in enumerate(chain):
        s.append(S.node(x, 80, 108, 46, a, c, b))
        if i:
            s.append(S.line(x - 16, 103, x - 2, 103, "#0a84ff", "ar0"))
        x += 124
    s.append("</svg>")
    return "".join(s)

def dbox(svg):
    return '<div class="diagram-box">%s</div>' % svg

# ═══════════════ sections ═══════════════
s0 = sec_open(0) + """
<div class="card" style="margin-bottom:14px">
<p><b style="color:var(--ink)">Kết luận ngắn:</b> spec và overstack theo đuổi <i>cùng một bất biến</i> —
mọi output quan trọng phải truy được về objective, plan, artifact, nguồn, đường trong graph, quyết định của
evaluator, và bản ghi thực thi có biên — nhưng dựng nó trên hai nền hoàn toàn khác nhau. Spec mô tả một
<b>platform</b>: FastAPI, Postgres, S3, Docker worker, một service commit-DAG. overstack là một
<b>lớp khung không hạ tầng</b>: git, file markdown, hook của vendor, Python thuần, cài bằng một dòng curl.</p>
<p style="margin-top:10px">Đếm sòng phẳng: <b>15/67 mục thiếu hẳn</b>, 36 mục có một phần. Nhưng 15 chỗ thiếu đó
không rải rác — chúng quy về đúng <b>ba nguyên nhân gốc</b>: (1) <b>không có ratchet theo điểm số</b> §4.1 —
vòng lặp dừng đúng lúc nhưng chưa giữ-cái-tốt-vứt-cái-tệ; (2) <b>cạnh đồ thị vô danh, không có edge ID</b>
§4.5 — kéo theo 5 loại cạnh, node Claim, và mắt xích 5 của bài nghiệm thu §10; (3) <b>không có dịch vụ
commit-DAG</b> §4.6 — nên không giữ được nhiều lineage thí nghiệm sống song song. Sửa ba gốc đó thì phần lớn
15 mục kia tự đóng.</p>
<p style="margin-top:10px">Phần "một phần" thì ngược lại: đa số là <i>chọn nền khác</i> chứ không phải làm dở —
artifact nằm trong git thay vì S3, execution là worktree thay vì container, graph dựng lại trong bộ nhớ thay vì
trú trong Postgres.</p></div>
<div class="grid g4" style="margin-bottom:14px">""" + "".join(
    '<div class="card stat"><b style="color:%s">%d%%</b><span>%s %s</span></div>' % (V[k][2], pct(k), V[k][0], V[k][1])
    for k in ("full", "part", "gap", "diff")) + """</div>
<p style="font-size:11.5px;color:var(--ink2);margin-bottom:14px">Tỷ lệ trên %d mục đối chiếu: 5 mặt phẳng ·
9 loại node · 11 loại cạnh · 4 bất biến ghi · 7 cấu phần · 13 hạng mục budget/rails · 10 hạng mục eval ·
8 điều kiện nghiệm thu.</p>
""" % TOTAL + dbox(diagram_stacks()) + """
<div class="grid g2">""" + card("Ba câu hỏi spec trả lời tốt hơn", ul([
    "<b>Giữ nhiều lineage thí nghiệm sống cùng lúc</b> — overstack chỉ có một dòng công việc tuyến tính",
    "<b>Đồ thị có confidence và mâu thuẫn tường minh</b> — wiki hiện coi mọi trang là đúng ngang nhau",
    "<b>Hợp đồng bàn giao có schema</b> — overstack bàn giao bằng markdown, reviewer nói 'ổn' vẫn hợp lệ",
])) + card("Ba câu hỏi overstack trả lời tốt hơn", ul([
    "<b>Luật có còn cắn không</b> — fire-drill của <code>medic.py</code>, spec không đặt câu hỏi này",
    "<b>Năng lực khai báo có dùng được thật không</b> — <code>dep-health.py</code> thăm dò, không kiểm tồn tại",
    "<b>Agent trích dẫn file có thật không</b> — <code>claim-receipts.py</code> chặn ảo giác trước commit",
])) + "</section>"

s1 = sec_open(1) + """
<div class="card"><p>Spec §2 tách năm mặt phẳng và cấm mặt này nuốt trách nhiệm mặt kia — đặc biệt:
<i>một transcript chat không bao giờ được trở thành cơ sở dữ liệu, workflow engine hay audit log</i>.
overstack tuân thủ nguyên tắc đó rất chặt (log sinh bằng máy, R4), nhưng hiện thực từng mặt bằng
vật liệu khác.</p></div>
<div class="table-wrap"><table><thead><tr><th>Mặt phẳng</th><th>Spec v1</th><th>overstack</th>
<th>Phán quyết</th></tr></thead><tbody>""" + "".join(
    '<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (E(n), E(sp), ov, badge(v))
    for n, sp, ov, v, _ in PLANES) + """</tbody></table></div>
<div class="grid g2" style="margin-top:14px">""" + "".join(
    card(n, "<p>%s</p>" % note) for n, sp, ov, v, note in PLANES[:2]) + "</div>" + """
<div class="grid g3" style="margin-top:14px">""" + "".join(
    card(n, "<p>%s</p>" % note) for n, sp, ov, v, note in PLANES[2:]) + "</div></section>"

s2 = sec_open(2) + """
<div class="card"><p>Spec §2.1 dứt khoát: <b>hai đồ thị không bao giờ được gộp</b>. Commit DAG trả lời
"cái gì đã đổi, nhánh nào đẻ ra từ nhánh nào, lineage nào còn sống". Knowledge graph trả lời "cái gì tồn tại,
liên hệ ra sao, gì chống lưng, gì mâu thuẫn". overstack có đồ thị tri thức (wiki) và có lịch sử git, nhưng
<b>chưa nối hai thứ đó bằng cạnh liên kết</b> — không có <code>(agent_run) -PRODUCED-&gt; (claim) -MODIFIED-&gt;
(commit)</code>.</p></div>
<div class="grid g2" style="margin-top:14px;align-items:start">
<div><h4 style="font-size:12px;margin-bottom:6px">9 loại node của spec</h4>""" + vtable(
    NODES, ["Node", "Phán quyết", "overstack có gì"]) + """</div>
<div><h4 style="font-size:12px;margin-bottom:6px">11 loại cạnh của spec</h4>""" + vtable(
    EDGES, ["Cạnh", "Phán quyết", "overstack có gì"]) + """
<p style="font-size:11.5px;color:var(--ink2);margin-top:8px">Cạnh <code>[[wikilink]]</code> chiếm đa số và
<b>không mang type</b> — đó là lý do phần lớn hàng trên là 🟡 hoặc 🔴. Thêm type cho cạnh là thay đổi rẻ nhất
có tác động lớn nhất ở mục này.</p></div></div>
<h4 style="font-size:12px;margin:20px 0 6px">Bốn bất biến ghi (§3.4 — spec bắt hard-fail)</h4>
<div class="grid g2">""" + "".join(
    card("%s %s" % (V[v][0], t), "<p>%s</p>" % note) for t, v, note in INVARIANTS) + """</div>
<div class="card" style="margin-top:14px"><h4>§3.5 — hợp nhất thực thể (entity resolution)</h4>
<p>%s <b>Thiếu hẳn.</b> Spec đòi mỗi thực thể canonical giữ <code>aliases[]</code>,
<code>source_docs[]</code>, <code>resolution_rationale</code>, <code>confidence</code>, <code>merge_run_id</code>,
và một lần gộp phải <b>đảo ngược được không cần chạy lại pipeline</b>. overstack không có tầng này; thứ gần nhất là
<code>harness/validators/duplicate_basename.py</code> — nhưng nó <i>chặn trùng slug</i> chứ không <i>hợp nhất</i>
hai trang nói về cùng một thứ.</p></div></section>""" % badge("gap")

def comp_pane(i, c):
    num, name, verdict, spec_says, blocks = c
    # h là HTML do chính file này soạn (có thể chứa <code>) — KHÔNG escape, escape sẽ hiện literal thẻ
    bs = "".join('<div class="card" style="margin-bottom:10px"><h4>%s</h4><p>%s</p></div>' % (h, b)
                 for h, b in blocks)
    return ('<div class="md-pane%s" data-p="%d"><h3>§%s %s %s</h3>'
            '<div class="card" style="margin-bottom:12px;border-left:3px solid var(--border)">'
            '<h4>Spec đòi gì</h4><p>%s</p></div>%s</div>'
            % (" on" if i == 0 else "", i, E(num), E(name), badge(verdict), spec_says, bs))

citems = "".join('<li role="option" data-i="%d" aria-selected="%s"><span class="mt">§%s %s</span>'
                 '<span class="ms">%s %s</span></li>'
                 % (i, "true" if i == 0 else "false", E(c[0]), E(c[1]), V[c[2]][0], V[c[2]][1])
                 for i, c in enumerate(COMPONENTS))
s3 = sec_open(3) + """
<div class="card"><p>Bảy cấu phần của spec §4, mỗi cái đối chiếu ba lớp: <b>spec đòi gì</b> ·
<b>overstack có gì (kèm file thật)</b> · <b>thiếu gì</b>. Bấm một mục bên trái để xem chi tiết.</p></div>
<div class="md-wrap"><ul class="md-list" role="listbox" data-md="comp">""" + citems + """</ul>
<div class="md-detail" data-mdp="comp">""" + "".join(
    comp_pane(i, c) for i, c in enumerate(COMPONENTS)) + "</div></div></section>"

s4 = sec_open(4) + """
<div class="card"><p>Spec §5 đòi <b>mọi lần chạy khai trước 10 hạn mức cứng</b>, và khi cạn thì trả về
artifact tốt nhất cộng lý do dừng — "câu trả lời trôi chảy che giấu thất bại một phần" được xếp là một
lớp lỗi phải theo dõi. overstack có ba hạn mức mạnh (token/tiền, wall-clock, retry) và bốn hạn mức
chưa có.</p></div>""" + vtable(BUDGETS, ["Hạng mục §5", "Phán quyết", "overstack"]) + """
<h4 style="font-size:12px;margin:20px 0 6px">§7 — Bộ đánh giá</h4>
<div class="card" style="margin-bottom:12px"><p>Đây là mặt overstack mạnh nhất so với spec ở khâu
<b>vận hành</b> (medic chạy mỗi phiên qua hook Stop, baseline có sàn chặn CI), và yếu nhất ở khâu
<b>gold set</b> — vì hai tầng extraction/resolution mà spec muốn đo thì overstack không có.</p></div>
""" + vtable(EVALS, ["Hạng mục §7", "Phán quyết", "overstack"]) + "</section>"

s5 = sec_open(5) + """
<div class="card"><p><b>Bài kiểm nghiệm thu §10:</b> lấy ngẫu nhiên một output quan trọng, auditor phải
truy được bảy thứ <i>mà không đọc một dòng transcript nào</i>. overstack qua được điều kiện khó nhất
(không phụ thuộc transcript) nhưng đứt ở mắt xích thứ năm.</p></div>
""" + dbox(diagram_trace()) + vtable(ACCEPT, ["Cần truy được", "Phán quyết", "overstack"]) + """
<h4 style="font-size:12px;margin:22px 0 8px">Việc nên làm, xếp theo giá trị trên công bỏ ra</h4>
<div class="grid g3">""" + card("P1 — rẻ, mở khoá nhiều thứ", ul([
    "<b>Edge ID ổn định</b> cho <code>wiki-graph.py</code> / <code>build-wiki-graph.py</code>, và bắt câu trả lời "
    "trích edge ID → mở khoá mắt xích 5 của §10",
    "<b>Type cho cạnh wiki</b> (supports / contradicts / supersedes / depends-on) — hiện <code>[[wikilink]]</code> "
    "vô danh, thêm type là đổi rẻ nhất mà tác động lớn nhất",
    "<b>Ratchet theo điểm số</b> cho <code>loop-runner.py</code>: nhận metric + chiều, revert bằng "
    "<code>git reset</code>, ghi <code>Trial{commit, score, status}</code>",
])) + card("P2 — vừa sức, đóng nốt §5 và §4.4", ul([
    "Thêm bốn hạn mức còn thiếu vào <code>token-budget.py</code>: model calls, sub-agents, concurrent workers, graph writes",
    "Hợp đồng review có schema: reviewer phải trả <code>{criterion_id, location, defect, severity}</code>, "
    "'nhìn ổn' thành không hợp lệ — sửa ở <code>/qc-code</code> và <code>council.py</code>",
    "Soft-delete cho trang wiki (chỉ SUPERSEDES), không xoá vật lý",
    "Plan JSON song song với PLAN.md + validator DAG (phụ thuộc treo, chu trình) trong <code>spec-gate.py</code>",
])) + card("P3 — cân nhắc kỹ, có thể ĐỪNG", ul([
    "<b>Commit-DAG hub</b> (children / leaves / lineage): chỉ đáng làm nếu thật sự cần giữ nhiều lineage thí nghiệm "
    "sống song song. Hiện overstack làm việc tuyến tính trên một nhánh và chưa thấy đau",
    "<b>Pipeline extraction/resolution bằng LLM</b>: chính spec §8 khuyên <b>đừng</b> xây KG khi quan hệ cố định "
    "và đơn giản, hoặc khi sai số extraction lớn hơn giá trị traversal. Đồ thị wikilink 0-token hiện tại "
    "có thể đã là điểm dừng đúng",
    "<b>Container hoá execution plane</b>: đổi lại là mất tính 'cài một dòng curl' — vốn là lý do overstack travel được",
])) + """</div>
<div class="card" style="margin-top:14px"><h4>Câu hỏi quyết định trước khi làm bất cứ mục nào ở trên (§8)</h4>
<ul class="checklist">
<li><input type="checkbox" id="q1"><label for="q1">Thành công có <b>verify</b> được không? Không → chưa được tự trị, phải có test/rubric/cổng người trước</label></li>
<li><input type="checkbox" id="q2"><label for="q2">Các bước có <b>ổn định</b> không? Có → dùng chuỗi tĩnh, đừng gọi planner</label></li>
<li><input type="checkbox" id="q3"><label for="q3">Các subtask có <b>độc lập</b> không? Không → mô hình hoá phụ thuộc, hạn chế ghi song song</label></li>
<li><input type="checkbox" id="q4"><label for="q4">Có cần giữ <b>nhiều lineage</b> sống cùng lúc không? Có → mới cần commit DAG</label></li>
<li><input type="checkbox" id="q5"><label for="q5">Sự thật có cần <b>sống sót qua lần chạy</b> không? Có → persist artifact + graph, đừng dựa tóm tắt transcript</label></li>
<li><input type="checkbox" id="q6"><label for="q6">Chi phí và độ trễ có <b>chịu được</b> không? Đặt budget TRƯỚC khi thêm worker</label></li>
</ul></div></section>"""

s6 = sec_open(6) + """
<div class="card"><p>Đối chiếu hai chiều mới công bằng. Bảy điều dưới đây overstack đã làm và spec
<b>không nhắc tới</b> — phần lớn sinh ra từ những lần trả giá thật, ghi trong
<code>llmwiki/wiki/log.md</code> và <code>fdk/wiki/</code>.</p></div>
<div class="grid g2">""" + "".join(
    card("%s %s" % (V["plus"][0], t), "<p>%s</p>" % b) for t, b in BEYOND) + """</div>
<div class="card" style="margin-top:14px"><h4>Đọc ngược: rủi ro spec nêu mà overstack chưa có phòng bị</h4>
""" + ul([
    "<b>Lỗi tương quan giữa các worker song song</b> — spec bắt sóng kiểm chứng phải khác prompt/bằng chứng/vai. "
    "overstack dispatch nhiều agent nhưng không ép điều này.",
    "<b>Hợp nhất thực thể sai làm hỏng traversal</b> — chưa áp dụng vì chưa có resolution, nhưng nếu làm P3 thì "
    "phải kèm chỉ số false-merge ngay từ đầu.",
    "<b>Phân mảnh làm hỏng việc cần mạch liền</b> (kiến trúc, refactor xoắn nhau) — spec nói rõ giữ những việc đó "
    "trong một context. overstack có <code>/wayfinder</code> cho việc lớn mù mờ nhưng chưa có luật cấm fan-out loại này.",
    "<b>Nổ chi phí khi chạy swarm lớn</b> — <code>token-budget.py</code> mới cap theo session, chưa cap theo swarm.",
]) + "</div></section>"

# ═══════════════ shell ═══════════════
navlinks = "".join(
    '<a href="#sec-%d"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>%s</a>'
    % (i, S.IC[i % len(S.IC)], E(SECTIONS[i][0])) for i in range(len(SECTIONS)))

EXTRA_CSS = """
.vb{display:inline-block;font-size:10px;font-weight:700;padding:1.5px 8px;border-radius:999px;white-space:nowrap}
.v-full{background:rgba(52,199,89,.14);color:#28a745}
.v-part{background:rgba(255,149,0,.15);color:#c26a00}
.v-gap{background:rgba(255,45,85,.12);color:#e0264b}
.v-diff{background:rgba(88,86,214,.12);color:#5856d6}
.v-plus{background:rgba(10,132,255,.12);color:#0a84ff}
.md-pane h3{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
"""

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>overstack ↔ Graph Engineering Spec v0.1</title>
<meta name="description" content="Đối chiếu overstack với graph-engineering-implementation-spec v0.1: năm mặt phẳng, hai đồ thị, bảy cấu phần, budget, eval và bài nghiệm thu truy vết.">
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%235856d6'/%3E%3C/svg%3E">
<script>(function(){try{var t=localStorage.getItem("osrcmap-theme");
if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}})();</script>
<style>__CSS__</style>
</head>
<body>
<a class="skip-link" href="#main">Bỏ qua điều hướng</a>
<nav>
  <div class="brand"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">__BRAND__</svg></span>
    <span><span class="logo-t">so sánh</span><br><span class="logo-s">overstack ↔ spec v0.1</span></span></div>
  __NAV__
</nav>
<main id="main">
<div class="hero">
  <span class="eyebrow">graph-engineering-implementation-spec v0.1 · overstack @ 9032ae4</span>
  <h1>Hệ hiện tại đối chiếu bản spec</h1>
  <p class="lead">Spec dựng một <b>platform</b> năm mặt phẳng trên FastAPI, Postgres, S3 và Docker.
  overstack là một <b>lớp khung không hạ tầng</b> trên git, file và hook của vendor. Cùng một bất biến
  truy vết, hai nền khác nhau. Đối chiếu 67 mục: 15 thiếu hẳn, 36 có một phần — và 15 chỗ thiếu đó
  quy về đúng ba nguyên nhân gốc.</p>
  <div class="meta"><span>__TOTAL__ mục đối chiếu</span><span>✅ __PFULL__%</span><span>🟡 __PPART__%</span>
  <span>🔴 __PGAP__%</span><span>◆ __PDIFF__%</span><span>7 cấu phần §4</span></div>
</div>
__SECS__
<footer>
  <p>Nguồn spec: <code>~/Downloads/graph-engineering-implementation-spec.md</code> v0.1 (306 dòng).
  Nguồn hệ hiện tại: đọc thẳng <code>harness/scripts/</code>, <code>fdk/tools/</code>,
  <code>harness/policy.yaml</code>, <code>harness/metrics/</code> tại commit <code>9032ae4</code> —
  mọi tên file trên trang đều tồn tại thật trên đĩa.</p>
  <p style="margin-top:6px">Trang liên quan: <code>llmwiki/html/290726-overstack-source-map.html</code>
  (bản đồ mã nguồn) · <code>llmwiki/html/onboarding-setup.html</code> (guided tour) ·
  <code>llmwiki/html/wiki-graph.html</code> (vector concept↔code).</p>
</footer>
</main>
<script>__JS__</script>
</body>
</html>"""

out = (HTML.replace("__CSS__", S.CSS_BASE + S.section_css() + S.dark_css() + EXTRA_CSS)
           .replace("__BRAND__", S.BRAND)
           .replace("__NAV__", navlinks)
           .replace("__TOTAL__", str(TOTAL))
           .replace("__PFULL__", str(pct("full"))).replace("__PPART__", str(pct("part")))
           .replace("__PGAP__", str(pct("gap"))).replace("__PDIFF__", str(pct("diff")))
           .replace("__SECS__", s0 + s1 + s2 + s3 + s4 + s5 + s6)
           .replace("__JS__", S.JS))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(out)
for tok in ("__CSS__", "__NAV__", "__SECS__", "__JS__", "__BRAND__", "__TOTAL__",
            "__PFULL__", "__PPART__", "__PGAP__", "__PDIFF__"):
    assert tok not in out, "token còn sót: " + tok
ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', out)
print("✅", OUT, len(out), "bytes")
print("external refs:", ext or "none ✅", "| sections:", out.count('<section id="sec-'))
print("tally:", dict(T), "| total:", TOTAL)
