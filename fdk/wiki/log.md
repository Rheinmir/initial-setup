# Operation Log

## 2026-07-02 — harness R15 — không ghi công AI trong commit
User: dọn ghi công AI khỏi GitHub (filter-repo cắt 50 `Co-Authored-By: Claude` + 1 `Generated with`, force-push toàn bộ branch/tag; contributor "claude" còn lại chỉ là cache GitHub) → rồi "thêm ràng buộc vào /fdk … ý là phần harness luôn". Qua /fdk (pre-flight + propose + gate): thêm **R15 no-ai-attribution** — `process_gate` git `commit-msg` (validators/no_ai_attribution.py, chỉ quét message, fail-open, selftest PASS). Bắt Co-Authored-By:<AI> / Generated with|by <AI> / 🤖. Khai R15 ở cả policy prod (list) + poc (dict) → drift-test 45/0. `.pre-commit-config` +hook stage commit-msg; `install-harness.sh` +`--hook-type commit-msg`. E2E: commit bẩn BỊ CHẶN (HEAD không đổi). ADR-016 + rule-registry (bổ sung luôn R13/R14 còn thiếu) + decisions. Ghi vào /fdk mục Rules (luật mềm) — R15 là sàn cứng git-level.

## 2026-06-29 — anti-drift — meta-gate bnal-selftest + dọn rác lỗi-vị-trí
User hỏi "sao vẫn drift, không có cơ chế ngầm?". Trả lời: gate cũ chỉ verify render==generator / config-có-ADAPT-CHECKLIST, KHÔNG ai cross-check "mọi script có --self-test ĐỀU được fdk-gate chạy" → thêm feature quên wire self-test thì trôi lọt. Thêm `bnal-selftest.py --check` (discover script có --self-test vs fdk-gate khai; thiếu→exit 2; EXEMPT fdk-gate/flywheel/bnal-selftest) + wire vào fdk-gate (17 step). Cũng tìm ra thủ phạm vụ `fdk/tools/` biến mất trước đây: có `fdk/wiki/tools/` = bản duplicate lỗi-vị-trí (untracked, thiếu edit mới) → đã xoá. fdk-gate 17/17.

## 2026-06-29 — fix — overstack.html: nhánh BNAL AUTO từ config (hết outdate, chống drift)
User báo overstack.html trông cũ — mind-map chỉ show 10 chức năng BNAL (2 nhánh hardcode "BNAL 2026"+"BNAL đợt 2") trong khi đã có ~20 adapter. Sửa GỐC ở `build-overstack-docs.py`: thay 2 nhánh cứng bằng AUTO-GEN — quét `harness/*.config.yaml`, đọc cờ `verified`, gom 2 nhóm verified:false (chờ hiệu chỉnh) / verified:true (đã chốt), desc từ map curated (fallback generic). Thêm config BNAL mới → tự vào mind map, không drift nữa (đúng /fdk "đếm LIVE, không hardcode"). Regen overstack.html; fdk-gate 16/16.

## 2026-06-29 — fix — nút copy dạng ICON (sửa GỐC ở docs-site-macos → lan proposal + mọi docs site)
User: nút copy nên là ICON không phải chữ "Copy"; truy nguồn — đúng từ `docs-site-macos` (R7 bắt `/propose` render glass docs-site-macos; `/orca-workflow` render theo nó → kế thừa pattern copy). Sửa GỐC: canonical `skills/docs-site-macos/SKILL.md` đổi `.code-copy` thành nút icon vuông 28×26 + `initCodeCopy` dùng SVG clipboard→check (bỏ text 'Copy'/'✓ Copied'); sync mirror. Đồng bộ generator `build-overstack-docs.py` (icon) → regen overstack.html. fdk-gate 16/16 (mirror parity + overstack current). Proposal/docs site sinh sau tự có icon.

## 2026-06-29 — fix — overstack.html: nút copy + wrapping + TRAVEL theo install
User báo 3 lỗi ở `llmwiki/html/overstack.html` (file hướng dẫn travel cùng khung xương): (1) thiếu nút copy ở khối lệnh, (2) `<pre>` overflow ngang làm lệnh "dài ngoằng" + thiếu padding, (3) cài từ README (bootstrap→install.sh) KHÔNG thấy file. Fix ở generator `build-overstack-docs.py`: thêm `.code-block` + `initCodeCopy` (nút Copy hover, fallback execCommand) + CSS `.code-copy`; `<pre>` đổi `overflow:auto`→`white-space:pre-wrap;word-break;overflow-wrap` + padding-right chừa nút. TRAVEL: PoC `install.sh` (block --with-wiki) curl `$REPO_RAW/llmwiki/html/overstack.html` → `llmwiki/html/`; `bootstrap.sh` export `REPO_RAW` (strip /harness/poc-vendor-neutral, đúng fork/branch). URL orca HTTP 200; fdk-gate 16/16.

## 2026-06-29 — feature — áp 5 archetype Boris Cherny vào template (sweep-gate + persona dispatch + phase-map)
Cái lens 5-archetype chẩn ra overstack **accrete** nhiều mà ít gọt. Làm 3 thứ (BNAL): (1) **sweep-gate** — đếm "đã thêm bao nhiêu kể từ Sweep cuối" (counted_globs vs marker) → nhắc gọt khi vượt ngưỡng (như R10 nhưng cho Sweeper); dogfood bnal_config+bnal_metrics. (2) **archetype.py** + `archetypes.config.yaml` + 5 posture `llmwiki/personas/*` → vừa **phase-map** (`--phase`: tool overstack hợp archetype) vừa **persona dispatch** (`--get /sweep`: in CLI gợi ý + preamble để orca-workflow inject cho agy/opencode/kiro). Từ khoá: `/proto /build /sweep /grow /maintain`. (3) Wire orca-workflow bước dispatch + 2 self-test vào fdk-gate (19 BNAL). Routing cli↔archetype `verified:false` (đoán, đo bằng orca-eval rồi chốt). → [[ADR-015-boris-archetypes-into-template]].

## 2026-06-29 — doc — Boris Cherny 5 agent role (deep-dive scope)
Tạo `fdk/wiki/concepts/boris-cherny-agent-roles.md`: deep-dive scope 5 role từ `.claude/agents` của Boris Cherny (code-architect·code-simplifier·verify-app·build-validator·oncall-guide, +sentry-errors), mỗi role: scope·khi chạy·ranh giới·vì sao hẹp + map sang đồ overstack (propose/simplify/verify-before-commit/fdk-gate/orca-sec-scans). Nguồn: howborisusesclaudecode.com + Pragmatic Engineer (ảnh user là nguồn xác thực; sửa nếu ảnh khác). Đặt ở fdk/wiki (KHÔNG llmwiki/patterns vì R14 khoá — đúng cơ chế). → [[boris-cherny-agent-roles]]. fdk-gate 16/16.

## 2026-06-29 — refactor — gọn 13 chức năng: merge flywheel + tách 3 module dùng chung
Theo review "đầu giống, cuối khác" (load_config trùng 17×, capture-jsonl 4×, emit-mode 6×): (1) **MERGE** failure+success-flywheel (trùng 11/11 hàm) → `flywheel.py --kind failure|success`; 2 file cũ thành shim `os.execv` giữ skill/fdk-gate refs. (2) **Tách 3 module dùng chung**: `bnal_config` (load adapter — 12 consumer dùng), `bnal_metrics` (capture JSONL by-code — flywheel dùng), `bnal_guard` (emit advisory/block theo mode+verified — egress+inject dùng). BNAL an toàn: mỗi feature giữ file config riêng (adapter = config, không phải loader). Verify: 17 self-test PASS, leak-gate xanh, 10/10 test, fdk-gate 16/16. Slash: chỉ web-crawl/web-clone cần (+/flywheel cho cặp merge); 11 cái còn lại là code chạy tự động/CI.

## 2026-06-29 — fix — web-crawl/web-clone tham chiếu đúng nguồn (Firecrawl + ai-website-cloner-template)
User hỏi thẳng: crawler có tham khảo Firecrawl không, cloner có tham khảo ai-website-cloner-template chưa. Trả lời thật: builtin crawl là đồ cơ bản (urllib+regex, không render JS) — Firecrawl/Crawl4AI mới là engine thật (đã nêu rõ trong SKILL.md + Related repo). web-clone thêm **2 mode**: `snapshot` (1-file faithful, SingleFile/monolith) + `reconstruct` (reverse-engineer → Next.js editable, distill 5-phase pipeline của JCodesMore/ai-website-cloner-template ~6k★: recon browser-MCP → design tokens → component spec → parallel builders → visual-diff QA). Config web-clone +mode adapter; SKILL.md cite cả 2 nguồn. sync mirror + regen capabilities/overstack; fdk-gate 16/16.

## 2026-06-29 — maintenance — dọn drift skill-registry (42 skill) + wire gate
`skill-registry --check` lâu nay đỏ: 42 skill thiếu khỏi bảng AGENT.md/CLAUDE.md, 35 thiếu khỏi marketplace.json (drift CŨ, không do skill mới). Đăng ký đủ: +42 row giống hệt vào CẢ 2 bảng (sinh từ frontmatter `name`+`description`+loop, sort theo name), +35 path vào marketplace (plugin 'project'). Giờ "all surfaces agree" (mkt 64+1 allowlist fdk, AGENT/CLAUDE/LOOP_MAP 65). **Wire `skill-registry --check` vào fdk-gate (16 step) + CI skills-sync** để drift không tái phát (gốc rễ: trước đây không có cổng gác surface này). agent↔claude parity giữ nguyên ✓.

## 2026-06-29 — feature — 2 skill web-crawl + web-clone (build-now-adapt-later)
`/web-crawl` (site/URL → markdown LLM-ready): script `web-crawl.py` builtin urllib+regex→markdown (offline, no key) + `--self-test`; adapter `web-crawl.config.yaml` (backend firecrawl/crawl4ai/jina, verified:false). `/web-clone` (clone UI faithful → 1 file self-contained): `web-clone.py` inline local CSS/JS/img (offline) + adapter engine single-file CLI/monolith. Register đủ 4 surface (LOOP_MAP·marketplace·AGENT·CLAUDE) + sinh mirror; fdk-gate giờ 17 self-test BNAL. **Test crawl thật** `signals.forwardfuture.com/loop-library` → builtin backend chạy OK. (skill-registry --check còn drift CŨ 35/42 skill chưa đăng ký đủ — KHÔNG do 2 skill này, không gate.)

## 2026-06-29 — feature+docs — kho pattern tham chiếu BẢO VỆ (R14) + crawl loop-library
Folder `llmwiki/patterns/` (README + 7 vai trò frontend/backend/adapter/system-design/ba/tester/pm + `loops.md`), mỗi file Patterns(When·Do·Why)+Anti-patterns(Smell·Why bad·Instead). **R14 patterns-protected** = `patterns_guard.py` wired PreToolUse: chặn Write/Edit/bash-ghi vào patterns/ trừ khi `LLMWIKI_PATTERNS_UNLOCK=1` (raw nhưng thấp 1 bậc). Khai R14 cả 2 policy (parity 14=14, drift ✓), test `patterns-guard-test.sh` 7/7 + CI. BNAL: folder+guard built now; nội dung seeded `verified:false` (config `pattern-library.config.yaml`) chờ user curate. Seed: /last30days + repo Rheinmir star (gstack/system-design-notes/SkillSpector) + **crawl** `signals.forwardfuture.com/loop-library` (70 loop). 7 role doc sinh song song qua subagent. fdk-gate 15/15. → [[ADR-014-protected-pattern-library]].

## 2026-06-29 — feature+docs — 5 trend 2026 NỮA → 5 chức năng (build-now-adapt-later, đợt 2)
Quét trend tiếp (last30days WebSearch-fallback) → 5 feature nữa, cùng khuôn BNAL: `mem-rank` (memory agent ADD/UPDATE/DELETE/NOOP + retrieve ranked), `token-budget` (governor token+$ per session/task — FinOps gap), `inject-scan` (quét OUTPUT tool tìm injection gián tiếp), `claim-receipts` (gate hallucination: verify reference resolve), `prospect-critic` (reflection trước-chạy soi plan vs taxonomy failure-flywheel). Mỗi cái `--self-test`; fdk-gate giờ 15 self-test BNAL; leak-gate xanh (14 adapter verified:false). CAPABILITIES + overstack regen (+nhánh "BNAL đợt 2"). fdk-gate 15/15, 9/9 test. → [[ADR-013-five-more-trend-features-bnal]].

## 2026-06-29 — feature+docs — 5 trend 2026 → 5 chức năng (build-now-adapt-later)
Dựng 5 feature từ lượt quét trend, mỗi cái core tất định + adapter `verified:false`: `success-flywheel` (gương dương của failure-flywheel), `egress-guard` (tool/MCP/egress security), `trace-otel` (span OTel-GenAI + truy nhân-quả), `spec-gate` (spec-driven anti-drift), `scoped-hooks` (guard ở frontmatter skill). Mỗi feature có `--self-test`; wire 10 self-test + leak-gate vào fdk-gate (mở `GENERIC_KEYS` cho recurrence_threshold/prompt vì flywheel song song). CAPABILITIES + overstack regen (+nhánh "BNAL 2026"). fdk-gate 15/15. → [[ADR-012-five-trend-features-bnal]]. Trend source: [[ADR-011-project-local-harness]] (egress/scoped bám vào).

## 2026-06-29 — feature+docs — project-local harness + docs-gate 2 trụ
Thêm cơ chế `harness-local/` (dự án tự viết rule `P<n>` chạy song song R1–R13, sync-safe vì ngoài manifest, framework chạy trước theo AND; sandbox 13 test) — [[ADR-011-project-local-harness]] + concept [[harness-local]]. Mở rộng R10 docs-gate nhắc cả **đánh giá/eval** (`wikieval`) bên cạnh tài liệu (cập nhật [[R10]]). decisions.md +2 row; index +2 file; overstack.html regen (node `harness-local` + `docs-gate 2 trụ`). Code: commit `4c0e370` + `7bdcd97`.

## 2026-06-28 — goal-set — gate decision→ADR (R13) + edit/delete-when-superseded (ADR-010)
`harness/validators/decision_adr.py`: (1) decisions.md row architecture phải ref `ADR-N` (hoặc `(no-adr:)`); (2) EDIT ADR tự do; (3) XÓA ADR chỉ khi đã bị đè (`Superseded by`/`supersedes`). Wire pre-commit (decision-adr-link · adr-delete-guard · self-test) + CI repo-health. Test 5/5. Retro-fit 3 row architecture cũ. → [[ADR-010-decision-to-adr-gate]].

## 2026-06-28 — goal-set — session-orientation + auto-index + force-query (ADR-009)
Phiên mới không còn "lơ ngơ": `session_start.py` `orient()` nhắc agent query code-index (code-graph, auto-watch) + wiki + CAPABILITIES. `stop.py` auto `index_sync --fix` (file wiki mới tự vào index). R7-f buộc propose có `## Context` (force-query). Test wire CI/pre-commit. Đóng #1 (overstack ships by-design) + #2 (pre-commit đã wired downstream). → [[ADR-009-session-orientation-autoindex-forcequery]].

## 2026-06-28 — migrate — wiki framework → fdk/wiki (the kit)
Tách wiki riêng của framework (64 file: ADR-001..008, concepts harness/fdk, decisions/index/log, evals) `mv` từ `llmwiki/wiki/` → `fdk/wiki/`. `llmwiki/wiki/` còn 1 file demo (khuôn per-project). Repath ~10 invocation (CI repo-health, pre-commit, `find_wiki_dir` +fdk/wiki, wikieval, okf-test, .gitignore). Validators cả hai root xanh. → [[ADR-008-framework-wiki-lives-in-the-kit]].

## 2026-06-28 — failure-flywheel — ADR-007 wiki-scanner skip gitignored
Đóng drift class "wiki-tree scanner không lọc gitignored → false-positive archive" (recur 3×: harness-events, audit, okf-check). Ba tầng: vá consumer · `content_files()` an-toàn-mặc-định · `harness-lint --scanners/--copies` vào CI repo-health. Promote seed `/failure-flywheel` (spec-violation ×3) → [[ADR-007-wiki-scanner-skip-gitignored-at-lister]]. Commit 06884e2/b0b238b/976c6c0.

## 2026-04-28 — init — Knowledge Base initialized
- Created folder structure: concepts/, entities/, sources/, sources/draft/
- Created wiki/index.md, wiki/log.md
- Created AGENT.md

## 2026-06-15 — health-check — pattern-sync version + skill + SessionStart hook
- Thêm harness/scripts/health-check.py + harness/version.json (fingerprint 49 pattern)
- Thêm skill /health-check + hook session_start.py (báo cáo không chặn)
- Wire R8 policy, install-harness.sh, sync-template Step 0/6b; +health-check.md vào manifest
- Draft: wiki/sources/draft/150626-health-check-pattern-sync.md

## 2026-06-22 — orca-workflow — design-pattern-html-refactor
- Refactor 3 HTML infographics: v1 (4→5 sections), v2 (4→7 sections), v3 (4→10 sections)
- v1 thêm: Rate Limiting section, CDN card, prose WHY/WHEN cho 5 building blocks, 6-row tradeoff table
- v2 thêm: Rate Limiting, Consensus Algorithms (Raft/Paxos/PBFT), Monitoring & Observability (Three Pillars, SLI/SLO/SLA)
- v3 thêm: Communication Patterns (Saga/Event Sourcing), Service Discovery, Retry+Jitter, Stateless Design, EDA, CQRS
- agy terminals blocked (codex-trust-workspace) → Claude main thực hiện trực tiếp
- Proposal: wiki/draft/orca/220626-design-pattern-html-refactor.md

## 2026-06-21 — orca-workflow + docs-site-macos — design-pattern-infographic
- Fetch 3 YouTube video metadata (Code Lủng · Học Từ Thiền Series: Phần 000/001/002)
- YouTube SPA → transcript không extract được; dùng fallback: metadata + System Design knowledge
- Created 3 MD: wiki/sources/draft/design-pattern-v{1,2,3}.md
- Created 3 HTML infographics: llmwiki/html/design-pattern-v{1,2,3}.html (docs-site-macos light glass)
- Created proposal: wiki/draft/orca/210626-design-pattern-infographic.md
- Created seq diagram: llmwiki/html/210626-design-pattern-infographic-seq.html

## 2026-06-18 — docs-site-macos — orca-framework-overview
- Created llmwiki/html/180626-orca-framework-overview.html (single-file overview, skill grid by color)
- Created draft wiki/sources/draft/180626-orca-framework-overview.md

## 2026-06-22 — install-harness — mode=migrate
- Cài harness L0–L4 (validators, hooks, pre-commit, wiki-health, health-check, evals)
- Backfill nợ: YAML frontmatter R9 (9 legacy files), ## Origin (design-pattern.md), index sync (5 rows)
- Fix pre-commit Windows: python3 bash-wrapper → python (real MZ exe); fix arch-scan UnicodeEncodeError

## 2026-06-22 — docs-site-macos — chown
- Created llmwiki/html/220626-chown.html (single-file docs về lệnh chown)
- Created draft wiki/sources/draft/220626-chown.md
- 2026-06-23 00:17 — session `07d80623` — 8 tool calls — files: 230626-docs-gate-register-seq.html, 230626-docs-gate-register.md, index.md, install-harness.sh, settings.json

## 2026-06-23 — docs-site-macos — harness-docs-gate-orca-guard
- 2026-06-23 01:07 — session `07d80623` — 22 tool calls — files: 230626-docs-gate-register-seq.html, 230626-docs-gate-register.md, 230626-harness-docs-gate-orca-guard-report.md, 230626-harness-docs-gate-orca-guard.html, 230626-orca-guard-hook-seq.html, 230626-orca-guard-hook.md, index.md, install-harness.sh …

## 2026-06-23 — orca-workflow: /harness-update < 30s
- Proposal 230626-harness-update-sub30s (gate duyệt) → impl T1-T4.
- T1 install-harness.sh `--self-heal`: tự backfill Origin+index+OKF in-process, re-audit 1 lần (gộp vòng lặp 3-reinstall agent → 1 lệnh).
- T2 harness/scripts/audit.py: gộp 3 audit về 1 process; Origin backfill 1 lượt git log.
- T3 `--no-clone` fast-fail (0.02s, không treo mạng) + skip pre-commit install nếu đã cài.
- T4 viết lại skill 1-phát-gọi + bench harness/metrics/harness-update-bench.json.
- Bench: migrate-có-nợ 0.56s, re-run sạch 0.31s, smoke ⛔×3. Dispatch opencode T3 treo → kill, claude-cli tiếp quản.

## 2026-06-23 — orca-workflow: skill tạo docs đạt chuẩn OKF v0.1
- Proposal 230626-docs-skill-okf (gate duyệt) → impl T1-T3.
- T1 orca-onboard: heredoc + example block `**Type:**` bold → YAML frontmatter `type: draft` (hết tạo nợ R9).
- T2 onboard-codebase + new-project-setup: thêm dòng Rule nhắc OKF (copy _template.md).
- T3 harness/tests/docs-skill-okf-test.sh: 10/10 PASS (skill .md áp OKF, skill HTML N/A, wiki repo OKF 7/8 chỉ còn legacy 220626-chown).
- Dispatch opencode T2 no-op (0 output) → claude-cli tiếp quản (lần 2 liên tiếp opencode hỏng).
- 2026-06-23 01:44 — session `31d9431b` — 27 tool calls — files: 230626-docs-skill-okf-seq.html, 230626-docs-skill-okf.md, 230626-harness-update-sub30s-seq.html, 230626-harness-update-sub30s.md, audit.py, docs-skill-okf-test.sh, harness-update-test.sh, harness-update.md …

## 2026-06-23 — orca-workflow: /sync-template < 30s (cờ --full)
- Proposal 230626-sync-template-sub30s (gate gate_70ba7f4b3b1d duyệt) → impl T1-T4.
- Phát hiện: script đã <1s; nút thắt >30s là 5-6 round-trip agent quanh Step 6a/6b/8 + log.md.
- T1-T3 sync-template.py: cờ `--full` gộp OKF backfill (import okf-check in-process) + fingerprint-sau-OKF + self-verify 3 vị trí + append log vào 1 process. Không cờ = hành vi cũ.
- T4: viết lại FAST PATH skill về 1 phát `--full`; bench harness/metrics/sync-template-bench.json — steady 0.27s, pull+install+verify 0.76s (cả hai <30s & <5s); phân loại + exit code giữ nguyên, CONFLICT vẫn exit 3.
- T3 dự kiến opencode → claude làm inline (coupled cùng file T1/T2, opencode dispatch bất ổn).

## 2026-06-23 — orca-workflow: hook fail-open + kênh giao hook (fix client cozyroom)
- Proposal 230626-orca-guard-failopen (gate gate_357120266bc7 duyệt) → impl T1-T3.
- Sự cố: client cozyroom mọi Bash bị chặn vì hook orca_guard.py thiếu file + lệnh hook trần không fail-open.
- T1: guard `if [ -f "<p>" ]; then python3 "<p>"; fi` ở install-harness.sh (GLOBAL cmd + ROOT h) + llmwiki/.claude/settings.json (7 command); re-merge dedup theo basename → nâng cấp lệnh trần cũ, không trùng, giữ user hook.
- T2: thêm 8 llmwiki/.claude/hooks/*.py + settings.json vào manifest (57 pattern); /sync-template --full giao được orca_guard.py.
- T3: installer WARN khi hook thiếu file (không fatal) + golden test harness/tests/orca-guard-failopen-test.sh 6/6 PASS; 3 python block embed compile OK.
- Gỡ ngay client: `git show origin/orca:llmwiki/.claude/hooks/orca_guard.py > llmwiki/.claude/hooks/orca_guard.py`.

## 2026-06-23 — orca-workflow: rà 26 npx skill vs bản cũ → vá 2 regression
- Audit 4 agent song song (old npx cdd3e08~1 vs canonical): 23 OK, 3 flag.
- orca-workflow: khôi phục section "An toàn container/DB" (Cozyroom DB path + bài học 05-29 recreate→mất DB) bị refactor b0f30e0 làm rớt → canonical + npx.
- tour-guide: canonical vốn bonbon-specific (fe/components/dms/...) → thay bằng bản generic self-contained (khớp published description) + có frontmatter (vá luôn gap thiếu frontmatter); npx regenerate.
- onboard-codebase: GIỮ NGUYÊN — canonical cố tình caveman-compress (commit 52827b7), npx mirror đúng harness.
- Kết quả: npx body == canonical cho toàn bộ skill (chuẩn so với harness).
## 2026-06-25 — orca-onboard — onboard-setup
## 2026-06-25 — orca-onboard — onboard-setup complete (4 phases, static-parse route, ~$0.04 actual)
## 2026-06-25 — docs-site-macos — harness-mcp-scenarios
## 2026-06-25 — docs-site-macos — harness-arch-vs-current
## 2026-06-25 — harness — poc-vendor-neutral (13/13 PASS)
## 2026-06-25 — concept — cursor-explain-site (distill cloner-template → extract-site Mode 3)
## 2026-06-25 — orca-eval — eval-report + promote skill cursor-animated-sites
## 2026-06-25 — cursor-animated-sites — cicd-lifecycle (kiểm chứng skill)
## 2026-06-25 — cursor-animated-sites — index gộp harness + CI/CD
## 2026-06-25 — cursor-animated-sites — gộp 3 trang (index+harness+cicd) thành 1 file walkthroughs
## 2026-06-27 — orca-workflow — framework-gap-backfill: proposal + R11 seq-glass-style + R12 pull-before-change (gate1 PreToolUse + gate2 pre-push)
## 2026-06-27 — orca-workflow — R12 rút gọn về (B) orchestrator pre-work sweep + (C) pre-push; BỎ (A) per-edit PreToolUse (cost cao, lệch đa-vendor)
## 2026-06-27 — orca-workflow — propose R12 v3 workspace-aware (pull-gate-sweep + --all-subrepos), gate chờ duyệt
## 2026-06-27 — orca-workflow — R12 v3 DUYỆT + impl T1-T5 (list-subrepos.py, pull-gate-sweep.sh, install --all-subrepos, Step 0 sweep ×2, test 4/4 PASS); Kiro thiếu → Claude inline
## 2026-06-27 — backfill — rule-registry (R1..R12 + flag drift R3/R8) + ADR-001/002 + lấp decisions.md
## 2026-06-27 — T1 reconcile — thêm R3/R4/R8/R10 (hook_event) vào policy.yaml (11 rule); điều tra: R3/R8 KHÔNG drift, gỡ flag; registry cập nhật
## 2026-06-27 — T5 drift-test — policy-converters-drift-test.sh (28/28 + negative bắt drift); wire .pre-commit
## 2026-06-27 — T4 — CONTRIBUTING-harness.md (runbook thêm rule); gap-backfill CLOSED (T1-T5 done)
## 2026-06-27 — policy-drives-wiring — gen-converters SINH hook claude từ hook_event rules (output identical, drift-test 36/0 + negative)
## 2026-06-27 — R11 [repo] — migrate 8 seq html flat → glass (override docs-site-macos); bật enforce_at [session,repo] + pre-commit seq-html-glass
## 2026-06-27 — R6 + two-policy — R6=verify-before-commit (KHÔNG reserved); reconcile harness/policy.yaml↔poc (cả hai R1-R12); drift-test check parity
## 2026-06-27 — fix broken wikilink — stub concepts extract-site + docs-site-macos-skill (wiki-health 0 broken)
## 2026-06-27 — fix — poc R7 thêm exclude_basenames (_template miễn, khớp production); full test sweep 10/10
## 2026-06-27 — review — session-review output report (13 commit, full sweep 10/10) + re-sync ~/.claude skill
## 2026-06-27 — commit — 5 wiki untracked có-sẵn được index trỏ (architecture, cursor-explain-site, onboarding-tour, project-structure, 250626-onboard-setup)
## 2026-06-27 — docs-site-macos — session-review-html (trang glass 6 section, self-contained, :8765)
## 2026-06-27 — feedback — siết luật: tắt caveman khi viết tài liệu (orca-workflow x2 + CLAUDE.md); lưu memory docs-no-caveman
## 2026-06-27 — feedback — tinh chỉnh luật caveman: máy đọc thì gọn được, người đọc thì đầy đủ (orca-workflow x2 + CLAUDE.md)
## 2026-06-27 — docs-site-macos — viết lại 270626-session-review.html bằng văn xuôi đầy đủ (theo feedback caveman), giữ design system glass
## 2026-06-27 — docs-site-macos — tinh gọn session-review.html (cô đọng vừa đủ, không sơ sài) theo feedback

## 2026-06-27 — propose — wiki-sync-structure
Draft proposal `270626-wiki-sync-structure.md` + seq HTML `270626-wiki-sync-structure-seq.html`. Skill tái gọi `/wiki-sync-structure` để phát hiện & sửa drift tài liệu cấu trúc (số liệu 32→56 / 25→44, gap file 03, bảng skill AGENT.md≠CLAUDE.md, dedupe design-pattern + infographic). 4 task, all claude. STOP chờ duyệt.

## 2026-06-27 — propose — propose-single-source
Draft `270626-propose-single-source.md` + seq HTML (glass-style). Refactor DRY: /propose hấp thụ gap glass-style → thành single source of truth; orca-workflow bước 2 đổi sang GỌI /propose (như bước 1 đã gọi query); giữ R12/query/gate/dispatch. 3 task, all claude. STOP chờ duyệt.

## 2026-06-27 — edit(skill) — propose step-7 rich-prose + glass
Sửa thẳng bước 7 của /propose (cả 3 bản: dev-loop canonical + mirror skills/ + global ~/.claude, diff=SAME): companion HTML phải có CẢ (A) animated diagram VÀ (B) prose chi tiết câu hoàn chỉnh cho mỗi task — chỉ-diagram = chưa đạt; + bắt buộc style docs-site-macos glass. Theo rule CLAUDE.md 2026-06-27 (HTML là tài liệu người-đọc). Gộp luôn gap glass-style của proposal #2-T1.

## 2026-06-27 — implement — propose-single-source (proposal #2)
Đã làm T1–T3: (T1) bước 7 /propose nuốt glass-style + prose (B); (T2) orca-workflow bước 2 → GỌI /propose + mô hình Claude-nghĩ/CLI-rẻ-render (OpenCode→agy→kiro, Full tier, watchdog+R7 gate+fallback); (T3) ADR-003 + decisions.md. Bonus: vá drift skill↔validator R7-(d) — /propose spec + 2 seq html đổi .msg opacity≥.82 (bài 130626). 5 file skill (3 propose + 2 orca-workflow) giữ diff=SAME. Chưa commit.

## 2026-06-27 — concept — fdk (Framework Development Kit)
Dựng bộ xương phát triển framework: front-door `concepts/fdk.md` (pre-flight gate + Phần 2 không-miss-rule + Phần 3 không-dẫm-module với lệnh inventory live, không hardcode số). Wire vào AGENT.md + CLAUDE.md (rule đầu), cross-link rule-registry + CONTRIBUTING-harness. index/decisions cập nhật.

## 2026-06-27 — hook — fdk context-pump (SessionStart)
session_start.py thêm fdk_context(): mỗi phiên tự bơm 1 block "framework có gì" (skills/validators/scripts/hooks/rules đếm live) + cửa vào fdk.md. Fail-open, test in đúng + exit 0. fdk.md ghi nhận cửa chủ động.

## 2026-06-27 — docs-site-macos — fdk-docs
Render fdk.md thành trang docs glass đọc được: llmwiki/html/270626-fdk-docs.html (sidebar + 6 section accent + draggable SVG pre-flight + checklist + copy/ripple/scroll-spy, self-contained). Cross-link fdk.md ↔ html.

## 2026-06-27 — fix+skill — fdk opt-in (/fdk) + audit
Sửa lỗi tư duy "mặc định phiên = dev framework": gỡ fdk_context() khỏi session_start.py (giữ pattern-health); tạo skill /fdk (canonical utils + mirror, diff=SAME) gọi chủ động; slim pointer AGENT/CLAUDE → /fdk điều kiện + đăng ký skill table; ADR-004 + audit 5 điểm auto-fire (2 phạm: fdk_context + pointer; 3 không). fdk.md + docs HTML section 4 cập nhật.

## 2026-06-27 — durability — ghim luật opt-in vào repo
Memory cá nhân là máy-local (không theo git) → ghim luật "auto-fire chỉ phục vụ dự án hiện tại; context nội-bộ-framework phải opt-in" vào AGENT.md + CLAUDE.md (## Rules, feedback 2026-06-27) + guard actionable trong fdk.md pre-flight + trang docs. Travel với repo, mọi máy/agent đều thấy.

## 2026-06-28 — goal — karpathy distill + skills cheatsheet + clean remote
(1) AGENT.md/CLAUDE.md: distill 4 nguyên tắc Karpathy gọn (~60→10 dòng) + attribute (multica-ai/andrej-karpathy-skills) + merge framework context. (2) Mind-map cheatsheet skill: llmwiki/html/280626-skills-cheatsheet.html (local-only do html gitignored). (3) Clean remote giữ local: gitignore + git rm --cached 21 docs html + 29 draft md — giữ file trên đĩa + row index (index_sync 2-chiều nhưng KHÔNG ở CI → local PASS, remote slim).

## 2026-06-28 — restructure — folder fdk/ quản lý dev-framework
Gom framework-dev vào folder riêng travel cùng repo: fdk/tools/build-cheatsheet.py (dời từ harness/scripts/), fdk/docs/CONTRIBUTING.md (git mv từ harness/CONTRIBUTING-harness.md), fdk/README.md (index + bản đồ doc). Impact-check: recipe.md/harness.md/DOCS.md coupled engine (pre-commit/install/validators) → GIỮ tại harness/, chỉ index. Cập nhật ref ở fdk.md + 2 bản skill fdk (diff=SAME). Validators PASS.

## 2026-06-28 — skill — /fdk self-contained
Viết lại /fdk (canonical + mirror, diff=SAME) thành self-contained: pre-flight + cách distill skill + inventory đứng độc lập, chạy ở project bất kỳ; mọi tham chiếu file repo-local dồn vào 1 mục điều kiện "nếu đang trong repo framework". KHÔNG thêm fdk/ vào install (ADR-004, downstream gọn). Skill travel qua global skills (npx --all). Docs HTML + cheatsheet cập nhật.

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-06-28 17:26:16 | `file.write` | llmwiki/CLAUDE.md · tool=Edit |
| 2026-06-28 17:30:51 | `file.write` | fdk/tools/docs-curate.py · tool=Edit |
| 2026-06-28 17:40:00 | `file.write` | fdk/tools/build-overstack-docs.py · tool=Edit |
| 2026-06-28 17:40:29 | `file.write` | fdk/tools/build-overstack-docs.py · tool=Edit |
| 2026-06-28 17:40:56 | `file.write` | fdk/tools/build-overstack-docs.py · tool=Edit |
| 2026-06-28 17:41:16 | `file.write` | fdk/tools/build-overstack-docs.py · tool=Edit |
| 2026-06-28 17:42:42 | `file.write` | llmwiki/.claude/hooks/stop.py · tool=Edit |
| 2026-06-28 17:42:57 | `file.write` | llmwiki/.claude/hooks/stop.py · tool=Edit |
| 2026-06-28 17:44:12 | `file.write` | fdk/tools/new-skill.py · tool=Edit |
| 2026-06-28 17:57:07 | `file.write` | fdk/tools/docs-curate.py · tool=Edit |
| 2026-06-28 17:58:01 | `file.write` | skills/docs-curate/SKILL.md · tool=Edit |
| 2026-06-28 18:03:58 | `file.write` | llmwiki/wiki/sources/adr/ADR-006-blocking-stays-hook-mcp-for-tooling.md · tool=Write |
| 2026-06-28 18:04:34 | `file.write` | llmwiki/wiki/concepts/harness-enforcement-floor.md · tool=Write |
| 2026-06-28 18:20:07 | `file.write` | harness/poc-vendor-neutral/bin/harness-events.py · tool=Edit |
| 2026-06-28 18:20:08 | `file.write` | harness/poc-vendor-neutral/bin/harness-events.py · tool=Edit |
| 2026-06-28 18:28:36 | `file.write` | harness/scripts/audit.py · tool=Edit |
| 2026-06-28 18:34:32 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:34:41 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:34:52 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:34:57 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:35:02 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:35:07 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:45:25 | `file.write` | harness/validators/index_sync.py · tool=Edit |
| 2026-06-28 18:45:32 | `file.write` | harness/validators/index_sync.py · tool=Edit |
| 2026-06-28 18:45:41 | `file.write` | harness/scripts/audit.py · tool=Edit |
| 2026-06-28 18:46:35 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:46:41 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:46:54 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:47:10 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:47:15 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:47:20 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:54:02 | `file.write` | harness/scripts/okf-check.py · tool=Edit |
| 2026-06-28 18:54:27 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:54:33 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:54:40 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 18:54:45 | `file.write` | harness/scripts/harness-lint.py · tool=Edit |
| 2026-06-28 19:13:08 | `file.write` | llmwiki/wiki/sources/adr/ADR-007-wiki-scanner-skip-gitignored-at-lister.md · tool=Write |
| 2026-06-28 19:14:37 | `file.write` | llmwiki/wiki/index.md · tool=Edit |
| 2026-06-28 19:15:02 | `file.write` | llmwiki/wiki/decisions.md · tool=Edit |
| 2026-06-28 19:15:09 | `file.write` | llmwiki/wiki/log.md · tool=Edit |

<!-- log:auto:end -->

## 2026-06-28 — docs-curate promote — ADR-006 (hook-vs-MCP) + concept harness-enforcement-floor (từ 3 draft analysis 250626; cicd-lifecycle skip=demo)
- 2026-06-29 07:53 — session `1fdd736b` — 100 tool calls — files: .pre-commit-config.yaml, 290626-bnal-trend-features-docs.md, 290626-bnal-trend-features.html, ADR-011-project-local-harness.md, ADR-012-five-trend-features-bnal.md, ADR-013-five-more-trend-features-bnal.md, ADR-014-protected-pattern-library.md, AGENT.md …

## 2026-06-30 — concept outer-harness-evaluation + index cleanup
- Tạo `concepts/outer-harness-evaluation.md` — distill Outer Harness (raw/outer-harness.md) + kết quả phiên /council (3 ghế, blind peer-rank seed 42, single-provider caveat); gap-map overstack vs 5 trụ cột + roadmap.
- Dọn `index.md`: xóa 21 dòng orphan trỏ tới `sources/draft/*.md` không tồn tại (đã được archive sang `sources/draft/archive/...`, auto-index block giữ bản đúng). 88→67 dòng (sau đó +1 entry mới).
- 2026-06-30 — docs-site-macos render: `llmwiki/html/300626-outer-harness-evaluation.html` (glass single-file, mind map + 2 draggable SVG + 5 section) cho concept outer-harness-evaluation. Self-contained, served :8765.
- 2026-06-30 13:10 — session `b5d0b1d7` — 13 tool calls — files: 300626-outer-harness-evaluation.html, answers.json, chairman_synthesis.md, code-logger.py, cost-rates.json, feature-catalog.md, index.md, outer-harness-evaluation.md …
- 2026-06-30 13:46 — session `1fdd736b` — 1 tool calls — files: fdk-gate.py
- 2026-06-30 15:34 — session `a4a5a012` — 4 tool calls — files: build-overstack-docs.py
- 2026-06-30 16:05 — session `42d7b209` — 18 tool calls — files: 300626-audit-fix-docs-site-macos.md, SKILL.md, index.md, log.md, stop.py
- 2026-06-30 16:05 — session `75158c72` — 36 tool calls — files: .pre-commit-config.yaml, 300626-outer-harness-evaluation.html, SKILL.md, code-logger.py
- 2026-06-30 21:35 — session `42d7b209` — 18 tool calls — files: 300626-audit-fix-docs-site-macos.md, SKILL.md, index.md, log.md, stop.py
- 2026-06-30 21:37 — session `75158c72` — 36 tool calls — files: .pre-commit-config.yaml, 300626-outer-harness-evaluation.html, SKILL.md, code-logger.py
- 2026-06-30 21:38 — session `a4a5a012` — 4 tool calls — files: build-overstack-docs.py
- 2026-06-30 22:02 — session `42d7b209` — 18 tool calls — files: 300626-audit-fix-docs-site-macos.md, SKILL.md, index.md, log.md, stop.py
- 2026-07-01 13:15 — session `42d7b209` — 82 tool calls — files: 010726-dev-harness-kit-council.html, 010726-dev-harness-kit.md, 010726-trupillar4-council-persona.md, 300626-outer-harness-evaluation.html, MEMORY.md, SKILL.md, build-overstack-docs.py, code_health.py …

## 2026-07-01 — verify-before-commit — query-retrieval-eval (promoted 632e29c → fdk/wiki/concepts/query-retrieval-eval.md)
- 2026-07-01 18:36 — session `071d8d58` — 16 tool calls — files: 010726-query-retrieval-eval.md, answers.json, harness.yml, query-log.py, query-proxy.py, query-retrieval-eval.md, query.md, retrieval-eval.py
- 2026-07-01 22:54 — session `87754f76` — 5 tool calls — files: 010726-21-quy-tac-docs.md, 010726-21-quy-tac.html, index.md, log.md
- 2026-07-01 23:32 — session `43086569` — 7 tool calls — files: SKILL.md, answers.json, judges.json
- 2026-07-02 08:13 — session `f7b1b1f6` — 31 tool calls — files: 020726-cor-pattern.md, SKILL.md, answers.json, co:controlled-output-pattern.md, cor-guide.md, cor.py, council.py, redesign-existing-projects.md
- 2026-07-02 09:19 — session `4aaab8ea` — 11 tool calls — files: 020726-overstack-docs-redesign.md, build-overstack-docs.py
- 2026-07-02 09:20 — session `aea1a0d5` — 14 tool calls — files: .pre-commit-config.yaml, ADR-016-no-ai-attribution-in-commits.md, LICENSE, SKILL.md, decisions.md, install-harness.sh, log.md, no_ai_attribution.py …
- 2026-07-02 13:07 — session `bf38cf4e` — 47 tool calls — files: 020726-eval-report.md, 020726-orca-issue-ledger-travel-seq.html, 020726-orca-issue-ledger-travel.md, SKILL.md, fdk-problem-tree.html, flush_problem_tree.py, install.sh, post_tool_use.py …
- 2026-07-02 13:08 — session `7c68668a` — 3 tool calls — files: 020726-adr-015-status.html, 020726-adr-015-status.md
- 2026-07-02 13:08 — session `4aaab8ea` — 18 tool calls — files: 020726-overstack-docs-redesign.md, AGENT.md, CLAUDE.md, build-overstack-docs.py, sync-skills.py
- 2026-07-02 13:08 — session `aea1a0d5` — 14 tool calls — files: .pre-commit-config.yaml, ADR-016-no-ai-attribution-in-commits.md, LICENSE, SKILL.md, decisions.md, install-harness.sh, log.md, no_ai_attribution.py …
- 2026-07-02 13:08 — session `7aba727b` — 3 tool calls — files: 020726-openai-compat-endpoint-pools.html, 020726-openai-compat-endpoint-pools.md

## 2026-07-02 — ingest — fdk-stragegy.md
- Created `concepts/fdk-dev-strategy.md` — pattern hóa 8 bài học Mông Cổ thành 8 nguyên tắc phát triển fdk
- Created `sources/mongol-ai-strategy.md` — tóm tắt nguồn raw `llmwiki/raw/fdk-stragegy.md`
- Updated `index.md` — thêm 2 trang mới
- 2026-07-02 13:19 — session `bf38cf4e` — 49 tool calls — files: 020726-eval-report.md, 020726-orca-issue-ledger-travel-seq.html, 020726-orca-issue-ledger-travel.md, SKILL.md, fdk-problem-tree.html, flush_problem_tree.py, harness-events.py, install.sh …
- 2026-07-02 13:21 — session `a1833594` — 6 tool calls — files: 020726-ingest-fdk-strategy.md, fdk-dev-strategy.md, index.md, mongol-ai-strategy.md
- 2026-07-02 13:47 — session `a1833594` — 8 tool calls — files: 020726-audit-fdk-strategy.md, 020726-ingest-fdk-strategy.md, fdk-dev-strategy.md, index.md, mongol-ai-strategy.md

## 2026-07-02 — fdk — wiki-core v2 buoc 1+2&3 (framework wiki)
- fdk/wiki cung nhan ledger + id/relations migrate (63 trang). Nguon: draft llmwiki 020726-wiki-core-relations (council-approved).
- 2026-07-02 21:31 — session `c0fd85d2` — 108 tool calls — files: 020726-docs-site-fdk-strategy.md, 020726-fdk-dev-strategy.html, 020726-wiki-core-relations.md, Dockerfile, SKILL.md, answers.json, build-wiki-graph.py, gen_board.py …
- 2026-07-02 21:31 — session `c0fd85d2` — 108 tool calls — files: 020726-docs-site-fdk-strategy.md, 020726-fdk-dev-strategy.html, 020726-wiki-core-relations.md, Dockerfile, SKILL.md, answers.json, build-wiki-graph.py, gen_board.py …
- 2026-07-02 21:31 — session `a1833594` — 11 tool calls — files: 020726-audit-fdk-strategy.html, 020726-audit-fdk-strategy.md, 020726-ingest-fdk-strategy.md, fdk-dev-strategy.md, framework-multi-session-dev.md, index.md, mongol-ai-strategy.md
- 2026-07-02 21:31 — session `bf38cf4e` — 49 tool calls — files: 020726-eval-report.md, 020726-orca-issue-ledger-travel-seq.html, 020726-orca-issue-ledger-travel.md, SKILL.md, fdk-problem-tree.html, flush_problem_tree.py, harness-events.py, install.sh …
- 2026-07-02 22:17 — session `bf38cf4e` — 49 tool calls — files: 020726-eval-report.md, 020726-orca-issue-ledger-travel-seq.html, 020726-orca-issue-ledger-travel.md, SKILL.md, fdk-problem-tree.html, flush_problem_tree.py, harness-events.py, install.sh …
- 2026-07-02 22:18 — session `c0fd85d2` — 108 tool calls — files: 020726-docs-site-fdk-strategy.md, 020726-fdk-dev-strategy.html, 020726-wiki-core-relations.md, Dockerfile, SKILL.md, answers.json, build-wiki-graph.py, gen_board.py …
- 2026-07-02 22:19 — session `a1833594` — 11 tool calls — files: 020726-audit-fdk-strategy.html, 020726-audit-fdk-strategy.md, 020726-ingest-fdk-strategy.md, fdk-dev-strategy.md, framework-multi-session-dev.md, index.md, mongol-ai-strategy.md
- 2026-07-03 22:03 — session `d1bd9518` — 28 tool calls — files: 030726-foundation-section.md, 030726-orca-independence-planb.md, 030726-skill-usage-dashboard.md, AGENT.md, CLAUDE.md, ISSUES.md, MEMORY.md, RELEASE-v1.0.6.md …

- 2026-07-03 frontier-gap-scan: concept mới (baseline overstack-vs-world 30d) + raise 5 issue gap (GH#9-13: memory, self-evolving-skills, observability, orchestration-scale, skill-resolve-supplychain). Report: llmwiki/html/overstack-vs-world-30d.html
- 2026-07-03 raise issue Ralph BR→frame production-line + harness/monitor (GH#15, ledger 030726-ralph-br-frame-production-line). Đổi scout tuần thành skill instant /frontier-scan (canonical+mirror+4 surface, checks xanh) vì routine cloud bị chặn GitHub.
- 2026-07-05 00:18 — session `db4de305` — 3 tool calls — files: 050726-ralph-interview-pipeline.html, 050726-ralph-interview-pipeline.md, index.md
- 2026-07-06 23:15 — session `49ec06f0` — 17 tool calls — files: ISSUES.md, framework-multi-session-dev.md, gen-converters.py, harness-integrity-test.sh, harness.yml, index.md, install-harness.sh, install.sh …
- 2026-07-07 13:19 — session `e2bc1e44` — 10 tool calls — files: 070726-adapt-modes.html, AGENT.md, CLAUDE.md, MEMORY.md, adapt-modes-taxonomy.md, adapt-modes.md, index.md, travel-policy.yaml
- 2026-07-07 14:55 — session `8d2bc3a0` — 4 tool calls — files: 070726-adapt-modes.html, build-overstack-docs.py, docs-site-macos.md
- 2026-07-07 15:06 — session `b2e273ec` — 4 tool calls — files: 060726-ponytail-distill-PLAN.md, 070726-ponytail-distill.md
- 2026-07-15 09:06 — session `36e6562b` — 21 tool calls — files: 150726-hallmark-design-foundation-seq.html, 150726-hallmark-design-foundation.md, 150726-mattpocock-absorb-seq.html, 150726-mattpocock-absorb.md, SKILL.md, frontier.py, issue-tracker.md, skill-craft.md …
- 2026-07-17 20:11 — session `b06734dd` — 13 tool calls — files: .template-manifest.json, 170726-gitignored-dedupe-seq.html, 170726-gitignored-dedupe.md, SKILL.md, index.md, log.md
- 2026-07-18 11:14 — session `246fa7ac` — 56 tool calls — files: 180726-archetype-tester-seq.html, 180726-archetype-tester.md, 180726-capability-proof-map-PLAN.md, 180726-capability-proof-map-seq.html, 180726-capability-proof-map.md, SKILL.md, adapt-modes-pick.md, archetype.py …
- 2026-07-18 11:14 — session `246fa7ac` — 56 tool calls — files: 180726-archetype-tester-seq.html, 180726-archetype-tester.md, 180726-capability-proof-map-PLAN.md, 180726-capability-proof-map-seq.html, 180726-capability-proof-map.md, SKILL.md, adapt-modes-pick.md, archetype.py …
- 2026-07-18 23:15 — session `246fa7ac` — 123 tool calls — files: 180726-archetype-tester-seq.html, 180726-archetype-tester.md, 180726-capability-proof-map-PLAN.md, 180726-capability-proof-map-seq.html, 180726-capability-proof-map.md, 180726-council-self-index-remaining-scope.md, RELEASE-v1.1.0.md, SKILL.md …
- 2026-07-19 21:03 — session `ee3f5da6` — 8 tool calls — files: 190726-travel-gap-forcing-functions-seq.html, 190726-travel-gap-forcing-functions.md
- 2026-07-20 12:57 — session `eec0806a` — 22 tool calls — files: 200726-code-graph-index-broken.md, 200726-orchestration-loop-closure-seq.html, 200726-orchestration-loop-closure.md, 200726-orchestration-triage.md, SKILL.md, council.personas.yaml, newcomer-adr.md, orca-dispatch.py …
