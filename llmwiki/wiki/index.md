# Wiki Index

> Khuôn wiki per-project (demo). Wiki RIÊNG của framework nằm ở `fdk/wiki/` (the kit — ADR-008).

| File | Type | Summary |
|------|------|---------|
| [example-concept](concepts/example-concept.md) | concept | Ví dụ một trang concept hợp lệ (Origin + OKF) cho project dùng llmwiki |
| [repowise](entities/repowise.md) | entity | Đối thủ codebase-intelligence (CLI+MCP, AGPL-3.0, 5088★): 5-lớp index, 10 MCP tool task-shaped, code-health 49-detector defect-validated, PR bot 0-LLM — so sánh điểm chạm thật với code-graph/ingest nội bộ |
| [adapt-modes](concepts/adapt-modes.md) | concept | 3 kiểu absorb năng lực vào dự án — HÒA TAN / KÉO NGOÀI / NHÚNG-SỞ-HỮU; gọi đúng tên chọn đúng phương án |
| [decision-anchoring](concepts/decision-anchoring.md) | concept | Neo quyết định vào symbol code, 4 trạng thái LIVE/STALE/ORPHAN/UNAVAILABLE suy từ code-graph, không cất tay |
| [log-model](concepts/log-model.md) | concept | Bản đồ 5 cơ chế "ghi lại chuyện đã xảy ra" (events/scratch-log/mem-rank/touches/provenance-log) — mỗi cái độc lập, đừng ép hợp nhất |
| [provenance-log](concepts/provenance-log.md) | concept | Sổ sự kiện artifact-level git-native, hash-chain theo writer, merge=union, CAP=AP — pattern Kafka rẻ dựng từ mảnh đã có sẵn |
| [evidence-terminal-chain](concepts/evidence-terminal-chain.md) | concept | Schema chuỗi chứng cứ và sáu loại điểm cuối của luật R19 — chuỗi kết luận phải chấm dứt ở thứ xem được, `web` đòi link đúng chỗ + ngày + trích nguyên văn, `parametric` (kiến thức từ training) đòi origin và cấm đứng một mình; kèm giới hạn "resolve path không đồng nghĩa chống lưng nội dung" |
| [commit-dag-hub](concepts/commit-dag-hub.md) | concept | Mỗi thí nghiệm ratchet thành một node commit trong `refs/hub/*` + `git notes`, hỏi được children/leaves/lineage/diff — opt-in, mặc định tắt, gỡ được sạch bằng ba tầng |
| [040726-issue4-trace-grader-plan](draft/040726-issue4-trace-grader-plan.md) | plan | Plan step-by-step GH#4: sửa run.ok transcript, lọc sidechain, check grounding edited_without_read — cho dev khác làm tiếp |
| [300626-audit-fix-docs-site-macos](draft/uiux/300626-audit-fix-docs-site-macos.md) | draft | Audit + 8 fix (a11y/head/glass) cho skill docs-site-macos, đồng bộ cả 2 bản mirror |
| [010726-onboard-html-tabs-redesign](draft/orca/010726-onboard-html-tabs-redesign.md) | draft | Redesign tầng báo cáo HTML orca-onboard: sidebar-nav scroll-spy, tour master-detail, tab Modules DB-style tự ẩn nếu mono |
| [300726-pr92-flow](sources/draft/300726-pr92-flow.md) | draft | Trang HTML giải thích PR #92 (graph-engineering): vấn đề, luồng 7 tính năng T1–T7, và bảng gọi-ra/khi-nào-kích-hoạt xác nhận bằng grep thật |
| [300726-hook-skill-layers](sources/draft/300726-hook-skill-layers.md) | draft | Walkthrough tương tác 8 bước lifecycle Claude Code (SessionStart→...→SessionEnd), cursor đi qua đúng file hook/skill/script thật, 2 ví dụ đã xảy ra trong hội thoại |
| [300726-fdk-uat-flow](sources/draft/300726-fdk-uat-flow.md) | draft | Walkthrough tương tác trace THẬT của lượt UAT vừa chạy: 1 prompt → 14 bước, push canary GitHub thật → fresh install → 6 self-test T1-T7 → workspace Orca thật + assert → dọn canary |
| [300726-pr92-model](sources/draft/300726-pr92-model.md) | draft | Sơ đồ kết cấu tĩnh (khác luồng thời gian) 7 tính năng PR #92: T7 phụ thuộc opt-in T1, T3 phụ thuộc dữ liệu T2, T4/T5 tự động qua hook, T6 đứng riêng |
| [300726-session-provenance-test-hook](sources/300726-session-provenance-test-hook.md) | source | Auto-distill scratch-log phiên "test-hook" — tách riêng khỏi 300726-session-provenance.md sau khi 2 phiên khác nhau cùng ngày bị trùng tên file (naming collision của scratch-log.py) |
| [010726-trupillar4-council-persona](draft/orca/010726-trupillar4-council-persona.md) | draft | Chốt cứng Trụ 4 (cổng CI code-health) + persona-lens 18 vĩ nhân cho council (BNAL) |
| [010726-dev-harness-kit](draft/orca/010726-dev-harness-kit.md) | draft | Thiết kế 'dev tự build harness' (BNAL) + council 18 ông chọn checksum-seal; report HTML |
| [020726-docs-site-fdk-strategy](sources/draft/archive/analysis/020726-docs-site-fdk-strategy.md) | draft | Render concept fdk-dev-strategy (Mongol pattern) thành docs site HTML liquid-glass |
| [060726-design-standard-ai-elite-PLAN](sources/draft/archive/proposals/060726-design-standard-ai-elite-PLAN.md) | plan | Nền chuẩn thiết kế AI-elite chống AI-slop: design-standard (canon) + ai-slop-lint 2 tầng + --fix kill-1-shot + design-review lens; distill design-tip + research 8 nguồn |
| [170726-gitignored-dedupe](sources/draft/170726-gitignored-dedupe.md) | draft | Chốt rule từ 3 failure flywheel `spec-violation`: trỏ `okf-check.py` về canonical `index_sync.gitignored` (dùng lại pattern `_load()` của `audit.py`); giữ nguyên `harness-events.py` vì ranh giới vendor-neutral |
| [wiki-core-relations](concepts/wiki-core-relations.md) | concept | Wiki-core v2 (đánh giá 6 tiêu chí + relations/ledger/validator, council-approved) — bước 1+2&3 shipped d4d8b90 |
| [architecture](sources/evals/retrieval/architecture.md) | eval | Golden truy-hồi: Kiến trúc repo setup gồm những gì? |
| [blocking-layer](sources/evals/retrieval/blocking-layer.md) | eval | Golden truy-hồi: Lớp CHẶN nằm ở hook/CI hay ở MCP? |
| [bnal-adapter](sources/evals/retrieval/bnal-adapter.md) | eval | Golden truy-hồi: build-now-adapt-later: core-now + adapter verified:false nghĩa là gì? |
| [boris-roles](sources/evals/retrieval/boris-roles.md) | eval | Golden truy-hồi: 5 vai vòng đời agent của Boris Cherny là gì? |
| [boris-template](sources/evals/retrieval/boris-template.md) | eval | Golden truy-hồi: Áp 5 archetype Boris Cherny vào template: sweep-gate + persona dispatc |
| [decision-adr-gate](sources/evals/retrieval/decision-adr-gate.md) | eval | Golden truy-hồi: Gate ép quyết định kiến trúc thành ADR (R13) hoạt động ra sao? |
| [docs-macos](sources/evals/retrieval/docs-macos.md) | eval | Golden truy-hồi: Skill docs-site-macos dùng để làm gì? |
| [enforcement-floor](sources/evals/retrieval/enforcement-floor.md) | eval | Golden truy-hồi: Vì sao CI mới là sàn enforcement thật, ba lớp chặn ra sao? |
| [explain-clone-site](sources/evals/retrieval/explain-clone-site.md) | eval | Golden truy-hồi: Làm sao explain và clone một website? |
| [fdk-optin](sources/evals/retrieval/fdk-optin.md) | eval | Golden truy-hồi: Vì sao framework-dev context là opt-in, không auto-bơm đầu phiên? |
| [fdk-what](sources/evals/retrieval/fdk-what.md) | eval | Golden truy-hồi: FDK — Framework Development Kit là gì, gọi khi nào? |
| [feature-catalog](sources/evals/retrieval/feature-catalog.md) | eval | Golden truy-hồi: Bản đồ mọi năng lực framework và vì sao cần nằm ở đâu? |
| [harness-local](sources/evals/retrieval/harness-local.md) | eval | Golden truy-hồi: Làm sao dự án tự build harness riêng mà KHÔNG chạm module gốc? |
| [logger-downstream](sources/evals/retrieval/logger-downstream.md) | eval | Golden truy-hồi: code-logger và bản đồ năng lực đi xuống dự án downstream thế nào? |
| [onboarding-tour](sources/evals/retrieval/onboarding-tour.md) | eval | Golden truy-hồi: Onboarding tour trong framework là gì? |
| [orient-forcequery](sources/evals/retrieval/orient-forcequery.md) | eval | Golden truy-hồi: Session orientation + auto-index + force-query quyết định thế nào? |
| [outer-eval](sources/evals/retrieval/outer-eval.md) | eval | Golden truy-hồi: Outer harness được đánh giá (evaluation) ra sao? |
| [policy-sot](sources/evals/retrieval/policy-sot.md) | eval | Golden truy-hồi: Policy là nguồn chân lý — quyết định enforcement nằm ở đâu? |
| [project-local-rule](sources/evals/retrieval/project-local-rule.md) | eval | Golden truy-hồi: Dự án tự phát triển rule riêng P-namespace sandbox-safe thế nào? |
| [protected-lib](sources/evals/retrieval/protected-lib.md) | eval | Golden truy-hồi: Cơ chế bảo vệ pattern library khỏi sửa nhầm là gì? |
| [pull-gate](sources/evals/retrieval/pull-gate.md) | eval | Golden truy-hồi: Pull-before-change gate hoạt động thế nào? |
| [query-eval](sources/evals/retrieval/query-eval.md) | eval | Golden truy-hồi: Cách đo truy hồi (recall + token) của skill query? |
| [r10](sources/evals/retrieval/r10.md) | eval | Golden truy-hồi: R10 policy — docs-gate hook nhắc bổ sung docs là gì? |
| [rule-registry](sources/evals/retrieval/rule-registry.md) | eval | Golden truy-hồi: Danh sách rule R1..R12 canonical nằm ở đâu? |
| [scanner-gitignore](sources/evals/retrieval/scanner-gitignore.md) | eval | Golden truy-hồi: wiki-tree scanner lọc file gitignored tại đâu? |
| [skill-sot](sources/evals/retrieval/skill-sot.md) | eval | Golden truy-hồi: Vì sao skill là single source of truth, sửa hành vi ở đâu? |
| [trend-bnal-1](sources/evals/retrieval/trend-bnal-1.md) | eval | Golden truy-hồi: 5 trend 2026 đầu áp qua build-now-adapt-later là gì? |
| [trend-bnal-2](sources/evals/retrieval/trend-bnal-2.md) | eval | Golden truy-hồi: 5 trend 2026 tiếp (memory, cost, injection, hallucination) áp ntn? |
| [wiki-in-kit](sources/evals/retrieval/wiki-in-kit.md) | eval | Golden truy-hồi: Vì sao wiki của framework sống trong kit (fdk)? |
| [010726-query-retrieval-eval](draft/orca/010726-query-retrieval-eval.md) | draft | Query L0→L1: eval truy-hồi + telemetry + query 3-tầng |
| [010726-21-quy-tac-docs](sources/draft/archive/analysis/010726-21-quy-tac-docs.md) | draft | Docs site bóc tách "21 Quy Tắc Không Thể Phá Vỡ" |
| [010726-council-report-redesign](draft/uiux/010726-council-report-redesign.md) | draft | Redesign council.report.html theo audit chống AI-slop: đổi font/palette/surface/states, giữ nguyên số liệu và cảnh báo verified:false |
| [020726-cor-pattern](draft/uiux/020726-cor-pattern.md) | draft | Chưng COR (Controlled Output Renderer) thành microlib dùng chung cor.py sau khảo sát 65 skill + council 5 ghế chốt scope hẹp |
| [020726-openai-compat-endpoint-pools](sources/draft/archive/analysis/020726-openai-compat-endpoint-pools.md) | draft | Docs site phân loại 4 pool endpoint tương thích OpenAI (cloud/gateway/compat-shim/local) + 1 pool agent CLI tiêu thụ |
| [020726-adr-015-status](sources/draft/archive/analysis/020726-adr-015-status.md) | draft | Chốt baseline sweep-gate (140 đơn vị) + docs site đối chiếu ADR-015 (5 archetype Boris Cherny) với hiện trạng, còn nợ gì |
| [020726-eval-report](sources/draft/archive/analysis/020726-eval-report.md) | draft | Eval session qua lens Donella Meadows (đòn bẩy hệ thống): 5 tín hiệu tái diễn, đề xuất nâng từ luồng thông tin lên luật chơi |
| [020726-orca-issue-ledger-travel](sources/020726-orca-issue-ledger-travel.md) | draft | Tạo skill orca-issue (vòng xử lý sự cố repro-first) + làm convention problem-tree travel theo mọi dự án cài overstack |
| [problem-tree](concepts/problem-tree.md) | concept | Sổ ledger append-only xuyên session, màu theo độ phủ 3 trụ (harness/skills/llmwiki), trigger tự xả qua R16/R17 |
| [020726-overstack-docs-redesign](draft/uiux/020726-overstack-docs-redesign.md) | draft | Redesign a11y + reorder mind map cho overstack.html, council 5-ghế soi từng node, sửa nhãn nav + phân loại lại 3 skill |
| [020726-ingest-fdk-strategy](sources/draft/archive/analysis/020726-ingest-fdk-strategy.md) | draft | Ingest fdk-stragegy.md → pattern 8 nguyên tắc "Mongol" cho dev fdk (ghi vào fdk/wiki) |
| [020726-audit-fdk-strategy](sources/draft/archive/analysis/020726-audit-fdk-strategy.md) | draft | Audit 3 trụ theo 8 nguyên tắc Mongol pattern — nợ lớn nhất ở #3 (policy chưa drive, drift che) |
| [020726-council-chon-de-thi-self-index](sources/draft/020726-council-chon-de-thi-self-index.md) | draft | Dựng app mẫu TS ngoài mẫu để council tự chọn đề thi, harass 8 loại vector quan hệ chống ludic fallacy (superseded → GH#81) |
| [030726-eval-report](draft/orca/030726-eval-report.md) | draft | Eval phiên dev phân mảnh (8 chủ đề nhảy, đổi ý giữa chừng) làm stress-test /fdk: 3 anti-pattern (hand-author/reinvent/quên verify) → 2 cổng tự-cắn |
| [030726-milestone-v106-harden](sources/draft/030726-milestone-v106-harden.md) | draft | Milestone v1.0.6: medic phủ 17/17 rule + hook gương-soi-cuối-phiên, hạ /query xuống optional, đo reinvent/cross-break-rate |
| [030726-session-provenance](sources/030726-session-provenance.md) | source | Auto-distill phiên b73d2c47: đặt tên medic, sửa sync SAI HƯỚNG gây R7 rail-đen, council chọn app mẫu TS plugin-host chống ludic-fallacy |
| [030726-secondary-memory](sources/draft/030726-secondary-memory.md) | draft | Thiết kế bộ nhớ thứ cấp 3-tầng (THÔ auto scratch-log → DISTILL → WIKI) file-first không RAG, view session/feature qua build-wiki-graph |
| [030726-narrative-as-data](sources/draft/030726-narrative-as-data.md) | draft | Rút narrative cơ-chế-phòng-thủ của overstack.html khỏi prose tay thành manifest mechanisms.yaml + medic probe narrative-drift cắn khi lệch |
| [030726-overstack-html-audit](sources/draft/archive/analysis/030726-overstack-html-audit.md) | draft | Audit đa-góc-nhìn overstack.html: 4 mâu thuẫn nội tại mức CAO, lỗi thời 3 commit (thiếu GH#8), thiếu dark-mode/search/a11y |
| [ISSUES](sources/ISSUES.md) | index | Issues — ledger local |
| [030726-foundation-section](sources/draft/archive/analysis/030726-foundation-section.md) | draft | Mọi wiki thiếu mục Foundation — bài toán · vì sao tồn tại · vì sao chọn công nghệ |
| [030726-foundation-section-PLAN](sources/draft/archive/proposals/030726-foundation-section-PLAN.md) | plan | Kế hoạch triển khai issue #6 Foundation section (foundation.yaml → generator → medic probe) |
| [030726-medic-cong-suc-khoe-tong](sources/draft/030726-medic-cong-suc-khoe-tong.md) | draft | medic — cổng sức khoẻ tổng / tuyến phòng thủ cuối của framework |
| [030726-multi-session-add-guard](sources/draft/archive/analysis/030726-multi-session-add-guard.md) | draft | Đa-session chung working tree: git add -A trộn việc — cần guard quy-session |
| [030726-orca-independence-planb](sources/draft/archive/analysis/030726-orca-independence-planb.md) | draft | Orca-independence — tự-build orchestration optional làm Plan B |
| [030726-skill-usage-dashboard](sources/draft/archive/analysis/030726-skill-usage-dashboard.md) | draft | Thống kê skill-usage thực tế → dashboard HTML báo cáo hàng tuần |
<!-- index:auto:start -->
| [030726-memory-episodic-vector](sources/draft/archive/analysis/030726-memory-episodic-vector.md) | issue | Issue: Memory — llmwiki mới có ~1.5/4 tầng nhớ |
| [030726-observability-runtime](sources/draft/archive/analysis/030726-observability-runtime.md) | issue | Issue: Thiếu observability/eval lúc chạy |
| [030726-orchestration-scale](sources/draft/archive/analysis/030726-orchestration-scale.md) | issue | Issue: Orchestration mới ở mức CHỚM về quy mô |
| [030726-ralph-br-frame-production-line](sources/draft/archive/analysis/030726-ralph-br-frame-production-line.md) | issue | Issue: Dây chuyền sản xuất ứng dụng khép kín (Ralph BR→frame→loop) chạy trên har |
| [030726-self-evolving-skills](sources/draft/archive/analysis/030726-self-evolving-skills.md) | issue | Issue: Skill chưa tự tiến hoá & thiếu eval-per-skill |
| [030726-skill-resolve-supplychain](sources/draft/archive/analysis/030726-skill-resolve-supplychain.md) | issue | Issue: Nhập nhằng skill + supply-chain chưa được đo/chặn |
| [030726-retrieval-eval-baseline-rot](sources/draft/archive/analysis/030726-retrieval-eval-baseline-rot.md) | issue | Issue: retrieval-eval baseline rot + guard-rail quá giòn |
| [040726-precommit-slow-fragile-on-commit](sources/draft/archive/analysis/040726-precommit-slow-fragile-on-commit.md) | issue | Issue: pre-commit chậm + giòn khi bị ngắt |
| [040726-episodic-vector-plan](sources/draft/archive/analysis/040726-episodic-vector-plan.md) | draft | Draft: đạt 4/4 tầng nhớ cho llmwiki (issue #9) |
| [ep-ci-tech-debt](sources/evals/episodic/ep-ci-tech-debt.md) | eval | Episodic golden: đóng tech-debt CI |
| [ep-episodic-wire](sources/evals/episodic/ep-episodic-wire.md) | eval | Episodic golden: nối episodic + vector retrieval |
| [caveman-commit](sources/evals/skill-resolve/caveman-commit.md) | auto | skill-resolve golden: caveman-commit |
| [caveman](sources/evals/skill-resolve/caveman.md) | auto | skill-resolve golden: caveman |
| [council](sources/evals/skill-resolve/council.md) | auto | skill-resolve golden: council |
| [design-frontend](sources/evals/skill-resolve/design-frontend.md) | auto | skill-resolve golden: design-frontend |
| [design-v1](sources/evals/skill-resolve/design-v1.md) | auto | skill-resolve golden: design-v1 |
| [frontier-scan](sources/evals/skill-resolve/frontier-scan.md) | auto | skill-resolve golden: frontier-scan |
| [health-check](sources/evals/skill-resolve/health-check.md) | auto | skill-resolve golden: health-check |
| [ingest](sources/evals/skill-resolve/ingest.md) | auto | skill-resolve golden: ingest |
| [medic](sources/evals/skill-resolve/medic.md) | auto | skill-resolve golden: medic |
| [new-skill](sources/evals/skill-resolve/new-skill.md) | auto | skill-resolve golden: new-skill |
| [onboard](sources/evals/skill-resolve/onboard.md) | auto | skill-resolve golden: onboard |
| [orca-issue](sources/evals/skill-resolve/orca-issue.md) | auto | skill-resolve golden: orca-issue |
| [raise-issue](sources/evals/skill-resolve/raise-issue.md) | auto | skill-resolve golden: raise-issue |
| [ship](sources/evals/skill-resolve/ship.md) | auto | skill-resolve golden: ship |
| [skill-provenance](sources/evals/skill-resolve/skill-provenance.md) | auto | skill-resolve golden: skill-provenance |
| [snapshot-push](sources/evals/skill-resolve/snapshot-push.md) | auto | skill-resolve golden: snapshot-push |
| [tour-basic](sources/evals/skill-resolve/tour-basic.md) | auto | skill-resolve golden: tour-basic |
| [tour-supademo](sources/evals/skill-resolve/tour-supademo.md) | auto | skill-resolve golden: tour-supademo |
| [040726-selftest-nested-commit-unguarded](sources/draft/archive/analysis/040726-selftest-nested-commit-unguarded.md) | issue | Issue: Self-test harness chạy `git commit` lồng không tắt hook |
| [050726-ship-selfindex-engine-downstream](sources/draft/archive/analysis/050726-ship-selfindex-engine-downstream.md) | issue | Issue: Ship self-index engine (wiki-graph + retrieval) xuống downstream |
| [050726-wikigraph-package-import-resolver](sources/draft/archive/analysis/050726-wikigraph-package-import-resolver.md) | issue | Issue: resolver Python của wiki-graph chỉ khớp basename 1-segment |
| [050726-wikigraph-dangling-wikilink](sources/draft/archive/analysis/050726-wikigraph-dangling-wikilink.md) | issue | Issue: broken wikilink đẻ cạnh dangling trong graph data |
| [050726-explicit-index-scope-yaml](sources/draft/archive/analysis/050726-explicit-index-scope-yaml.md) | issue | Issue: khai báo scope index tường minh qua .overstack.yaml |
| [050726-unify-install-manifest](sources/draft/archive/analysis/050726-unify-install-manifest.md) | issue | Issue: thống nhất install path qua manifest |
| [050726-reachability-sweep-skill-tools](sources/draft/archive/analysis/050726-reachability-sweep-skill-tools.md) | issue | Issue: reachability sweep skill→tool (GH#54) |
| [050726-map-not-territory-fable5-unknowns](sources/draft/archive/analysis/050726-map-not-territory-fable5-unknowns.md) | issue | Issue: Map-is-not-Territory — tìm unknowns đối chiếu & vá overstack (GH#40) |
| [060726-wiki-sync-openwiki-distill](sources/draft/archive/analysis/060726-wiki-sync-openwiki-distill.md) | draft | 060726-wiki-sync-openwiki-distill |
<!-- index:auto:end -->
| [140726-propose-plan-split-superpowers](sources/draft/140726-propose-plan-split-superpowers.md) | draft | Tách vòng đời đề xuất thành SPEC (/propose, người duyệt) và PLAN (/plan mới, agent mù thi hành), mở rộng R7 cắn cả hai |
| [110726-shipped-vs-documented-parity](sources/draft/110726-shipped-vs-documented-parity.md) | draft | Issue: tài liệu hứa 74 skill nhưng npx chỉ giao 67 trong im lặng — cần cổng so hứa với giao ở fresh-install-smoke --remote |
| [130726-session-provenance](sources/130726-session-provenance.md) | source | Auto-distill phiên c82ce215: fix bỏ dòng secondary-memory bị trùng do resolve merge sai (32 file dirty) |
| [140726-session-provenance](sources/140726-session-provenance.md) | source | Auto-distill phiên 36e6562b: parity hứa↔giao phải chạy ở MỌI mode smoke, không thì cổng required mù với nó (#77) |
| [060726-ponytail-distill-PLAN](sources/draft/archive/proposals/060726-ponytail-distill-PLAN.md) | draft | Plan chưng cất ponytail (anti-over-engineering, MIT) vào overstack: the ladder 7 bậc + carve-out + marker nợ, bỏ phần bao bì phân phối |
| [070726-ponytail-distill](sources/draft/archive/analysis/070726-ponytail-distill.md) | draft | Issue: overstack chưa có luật chống over-engineering áp LÚC VIẾT code — chưng cất ladder 7 bậc + marker nợ từ ponytail |
| [110726-anti-fabrication-observed-metrics](sources/draft/110726-anti-fabrication-observed-metrics.md) | draft | Issue: claim-receipts chỉ chống bịa reference file/API, chưa bắt agent tự bịa số đo về người-dùng/thế-giới không quan sát được |
| [110726-auto-wire-eval-loop](sources/draft/110726-auto-wire-eval-loop.md) | draft | Issue: các guard chống-lạc-quan (council/wikieval/trace-grader/claim-receipts) đều là skill gọi tay, thiếu loop tự-kích khép kín qua hook |
| [110726-eval-blinding-grader-context](sources/draft/110726-eval-blinding-grader-context.md) | draft | Issue: grader nội bộ (wikieval/trace-grader) thấy toàn bộ transcript sinh output nên bị mồi lạc quan — cần contract blind theo context |
| [110726-gold-set-meta-eval-grader](sources/draft/110726-gold-set-meta-eval-grader.md) | draft | Issue: chưa có gold-set + QWK để đo độ ĐÚNG của chính grader (wikieval/trace-grader) — grader có thể trôi mà không ai biết |
| [140726-spec-kit-traceability](sources/draft/140726-spec-kit-traceability.md) | draft | Hấp thụ 3 điểm mạnh của github/spec-kit vào /propose+/plan: id FR-xxx/SC-xxx truy vết, tag (default)/[CẦN LÀM RÕ], sửa /fdk-uat sang nhánh canary |
| [skill-craft](concepts/skill-craft.md) | concept | Bộ từ vựng viết/soi skill: context-load vs cognitive-load, information hierarchy, completion criterion, leading word (chưng cất từ mattpocock/skills) |
| [issue-tracker](sources/issue-tracker.md) | reference | Hợp đồng adapter cho issue tracker của repo — ledger ISSUES.md là gốc, GitHub là mirror, 5 nhãn triage + frontier.py |
| [150726-mattpocock-absorb](sources/draft/archive/proposals/150726-mattpocock-absorb.md) | draft | Hấp thụ mattpocock/skills: cắt context-load (tắt model-invocation hàng loạt), thêm nhãn ready-for-agent/blocked_by/claim cho ledger issue, thêm /wayfinder |
| [150726-session-provenance](sources/150726-session-provenance.md) | source | Auto-distill phiên 36e6562b: tạo concept design-foundation + skill-craft, soạn 4 draft (hallmark-design-foundation/mattpocock-absorb/qc-code-skill/unknown-ledger) |
| [design-foundation](concepts/design-foundation.md) | concept | hallmark (Together AI) là sàn chung 6 discipline + slop-test cho mọi UI; skill design khác là flavour đứng trên, docs-site-macos là ngoại lệ nội bộ |
| [150726-hallmark-design-foundation](sources/draft/archive/proposals/150726-hallmark-design-foundation.md) | draft | Hấp thụ Nutlope/hallmark làm nền design chung: nâng cổng tất định frontend-antipattern.py bằng slop-test cơ học + nối catalog vào /propose làm fill-default |
| [290626-failure-spec-violation](sources/draft/archive/analysis/290626-failure-spec-violation.md) | draft | Rule stub từ failure-flywheel: spec-violation tái diễn 3× (scanner R3/R9 không skip file gitignored) — chờ người distill thành rule |
| [150726-unknown-ledger](sources/draft/archive/proposals/150726-unknown-ledger.md) | draft | Biến default lặng khi model tự điền gap thành sổ nợ unknown-ledger truy vết được: lựa chọn fill-first-find-out-later + file wiki/draft/unknown/ |
| [150726-qc-code-skill](sources/draft/archive/proposals/150726-qc-code-skill.md) | draft | Thêm skill /qc-code: review senior 4 mục (security/performance/naming/logic) chấm điểm + verdict, mỗi bug logic sinh test tái hiện auto-chạy qua hook tất định |
| [160726-teach-me-skill](sources/draft/archive/proposals/160726-teach-me-skill.md) | draft | Thêm skill /teach-me: giải thích một thứ ở 2 cấp (hệ thống + code) + bộ ba vấn-đề/workflow/chi-tiết, chứng bằng runtime thật (breakpoint/instrument) thay vì đoán tĩnh |
| [160726-session-provenance](sources/160726-session-provenance.md) | source | Auto-distill phiên 36e6562b: tiếp tục design-foundation/skill-craft, thêm draft teach-me-skill vào bộ proposal absorb |
| [170726-session-provenance](sources/170726-session-provenance.md) | source | Auto-distill phiên 246fa7ac: chạy capability-stamp (medic gương-soi) sau khi dùng framework, ghi unknown-frontend-design + draft absorb-six-sources |
| [170726-absorb-six-sources](sources/draft/archive/proposals/170726-absorb-six-sources.md) | draft | Absorb HÒA TAN 6 nguồn GitHub vào 5 bề mặt sẵn có (qc-code/orca-sec-scans/mem-rank/design-foundation/orca-issue), không thêm skill mới |
| [170726-absorb-six-sources-PLAN](sources/draft/archive/proposals/170726-absorb-six-sources-PLAN.md) | draft | Plan thi hành absorb 6 nguồn: task-by-task nối vào qc-code/orca-sec-scans/hallmark/mem-rank, verify bằng rg + self-test, sync mirror ở T6 |
| [180726-capability-proof-map](sources/draft/archive/proposals/180726-capability-proof-map.md) | draft | Nâng CAPABILITIES.md từ liệt-kê sang chứng-minh-còn-sống: cột Proof + mục UNPROVEN + đảo chiều bêu cơ chế TRÙNG LẶP, medic probe capproof ratchet |
| [180726-capability-proof-map-PLAN](sources/draft/archive/proposals/180726-capability-proof-map-PLAN.md) | draft | Plan thi hành capproof: proof-resolver trong build-capabilities.py + medic probe capproof + baseline ratchet JSON + guard fire-drill CI |
| [unknown-frontend-design](draft/unknown/unknown-frontend-design.md) | unknown-ledger | Unknown: xác nhận skill frontend-design có tồn tại trong anthropics/skills không — đã resolved CÓ, dùng cho absorb-six-sources |
| [180726-session-provenance](sources/180726-session-provenance.md) | source | Auto-distill phiên ee3f5da6: fix CI cập nhật provenance sau sửa nội dung, skill-provenance lint đang đỏ |
| [180726-archetype-tester](sources/draft/archive/proposals/180726-archetype-tester.md) | draft | Thêm archetype thứ 6 tester (/test): persona senior tester sinh kịch bản test neo FR/SC + code test qc-* chạy tất định qua qc-regression |
| [180726-council-self-index-remaining-scope](sources/draft/180726-council-self-index-remaining-scope.md) | issue | Issue: council tự chọn đề thi — phần lõi chưa ship (GH#81) |
| [190726-travel-gap-forcing-functions](sources/draft/190726-travel-gap-forcing-functions.md) | draft | Bịt 3 lỗ travel đường curl update (path repo-relative chết ở downstream, capability-stamp thiếu 4 nhóm file global, fdk-uat chỉ test dự án trống) — mỗi fix kèm hàng rào tự gác |
| [190726-graph-lessons-grapuco](sources/draft/190726-graph-lessons-grapuco.md) | draft | Đối chiếu thread cộng đồng Grapuco qua 3 lens Grower/Prototyper/Maintainer, rút việc phải làm cho graph stack overstack (sửa 2, đo 3, nháp 1) |
| [200726-code-graph-index-broken](sources/draft/200726-code-graph-index-broken.md) | issue | Issue: code-graph MCP hỏng do 1 database thiếu schema giết cả fan-out truy vấn + list_projects lộ tên file thay tên repo — đã sửa bằng guard is_usable_db() |
| [grapuco-discuss](draft/grapuco-discuss.md) | draft | Nguồn thảo luận cộng đồng về sản phẩm Grapuco (context-management/graph cho multi-agent), chất liệu đối chiếu cho graph-lessons-grapuco |
| [newcomer-adr](sources/evals/retrieval/newcomer-adr.md) | eval | Golden truy-hồi mô phỏng người mới hỏi bằng ý định (không thuật ngữ wiki) để kiểm ADR-004 có nổi lên trước khi bị vi phạm |
| [190726-session-provenance](sources/190726-session-provenance.md) | source | Auto-distill phiên eec0806a: fix CI cập nhật provenance sau sửa nội dung, skill-provenance lint đang đỏ, chạm draft graph-lessons-grapuco |
| [200726-session-provenance](sources/200726-session-provenance.md) | source | Auto-distill phiên 765fc26c: thêm skill /orca-handover sinh file bàn giao đủ dày cho phiên khác bắt đầu ngay |
| [200726-orchestration-loop-closure](sources/draft/200726-orchestration-loop-closure.md) | draft | Đo được 78% task orchestration Orca chưa từng dispatch — gốc là coordinator không biết khi nào worker xong (orca terminal wait timeout sai); bản 2 sau khi user bác bỏ chẩn đoán bản 1 |
| [200726-orchestration-triage](sources/draft/200726-orchestration-triage.md) | draft | Đối soát 17 task orchestration treo: sổ task Orca là runtime-global lẫn nhiều dự án, 3 task đóng được (đã ship nơi khác), 11 task thuộc dự án khác đã user xác nhận |
| [graph-model](concepts/graph-model.md) | concept | 5 bản cài graph trong repo đều giải chung một bài toán (artifact liên quan gì code); lát cắt touches artifact↔code là thứ không nguồn nào khác thay được |
| [200726-graph-foundation-handoff](sources/handover/200726-graph-foundation-handoff.md) | draft | Bàn giao việc tiếp theo cho nền graph: đồng bộ travel-policy.yaml với installer, wiki-graph quét nhiều kho, bỏ lớp imports trùng code-graph, wiki-sync đọc graph thay vì grep |
| [210721-decision-anchoring](sources/draft/210721-decision-anchoring.md) | draft | Neo quyết định vào symbol code (không chỉ file), 4 trạng thái LIVE/STALE/ORPHAN/UNAVAILABLE suy từ code-graph — mở rộng mechanisms.yaml xuống mức symbol |
| [210721-decision-anchoring-PLAN](sources/draft/210721-decision-anchoring-PLAN.md) | draft | Plan thi hành decision-anchoring T1-T8: engine decision-liveness.py đọc trực tiếp index.db (không qua MCP), checksum-freshness thay is_file(), test trên sandbox |
| [220722-artifact-provenance-eventlog](sources/draft/220722-artifact-provenance-eventlog.md) | draft | Thiết kế event log Kafka-pattern git-native cho artifact-provenance: sổ sự kiện đa-writer merge qua git branch, chọn CAP=AP, tương quan code↔docs |
| [220722-artifact-provenance-eventlog-PLAN](sources/draft/220722-artifact-provenance-eventlog-PLAN.md) | draft | PLAN thi hành T1-T5 (T6 hoãn, chờ trả nợ U-05): adapter provenance-log.py, merge=union, wiring decision-anchoring + Stop hook |
| [230726-webclone-extractsite-dedup](sources/draft/230726-webclone-extractsite-dedup.md) | draft | Gộp trùng lặp pipeline reconstruct viết ở cả extract-site Mode 3 và web-clone Mode B — web-clone là canonical, extract-site trỏ sang |
| [210721-decision-anchoring-adoption-metric](sources/draft/210721-decision-anchoring-adoption-metric.md) | issue | Decision-anchoring chưa có metric adoption, chưa có kill-switch nếu không ai dùng — issue mở, assignee grower |
| [unknown-context-hygiene](draft/unknown/unknown-context-hygiene.md) | unknown-ledger | Sổ nợ unknown cho context-hygiene-budget: U-02 trần code-graph mặc định (open), U-03 so-diff theo mục hay nguyên file (resolved) |
| [210726-session-provenance](sources/210726-session-provenance.md) | source | Auto-distill scratch-log phiên 765fc26c ngày 21/07 |
| [220726-session-provenance](sources/220726-session-provenance.md) | source | Auto-distill scratch-log phiên 501779e7 ngày 22/07 |
| [230726-session-provenance](sources/230726-session-provenance.md) | source | Auto-distill scratch-log phiên 3c7d0f9c ngày 23/07 |
| [280726-onboard-setup](draft/orca/280726-onboard-setup.md) | draft | Onboard chính repo overstack: knowledge graph 846 node/2905 cạnh/15 tầng (static parse 0 token), domain-graph 7 miền 124 bước có file:line thật, HTML onboarding + vector wiki-graph |
| [290726-session-provenance](sources/290726-session-provenance.md) | source | Auto-distill scratch-log phiên dff80143 ngày 29/07 — vá fdk-uat gate cứng bắt buộc tạo+verify workspace Orca thật, không còn tuỳ chọn |
| [290726-session-provenance-1319b8e1](sources/290726-session-provenance-1319b8e1.md) | source | Auto-distill scratch-log phiên 1319b8e1 ngày 29/07 — phiên chạy /orca-onboard lên chính repo overstack, sinh overstack-source-map/spec-vs-overstack/graph-engineering-PLAN |
| [290726-overstack-source-map](sources/draft/290726-overstack-source-map.md) | draft | Trang HTML mô tả mã nguồn overstack: 15 tầng file, 18 luật từ policy.yaml, 7 miền với 124 bước file:line, sinh tất định từ knowledge graph |
| [290726-spec-vs-overstack](sources/draft/290726-spec-vs-overstack.md) | draft | Đối chiếu overstack với graph-engineering-implementation-spec v0.1 trên 67 mục: 22% đủ, 54% một phần, 22% thiếu — 15 chỗ thiếu quy về 3 gốc (ratchet theo điểm, edge ID, commit-DAG) |
| [290726-graph-engineering-PLAN](sources/draft/290726-graph-engineering-PLAN.md) | draft | PLAN thi hành 6 task đóng gap theo PDF Graph Engineering trên nhánh graph-engineering: ratchet điểm số cho loop-runner, edge ID + typed edges, /query trích evidence, grounding-check schema, 4 trần budget, sổ giả thuyết đã bỏ — commit-DAG và KG-LLM hoãn có trigger |
| [290726-ge-test-PLAN](sources/draft/290726-ge-test-PLAN.md) | draft | PLAN kiểm thử T1–T7: 6 test script bịt 4 lỗ mà self-test đơn vị không thấy — ghép, hồi quy dữ liệu cũ, travel xuống downstream, kill-switch gỡ sạch |
| [300726-session-provenance](sources/300726-session-provenance.md) | source | Auto-distill scratch-log phiên 0121bc61 ngày 30/07 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [300726-session-provenance-350f10dd](sources/300726-session-provenance-350f10dd.md) | source | Auto-distill scratch-log phiên 350f10dd ngày 30/07 — thêm index row cho session-provenance + regen docs, sinh hook-skill-layers/pr92-flow |
| [010826-session-provenance](sources/010826-session-provenance.md) | source | Auto-distill scratch-log phiên 8a8ad17d ngày 01/08 (stub, trùng nội dung 020826) — chỉ chạm `gitignore`/`ISSUES.md`/`010826-wiki-mental-model-taxonomy.md`, chưa ghi why thủ công |
| [010826-session-provenance-350f10dd](sources/010826-session-provenance-350f10dd.md) | source | Auto-distill scratch-log phiên 350f10dd ngày 01/08 — vá 3 bug blocking loop-runner/wiki-graph/grounding-check, merge PR#92 vào orca, cập nhật khung teach-me thành bảy bước |
| [310726-session-provenance](sources/310726-session-provenance.md) | source | Auto-distill scratch-log phiên d2978bf3 ngày 31/07 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [310726-session-provenance-1319b8e1](sources/310726-session-provenance-1319b8e1.md) | source | Auto-distill scratch-log phiên 1319b8e1 ngày 31/07 — vá hook token-budget/grounding, dựng agent-trace, đủ 10/10 cap spec §5 |
| [030826-session-provenance](sources/030826-session-provenance.md) | source | Auto-distill scratch-log phiên d1a42e6e ngày 03/08 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [030826-session-provenance-3b20b398](sources/030826-session-provenance-3b20b398.md) | source | Auto-distill scratch-log phiên 3b20b398 ngày 03/08 — fix GH#94 docs-site-macos theme-switch collapse 0×0 (thêm display:inline-block), regen overstack docs |
| [020826-session-provenance](sources/020826-session-provenance.md) | source | Auto-distill scratch-log phiên 8a8ad17d ngày 02/08 (stub, trùng nội dung 010826) — chỉ chạm `gitignore`/`ISSUES.md`/`010826-wiki-mental-model-taxonomy.md`, chưa ghi why thủ công |
| [020826-session-provenance-1319b8e1](sources/020826-session-provenance-1319b8e1.md) | source | Auto-distill scratch-log phiên 1319b8e1 ngày 02/08 — pull 9 commit upstream (gồm 3 bug fix từ review PR#92), thêm provider Azure Foundry askctd vào opencode |
| [030826-session-provenance-b8afb386](sources/030826-session-provenance-b8afb386.md) | source | Auto-distill scratch-log phiên b8afb386 ngày 03/08 — verify installer đăng ký hook vào ~/.openclaude: vá 3 lỗi (trục trặc phía OpenClaude bóp chết cài Claude global, ghi atomic siết quyền 644→600, chữ có dấu bị escape), test 25/25 + wire CI |
| [050826-session-provenance](sources/050826-session-provenance.md) | source | Auto-distill scratch-log phiên d3d1153e ngày 05/08 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [050826-session-provenance-b8afb386](sources/050826-session-provenance-b8afb386.md) | source | Auto-distill scratch-log phiên b8afb386 ngày 05/08 — thi hành trọn luật R19 evidence-terminal (9 task, bật strict sau khi đo báo oan 0/2, bịt cổng câm ở post_tool_use và lỗi suy root ở bản deploy tier-2), gỡ 3 cổng pre-push, và chuyển model mặc định opencode sang ctd/gpt-5.6-terra |
| [050826-setup-openclaude-opencode](sources/050826-setup-openclaude-opencode.md) | source | Runbook dựng lại đúng cấu hình OpenClaude + OpenCode đang chạy — 5 provider Azure/9router kèm baseURL và model, mặc định `ctd/gpt-5.6-terra`, 12 event hook (10 Orca telemetry + 8 harness), và 3 nợ đã biết; token để ngoài repo ở `~/.config/overstack/ai-secrets.env` |
| [060826-session-provenance](sources/060826-session-provenance.md) | source | Auto-distill scratch-log phiên 2015d100 ngày 06/08 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [060826-session-provenance-b8afb386](sources/060826-session-provenance-b8afb386.md) | source | Auto-distill scratch-log phiên b8afb386 ngày 06/08 — viết runbook setup OpenClaude+OpenCode (token tách ra ngoài repo), gỡ provider orcaflow chết, và chẩn đoán refusal 0-token trên CoopCons: chỉ nhánh gpt-5.6-sol dính, còn khoá `model` trong settings openclaude bị bỏ qua |
| [070826-session-provenance](sources/070826-session-provenance.md) | source | Auto-distill scratch-log phiên 55337220 ngày 07/08 (stub) — chỉ chạm `gitignore`, chưa ghi why thủ công |
| [070826-session-provenance-b8afb386](sources/070826-session-provenance-b8afb386.md) | source | Auto-distill scratch-log phiên b8afb386 ngày 07/08 — vá GH_HOME khiến install.sh crash khi thiếu --with-wiki, symlink skill cho openclaude (trước đó thấy 0 skill), và đo ra anti-idle KHÔNG chặn được trên OpenClaude vì runtime không có khái niệm block-stop |
| [090826-session-provenance](sources/090826-session-provenance.md) | source | Auto-distill scratch-log phiên b8afb386 ngày 09/08 — chuyển endpoint opencode sang ctd-opus services.ai (2 key đều chạy), mở egress allow-list 2 host, và chứng minh openclaude KHÔNG đổi provider được bằng env: 401 với 0 request ra mạng, phải dùng /provider trong TUI |
| [030826-evidence-terminal-chain-harness](sources/draft/030826-evidence-terminal-chain-harness.md) | draft | SPEC luật R19 evidence-terminal — mọi chuỗi kết luận phải chấm dứt ở chứng cứ xem được chứ không ở một suy luận khác; taxonomy 6 loại điểm cuối, trong đó `web` phải kèm link tới đúng chỗ tìm + ngày + trích nguyên văn, và `parametric` (kiến thức từ training model) phải khai nguồn gốc và không được làm điểm cuối duy nhất |
| [030826-evidence-terminal-chain-PLAN](sources/draft/030826-evidence-terminal-chain-PLAN.md) | draft | PLAN thi hành 9 task cho luật R19 evidence-terminal — validator đồ thị chuỗi chứng cứ, 6 loại điểm cuối (web đòi link+ngày+trích, parametric đòi origin và cấm đứng một mình), công tắc bật/tắt ba tầng tắt-vẫn-báo, bite-test + wire CI |
