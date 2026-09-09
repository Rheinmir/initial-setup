# Overstack — Bảng chức năng ĐẦY ĐỦ (feature inventory)

> Rà từ các nguồn chân lý: `harness/poc-vendor-neutral/policy.yaml` (rules), `harness/mechanisms.yaml`
> (mechanisms), `skills/*/SKILL.md` (72 skill), `harness/validators/*.py` (14), `fdk/tools/*.py` (16),
> `harness/scripts/*.py` (44). Sinh 2026-07-05. **Tổng: 4 nền tảng · 17 rule · 17 cơ chế · 72 skill · 14 validator · 16 fdk-tool · 44 harness-script.**

## 0 · Nền tảng (3 trụ + lớp điều phối)

| # | Trụ | Chức năng |
|---|-----|-----------|
| N1 | Wiki (tri thức) | Bộ nhớ dự án: concepts/entities/sources/ADR/draft; mỗi trang truy được nguồn (`## Origin`); đồ thị quan hệ + code (wiki-graph). |
| N2 | Harness (rào chắn) | Luật tất định bằng code (17 rule) chặn agent làm bậy; 0 token; không bypass được khi merge (pre-commit L2 + CI). |
| N3 | Skills (kỹ năng) | 72 quy trình đóng gói, gọi bằng `/tên`, cài global dùng mọi dự án. |
| N4 | Orca (điều phối) | LỚP chạy nhiều agent trên 3 trụ: propose → gate → dispatch → verify; worktree/terminal/orchestration. |

## 1 · RULES — 17 luật harness (policy.yaml, gác tất định)

| ID | Tên | Chức năng |
|----|-----|-----------|
| R1 | no-write-raw | `raw/` là inbox người — agent chỉ đọc, cấm ghi. |
| R2 | require-origin | Mọi wiki file phải có `## Origin` truy nguồn. |
| R3 | index-sync | `wiki/index.md` phải khớp tập file wiki thật; lệch → chặn. |
| R4 | audit-log | Mọi tool-call ghi `audit.jsonl` + sinh `log.md` người-đọc. |
| R5 | folder-structure | Wiki file phải nằm trong concepts/entities/sources/draft/architecture/tours — không ở root. |
| R6 | verify-before-commit | Mọi commit qua gate: validators + lint + drift-test + seq-glass. |
| R7 | proposal-complete | Proposal chờ duyệt phải khai Agent Task Assignment + link Sequence diagram. |
| R8 | session-health | Đầu phiên: báo số rule đang gác + check drift policy/version vs remote. |
| R9 | okf-frontmatter | Wiki content phải có YAML frontmatter OKF (`type` không rỗng). |
| R10 | docs-gate | Mỗi N prompt chưa dùng docs/orca-workflow → nhắc bổ sung tài liệu/eval. |
| R11 | seq-html-glass | Seq diagram HTML phải theo style liquid-glass (docs-site-macos). |
| R12 | pull-before-change | Trước khi làm/fan-out: orchestrator chạy pull-gate sweep 1 lần. |
| R13 | decision-adr | Quyết định 'architecture' phải ref một ADR; vòng đời ADR có gate. |
| R14 | patterns-guard | Kho `llmwiki/patterns/` chỉ sửa khi `LLMWIKI_PATTERNS_UNLOCK=1`. |
| R15 | no-ai-attribution | Commit message cấm ghi công AI (Co-Authored-By/Generated…). |
| R16 | report-show-path | HTML report dưới `llmwiki/html/` phải tự khai đường dẫn tự thân. |
| R17 | problem-tree-flush | SessionEnd: phiên chạm bề mặt framework → xả sổ cây vấn đề. |

## 2 · MECHANISMS — 17 cơ chế (mechanisms.yaml)

| ID | Kind | Chức năng |
|----|------|-----------|
| orientation | hook | Đầu phiên chỉ nguồn query (code-index, wiki, CAPABILITIES) thay vì grep mù. |
| auto-index | hook | Tự thêm row cho wiki file mới vào index.md (self-heal R3). |
| force-query | rule | Ép query wiki/code-graph trước khi đọc/grep rộng. |
| code-index | tool | Code-graph index (search_symbols/get_callers), auto-reindex khi code đổi. |
| code-logger | hook | Ghi log framework bằng code (không nhờ agent nhớ). |
| health-check | tool | So version pattern local ↔ remote ↔ disk (0 token). |
| wiki→fdk | tool | Migrate/mirror wiki cũ sang the-kit (fdk/wiki). |
| harness-lint | tool | Harness tự gác chính nó chống guard câm lặng. |
| harness-doctor | tool | Fire-drill chứng minh từng rule còn cắn (BAD/GOOD). |
| fdk-gate | tool | Cổng "đủ step mới cho push" khi dev framework. |
| harness-local | rule | Gác commit-time local (không chỉ CI). |
| docs-gate | rule | 2 trụ: nhắc bổ sung docs + eval mỗi N lượt. |
| medic | skill | Cổng sức khoẻ tổng / tuyến phòng thủ cuối. |
| medic-mirror | hook | Cuối phiên chạm framework → tự soi medic sớm. |
| secondary-memory | tool | Bộ nhớ thứ cấp: scratch-log + events + memory-map. |
| harness-update | skill | Tự bảo trì framework trên máy user (self-heal). |
| code-state | tool | Overstack tự tường thuật trạng thái code hiện thời. |

## 3 · SKILLS — 72 (gọi bằng `/tên`)

### 3a · wiki-loop (4) — vòng tri thức
| Skill | Chức năng |
|-------|-----------|
| ingest | Xử lý file mới trong `raw/` → chưng cất thành trang wiki. |
| query | Tổng hợp câu trả lời từ wiki; lưu insight mới thành wiki. |
| lint | Health-check wiki định kỳ: orphan, link gãy, mâu thuẫn, stale, index. |
| wiki-room | Mở room (subagent 1 tầng) nạp chi tiết wiki khi context phiên chính rot. |

### 3b · dev-loop (12) — vòng phát triển
| Skill | Chức năng |
|-------|-----------|
| propose | Plan feature trước khi code — draft ở `sources/draft/`, dừng chờ duyệt. |
| impact-check | Map mọi caller/dependent của symbol trước khi sửa code chung. |
| safe-change | Sửa code chung không phá caller hiện có. |
| verify-before-commit | Gate mọi commit: typecheck/lint/smoke → promote draft lên wiki. |
| onboard-codebase | Phân tích sâu codebase → điền wiki architecture/concepts/entities. |
| new-project-setup | Deploy llmwiki vào project mới: template pull, skill install, RTK, seed, onboard. |
| new-skill | Scaffold skill vào cả 2 cây publish cùng lúc. |
| ship | Workflow chốt PUSH/RELEASE/PR/MR: checklist medic + git sạch + version + note. |
| wikieval | Biến wiki golden pages thành eval suite chặn-CI (cheap→expensive). |
| build-now-adapt-later | Dựng phần chắc chắn ngay, nhốt ẩn số sau MỘT adapter để chỉnh sau. |
| loop-runner | Agent-loop có phanh tất định (max_iter/budget/no-progress/escalate). |
| failure-flywheel | Bắt lỗi agent → đếm → tự scaffold rule/skill khi tái diễn (self-evolving). |

### 3c · orchestrate (11) — điều phối đa-agent
| Skill | Chức năng |
|-------|-----------|
| orchestration | Điều phối đa-agent Orca: message/ask-reply/dispatch/DAG/decision-gate. |
| orca-cli | Vận hành Orca worktree/terminal/repo/browser qua CLI công khai. |
| orca-workflow | Quy trình ngày: propose → gate → dispatch → verify. |
| orca-onboard | Onboard codebase song song (scan + git history + batch analyze → wiki+HTML). |
| orca-issue | Vòng xử lý SỰ CỐ first-class (bug/runtime), repro-first. |
| orca-eval | Quét N session gần nhất → distill best-practice → report + action cải tiến. |
| orca-sec-scans | Quét bảo mật (Trivy) + kiểm chứng động giả định dev hay sai. |
| orca-dispatch-reference | Tham chiếu dispatch Antigravity/OpenCode, skill install, AgentMemory, RTK. |
| council | LLM council 3-stage: N seat trả lời → blind peer-rank → chairman + report HTML. |
| trace-grader | Chấm ĐƯỜNG agent đi (tool choice/thứ tự/retry/lặp-lại), không chỉ output. |
| jenkins-agent-l3-deploy | Deploy docker-compose qua Jenkins inbound agent (no-SSH, docker-secrets L3). |

### 3d · utils (45) — tiện ích
| Skill | Chức năng |
|-------|-----------|
| fdk | Front-door dev framework HOẶC distill/author skill (self-contained). |
| medic | Cổng sức khoẻ tổng: luật cắn/drift/docs/code/eval — tuyến phòng thủ cuối. |
| harness-update | Tự bảo trì/migrate/update harness trên máy user (1 lệnh self-heal). |
| harness-tour | Claude tự diễn cho user xem harness chặn mình theo thời gian thực. |
| health-check | Kiểm sức khoẻ pattern template: đủ chưa, drift local, cần sync chưa. |
| sync-template | Sync cải tiến cấu trúc project ↔ repo template master. |
| join-project | Orient nhanh vào project đang chạy đã có llmwiki (read-only). |
| raise-issue | Raise issue đầy bối cảnh vào ledger local + mirror tracker remote. |
| tidy | Sắp xếp gọn kho tài liệu local (html + draft): promote/archive/re-index. |
| ovs-notes | Viewer release-notes overstack tức thì (kiểu /release-notes). |
| frontier-scan | Quét biên giới agent-framework 30 ngày + đối chiếu overstack 8 trục. |
| find-skills | Giúp user khám phá + cài skill khi hỏi "làm sao X / có skill nào cho X". |
| last30days | Nghiên cứu người ta nói gì về topic trong 30 ngày (Reddit/X/YT/HN…). |
| md-to-html | Render Markdown → HTML standalone (Mermaid, Chart.js, table, TOC). |
| docs-site-macos | Docs site macOS liquid-glass (1 HTML, diagram SVG động, traffic-light). |
| cursor-animated-sites | Walkthrough cursor-animated (step-list + folder-tree gõ-vào theo bước). |
| tour-guide | In-app product tour (spotlight overlay tự viết, 0 dependency). |
| tour-guide-supademo | Style Supademo cho tour-guide (blinker hotspot/tooltip/progress). |
| extract-site | Trích + chuyển website/docs site thành markdown sạch. |
| web-clone | Lưu 1 trang thành MỘT HTML tự-chứa (UI+resource offline). |
| web-crawl | Crawl/scrape web → markdown sạch cho LLM. |
| check-approve | Sinh 1-liner trace lệnh approve/return/reject DMS trên log BE+FE. |
| uat-nonit-testcase | Sinh test case/checklist UAT cho người dùng nghiệp vụ NON-IT. |
| computer-use | Điều khiển desktop app qua accessibility tree/screenshot/action. |
| cavecrew | Hướng dẫn delegate cho subagent caveman (investigator/builder/reviewer). |
| caveman | Chế độ giao tiếp siêu-nén (~75% ít token), giữ chính xác kỹ thuật. |
| caveman-commit | Sinh commit message siêu-nén (Conventional Commits). |
| caveman-compress | Nén file memory (CLAUDE.md/todo) sang caveman format. |
| caveman-review | Review PR siêu-nén (1 dòng: vị trí/vấn đề/fix). |
| caveman-stats | Hiện token thật + tiết kiệm phiên (đọc session log). |
| caveman-help | Thẻ tham chiếu nhanh mọi mode/skill caveman. |
| brandkit | Sinh ảnh brand-kit cao cấp (logo/identity/visual-world). |
| design-taste-frontend | Anti-slop frontend (landing/portfolio/redesign) — design system thật. |
| design-taste-frontend-v1 | Bản v1 gốc của taste-skill (giữ tương thích ngược). |
| redesign-existing-projects | Nâng cấp web/app cũ lên chất lượng cao, không phá chức năng. |
| high-end-visual-design | Dạy AI thiết kế như agency: font/spacing/shadow/card/animation "đắt tiền". |
| gpt-taste | UX/UI + GSAP motion cao cấp (randomize layout, AIDA, ScrollTrigger). |
| minimalist-ui | Giao diện editorial tối giản (monochrome ấm, bento phẳng, pastel). |
| industrial-brutalist-ui | Giao diện brutalist cơ khí (Swiss print + military terminal). |
| image-to-code | Image-to-code web cho Codex (sinh design image → implement khớp). |
| imagegen-frontend-web | Sinh ảnh direction web (1 ảnh/section, palette nhất quán). |
| imagegen-frontend-mobile | Sinh ảnh concept màn hình app mobile (iOS/Android, phone mockup). |
| stitch-design-taste | Design system cho Google Stitch (sinh DESIGN.md agent-friendly). |
| full-output-enforcement | Ép sinh code đầy đủ, cấm placeholder, xử lý token-limit sạch. |
| snapshot-push | Push repo ngoài (bonbon-ai) dạng snapshot đầy đủ (be/+fe/). |

## 4 · VALIDATORS — 14 (ép rule bằng code)

| Validator | Ép rule | Chức năng |
|-----------|---------|-----------|
| no_write_raw | R1 | Chặn ghi vào `raw/`. |
| origin_required | R2 | File wiki phải có `## Origin`. |
| index_sync | R3 | `index.md` khớp file wiki thật (git-aware). |
| folder_structure | R5 | Wiki file nằm đúng subfolder, không ở root. |
| proposal_complete | R7 | Proposal khai đủ ai-làm-gì + seq diagram. |
| okf_frontmatter | R9 | Wiki content tuân OKF v0.1 (YAML `type`). |
| decision_adr | R13 | Quyết định architecture → ADR + vòng đời ADR. |
| patterns_guard | R14 | Bảo vệ kho `llmwiki/patterns/`. |
| no_ai_attribution | R15 | Commit không ghi công AI. |
| report_show_path | R16 | HTML report tự khai đường dẫn. |
| task_lifecycle | Trụ 3 | Ép task-tracking bằng code (proposed→done, audit chain). |
| code_health | Trụ 4 | Cổng CI ngôn-ngữ tất định (compile/lint). |
| agent_claude_parity | — | `AGENT.md` ↔ `CLAUDE.md` mục Skills khớp nhau. |
| duplicate_basename | — | Dưới `wiki/`, không basename `.md` trùng ở 2 nơi. |

## 5 · fdk/tools — 16 công cụ dev framework

| Tool | Chức năng |
|------|-----------|
| build-wiki-graph | Sinh wiki-graph whiteboard: đồ thị wiki + code (import đa ngôn ngữ). |
| code_imports | Trích quan hệ `imports` language-agnostic self-contained. |
| build-overstack-docs | Sinh tài liệu USER cho overstack (overstack.html). |
| build-capabilities | Sinh bản đồ năng lực bằng code, luôn-mới, cả 2 bối cảnh. |
| build-cheatsheet | Nhồi toàn bộ SKILL.md vào trang cheatsheet để search. |
| build-docs-index | Sinh 1 trang glass HTML làm dashboard chính cho llmwiki. |
| build-health-dashboard | Sinh trang glass "sức khỏe framework". |
| build-skill-search | Index BM25 + CLI search cho skill Orca. |
| whiteboard-skill-map | Bản đồ quan hệ skill dạng đồ thị (reuse engine wiki-graph). |
| wiki-relations | Migrate frontmatter `id` + `relations` cho trang wiki. |
| medic | Cổng sức khoẻ tổng / tuyến phòng thủ cuối. |
| code-state | Overstack tự tường thuật trạng thái code. |
| memory-map | VIEW bộ nhớ thứ cấp: scratch-log + ledger + events theo session. |
| artifacts | Manifest vòng đời artifact local-only (render/draft). |
| docs-curate | Sắp xếp gọn kho tài liệu local. |
| new-skill | Scaffold skill vào cả 2 cây publish. |

## 6 · harness/scripts — 44 script hạ tầng

| Script | Chức năng |
|--------|-----------|
| harness-lint | Harness tự gác chính nó chống guard câm lặng. |
| harness-doctor | Fire-drill chứng minh từng rule còn cắn. |
| fdk-gate | Cổng "đủ step mới cho push" khi dev framework. |
| health-check | L4 eval (0 token): sức khoẻ pattern sync version vs remote. |
| wiki-health | L4 eval tĩnh (0 token): broken wikilink/orphan/stale. |
| wiki-graph | Query đồ thị tri thức (0 token, no-LLM): backlinks/orphans/broken. |
| okf-check | Kiểm + migrate OKF v0.1 cho cây wiki. |
| sync-template | Downstream /sync-template một-shot (kéo file-list từ manifest). |
| sync-skills | Giữ 2 cây skill khớp nhau chống drift. |
| skill-registry | Nguồn chân lý danh tính skill, cross-check. |
| arch-scan | Quét xung đột "văn bản vs luật" trong skill/doc. |
| archetype | Gọi 5 archetype Boris Cherny như persona dispatch. |
| audit | Audit + backfill nợ wiki trong 1 process. |
| code-logger | Ghi log framework bằng code + task-lifecycle (T-id). |
| council | Engine protocol tất định LLM-council (anonymize/rank/report). |
| mem-rank | Agent-memory layer: ADD/UPDATE/DELETE/NOOP + retrieve token-overlap. |
| retrieval-eval | Đo truy hồi skill query (hit@k + token), baseline + diff. |
| query-log | Telemetry bằng code cho skill query. |
| query-proxy | Bản tất định mô phỏng chiến lược truy hồi query. |
| scratch-log | Bộ nhớ thứ cấp tầng thô + distill. |
| trace-grader | Chấm ĐƯỜNG agent đi, không chỉ output. |
| trace-otel | Biến audit log phẳng thành OpenTelemetry có cấu trúc. |
| token-budget | Governor token + dollar per-session/per-task. |
| loop-runner | Agent-loop có phanh tất định (engine). |
| flywheel | Máy self-evolving capture→count→draft (fail/success). |
| failure-flywheel | Shim → flywheel --kind failure. |
| success-flywheel | Shim → flywheel --kind success. |
| dispatch-verify | Hậu-kiểm R7: đối chiếu lời-hứa proposal. |
| spec-gate | Cổng Spec-Driven Development (spec = nguồn chân lý). |
| sweep-gate | Institutionalise archetype "Sweeper" của Boris Cherny. |
| prospect-critic | Reflection PROSPECTIVE: kiểm PLAN trước khi chạy. |
| claim-receipts | Gate hallucination trực tiếp: trích file-claim kiểm chứng. |
| inject-scan | Quét tool-output/retrieved content tìm prompt-injection gián tiếp. |
| egress-guard | Least-privilege guard cho egress mạng của agent. |
| scoped-hooks | Cho SKILL.md khai validator guard riêng của nó. |
| adapt-registry | Câu trả lời đứng "cái gì còn chưa verify". |
| bnal_config | Shared BNAL adapter loader (nơi duy nhất map). |
| bnal_guard | Shared emit advisory/block per mode+verified. |
| bnal_metrics | Shared by-code JSONL capture (gitignore + fail-open). |
| bnal-selftest | Meta-gate chống drift danh sách self-test. |
| cor | Controlled Output Renderer (shared invariants). |
| web-clone | Lưu page thành 1 HTML tự-chứa. |
| web-crawl | Fetch page → markdown cho LLM. |
| wikieval | Biến wiki golden pages thành eval chặn-CI. |

## Origin
- Rà + sinh 2026-07-05 từ policy.yaml / mechanisms.yaml / skills / validators / fdk-tools / harness-scripts.
- Đối chiếu chéo với `fdk/CAPABILITIES.md` (bản đồ năng lực auto-gen) + `llmwiki/html/overstack.html`.
