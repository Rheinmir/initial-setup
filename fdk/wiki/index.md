# Wiki Index

| File | Type | Summary |
|------|------|---------|
| [frontier-gap-scan](concepts/frontier-gap-scan.md) | concept | Quét đối thủ hàng tuần để overstack là frontier TOÀN DIỆN — baseline 03/07 + runbook scout + 5 issue gap |
| [query-retrieval-eval](concepts/query-retrieval-eval.md) | concept | Đo TRUY HỒI của skill query (hit@k+token), telemetry + query 3-tầng L0→L1, −65% token giữ recall |
| [design-pattern-v1](sources/design-pattern-v1.md) | source | Học Từ Thiền Phần 000 — System Design fundamentals · Phan Văn Ngọc Thắng |
| [design-pattern-v2](sources/design-pattern-v2.md) | source | Học Từ Thiền Phần 001 — Data, APIs & Distributed Systems · Trần Hồng Gấm |
| [design-pattern-v3](sources/design-pattern-v3.md) | source | Học Từ Thiền Phần 002 — Microservices, Caching & HA Patterns · Bạch Hồng Vinh |
| [R10](concepts/R10.md) | concept | R10 policy: docs-gate hook nhắc bổ sung docs mỗi N prompt (UserPromptSubmit) |
| [architecture](concepts/architecture.md) | concept | Architecture of the setup template/skill/harness repo — 4 layers |
| [onboarding-tour](concepts/onboarding-tour.md) | concept | 10-step guided tour of the setup repo |
| [project-structure](entities/project-structure.md) | entity | Top-level structure + hot files of the setup repo |
| [cursor-explain-site](concepts/cursor-explain-site.md) | concept | How-to reverse-engineer & clone a site (extract-site Mode 3) |
| [250626-walkthroughs](html/250626-walkthroughs.html) | index | 2026-06-25 |
| [rule-registry](concepts/rule-registry.md) | concept | 2026-06-27 — Registry R1..R12 (1 trang) + 2 policy.yaml + R6=verify-before-commit |
| [fdk](concepts/fdk.md) | concept | 2026-06-27 — Framework Development Kit: front-door + pre-flight + module map (không miss rule, không dẫm module cũ) |
| [ADR-001-policy-as-source-of-truth](sources/adr/ADR-001-policy-as-source-of-truth.md) | decision | 2026-06-27 — policy.yaml nguồn chân lý, thin-adapter (case R11) |
| [ADR-002-pull-before-change-gates](sources/adr/ADR-002-pull-before-change-gates.md) | decision | 2026-06-27 — R12 git-level+orchestrator, bỏ per-edit, đa-vendor/đa-subrepo |
| [ADR-003-skill-as-single-source-of-truth](sources/adr/ADR-003-skill-as-single-source-of-truth.md) | decision | 2026-06-27 — skill con = SoT, orchestrator delegate; Claude nghĩ / CLI rẻ render |
| [ADR-004-framework-dev-context-opt-in](sources/adr/ADR-004-framework-dev-context-opt-in.md) | decision | 2026-06-27 — framework-dev context opt-in (/fdk), không auto-bơm SessionStart; audit lỗi tư duy |
| [extract-site](concepts/extract-site.md) | concept | 2026-06-27 — stub skill extract-site (giải broken wikilink) |
| [docs-site-macos-skill](concepts/docs-site-macos-skill.md) | concept | 2026-06-27 — stub skill docs-site-macos (giải broken wikilink) |
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
| [ADR-016-no-ai-attribution-in-commits](sources/adr/ADR-016-no-ai-attribution-in-commits.md) | decision | ADR-016: Không ghi công AI trong commit (R15) |
| [framework-dev-antipatterns](concepts/framework-dev-antipatterns.md) | concept | Framework-dev anti-patterns |
| [ADR-017-global-shared-engine-repo-data-travel](sources/adr/ADR-017-global-shared-engine-repo-data-travel.md) | decision | ADR-017: Global-shared engine + repo-data travel |
| [010726-council-output](draft/orca/010726-council-output.md) | auto |  |
| [adapt-modes-pick](sources/evals/adapt-modes-pick.md) | eval | Golden: adapt-modes-pick |
| [capproof-liveness](sources/evals/capproof-liveness.md) | eval | Golden: capproof-liveness |
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
