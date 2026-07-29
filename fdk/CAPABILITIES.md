<!-- SINH BẰNG CODE: build-capabilities.py — ĐỪNG sửa tay; chạy lại để cập nhật. -->
# CAPABILITIES — toàn bộ đồ nghề (luôn-mới, đếm từ đĩa)

**84 skill · 18 rule · 19 fdk-tool · 65 harness-script.** Agent: đây là danh sách ĐẦY ĐỦ những gì bạn có để dùng. Tìm nhanh: `python3 fdk/tools/build-skill-search.py` rồi `find-skill "<việc cần làm>"`. Phát triển framework: gọi `/fdk`.

## Skills (gọi bằng `/<tên>`)

### wiki-loop (5)
- **`/ingest`** — Process new file in llmwiki/raw/ and distill into wiki pages
- **`/lint`** — Periodic wiki health check
- **`/query`** — Synthesize answer from wiki; persist new insights as wiki entries
- **`/record-episode`** — Ghi một SESSION EPISODE có cấu trúc (tầng nhớ episodic) vào memory store để phiên sau truy…
- **`/wiki-room`** — Mở room (subagent 1 tầng) nạp chi tiết wiki khi context phiên chính đã rot

### dev-loop (16)
- **`/build-now-adapt-later`** — When a task is blocked by missing or unverified information (an undocumented protocol, an …
- **`/failure-flywheel`** — Capture each agent failure, bucket and count it deterministically, and when a failure clas…
- **`/impact-check`** — Map all callers and dependents of a symbol before modifying shared code
- **`/loop-runner`** — Deterministic guardrailed agent-loop driver
- **`/new-project-setup`** — Deploy llmwiki từ đầu vào project mới
- **`/new-skill`** — Scaffold a new skill into both publish trees at once
- **`/onboard-codebase`** — Deep codebase analysis
- **`/plan`** — Mở rộng một draft SPEC ĐÃ ĐƯỢC DUYỆT thành kế hoạch thi hành được
- **`/propose`** — Plan a feature before coding
- **`/qc-code`** — Review code phong cách SENIOR 10 năm
- **`/safe-change`** — Modify shared code without breaking existing callers
- **`/ship`** — Workflow chốt PUSH/RELEASE/PR/MR
- **`/skill-provenance`** — Ghi và kiểm provenance (nguồn + sha256 checksum) cho skill
- **`/teach-me`** — Giải thích MỘT thứ (một file, hàm, tính năng, hay hệ thống) theo cấu trúc cố định: cách ch…
- **`/verify-before-commit`** — Gate every commit
- **`/wikieval`** — Turn wiki golden pages into a CI-blocking eval suite with a cheap→expensive assertion casc…

### orchestrate (13)
- **`/council`** — Run a Karpathy-style LLM council (3-stage multi-agent evaluation) on top of the existing o…
- **`/jenkins-agent-l3-deploy`** — Deploy a docker-compose app via a Jenkins INBOUND AGENT running on the target server (no S…
- **`/orca-cli`** — Use the public `orca` CLI to operate Orca-managed worktrees/workspaces, terminals, repos, …
- **`/orca-dispatch-reference`** — Reference for Antigravity/OpenCode dispatch, skill installation, AgentMemory, RTK token pr…
- **`/orca-eval`** — Quét N session Claude Code gần nhất, distill best practices thành report md + đề xuất acti…
- **`/orca-handover`** — Sinh MỘT file .md bàn giao đủ dày để một phiên KHÁC (người hoặc agent, không có context nà…
- **`/orca-issue`** — Vòng xử lý SỰ CỐ first-class
- **`/orca-onboard`** — Parallel codebase onboarding
- **`/orca-sec-scans`** — Quét bảo mật mã nguồn bằng Trivy
- **`/orca-workflow`** — Daily propose → gate → dispatch workflow with Orca
- **`/orchestration`** — Use Orca orchestration for structured multi-agent coordination: threaded messages, blockin…
- **`/trace-grader`** — Score the PATH an agent took (tool choice, ordering, retries, repeatability, grounding)
- **`/wayfinder`** — Lập bản đồ cho một chunk việc QUÁ LỚN với một phiên agent và còn MÙ MỜ

### utils (50)
- **`/agent-reach`** — MUST USE when user wants to research/search/look up/find anything on the internet
- **`/brandkit`** — Premium brand-kit image generation skill for creating high-end brand-guidelines boards, lo…
- **`/cavecrew`** — Decision guide for delegating to caveman-style subagents
- **`/caveman`** — Ultra-compressed communication mode
- **`/caveman-commit`** — Ultra-compressed commit message generator
- **`/caveman-compress`** — Compress natural language memory files (CLAUDE.md, todos, preferences) into caveman format…
- **`/caveman-help`** — Quick-reference card for all caveman modes, skills, and commands
- **`/caveman-review`** — Ultra-compressed code review comments
- **`/caveman-stats`** — Show real token usage and estimated savings for the current session
- **`/check-approve`** — Sinh sẵn 1-liner để trace 1 lệnh approve/return/reject của DMS trên log BE (docker) + FE p…
- **`/computer-use`** — Use Orca's computer-use CLI to inspect and operate local desktop app windows through acces…
- **`/cursor-animated-sites`** — Build an interactive "cursor-animated walkthrough" page on top of the /docs-site-macos gla…
- **`/design-taste-frontend`** — Anti-slop frontend skill for landing pages, portfolios, and redesigns
- **`/design-taste-frontend-v1`** — The original v1 taste-skill, preserved for projects depending on its exact behavior
- **`/docs-curate`** — Sắp xếp gọn kho tài liệu LOCAL (llmwiki/html/ + wiki/sources/draft/) khi phình to
- **`/docs-site-macos`** — Build a beautiful macOS-inspired documentation site (single HTML file) with a liquid-glass…
- **`/extract-site`** — Extract and convert a website or docs site into clean markdown
- **`/fable5`** — Reasoning protocol distilled from Claude Fable 5
- **`/fdk`** — Front-door on-demand cho phát triển framework HOẶC distill/author một skill
- **`/fdk-uat`** — UAT THẬT cho một bản framework sắp phát hành
- **`/find-skills`** — Helps users discover and install agent skills when they ask questions like "how do I do X"…
- **`/frontier-scan`** — Quét biên giới agent-framework 30 ngày qua và đối chiếu overstack theo 8 trục (frontier-ga…
- **`/full-output-enforcement`** — Overrides default LLM truncation behavior
- **`/gpt-taste`** — Elite UX/UI & Advanced GSAP Motion Engineer
- **`/hallmark`** — SÀN design mặc định của overstack (anti-AI-slop)
- **`/harness-tour`** — Tour
- **`/harness-update`** — TỰ BẢO TRÌ framework overstack trên máy user (self-maintain)
- **`/health-check`** — Kiểm tra sức khỏe "pattern chuẩn" của template
- **`/high-end-visual-design`** — Teaches the AI to design like a high-end agency
- **`/i-have-adhd`** — Shape output for a reader with ADHD
- **`/image-to-code`** — Elite website image-to-code skill for Codex
- **`/imagegen-frontend-mobile`** — Elite mobile app image-generation skill for creating premium, app-native screen concepts a…
- **`/imagegen-frontend-web`** — Elite frontend image-direction skill for generating premium, conversion-aware website desi…
- **`/industrial-brutalist-ui`** — Raw mechanical interfaces fusing Swiss typographic print with military terminal aesthetics
- **`/join-project`** — Orient nhanh vào dự án đang chạy đã có llmwiki
- **`/last30days`** — Research what people actually say about any topic in the last 30 days
- **`/md-to-html`** — Render Markdown thành standalone HTML
- **`/medic`** — Cổng sức khoẻ tổng / tuyến phòng thủ cuối của framework overstack
- **`/minimalist-ui`** — Clean editorial-style interfaces
- **`/ovs-notes`** — Viewer release-notes overstack TỨC THÌ (kiểu /release-notes của Claude CLI)
- **`/raise-issue`** — Raise một ISSUE đầy đủ bối cảnh vào ledger local (draft) để dev khác pull về xử lý ở BẤT K…
- **`/redesign-existing-projects`** — Upgrades existing websites and apps to premium quality
- **`/snapshot-push`** — Push bonbon-ai outer repo as full snapshot, including be/ and fe/ content
- **`/stitch-design-taste`** — Semantic Design System Skill for Google Stitch
- **`/sync-template`** — Sync structural improvements between project and master template repo
- **`/tour-guide`** — Thêm một in-app product tour (spotlight onboarding overlay) tự viết, KHÔNG cần thư viện (k…
- **`/tour-guide-supademo`** — Style thiết kế Supademo cho in-app product tour (dùng kèm skill tour-guide
- **`/uat-nonit-testcase`** — Tạo bộ test case / checklist UAT cho người dùng nghiệp vụ NON-IT (C&B, kế toán, vận hành)
- **`/web-clone`** — Clone a website
- **`/web-crawl`** — Crawl/scrape a website or single page into clean LLM-ready MARKDOWN

## Harness rules (gác tự động — vi phạm bị chặn)
- **R1** — no-write-raw
- **R2** — origin-required
- **R3** — index-sync
- **R4** — audit-log
- **R5** — folder-structure
- **R6** — verify-before-commit
- **R7** — proposal-complete
- **R8** — session-health
- **R9** — okf-frontmatter
- **R10** — docs-gate
- **R11** — seq-html-glass-style
- **R12** — pull-before-change
- **R13** — decision-to-adr
- **R14** — patterns-protected
- **R15** — no-ai-attribution
- **R16** — report-show-path
- **R17** — problem-tree-flush
- **R18** — plan-executable

## FDK tools (`python3 fdk/tools/<x>`)
- `artifacts.py`
- `build-capabilities.py`
- `build-cheatsheet.py`
- `build-docs-index.py`
- `build-health-dashboard.py`
- `build-overstack-docs.py`
- `build-skill-search.py`
- `build-wiki-graph.py`
- `code-state.py`
- `code_imports.py`
- `docs-curate.py`
- `frontend-antipattern.py`
- `medic.py`
- `memory-map.py`
- `new-skill.py`
- `skill-provenance.py`
- `skill-usage.py`
- `whiteboard-skill-map.py`
- `wiki-relations.py`

## Harness scripts (`python3 harness/scripts/<x>`)
- `adapt-registry.py`
- `arch-scan.py`
- `archetype.py`
- `audit.py`
- `bnal-selftest.py`
- `bnal_config.py`
- `bnal_guard.py`
- `bnal_metrics.py`
- `capability-stamp.py`
- `claim-receipts.py`
- `code-logger.py`
- `council.py`
- `decision-anchoring-crosscheck.py`
- `decision-guard.py`
- `decision-liveness.py`
- `dep-health.py`
- `design-variety.py`
- `dispatch-verify.py`
- `egress-guard.py`
- `embed-ollama.py`
- `embed-voyage.py`
- `failure-flywheel.py`
- `fdk-gate.py`
- `flywheel.py`
- `frontier.py`
- `grounding-check.py`
- `harness-doctor.py`
- `harness-lint.py`
- `health-check.py`
- `hub.py`
- `inject-scan.py`
- `ledger-snapshot.py`
- `loop-runner.py`
- `mem-proxy.py`
- `mem-rank.py`
- `okf-check.py`
- `orca-dispatch.py`
- `orca-reconcile.py`
- `ovs-notes.py`
- `prospect-critic.py`
- `provenance-log.py`
- `qc-regression.py`
- `query-log.py`
- `query-proxy.py`
- `retrieval-eval.py`
- `scoped-hooks.py`
- `scratch-log.py`
- `skill-health.py`
- `skill-registry.py`
- `skill-resolve-eval.py`
- `spec-gate.py`
- `success-flywheel.py`
- `sweep-gate.py`
- `sync-skills.py`
- `sync-template.py`
- `token-budget.py`
- `trace-grader.py`
- `trace-otel.py`
- `unknown-ledger.py`
- `web-clone.py`
- `web-crawl.py`
- `wiki-graph.py`
- `wiki-health.py`
- `wiki-sync.py`
- `wikieval.py`

## Neo bằng chứng — 211/211 năng lực có neo KHAI BÁO
**Đọc cho đúng: đây KHÔNG phải bằng chứng năng lực còn SỐNG.** Mỗi năng lực được map tất định tới một *điểm neo* bằng chứng trên đĩa (frontmatter `proof:` > rule-map > tests > self-test > golden > medic). Việc map là **tĩnh** — nó kiểm file/chuỗi có mặt, **không thực thi gì cả**. Nó bắt được ca 'năng lực này chẳng có test/golden/rule nào neo vào' (hữu ích thật), nhưng KHÔNG bắt được ca 'test có mà đỏ' hay 'engine có mà chết'. Muốn biết một dependency ngoài còn sống thì hỏi `harness/scripts/dep-health.py`. Chi tiết neo: `build-capabilities.py --capproof-json`.

## TRÙNG-ỨNG-VIÊN (19) — máy phát hiện, NGƯỜI phán (dedupe = vòng /propose riêng)
- `mech:medic` ↔ `mech:medic-mirror` — name-token: medic
- `script:embed-ollama.py` ↔ `script:embed-voyage.py` — desc-jaccard 0.82
- `script:failure-flywheel.py` ↔ `script:flywheel.py` — name-token: flywheel
- `script:failure-flywheel.py` ↔ `script:success-flywheel.py` — desc-jaccard 0.50
- `script:flywheel.py` ↔ `script:success-flywheel.py` — name-token: flywheel
- `script:flywheel.py` ↔ `skill:failure-flywheel` — name-token: flywheel
- `script:frontier.py` ↔ `skill:frontier-scan` — name-token: frontier
- `script:harness-lint.py` ↔ `skill:lint` — name-token: lint
- `script:orca-dispatch.py` ↔ `skill:orca-dispatch-reference` — name-token: dispatch
- `script:query-log.py` ↔ `skill:query` — name-token: query
- `script:query-proxy.py` ↔ `skill:query` — name-token: query
- `script:wiki-graph.py` ↔ `tool:build-wiki-graph.py` — name-token: graph
- `skill:caveman` ↔ `skill:caveman-commit` — name-token: caveman
- `skill:caveman` ↔ `skill:caveman-compress` — name-token: caveman
- `skill:caveman` ↔ `skill:caveman-help` — name-token: caveman
- `skill:caveman` ↔ `skill:caveman-review` — name-token: caveman
- `skill:caveman` ↔ `skill:caveman-stats` — name-token: caveman
- `skill:design-taste-frontend` ↔ `skill:design-taste-frontend-v1` — name-token: design+frontend
- `skill:tour-guide` ↔ `skill:tour-guide-supademo` — name-token: guide+tour

## Origin
- Sinh bằng `fdk/tools/build-capabilities.py` từ đĩa (skills/, policy.yaml, fdk/tools/, harness/scripts/, sync-skills LOOP_MAP). KHÔNG hardcode.
