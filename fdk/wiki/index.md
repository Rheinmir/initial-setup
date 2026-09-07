# Wiki Index

| File | Type | Summary |
|------|------|---------|
| [frontier-gap-scan](concepts/frontier-gap-scan.md) | concept | Quét đối thủ hàng tuần để overstack là frontier TOÀN DIỆN — baseline 03/07 + runbook scout + 5 issue gap |
| [query-retrieval-eval](concepts/query-retrieval-eval.md) | concept | Đo TRUY HỒI của skill query (hit@k+token), telemetry + query 3-tầng L0→L1, −65% token giữ recall |
| [design-pattern-v1](sources/design-pattern-v1.md) | source | Học Từ Thiền Phần 000 — System Design fundamentals · Phan Văn Ngọc Thắng |
| [design-pattern-v2](sources/design-pattern-v2.md) | source | Học Từ Thiền Phần 001 — Data, APIs & Distributed Systems · Trần Hồng Gấm |
| [design-pattern-v3](sources/design-pattern-v3.md) | source | Học Từ Thiền Phần 002 — Microservices, Caching & HA Patterns · Bạch Hồng Vinh |
| [210626-design-pattern-infographic](draft/orca/210626-design-pattern-infographic.md) | draft | Output report — orca-workflow: 3 MD + 3 HTML infographic từ Học Từ Thiền series |
| [design-pattern](sources/draft/design-pattern.md) | source | 3 YouTube links Học Từ Thiền series — nguồn gốc request infographic |
| [sync-template](sources/draft/sync-template.md) | source | Skill sync template harness từ remote — Step 0 health-check + Step 6b refresh version.json |
| [220626-design-pattern-html-refactor](draft/orca/220626-design-pattern-html-refactor.md) | draft | 2026-06-22 — Refactor 3 HTML: v1→5 sections, v2→7 sections, v3→10 sections |
| [R10](concepts/R10.md) | concept | R10 policy: docs-gate hook nhắc bổ sung docs mỗi N prompt (UserPromptSubmit) |
| [250626-onboard-setup](draft/orca/250626-onboard-setup.md) | draft | 2026-06-25 |
| [architecture](concepts/architecture.md) | concept | Architecture of the setup template/skill/harness repo — 4 layers |
| [onboarding-tour](concepts/onboarding-tour.md) | concept | 10-step guided tour of the setup repo |
| [project-structure](entities/project-structure.md) | entity | Top-level structure + hot files of the setup repo |
| [cursor-explain-site](concepts/cursor-explain-site.md) | concept | How-to reverse-engineer & clone a site (extract-site Mode 3) |
| [250626-eval-report](draft/orca/250626-eval-report.md) | draft | 2026-06-25 |
| [250626-walkthroughs](html/250626-walkthroughs.html) | index | 2026-06-25 |
| [rule-registry](concepts/rule-registry.md) | concept | 2026-06-27 — Registry R1..R12 (1 trang) + 2 policy.yaml + R6=verify-before-commit |
| [fdk](concepts/fdk.md) | concept | 2026-06-27 — Framework Development Kit: front-door + pre-flight + module map (không miss rule, không dẫm module cũ) |
| [ADR-001-policy-as-source-of-truth](sources/adr/ADR-001-policy-as-source-of-truth.md) | decision | 2026-06-27 — policy.yaml nguồn chân lý, thin-adapter (case R11) |
| [ADR-002-pull-before-change-gates](sources/adr/ADR-002-pull-before-change-gates.md) | decision | 2026-06-27 — R12 git-level+orchestrator, bỏ per-edit, đa-vendor/đa-subrepo |
| [ADR-003-skill-as-single-source-of-truth](sources/adr/ADR-003-skill-as-single-source-of-truth.md) | decision | 2026-06-27 — skill con = SoT, orchestrator delegate; Claude nghĩ / CLI rẻ render |
| [ADR-004-framework-dev-context-opt-in](sources/adr/ADR-004-framework-dev-context-opt-in.md) | decision | 2026-06-27 — framework-dev context opt-in (/fdk), không auto-bơm SessionStart; audit lỗi tư duy |
| [extract-site](concepts/extract-site.md) | concept | 2026-06-27 — stub skill extract-site (giải broken wikilink) |
| [docs-site-macos-skill](concepts/docs-site-macos-skill.md) | concept | 2026-06-27 — stub skill docs-site-macos (giải broken wikilink) |
| [270626-session-review](draft/orca/270626-session-review.md) | draft | 2026-06-27 — Review tổng hợp phiên: 13 commit, 10/10 test, caveat |
| [270626-session-review-html](sources/draft/270626-session-review-html.md) | draft | 2026-06-27 — docs-site-macos render của session review |
<!-- index:auto:start -->
| [r2-origin-section](sources/evals/r2-origin-section.md) | eval | Golden: R2 origin-required |
| [sql-active-users](sources/evals/sql-active-users.md) | eval | Golden: SQL active users |
| [feature-catalog](concepts/feature-catalog.md) | concept | Feature Catalog — và VÌ SAO mỗi cái phải có |
| [ADR-005-logger-and-capabilities-travel-downstream](sources/adr/ADR-005-logger-and-capabilities-travel-downstream.md) | decision | ADR-005: logger + capability-map đi xuống cùng dự án (scoped) |
| [harness-enforcement-floor](concepts/harness-enforcement-floor.md) | concept | Harness enforcement floor — vì sao CI mới là sàn thật |
| [ADR-006-blocking-stays-hook-mcp-for-tooling](sources/adr/ADR-006-blocking-stays-hook-mcp-for-tooling.md) | decision | ADR-006: lớp chặn giữ là hook/CI, MCP chỉ cho công cụ/đọc |
| [ADR-007-wiki-scanner-skip-gitignored-at-lister](sources/adr/ADR-007-wiki-scanner-skip-gitignored-at-lister.md) | decision | ADR-007: wiki-tree scanner lọc gitignored tại lister (nguồn), không per-consumer; guard mọi bản hand-synced |
| [ADR-008-framework-wiki-lives-in-the-kit](sources/adr/ADR-008-framework-wiki-lives-in-the-kit.md) | decision | ADR-008: wiki riêng của framework sống trong the kit (fdk/wiki); llmwiki/wiki là khuôn per-project |
| [ADR-009-session-orientation-autoindex-forcequery](sources/adr/ADR-009-session-orientation-autoindex-forcequery.md) | decision | ADR-009: phiên mới biết hệ thống có gì (orientation) + auto-index + force-query grounding |
| [ADR-010-decision-to-adr-gate](sources/adr/ADR-010-decision-to-adr-gate.md) | decision | ADR-010: gate decision→ADR (R13) — ép quyết định có ADR, nhưng cho edit + xóa khi bị đè |
| [290626-bnal-trend-features-docs](sources/draft/290626-bnal-trend-features-docs.md) | draft | 290626-bnal-trend-features-docs |
| [150626-health-check-pattern-sync](sources/draft/archive/analysis/150626-health-check-pattern-sync.md) | draft | 150626-health-check-pattern-sync |
| [180626-orca-framework-overview](sources/draft/archive/analysis/180626-orca-framework-overview.md) | draft | 180626-orca-framework-overview |
| [230626-harness-docs-gate-orca-guard-report](sources/draft/archive/analysis/230626-harness-docs-gate-orca-guard-report.md) | draft | 230626-harness-docs-gate-orca-guard-report |
| [250626-cicd-lifecycle](sources/draft/archive/analysis/250626-cicd-lifecycle.md) | draft | 250626-cicd-lifecycle |
| [250626-harness-arch-vs-current](sources/draft/archive/analysis/250626-harness-arch-vs-current.md) | draft | 250626-harness-arch-vs-current |
| [250626-harness-mcp-scenarios](sources/draft/archive/analysis/250626-harness-mcp-scenarios.md) | draft | 250626-harness-mcp-scenarios |
| [250626-harness-poc-vendor-neutral](sources/draft/archive/analysis/250626-harness-poc-vendor-neutral.md) | draft | 250626-harness-poc-vendor-neutral |
| [230626-docs-gate-register](sources/draft/archive/proposals/230626-docs-gate-register.md) | draft | Proposal: Hoàn tất đăng ký docs-gate hook (R10) |
| [230626-docs-skill-okf](sources/draft/archive/proposals/230626-docs-skill-okf.md) | draft | Proposal: skill tạo docs đạt chuẩn OKF v0.1 (vá nguồn tạo nợ) |
| [230626-harness-update-sub30s](sources/draft/archive/proposals/230626-harness-update-sub30s.md) | draft | Proposal: đưa `/harness-update` về dưới 30s |
| [230626-orca-guard-failopen](sources/draft/archive/proposals/230626-orca-guard-failopen.md) | draft | Proposal: hook thiếu file phải FAIL-OPEN, đừng chặn cả CLI |
| [230626-orca-guard-hook](sources/draft/archive/proposals/230626-orca-guard-hook.md) | draft | Proposal: orca_guard.py — chặn lỗi orca CLI bằng máy, không bằng prose |
| [230626-sync-template-sub30s](sources/draft/archive/proposals/230626-sync-template-sub30s.md) | draft | Proposal: đưa `/sync-template` về dưới 30s |
| [270626-framework-gap-backfill](sources/draft/archive/proposals/270626-framework-gap-backfill.md) | draft | 270626 — Framework gap backfill |
| [270626-propose-single-source](sources/draft/archive/proposals/270626-propose-single-source.md) | draft | 270626-propose-single-source |
| [270626-r12-v3-workspace-aware](sources/draft/archive/proposals/270626-r12-v3-workspace-aware.md) | draft | 270626 — R12 v3 workspace-aware |
| [270626-wiki-sync-structure](sources/draft/archive/proposals/270626-wiki-sync-structure.md) | draft | 270626-wiki-sync-structure |
| [280626-merge-docs-site-macos-dup](sources/draft/archive/proposals/280626-merge-docs-site-macos-dup.md) | draft | Hợp nhất 2 skill docs-site-macos trùng tên |
| [ADR-016-no-ai-attribution-in-commits](sources/adr/ADR-016-no-ai-attribution-in-commits.md) | decision | ADR-016: Không ghi công AI trong commit (R15) |
| [framework-dev-antipatterns](concepts/framework-dev-antipatterns.md) | concept | Framework-dev anti-patterns |
| [ADR-017-global-shared-engine-repo-data-travel](sources/adr/ADR-017-global-shared-engine-repo-data-travel.md) | decision | ADR-017: Global-shared engine + repo-data travel |
| [010726-council-output](draft/orca/010726-council-output.md) | auto |  |
| [adapt-modes-pick](sources/evals/adapt-modes-pick.md) | eval | Golden: adapt-modes-pick |
| [capproof-liveness](sources/evals/capproof-liveness.md) | eval | Golden: capproof-liveness |
| [map-not-territory](concepts/map-not-territory.md) | concept | map-not-territory — tìm unknowns trước khi prompt |
<!-- index:auto:end -->
| [harness-local](concepts/harness-local.md) | concept | harness-local — harness RIÊNG của dự án |
| [ADR-011-project-local-harness](sources/adr/ADR-011-project-local-harness.md) | source | "ADR-011: project-local harness — dự án tự phát triển rule riêng (P-namespace, sandbox-safe)" |
| [ADR-012-five-trend-features-bnal](sources/adr/ADR-012-five-trend-features-bnal.md) | source | "ADR-012: 5 trend 2026 → 5 chức năng qua build-now-adapt-later (core now, adapter verified:false)" |
| [ADR-013-five-more-trend-features-bnal](sources/adr/ADR-013-five-more-trend-features-bnal.md) | source | "ADR-013: 5 trend 2026 nữa → 5 chức năng qua build-now-adapt-later (memory · cost · injection · hallucination · prospect |
| [ADR-014-protected-pattern-library](sources/adr/ADR-014-protected-pattern-library.md) | source | "ADR-014: kho pattern tham chiếu BẢO VỆ (llmwiki/patterns/) + R14 patterns-protected" |
| [boris-cherny-agent-roles](concepts/boris-cherny-agent-roles.md) | concept | "Boris Cherny — 5 agent role trong Claude Code (scope deep-dive)" |
| [ADR-015-boris-archetypes-into-template](sources/adr/ADR-015-boris-archetypes-into-template.md) | source | "ADR-015: áp 5 archetype Boris Cherny vào template — sweep-gate (nhịp Sweeper) + persona dispatch + phase-map" |
| [outer-harness-evaluation](concepts/outer-harness-evaluation.md) | concept | 2026-06-30 — Distill Outer Harness (Phúc) + council 3-ghế đánh giá: overstack mạnh Trụ 2/4, thiếu Trụ 1 (cost) & 5 (audit); roadmap per-run JSONL trước |
| [fdk-dev-strategy](concepts/fdk-dev-strategy.md) | concept | 8 nguyên tắc "Mongol pattern" cho phát triển framework — decision latency, chuẩn hóa, modular, intelligence-first, logistics/harness, demo liên tục |
| [mongol-ai-strategy](sources/mongol-ai-strategy.md) | source | Nguồn raw: 8 bài học Đế quốc Mông Cổ → chiến lược AI (`llmwiki/raw/fdk-stragegy.md`) |
