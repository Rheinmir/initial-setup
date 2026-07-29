#!/usr/bin/env python3
"""STEP A fallback (Claude main thread): assemble ONBOARD_JSON theo schema skeleton v2.
Nội dung do Claude soạn từ ONBOARDING.md + domain-graph.json; churn/hot lấy từ knowledge-graph.json."""
import json, os, sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
G = json.load(open(os.path.join(ROOT, ".understand-anything/knowledge-graph.json")))
churn = {n["filePath"]: n.get("churn", 0) for n in G["nodes"]}
assert os.path.isfile(os.path.join(ROOT, ".orca-onboard/intermediate/domain-graph.json"))

def hot(p):  # 'hot' = top-churn (>=14 chạm/365 ngày), cùng ngưỡng Phase 1
    return churn.get(p, 0) >= 14

TOUR = [
    ("Ba trụ — đọc README trước", "README.md", 1,
     "Cửa vào cho người mới. Giải thích overstack là lớp khung đặt LÊN dự án, không phải thư viện import.",
     ["người mới clone repo"], ["hiểu 3 trụ: llmwiki · harness · skills"],
     "overstack biến AI agent thành cộng sự tự-kỷ-luật. Ba trụ: llmwiki/ là trí nhớ dài hạn, harness/ là "
     "guardrail tất định chạy 0 token, skills/ là 84 quy trình đóng gói gọi bằng /<tên>. Điểm khác biệt so "
     "với 'prompt cho giỏi': kỷ luật được cài bằng code chạy trước và sau mỗi hành động, agent không có "
     "quyền phủ quyết. Nhánh làm việc và phát hành đều là orca, không phải main."),

    ("Một dòng cài — bootstrap kéo cả ba trụ", "harness/poc-vendor-neutral/bootstrap.sh", 33,
     "Bề mặt tiếp xúc duy nhất với người dùng mới: curl | bash trong thư mục dự án đích.",
     ["curl từ raw.githubusercontent nhánh orca"], ["harness per-project", "skills global", "khung llmwiki"],
     "Dòng lệnh này cài hoặc update CẢ BA trụ rồi in bảng trạng thái. Cờ --harness-only bỏ skills và "
     "llmwiki; --clean gỡ cũ rồi cài mới; --vendor ép vendor thay vì tự dò. Phạm vi khác nhau và hay bị "
     "nhầm: harness + llmwiki cài per-project, skills cài GLOBAL vào ~/.claude/skills. Một hiểu lầm nữa "
     "được tài liệu nhắc nhiều lần — harness là HOOK chứ không phải MCP, cài xong không thấy trong /mcp "
     "là đúng, phải kiểm bằng /hooks."),

    ("policy.yaml — luật là dữ liệu, không phải code", "harness/policy.yaml", 6,
     "Nguồn chân lý duy nhất: 18 rule khai báo bằng YAML, không phụ thuộc vendor nào.",
     ["yêu cầu kỷ luật mới"], ["rule entry + validator tương ứng"],
     "R1 no-write-raw, R2 origin-required, R3 index-sync, R4 log-append, R5 folder-structure, R6 "
     "verify-before-commit, R7 proposal-complete, R9 okf-frontmatter, R13 decision-to-adr, R15 "
     "no-ai-attribution, R18 plan-executable… Thêm luật nghĩa là thêm một entry ở đây rồi nối validator, "
     "chứ không rải if khắp hook. Vì luật là dữ liệu, cùng một policy cắn được ở Claude Code, ở opencode "
     "và ở CI mà không viết lại ba lần."),

    ("Lõi thực thi — một CLI đọc policy rồi phán", "harness/poc-vendor-neutral/bin/llmwiki-validate.py", 203,
     "apply_rule(): khớp từng rule với (path, content, command) và trả verdict allow/deny.",
     ["payload hook từ vendor bất kỳ"], ["verdict allow / deny + stderr viết cho agent đọc"],
     "Đây là câu trả lời kiến trúc quan trọng nhất của repo: logic chặn KHÔNG nằm trong MCP, cũng KHÔNG "
     "nhúng vào một vendor — nó là một CLI lõi đọc policy.yaml, mỗi vendor chỉ là caller mỏng gọi vào. "
     "mode_claude_hook() ở dòng 229 nhận payload hook, load_policy() ở dòng 60 nạp luật, rồi từng hàm "
     "check_* thi hành. Thông điệp lỗi được viết để AGENT đọc và tự sửa, không phải để người debug — đó "
     "là lý do harness hoạt động mà không cần ai ngồi canh."),

    ("15 validator — mỗi luật một file, chạy 0 token", "harness/validators/no_write_raw.py", 1,
     "Validator Python thuần, không LLM, không token, không thể bị thuyết phục.",
     ["đường dẫn + nội dung sắp ghi"], ["exit code 0 hoặc 2"],
     "no_write_raw chặn ghi vào llmwiki/raw/; origin_required ép mọi trang wiki có '## Origin'; index_sync "
     "bắt index.md khớp đĩa; folder_structure chặn phát minh thư mục mới; decision_adr ép quyết định kiến "
     "trúc phải trỏ một ADR; agent_claude_parity giữ bảng skill trong AGENT.md khớp CLAUDE.md; "
     "travel_policy_sync canh việc fdk/ không được travel xuống dự án con. Không LLM nào được quyền phủ "
     "quyết những file này."),

    ("Dây cắm vendor — hook Claude Code, fail-open", "llmwiki/.claude/hooks/pre_tool_use.py", 73,
     "Adapter mỏng nối event của vendor vào lõi. Chặn TRƯỚC khi Write/Edit/Bash xảy ra.",
     ["event JSON qua stdin"], ["cho phép, hoặc chặn + ghi 'luật đã cắn' vào metrics"],
     "Năm hook được đăng ký: PreToolUse chặn sớm nhất, PostToolUse ghi audit.jsonl và sinh log.md, Stop "
     "chặn kết thúc lượt nếu index.md lệch, SessionStart in trạng thái và drift, UserPromptSubmit nhắc "
     "sinh docs. Với Bash còn chạy egress-guard trước để chặn rò dữ liệu ra ngoài (vừa nối thật ngày "
     "27/07). Mọi hook FAIL-OPEN: lỗi hạ tầng thì exit 0 và ghi cảnh báo — guardrail hỏng thầm lặng vẫn "
     "tốt hơn guardrail làm agent không dùng được."),

    ("Trụ tri thức — llmwiki/wiki là bộ nhớ dài hạn", "llmwiki/wiki/index.md", 1,
     "concepts / entities / sources / adr / draft, cộng index.md (R3) và log.md (R4).",
     ["tri thức học được trong phiên"], ["trang wiki có Origin + row trong index"],
     "Agent QUERY wiki trước khi grep code — đó là lý do context không rot qua nhiều phiên. index.md là "
     "mục lục bắt buộc khớp đĩa: Stop hook tự thêm row cho file mới (self-heal), còn chiều ngược lại "
     "(xoá file mà còn row) thì chặn cứng. log.md là nhật ký append-only sinh bằng máy từ audit, không "
     "nhờ model tự nhớ — nên nó là file nóng nhất repo với 166 lần chạm, và đó là bình thường chứ không "
     "phải mùi xấu."),

    ("Trụ kỹ năng — canonical rồi mirror", "harness/scripts/sync-skills.py", 69,
     "pairs(): ghép skills/<tên>/SKILL.md ↔ llmwiki/skills/<loop>/<tên>.md.",
     ["SKILL.md canonical"], ["mirror trong llmwiki/skills/", "bản cài ~/.claude/skills"],
     "Mỗi skill tồn tại ở BA nơi: canonical trong skills/, mirror trong llmwiki/skills/ để đi kèm khuôn "
     "wiki, và bản cài global do npx skills add đặt vào ~/.claude/skills. Đây là nguồn drift thường trực "
     "— phân tích co-change tìm được 115 cặp file luôn đổi cùng nhau, phần lớn chính là cặp "
     "canonical↔mirror. CI có job riêng bắt mirror-drift. Trước khi kết luận 'skill này vá rồi', kiểm cả "
     "ba bản."),

    ("Vòng hằng ngày — propose → gate → dispatch", "skills/orca-workflow/SKILL.md", 1,
     "Quy trình chủ đạo, và cũng là file skill được sửa nhiều nhất (32 lần chạm).",
     ["một yêu cầu tính năng"], ["draft đã duyệt → PLAN → agent chạy → wiki thật + commit"],
     "/propose viết draft rồi DỪNG chờ người duyệt. Người gật thì /plan mở thành brief thi hành được — "
     "đường dẫn chính xác, bước 2-5 phút, khối Interfaces khai chữ ký cho task hàng xóm, để một agent CLI "
     "rẻ chạy headless không hỏi lại được vẫn làm đúng. Rồi dispatch song song qua Orca worktree. Cuối "
     "cùng /verify-before-commit chạy typecheck + lint + smoke, promote draft thành wiki thật, điền "
     "Origin.Commit, rồi mới mở cổng commit. Human-in-the-loop nằm ở CỔNG, không nằm ở lời nhắc — agent "
     "không thể 'quên hỏi' vì skill dừng bằng cấu trúc."),

    ("FDK — đồ nghề làm chính framework", "fdk/tools/build-capabilities.py", 273,
     "build(): đếm skill/rule/tool THẲNG từ đĩa rồi sinh CAPABILITIES.md.",
     ["cây skills/, policy.yaml, fdk/tools/"], ["fdk/CAPABILITIES.md — 84 skill · 18 rule · 19 tool"],
     "fdk/ là dev-kit của người làm framework và KHÔNG travel xuống dự án con (ADR-004/008) — có validator "
     "canh luật này. capproof() ở dòng 215 làm một việc đáng học: mỗi năng lực được quảng cáo phải có "
     "BẰNG CHỨNG nguồn, không được khai suông. CAPABILITIES.md mở đầu bằng dòng 'SINH BẰNG CODE — ĐỪNG "
     "sửa tay', nên bảng năng lực không thể lệch thực tế."),

    ("Docs sinh bằng code — không thể nói dối", "fdk/tools/build-overstack-docs.py", 82,
     "rules(): đọc thẳng policy.yaml để dựng bảng rule trong tài liệu.",
     ["skills/ + policy.yaml + fdk/tools/"], ["llmwiki/html/overstack.html self-contained"],
     "overstack.html là tài liệu chính thức cho người đọc, self-contained, đi theo dự án khi cài, không "
     "cần mạng và không cần build. Vì sinh từ đĩa nên bảng skill/rule luôn khớp thực tế — đó cũng là lý "
     "do file này bị chạm 99 lần (regen mỗi khi nội dung đổi). Cạnh nó là build-wiki-graph.py vẽ vector "
     "quan hệ concept↔code, tự suy cạnh imports từ code thật với 0 token."),

    ("Cổng sức khoẻ cuối — chứng minh luật CÒN CẮN", "fdk/tools/medic.py", 40,
     "p_rules(): fire-drill — cố tình vi phạm rồi xác nhận bị chặn thật.",
     ["trạng thái repo hiện tại"], ["verdict xanh/đỏ cho rule · docs · code · eval · fresh-install"],
     "medic không kiểm tra 'file có tồn tại không' mà chạy diễn tập chữa cháy: cố tình vi phạm rồi xác "
     "nhận bị chặn. Đằng sau là bài học đắt nhất lịch sử repo — code-graph MCP hỏng nhiều tuần mà mọi "
     "phiên vẫn bị lùa vào dùng, vì code chỉ kiểm server có được KHAI BÁO trong config hay không. Từ đó "
     "sinh ra nguyên tắc 'tồn tại ≠ dùng được': quảng cáo năng lực phải THĂM DÒ thật. Dưới medic còn hai "
     "tầng: pre-commit gate mọi commit, và CI harness.yml chạy 67 assertion mỗi PR."),

    ("Dựng dự án mới — dán một prompt là xong", "00-New-Project.md", 1,
     "Prompt một-lần: agent tự cài, hỏi 3 câu, dựng knowledge base, scaffold MVP.",
     ["thư mục trống"], ["dự án có đủ 3 trụ + wiki khởi tạo + MVP scaffold"],
     "Không copy folder, không feed từng file: mở agent ở thư mục gốc dự án mới rồi dán nội dung "
     "00-New-Project.md. Bốn pha 00→03 tách sẵn nếu muốn đi chậm, chi tiết trong setup.md. Agent dừng "
     "đúng chỗ cần người quyết — cùng triết lý cổng với /propose."),
]

data = {
    "project": {
        "name": "overstack",
        "subtitle": "rheinmir/setup · nhánh orca · the self-disciplined AI-agent framework",
        "about": "Một lớp khung đặt LÊN TRÊN dự án của bạn, biến AI agent (Claude Code · opencode · "
                 "Antigravity · Cursor) thành cộng sự kỹ thuật tự-kỷ-luật: có trí nhớ dài hạn (llmwiki), "
                 "có nguyên tắc không thể phá (harness — 18 rule tất định, 0 token), có tay nghề đóng gói "
                 "sẵn (84 skill), và biết điều phối nhiều agent (Orca). Cài bằng một dòng curl. Kỷ luật ở "
                 "đây không phải lời dặn trong prompt mà là code chạy trước và sau mỗi hành động của "
                 "agent — agent không có quyền phủ quyết.",
        "stack": [
            {"name": "Markdown", "role": "585 file — tri thức và skill CHÍNH LÀ sản phẩm"},
            {"name": "Python", "role": "125 file — validator, hook, tool sinh docs"},
            {"name": "Shell", "role": "39 file — installer, bootstrap, gate"},
            {"name": "YAML", "role": "32 file — policy.yaml và cấu hình cơ chế"},
            {"name": "JSON", "role": "30 file — manifest, metrics, ledger"},
            {"name": "HTML", "role": "8 file — docs self-contained sinh bằng code"},
        ],
        "versions": [
            {"name": "branch", "ver": "orca"},
            {"name": "commit", "ver": "9032ae4"},
            {"name": "agy", "ver": "1.0.3"},
            {"name": "opencode", "ver": "1.15.10"},
            {"name": "phân tích", "ver": "2026-07-28"},
        ],
        "stats": [
            {"n": "846", "l": "file phân tích"},
            {"n": "18", "l": "rule đang gác"},
            {"n": "84", "l": "skill"},
            {"n": "15", "l": "validator"},
            {"n": "15", "l": "tầng kiến trúc"},
            {"n": "620", "l": "commit"},
        ],
    },
    "architecture": {
        "layers": [
            {"name": "L0 · Policy", "desc": "harness/policy.yaml — 18 rule bất biến, khai báo bằng YAML, "
             "không phụ thuộc vendor. Thêm luật = thêm entry, không rải if khắp hook."},
            {"name": "L1 · Session (adapter)", "desc": "Hook per-vendor: PreToolUse chặn trước khi ghi, "
             "PostToolUse ghi audit, Stop gác index, SessionStart báo trạng thái. Tất cả fail-open."},
            {"name": "L2 · Repo backstop", "desc": ".pre-commit-config.yaml gate mọi commit bất kể agent "
             "nào gõ — bắt được cả khi vendor bị tắt."},
            {"name": "L3 · Audit", "desc": "audit.jsonl + provenance-log.jsonl ghi bằng máy, sinh log.md "
             "tự động. Không nhờ model tự nhớ đã làm gì."},
            {"name": "L4 · Evals", "desc": "wiki-health 0 token + promptfoo golden questions + "
             "retrieval-eval có sàn, chạy trong CI để không regress lặng lẽ."},
            {"name": "Trụ tri thức — llmwiki/", "desc": "224 file: concepts, entities, sources, adr, "
             "draft, index.md, log.md. Bộ nhớ dài hạn agent đọc TRƯỚC khi hành động."},
            {"name": "Trụ kỹ năng — skills/", "desc": "84 skill canonical dạng SKILL.md gọi bằng /<tên>, "
             "mirror sang llmwiki/skills/ và cài global vào ~/.claude/skills."},
            {"name": "FDK — fdk/", "desc": "Đồ nghề phát triển CHÍNH framework + wiki riêng của framework "
             "(ADR-001..010). Không travel xuống dự án con (ADR-004/008)."},
        ],
        "diagram": {
            "nodes": [
                {"label": "Agent (Claude Code · opencode)", "x": 250, "y": 14, "w": 260, "h": 44, "color": "#2563eb"},
                {"label": "PreToolUse", "x": 40,  "y": 96, "w": 150, "h": 40, "color": "#0891b2"},
                {"label": "Stop", "x": 250, "y": 96, "w": 130, "h": 40, "color": "#0891b2"},
                {"label": "PostToolUse", "x": 430, "y": 96, "w": 150, "h": 40, "color": "#0891b2"},
                {"label": "SessionStart", "x": 615, "y": 96, "w": 130, "h": 40, "color": "#0891b2"},
                {"label": "llmwiki-validate.py — lõi vendor-neutral", "x": 130, "y": 178, "w": 340, "h": 46, "color": "#7c3aed"},
                {"label": "policy.yaml · 18 rule", "x": 60,  "y": 262, "w": 200, "h": 42, "color": "#dc2626"},
                {"label": "15 validators", "x": 310, "y": 262, "w": 160, "h": 42, "color": "#ea580c"},
                {"label": "llmwiki/ · wiki", "x": 30,  "y": 348, "w": 160, "h": 44, "color": "#059669"},
                {"label": "skills/ · 84", "x": 225, "y": 348, "w": 140, "h": 44, "color": "#059669"},
                {"label": "fdk/ · tools", "x": 400, "y": 348, "w": 140, "h": 44, "color": "#059669"},
                {"label": "docs sinh bằng code", "x": 575, "y": 348, "w": 175, "h": 44, "color": "#0d9488"},
                {"label": "pre-commit", "x": 150, "y": 434, "w": 150, "h": 40, "color": "#64748b"},
                {"label": "CI harness.yml", "x": 355, "y": 434, "w": 170, "h": 40, "color": "#64748b"},
            ],
            "edges": [[0,1],[0,2],[0,3],[0,4],[1,5],[2,5],[3,5],[5,6],[5,7],[7,8],[2,8],[10,11],[10,9],
                      [8,12],[12,13],[9,8],[6,7]],
        },
    },
    "tour": [
        {"t": t, "badge": f"{i:02d}", "file": f, "line": ln, "role": role, "in": ins, "out": outs,
         "hot": hot(f), "narr": narr}
        for i, (t, f, ln, role, ins, outs, narr) in enumerate(TOUR, 1)
    ],
    "modules": [],
    "docker": None,
}

out = os.path.join(ROOT, ".orca-onboard/tmp/onboard.json")
json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
missing = [s["file"] for s in data["tour"] if not os.path.isfile(os.path.join(ROOT, s["file"]))]
print("✅ wrote", out)
print(f"tour={len(data['tour'])} hot={sum(1 for s in data['tour'] if s['hot'])} "
      f"layers={len(data['architecture']['layers'])} "
      f"diagram nodes={len(data['architecture']['diagram']['nodes'])} "
      f"edges={len(data['architecture']['diagram']['edges'])}")
print("missing tour files:", missing or "none ✅")
