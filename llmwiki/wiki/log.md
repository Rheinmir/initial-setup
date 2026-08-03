# Operation Log

## 2026-06-28 — migrate — framework wiki → fdk/wiki
`llmwiki/wiki` giờ là khuôn per-project (chỉ giữ 1 file demo). Wiki riêng của framework
(64 file: ADR-001..008, concepts harness/fdk) chuyển sang `fdk/wiki/` — "the kit". Xem ADR-008.

## 2026-06-30 — redesign-existing-projects — audit-fix-docs-site-macos
Audit skill `docs-site-macos` theo checklist redesign; vá 8 defect (focus-ring, viewport/meta+favicon, collapse-clip, prototype self-contained, Output-Report lặp, shadow tint, smooth-scroll, reduced-motion) + a11y (skip-link/`<main>`/SVG-aria/tabular-nums/text-wrap). Áp cho CẢ 2 bản mirror (`skills/docs-site-macos/SKILL.md` ↔ `llmwiki/skills/utils/docs-site-macos.md`), verify content identical (939 dòng, diff=0). Mở rộng audit sang 3 skill sinh-HTML họ hàng (cursor-animated-sites, md-to-html, uat-nonit-testcase). Quyết định chiến thuật parity: GIỮ committed-mirror + gate (bác generate-at-install vì gây cross-project drift); vá `stop.py` để tự chạy `sync-skills.py` cuối mỗi lượt đụng skill. Toàn bộ 65 cặp canonical↔mirror verify identical.

## 2026-07-01 — build-now-adapt-later — trupillar4-council-persona
Chốt cứng Trụ 4 bằng cổng CI tất định không-LLM (`code_health.py`: mọi .py compile sạch, wire fdk-gate+CI; lint sâu advisory — BNAL). Triển khai persona-lens council: 18 vĩ nhân + 13 cặp đối-trọng + lệnh `council.py roster --case` (thuần lookup, ép ≥1 cặp). Commit 490df16 + 04b3fcd, fdk-gate 20/20.

## 2026-07-01 — fdk+bnal+council — dev-harness-kit
Thiết kế cơ chế 'dev tự build harness riêng' (skeleton + không-chạm-core + protected/seal) theo BNAL: nền đã có harness-local(ADR-011)+R14; chốt 3 mảnh CHẮC (scaffolder/seal-command/R14-ext) + cô lập 2 ẩn số. Council 18 persona (council.py mean-rank, thoát loop) chọn checksum-seal #1 (1.39) > R14-ext (1.72) > chmod (3.0) > zip (3.89). Report: llmwiki/html/010726-dev-harness-kit-council.html.

## 2026-07-01 — orca-onboard — html-tabs-redesign (propose)
## 2026-07-01 — docs-site-macos — 21-quy-tac-docs

## 2026-07-01 — redesign-existing-projects — council-report-redesign

## 2026-07-02 — build-now-adapt-later+fdk — cor-controlled-output-renderer (council verdict: khả thi/hẹp)
## 2026-07-02 — docs-site-macos — openai-compat-endpoint-pools

## 2026-07-02 — docs-site-macos — adr-015-status

## 2026-07-02 — redesign-existing-projects — overstack-docs-redesign

## 2026-07-02 — orca-eval — eval-report session hiện tại (lens Meadows)

## 2026-07-02 — propose — orca-issue-ledger-travel (T-260702-01, p-02+p-04)

## 2026-07-02 — orca-issue+ledger-travel — T1-T5 implemented (skill orca-issue, orca-workflow rẽ nhánh, seed template, R17 fallback, concept problem-tree)

## 2026-07-02 — ingest — fdk-stragegy
- Distill `raw/fdk-stragegy.md` → `fdk/wiki/concepts/fdk-dev-strategy.md` + `fdk/wiki/sources/mongol-ai-strategy.md` (wiki framework, ADR-008)
- Draft report: `wiki/sources/draft/020726-ingest-fdk-strategy.md`

## 2026-07-02 — verify-before-commit — promoted 020726-orca-issue-ledger-travel (commit 49d2361, task T-260702-01 done, 20/20 test + drift 52/0)

## 2026-07-02 — docs-site-macos — docs-site-fdk-strategy
- Render `fdk/wiki/concepts/fdk-dev-strategy.md` → `llmwiki/html/020726-fdk-dev-strategy.html` (mind map + 6 section + 4 diagram kéo-thả); draft `sources/draft/020726-docs-site-fdk-strategy.md`.

## 2026-07-02 — fdk — audit-fdk-strategy
- Audit 3 trụ (harness/skills/llmwiki) theo kim chỉ nam fdk-dev-strategy, 3 agent song song
- Draft report: `wiki/sources/draft/020726-audit-fdk-strategy.md`
- Problem-tree: thêm 4 node p-07..p-10 (policy-not-drive, drift-che-version, mép đăng ký skill, nhịp ship wiki)

## 2026-07-02 — docs-site-macos — audit-fdk-strategy-html
- Render báo cáo audit thành `llmwiki/html/020726-audit-fdk-strategy.html` (liquid-glass, mind map, diagram kéo-thả)
- Bổ sung tình báo multi-session vào draft audit; memory mới `framework-multi-session-dev`

## 2026-07-02 — propose — wiki-core-relations
- Đánh giá hệ thống wiki (6 tiêu chí PROV/KG/context-eng) + proposal wiki-core v2: `sources/draft/020726-wiki-core-relations.md` — chờ duyệt.

## 2026-07-02 — council — wiki-core-relations
- 5 seat (Taleb/Ilya/Munger/Kahneman/Aurelius) phan bien proposal 020726-wiki-core-relations; 3 judge blind-rank, winner Ilya (mean-rank 1.0). Chairman synthesis: thu hep pham vi + 7 guardrail bat buoc (concurrency ledger, depth-cap room, migrate//validator song song...) ghi vao Phan 3 cua draft. Transcript: sources/draft/020726-council-transcript-wiki-core.json; report: html/council/council-report-005-seed42.html.

## 2026-07-02 — fdk — wiki-core v2 buoc 1+2&3
- Ledger JSONL (wiki_ledger.py, flock G1, test 8-process pass) + tombstone; migrate id+relations 82 trang (fdk/tools/wiki-relations.py, idempotent); validator rel_integrity.py warn-only (G4/G7, full-scan 0 canh bao that). Problem-tree +p-11 (partial 2/3). Buoc 4-6 cho on dinh 4-6 tuan.

## 2026-07-02 — verify-before-commit — promoted wiki-core-relations
- Gate: py_compile OK, task_lifecycle OK (backfill T-260702-01), G1 test 400/400 pass, rel-scan 0 canh bao, patterns-guard OK. Commit d4d8b90. Draft -> concepts/wiki-core-relations.md, Origin dien commit.

## 2026-07-02 — fdk — wiki-core v2 buoc 4-6 (day som theo quyet dinh user)
- Stale-propagation cap=1 buoc (G2, test A-B-C + chu trinh + tuoi-lai; 9.8ms/lan ghi tren 63 trang). Skill /wiki-room (G3: depth cap=1, budget, circuit breaker) — register du marketplace/LOOP_MAP/AGENT/CLAUDE, skill-registry all agree. Wiki-graph HTML: build-wiki-graph.py (13ms) -> html/wiki-graph-fdk.html + wiki-graph-llmwiki.html. Problem-tree p-11 -> solved 3/3.

## 2026-07-02 — fdk — wiki-graph het flat
- build-wiki-graph.py ve them [[wikilink]] than bai = canh mem net dut (khong gia ngu nghia); them 12 relations co kieu that cho 6 trang loi (validator bat 1 cross-wiki dangling -> go). Demo stale: sua rule-registry -> fdk-dev-strategy stale (badge S trong graph). fdk 121 canh / llmwiki 18 canh, build 5ms/3ms.

## 2026-07-02 — propose — council-chon-de-thi-self-index
- Draft: dung app mau NGOAI mau + harass 8 loai vector, de COUNCIL tu chon de thi (chong ludic fallacy ma council seed42 vua neu). T-260702-02. Pair md+seq.html (5 task). Derives-from [[020726-wiki-core-relations]] + [[010726-query-retrieval-eval]].

## 2026-07-03 — council — T1 chọn đề thi self-index
- Council seed42 (roster risk: taleb/ilya/munger/kahneman/aurelius) blind peer-rank → winner Munger (TS plugin-host ~150 file). Đề thi chốt: 10 đòn harass 8 vector + đòn âm tính (chống bịa cạnh) + ca để-trống (đo giới hạn suy-ngầm), ground-truth niêm phong chống ludic fallacy. Report council-report-010-seed42.html. T-260702-02 T1 done.

## 2026-07-03 — last30days+apply — benchmark self-index
- /last30days: cơ chế benchmark chuẩn = gold-edge interval-overlap P/R/F1 (ContextBench), triplet-F1 + hallucination/omission-rate per-triple + held-out fixed-seed (Unified-KG-Benchmark), MRR/Hits@k, LLM-judge-calibrate-với-người. Áp vào scorer plugin-host/score.py (edge P/R/F1 + hallucination-rate + negative-control + limit tách riêng, verdict gate F1>=0.7 & neg=PASS & halluc<=0.15). Kiểm chứng: engine-tốt giả→PASS 1.0, xấu→FAIL. App mẫu T2 42 file reseal hash 65f51295. T-260702-02 T2 done, T5 scorer ready.

## 2026-07-03 — T3/T4 — chạy engine thật self-index
- adapter.py onboard app→wiki-shape, gọi build-wiki-graph.py THẬT (scan+enrich_code), map→engine-edges.json. score.py chấm mù (seal verified): core F1 0.842 (P .889/R .8), hallucination .125, negative PASS. Per-capability: MẠNH đọc 5/5 quan hệ frontmatter khai tường minh + không bịa cạnh negative + không đối-xứng-hóa contradicts; MÙ imports/touches code TS (enrich_code chỉ .py); thiếu cờ cycle/quarantine trong graph-builder; trích [[NotALink]] từ code-fence (1 false-pos). Xác nhận council seed42: robust ở mặt thiết kế, giòn ở đuôi ngoài-mẫu → chưa anti-fragile. 3 defect chờ đẩy failure-flywheel (T5). T-260702-02 T3+T4 done.

## 2026-07-03 — T5 — distill benchmark self-index
- Report HTML 030726-self-index-benchmark-report.html (glass, KPI + bảng năng lực + 3 defect + kết luận robust-chưa-anti-fragile + phạm vi no-silent-cap). 3 defect vào failure-flywheel (coverage-gap ×2: mù code-TS, thiếu cờ cycle/quarantine; hallucination ×1: wikilink không strip code-fence). Cập nhật concept wiki-core-relations mục "Kiểm chứng NGOÀI-MẪU". T-260702-02 T5 done → proposal 5/5 task xong.

## 2026-07-03 — plan Mảnh A-C — engine tự-index self-contained
- Vá 3 defect benchmark KHÔNG phụ thuộc SW ngoài. Mảnh A: fdk/tools/code_imports.py (stdlib-only, EXTRACTORS TS/JS/Go/Rust + Python-ast, resolve relative+tsconfig-alias, dynamic→unresolved không bịa) thay vai code-graph MCP; wire vào enrich_code đa-ngôn-ngữ. Mảnh B: strip code-fence/inline trước WIKILINK_RE. Mảnh C: detect_cycles DFS + _frontmatter_ok quarantine. Chấm lại: recall 1.0 (11/11), provably-false 0, negative PASS, 9/10 đòn full-pass (đòn 8 touches chờ Mảnh D). Đòn 1 1/3→3/3, 2 1/2→2/2, 3 forbid pass, 4 3/4→4/4, 7 2/3→3/3. Smoke graph thật OK 129 node. Grep: 0 dependency ngoài. Scorer sửa: precision không tính từ gold-thưa (import thật vắng gold ≠ bịa); đo recall + provably-false.

## 2026-07-03 — plan Mảnh D — impact touches self-contained
- impact_reverse(target,edges,rel=imports,cap=1) trong build-wiki-graph.py: touches lan-truyền = reverse-imports 1-hop trên import-graph (cùng cap=1 propagate_stale, self-contained, không hook/tool ngoài). Đòn 8 0→1/1 (khớp 3 dependents thật: di/container, index barrel, wiring). Chấm CUỐI: 22/22 check, 10/10 đòn full-pass, recall 1.0, provably-false 0, negative PASS, seal verified. Smoke graph thật OK 129 node 177ms. plan.md A-D done. Ground-truth sửa 2 lần (setup.md link prose không backtick; đòn8 thêm index.ts barrel là dependent thật) — engine đúng, gold thiếu.

## 2026-07-03 — full 1 luồng + graph HTML
- run.sh gói full pipeline: generate → adapter (engine thật scan+enrich_code đa-ngôn-ngữ + cycle + quarantine + impact + RENDER build_static) → score. Graph HTML thật llmwiki/html/030726-plugin-host-graph.html (34 node, đủ 7 loại vector: imports/derives-from/supersedes/contradicts/implements/depends-on/wikilink, offline 0-JS, self-path R16). Chấm: 22/22, 10/10 đòn, recall 1.0, provably-false 0, VERDICT PASS. Link graph vào report 030726-self-index-benchmark-report.html.

## 2026-07-03 — sửa kỷ luật: graph qua CLI thật (như overstack vào project)
- Phá kỷ luật trước đó (hand-render build_static ra doc dated 030726-plugin-host-graph.html) → XOÁ. Thêm 2 flag CLI THẬT vào build-wiki-graph.py: --code-root (seed node code từ thư mục → dựng import-graph đầy đủ, opt-in default OFF nên graph framework không đổi) + --json (dump nodes/edges/cycles cho eval). run.sh giờ: generate → onboard (wiki-shape như overstack) → CHẠY CLI THẬT build-wiki-graph.py sinh plugin-host/wiki-graph.html chuẩn + graph.json → map_score. Vẫn 22/22, 10/10, recall 1.0, VERDICT PASS. Refresh canonical llmwiki/html/wiki-graph.html + wiki-graph-static.html qua CLI (129 node, engine backward-compat). Harness (score.py) tách khỏi plugin-host/ (app pure, tách-1-bản sạch).

## 2026-07-03 — fdk — ràng buộc rồi đo (feedback loop self-index)
- Meadows: biến fix Mảnh A-D từ vá-một-phát thành vòng phản hồi bound+measured. ĐO: baseline.json đóng băng (recall 1.0, provably_false 0, 10/10 đòn, verdict PASS). RÀNG BUỘC: check.py regress bất kỳ chiều (recall↓/provably-false↑/full-pass↓/negative FAIL/seal vỡ) → exit≠0. run.sh xoá result.json+graph.json cũ đầu run (chống gate đọc stale → false-green — lỗ hổng đã phát hiện & vá). CHỨNG MINH cắn thật: bỏ code_imports.py → engine degrade mượt recall 0.8 → check ❌ REGRESS. Vá guard build-wiki-graph --code-root (if code_root and code_imports) cho fail-open đúng. problem-tree p-12 (con p-11) partial 2/3 trụ. CÒN full: promote eval khỏi scratchpad + wire fdk-gate/CI (cần duyệt) + skill bọc.

## 2026-07-03 — fdk — rà rule "có cắn không" + overstack generator
- Câu hỏi "rà tất cả luật có cắn chính xác không": harness-doctor.py ĐÃ tồn tại (fire-drill BAD/GOOD fixture per validator) nhưng chỉ phủ 5/17 rule (R1/R2/R5/R7/R9). 12 rule chưa chứng minh cắn (hook_event/process_gate/repo_gate/deny_write/vài content_check). Chạy NGAY lộ 2 live: proposal_complete.py DRIFT (hooks-copy vs harness-src), pre-commit chưa cài. → problem-tree p-13 (open). overstack.html: build-overstack-docs.py ĐÃ live-from-disk + wired stop.py; fix orca-issue vào LOOP_GROUPS.orchestrate.ops → regen, --check xanh (0 dẫm module cũ). Thiết kế mở rộng harness-doctor 4 tầng phủ 17/17 — chờ duyệt để build.

## 2026-07-03 — fdk — medic (cổng sức khoẻ tổng) + kim chỉ nam hub
- Kim chỉ nam 2 (hub 1-tên/mô-tả-phạm-vi/TL;DR+recap/transparent) ghi vào skills/fdk/SKILL.md (travel, cạnh Meadows) + sync. medic: fdk/tools/medic.py (stdlib, 6 probe compose harness-doctor/build-*.py --check/compileall/policy-live, scope-arg, --ci, --list, output có recap+use-case+cấu-trúc). Gõ toàn cục ~/.local/bin/medic + /medic slash skill (new-skill scaffold → SKILL.md thin → register LOOP_MAP/marketplace/AGENT/CLAUDE/LOOP_GROUPS.fdk → sync-skills+registry ✓ → regen overstack/capabilities). medic tự bắt & tôi sửa: capabilities stale, validator drift; medic bắt cú SYNC SAI HƯỚNG của tôi (R7 rail-đen 4/5) → khôi phục hooks-copy. Verdict KHOẺ (2 warn nợ: coverage 5/17, pre-commit off). Proposal 030726-medic (T1-2 done, T3-5 pending) pair md+seq.html. problem-tree p-13 partial 2/3 trụ. Memory: fdk-hub-ux-principles + medic-last-line-of-defense.

## 2026-07-03 — council — whiteboard skill: embed vs tách (UX)
- Council design roster (rams/ada/linus/taleb/laozi) đánh giá "whiteboard quan hệ skill vào overstack.html hay tách". Winner Linus (embed-block-tự-chứa 1.33), á quân Taleb (tách). Chairman hoà giải: cả hai đồng thuận whiteboard = ARTIFACT TỰ CHỨA sinh từ registry (không nhét logic vào build-overstack-docs). CHỐT: TÁCH file riêng skill-whiteboard.html + link mỏng từ overstack; bắt đầu TỐI GIẢN (sơ đồ tĩnh, cỡ theo cấu trúc/số-skill-con, KHÔNG bịa usage); tái dùng build-wiki-graph.py + LOOP_GROUPS + build-skill-search metadata; nâng tương tác sau khi có log thật (Laozi). Report council-report-012-seed42.html.

## 2026-07-03 — build — skill-whiteboard (bản đồ quan hệ skill, tĩnh)
- Thực thi quyết định council 012: fdk/tools/whiteboard-skill-map.py → llmwiki/html/skill-whiteboard.html (tĩnh, self-contained, 68 skill / 4 loop-hub, cỡ hub theo CẤU TRÚC số-skill-con KHÔNG bịa usage, ◆ đánh dấu skill bao trùm, mô tả phạm vi từ SKILL.md frontmatter LIVE, có --check anti-drift). Link mỏng "🗺️ Xem bản đồ quan hệ skill đầy đủ →" thêm vào overstack qua generator (không hand-edit). Tương tác (tìm/lọc/route) để sau khi có nhu cầu+log (Laozi). Bắt đầu tối giản đúng chốt.

## 2026-07-03 — fix(council) — report hiện tên uỷ viên thay vì seat-N
- Bug: render map author→tên bằng persona-id nhưng author=seat-id → rơi 'seat-N', mất lens (phong cách). Vá gốc council.py _load_persona_meta: index thêm theo seat-id từ config.seats[].persona. selftest OK. Re-render → council-report-013-seed42.html hiện Dieter Rams/Ada Lovelace/Linus/Nassim Taleb/Lão Tử + lens. problem-tree p-14 solved (harness). Mọi report tương lai tự đúng.

## 2026-07-03 — redesign(council-report) + council(release) + patch note v1.0.5
- Redesign template render_report_html (council.py): font Việt-an-toàn (bỏ Iowan/Palatino vỡ dấu → Georgia/Cambria), .plens có style riêng (italic accent, sans Việt), lead nổi bật + border-left accent per-card chống wall-of-text. selftest OK. Re-render → council-report-014-seed42.html.
- Council release (roster taleb/linus/munger/kahneman/rams): đồng thuận GATE = gitignore scratchpad + patch note trung thực (medic 5/17 KHÔNG suy toàn hệ, benchmark N nhỏ) TRƯỚC rồi push. 2 push-after / 3 hoãn-until = cùng gate. .gitignore += scratchpad/ (co-council đã track → cần git rm --cached lúc tag). RELEASE-v1.0.5.md (v1.0.4+1) với Known-limitations thẳng.

## 2026-07-03 — whiteboard-graph + skill /ship + council i18n
- skill-whiteboard: dựng LẠI thành ĐỒ THỊ qua chính engine build-wiki-graph (build_html JS force-layout) thay layout thẻ tĩnh — user muốn giống wiki-graph. Node loop-hub + skill, cạnh contains(loop→skill) + orchestrates(skill-bao-trùm→con), rel màu nhét in-memory. 42KB, 72 node, SVG cạnh.
- skill /ship (dev-loop): workflow chốt push/release — checklist medic-gate/git-sạch/selftest/version-x.x.x+1/patch-note-trung-thực; 2 mức push|release; STOP chờ duyệt trước side-effect. Register đủ mặt (sync-skills+registry ✓).
- council report i18n: KPI "Winner/Most contested"→"Quán quân/Gây tranh cãi nhất"; bảng "Blind/Mean rank/Judge ranks"→"Nhãn ẩn/Điểm hạng TB/Hạng từng GK"; "Reveal map"→"Bản lộ danh"; blindtag/mc/winner cells→Việt. (council.py đang được refactor sang module cor song song.)

## 2026-07-03 — orca-eval — distill phiên phân mảnh làm stress-test /fdk
- Scan session hiện tại (30 prompt, 8 chủ đề, 6 vòng design). Report draft/orca/030726-eval-report.md: 5 best-practice (fix-at-engine, medic-last-line, điểm-trung-thực, council-chọn-đề, kim-chỉ-nam-travel) + 8 friction (F1 hand-author, F2 reinvent, F3 regression, F4 sync-sai-hướng, F5 quên-regen, F6 lẫn-ngôn-ngữ, F7 over-design, F8 quên-verify) + 7 action A1-A7. Council (linus/taleb/munger/rams/laozi) đánh giá: winner Lão Tử — đòn bẩy = medic-GƯƠNG-SOI-cuối-phiên (khi đụng framework), giữ 2 cổng tự-cắn A1+A7, gộp A4/A5, hấp thụ A3 vào A7-coverage, A2/A6 thành phụ lục, KHÔNG 7 luật rời. report council-report-020-seed42.html. Bước tiếp: propose hook framework-touch-detector + mở rộng medic 17/17.

## 2026-07-03 — council(tư vấn) — hạ tầng retrieval có hữu ích nếu agent không query?
- Nghi vấn: agent ít gọi /query (31% edit "mù", cận dưới vì grep không đếm) → hạ tầng vô dụng? Council (kahneman/taleb/munger/ada/linus). Chốt: query-rate là ĐO NHẦM (vanity/Goodhart). Tách 3 lớp: wiki-content=tiền-đề (grep trúng nhờ nó tồn tại) GIỮ; code-graph/quan-hệ-phi-cục-bộ = giá trị BỀN grep-không-thay GIỮ+đầu-tư; /query-skill = lớp-bọc → HẠ xuống optional. ĐO reinvent-rate + cross-break + harm-when-missing + retro-test; BỎ query-rate; KHÔNG ép query (theater). Hành động: retro-test 31% mù trước; code-graph entrypoint rẻ 1-lệnh; retrieval tự-surface (hook pre-edit cảnh báo cross-break). report council-report-022-seed42.html.

## 2026-07-03 — propose — milestone v1.0.6 (mở nợ sau release)
- Sau release v1.0.5, mở milestone sau: proposal 030726-milestone-v106-harden (T-260703-02) gộp 4 nợ thành roadmap 6 task. Context = council-020 (medic gương-soi + A1/A7 + hấp thụ A3) + council-022 (query: đừng ép, đo reinvent/cross-break, hạ /query, code-graph rẻ, tự-surface) + issue #4 (logger). Tasks: T1 medic 17/17, T2 framework-touch hook, T3 A1 generator-probe, T4 code-graph entrypoint rẻ, T5 retrieval tự-surface (pre-edit cross-break), T6 đo reinvent/cross-break (không query-rate) + rà issue #4. Cặp md+seq.html (6 diagram). Bằng chứng cấp thiết: bug R7-f dark-rail vừa lọt medic 5/17 ở release. DỪNG chờ duyệt.

## 2026-07-03 — provenance — bản ghi phiên b73d2c47
- User lo: session mới không tra được chức năng sinh từ phiên nào + context gì. Trace hiện HỞ: ledger.jsonl ghi session cho WIKI-file nhưng code (events.jsonl) KHÔNG có session, không neo context. Giải: sources/030726-session-provenance.md — neo session-id → 7 chức năng → context (council report + proposal) → commit f71e17f. Queryable: query medic → tới đây. Systematic auto-capture = thêm T7 vào milestone v1.0.6.

## 2026-07-03 — last30days+council — bộ nhớ thứ cấp (context vụn)
- Issue #5: wiki chỉ lưu proposal, sửa+context vụn mất. /last30days: cộng đồng dùng markdown-first (AGENTS.md 60k), event-sourced journal (PROJECTMEM), ADR/MADR immutable, bỏ RAG. Council (ada/taleb/linus/rams/munger): kiến trúc 3 tầng THÔ(auto scratch-log.jsonl tách ledger, append-only, vì-sao optional, ngưỡng commit/save) → JOURNAL-DISTILL(markdown-ngày, người promote) → WIKI(curated). Mâu thuẫn rotate-vs-không-mất giải bằng GIT (rotate view, history bất biến). 3 khe Linus: events.jsonl +session, VIEW gom session/feature reuse problem-tree/wiki-graph 2-zoom, chỗ ghi 1-dòng vì-sao. Reuse KHÔNG RAG/SQLite. Judgment-at-READ. report council-report-024-seed42.html.

## 2026-07-03 — propose — bộ nhớ thứ cấp 3-tầng (issue #5)
- Proposal 030726-secondary-memory (T-260703-03) từ council-024 + /last30days + issue #5. 4 task: T1 hook auto scratch-log.jsonl (append-only, why optional, tách ledger), T2 events.jsonl +session, T3 VIEW memory-map 2-zoom reuse build-wiki-graph (không RAG), T4 distill auto session-provenance (hấp thụ T7 v1.0.6, không xoá thô). Nguyên tắc: git=lưới an toàn không-mất, judgment-at-read, reuse không SQLite/RAG. Cặp md+seq.html (4 diagram). DỪNG chờ duyệt.

## 2026-07-03 — implement — secondary-memory T1+T4 (scratch-log)
- harness/scripts/scratch-log.py: T1 note (append context vụn → scratch-log.jsonl TRACKED, git giữ vĩnh viễn, why optional) + T4 distill (gom scratch+ledger theo phiên → sources/DDMMYY-session-provenance.md, KHÔNG xoá thô). Test: ghi 3 why phiên này → distill ra 030726-session-provenance.md (auto thay bản tay; bản tay giàu vẫn trong git ff7c47e — chính nguyên tắc không-mất). CÒN: T2 (events.jsonl +session — cần hook truyền session-id), T3 (memory-map 2-zoom reuse build-wiki-graph). scratch-log.jsonl KHÔNG gitignore (khác events.jsonl).

## 2026-07-03 — propose — narrative-as-data + medic narrative-drift probe

- 2026-07-03 raise-issue x5 (frontier gap) → ledger draft + ISSUES.md + GH#9-13. Concept fdk/wiki/concepts/frontier-gap-scan.md. Report overstack-vs-world-30d.html chuyển vào llmwiki/html/.
- 2026-07-03 bổ sung mục "Repo/paper tham khảo" vào 5 issue frontier gap (ledger + comment GH#9-13).

## 2026-07-04 — fdk issue#9 — memory episodic + vector + temporal (4/4 tầng nhớ)

- mem-rank.py: thêm `episode` subcommand + temporal `ts`/`supersedes` + `--kind-filter`; self-test mở rộng (episodic + supersede).
- Skill mới `record-episode` (wiki-loop) ghi session episode; wire Tầng-0 truy hồi ngữ nghĩa vào `query` + `wiki-room`.
- Eval: `mem-proxy.py` (sinh output episodic tất định, không model) + fixtures + 2 golden episodic + `episodic-baseline.json`, gate qua medic `p_eval`. hit@k 2/2.
- Đăng ký: sync-skills mirror, CAPABILITIES, bảng AGENT/CLAUDE. Problem-tree node p-17 (solved 3/3 trụ).

- 2026-07-04 — plan cho issue #6 Foundation: ghi `030726-foundation-section-PLAN.md` (fable), index-sync.
- 2026-07-04 — GH#6 Foundation: tạo harness/foundation.yaml + template seed; generator tab "Nền tảng" derive; medic probe p_foundation; seed 2 installer; regen overstack.html. Ledger status→done.
## 2026-07-04 — fdk (GH#13) — skill-resolve ambiguity + supply-chain
Giải issue `030726-skill-resolve-supplychain` (trục #5 frontier-gap-scan, Chớm→có cơ chế). 3 cơ chế:
- `new-skill.py`: cảnh báo TRÙNG NĂNG LỰC lúc scaffold — tái dùng BM25 của `build-skill-search.py`, ngưỡng 12.0 (calibrate: biến thể trùng ≈26–44, skill lạ ≈7); flag `--strict` chặn cho CI. Chỉ cảnh báo, không chặn biến thể hợp lệ.
- Golden `skill-resolve-eval.py` + 18 case `sources/evals/skill-resolve/` (cặp nhập nhằng thật) — hit@1 18/18, baseline chốt, `--check` exit 2 khi regress; gắn CI `skills-sync.yml`.
- Skill+tool `skill-provenance` (`fdk/tools/skill-provenance.py`, store `fdk/skills.provenance.json`) — ghi nguồn+sha256, `check --ci` chặn MODIFIED/UNTRACKED; backfill 74 skill = local-authored. Bổ trợ orca-sec-scans.
Đăng ký: LOOP_MAP + marketplace + AGENT/CLAUDE + LOOP_GROUPS mind-map; regen overstack.html + skills.search.json + CAPABILITIES. Ledger status→resolved, index +18, concept trục #5 cập nhật.

## 2026-07-04 — fdk issue#18 — pre-commit chậm >2ph → tách tầng L2/CI

- Gốc (Meadows): 25 hook nhân bản trọn CI mỗi commit → stash + spawn nặng. Đưa L2 về đúng vai (concept enforcement-floor): chỉ content-validator theo file-đổi.
- `.pre-commit-config.yaml`: 25→12 hook nhanh; `pre-commit run` 0.16s (trước >2ph). Fire-drill nặng dời sang CI "repo health" (đã có) + thêm `policy-converters-drift` vào harness.yml (chưa có → không mất phủ).
- Đường cứu index-hỏng-khi-kill ghi vào comment config. Ledger done, problem-tree.

## 2026-07-04 — fdk issue#14 — overstack.html audit (đợt 1+2)

- Mọi fix ở generator build-overstack-docs.py (không sửa tay HTML), --check pass.
- Đợt 1 sự thật: "Bốn lớp"→"Ba lớp CHẶN"+giải thích L3 trống; slogan validator khớp FACT (rule enforce bởi validator+hook); BNAL nhãn tự khớp; bảng rule render 1 lần (bỏ lặp ×2); LOOP_GROUPS +ovs-notes/frontier-scan; GH#8 skill-usage auto-derive.
- Đợt 2 UX: dark mode (prefers-color-scheme), .table-wrap overflow-x (class trước KHÔNG có CSS), mind-map keyboard a11y, skip-link + nav aria-label.
- Problem-tree p-20. Đợt 3 biên tập defer (ngoài DoD).

## 2026-07-06 — fdk — wiki-sync distill openwiki (code→wiki drift)

- Đối chiếu openwiki (langchain-ai): distill 3 cái hay, nấu lại — 4 trục họ hơn nay phủ đủ.
- Mới: harness/scripts/wiki-sync.py (neo .last-sync.json, --check no-op 0 token, cờ code-drift vào stale.json flock; --mark-synced content-hash chống churn) + wiki-sync-test.sh 8/8.
- session_start.wiki_drift nhắc đầu phiên (trước early-exit — downstream v4 nhận); /lint bước 0+9 + kỷ luật surgical; /ingest docs-impact-plan; sync 3 bản.
- gen-converters sinh ci/wiki-refresh.yml (cron→PR, degrade tử tế khi không key); wiki-sync.py vào template-manifest.
- overstack.html mục Wiki viết lại đầy đủ + đối chiếu thẳng thắn openwiki (kèm giới hạn). Problem-tree p-22 (solved 3/3 trụ).
- Draft: sources/draft/060726-wiki-sync-openwiki-distill.md. Điều kiện ship: test 5 project qua orca-cli trước commit.

## 2026-07-06 — fdk — theme toggle sáng/tối cho HTML (feedback nhắc lần 2)

- build-overstack-docs.py: _DARK_RULES một-nguồn emit 2 khối (@media guard :not([data-theme=light]) + [data-theme=dark]), chip toggle ☀️/🌙 góc phải + localStorage + script chống FOUC trong head; regen overstack.html, verify click thật trên Safari (dark→light OK).
- Mã hoá thành LUẬT: docs-site-macos § "Theme Toggle sáng/tối (REQUIRED)" (snippet chuẩn 3 mảnh), /fdk § Rules (HTML cho người xem phải có toggle). Sync canonical+mirror+bản cài; provenance re-record.
- Memory feedback html-theme-toggle-required (user nhắc 2 lần — không tái phạm).

## 2026-07-06 — fdk — theme switch: nút gạt đáy sidebar (feedback vị trí ×2)

- Bỏ chip icon 2 góc → NÚT GẠT track 50×26 (☀️/🌙 hai đầu, knob trượt, role=switch + keyboard), hàng "Giao diện" sticky đáy sidebar, vách ngăn mảnh, glass cả 2 mode.
- Snippet chuẩn trong docs-site-macos viết lại theo dạng gạt-trong-sidebar; /fdk rule + memory ghi rõ "không chip trôi nổi rải góc, không chen dưới logo".
- Verify click thật Safari: light↔dark mượt, persist localStorage. medic XANH.

## 2026-07-06 — fdk — nâng thang cỡ chữ overstack.html (feedback "co nhỏ quá mức")

- 16 cỡ chữ nâng trong build-overstack-docs.py: nav 12.5→14px (padding 5.5→7px), p 14.5→15.5, ul.s 13.5→14.5, .grp/.logo small/.lbl/chip/kpi/pcard/th đều +1px; regen + verify Safari.
- Luật hoá SÀN CỠ CHỮ: docs-site-macos § Best Practices (≥14px text chính, ≥11px nhãn, cấm <10px trừ badge) + /fdk Rules; memory cập nhật.

## 2026-07-06 — fdk — ĐẢO chiều thang cỡ chữ: compact cho màn 13″ (feedback đúng ý)

- Hiểu ngược feedback trước (đã tăng size) → user chỉnh: phải GIẢM. Hạ 22 cỡ dưới cả mức gốc: nav 12px, body 13.5, lead 14, list/bảng 12.5, nhãn 10–10.5, h2 21, hero clamp(26,4vw,40).
- Luật trong docs-site-macos + /fdk + memory VIẾT LẠI đúng chiều: THANG COMPACT 13″, "dễ đọc = line-height/contrast, không phải font to", ghi chú đã-đảo-chiều-một-lần để không lặp.

## 2026-07-06 — Proposal: nền chuẩn thiết kế AI-elite chống AI-slop
- Distill `raw/design-tip-of-someone-on-internet.md` → bảng 13 tip (3 trục: ĐO ĐƯỢC/QUY TRÌNH/PHÁN ĐOÁN).
- `/last30days`: engine binary thiếu (chỉ SKILL.md) → dùng WebSearch thay; agent nền `a5a9a19` đào 8 nguồn design-agent (taste-skill, avoid-ai-design, Anthropic frontend-design, Emil Kowalski motion, high-end-visual-design, Refactoring UI, claude-design-auditor, Meta Astryx) → corpus có nguồn.
- User chốt: gác CẢ HAI đầu ra (HTML framework + skill design) bằng 1 nền chung; 2 tầng nhưng chốt-sửa thì kill 1-shot.
- Ra draft cặp: `sources/draft/060726-design-standard-ai-elite-PLAN.md` + `html/060726-design-standard-ai-elite-PLAN.html`. Index cập nhật. Problem-tree +node p-23 (open, 0/3 trụ). CHỜ DUYỆT — chưa build.

## 2026-07-07 — fdk — sidebar cuộn-không-nén, scrollbar ẩn (feedback)

- Bệnh gốc "co nhỏ quá mức" = flex-shrink nén item khi thiếu chỗ. Fix: nav>*{flex-shrink:0} + overflow-y:auto + ẩn scrollbar hoàn toàn (scrollbar-width:none, ::-webkit-scrollbar display:none).
- Luật vào docs-site-macos § Best Practices ("SIDEBAR: CUỘN chứ không NÉN") + memory; verify Safari.

## 2026-07-07 — fdk — fix vỡ selector CSS: block chống-nén chèn giữa `nav\n.logo`

- User báo "chưa thấy thay đổi" → tự capture (headless Chrome + playwright) mới lộ: block chèn hôm qua rơi GIỮA selector `nav\n.logo` viết tách 2 dòng → parser đọc thành `nav nav>*` (không match gì) + `.logo` mất scope; flex-shrink:0 không ăn, link vẫn nén còn 10px.
- Fix: trả `nav\n.logo` liền lại, chèn block trước rule `nav{position:fixed…}` (anchor không mơ hồ). Verify computed-style thật: h=29px, flexShrink=0, nav scrollable, scrollbar none, cả dark+light.
- Bài học verify: grep thấy rule trong file ≠ rule được parse — phải đo computed style/behavior thật.

## 2026-07-07 — fdk — gỡ note so sánh openwiki khỏi overstack.html (feedback)

- Docs chính thức không bình phẩm sản phẩm khác: xoá note "Đối chiếu thẳng thắn với openwiki" + attribution inline; nội dung mục Wiki giờ chỉ nói năng lực của mình.

## 2026-07-07 — Cài last30days + agent-reach (external-pull) + concept adapt-modes
- Cài engine last30days v3.11.0 (mvanhorn) vào ~/.agents/skills; cài agent-reach v1.5.0 (Panniantong) qua pipx (tarball gh-api, không PyPI). Provenance ghi cả hai (.provenance.yaml + fdk/skills.provenance.json, adapt_mode=external-pull).
- Wiring travel kiểu external-pull: travel-policy.yaml Tầng 1 +research_reach; mirror SKILL.md (last30days→v3.11.0, agent-reach mới); bảng skill CLAUDE.md/AGENT.md +agent-reach.
- Concept mới `adapt-modes`: đặt tên 3 kiểu absorb (HÒA TAN / KÉO NGOÀI / NHÚNG-SỞ-HỮU) + bảng quyết định. Sẽ render docs-site-macos.

- Render docs-site-macos concept adapt-modes → llmwiki/html/070726-adapt-modes.html (mind-map + sơ đồ định vị kéo-thả + theme toggle + 3 section kiểu adapt).

## 2026-07-07 — Chưng cất ponytail (anti-over-engineering) vào overstack
- B1: thêm khối luật luôn-nạp "Cái thang chống over-engineering" vào llmwiki/AGENT.md + llmwiki/CLAUDE.md (ladder 7 bậc + hiểu-bài-trước + root-cause fix + carve-out an toàn + format review 1-dòng/tag/net:-N). Nguồn: 060726-ponytail-distill (ponytail, MIT).
- B2: /lint thêm bước 8 grep marker nợ `shortcut: <trần>, <trigger>` thiếu trigger (canonical skills/lint/SKILL.md → sync-skill.sh ra mirror + bản cài); bước log/neo dời thành 9/10.
- B3: gộp format review 1-dòng vào khối B1 (không đẻ skill song song — /simplify là built-in). fdk-problem-tree +node p-24 (solved 2/3 trụ). medic --ci: 9/9 xanh.

- 2026-07-12 · frontier-scan #3 · quét 5 WebSearch, đối chiếu 8 trục vs kỳ #2 (04/07). Diff: không trục nào tụt hạng, không trục mới; 5 trục Thua/Chớm đều đã có issue mở chỉ còn 3 trục mở GH#10/#11/#12; đính chính: GH#9 (Memory) + GH#13 (Skill-security) đã CLOSED có code thật, kỳ #2 chép nhầm nhãn Thua/Chớm → cập nhật bằng chứng, không raise trùng (R7-f). Bằng chứng mới: Skill-security số liệu cứng (42.447 skill 26.1% lỗ hổng, Antiy 1.184 skill độc ClawHub, 80% lệch khai-báo↔hành-vi), Orchestration mốc scale (Kimi K2.5 100 sub-agent song song), Memory blueprint (Zep/Graphiti temporal KG + BEAM/LoCoMo/LongMemEval), Self-Harness/ComfyClaw/MetaSkill-Evolve (vẫn buộc verifier độc lập). Report: llmwiki/html/overstack-vs-world-30d.html.

## 2026-07-14 — R18 plan-executable + /fdk-uat (UAT THẬT, PASS)
- Lỗ: nhánh PLAN của R7 chỉ sống trong validator Python; downstream chạy engine khai báo → luật KHÔNG tới tay người cài. Cổng vẫn xanh vì rule_parity chỉ so danh sách rule id.
- Fix: R18 khai ở cả hai policy (khai báo travel downstream + production gác từng task). Bite-test 2 tầng: doctor 18/18 rails, test-broad 72/72.
- /fdk-uat: skill UAT thật — push trước (đường remote chỉ tồn tại sau push), test sau, không pass thì gỡ commit khỏi remote.
- UAT chạy thật trên dự án TRỐNG cài bằng curl từ GitHub: 3 trụ đủ · test-broad 72/72 · R18 CẮN đúng lý do · 3 skill orchestration reachable · orca runtime UP · 84 skill global · 18 rule. PASS → giữ commit c5efc57.
- UAT HAI PHA chạy thật: pha 1 canary PASS (74/74, luật mới cắn, SKILLS_REF chứng minh cài đúng bản canary chứ không phải orca). Pha 2 main-URL lần đầu ĐỎ (72/74) — điều tra ra raw.githubusercontent propagate TRỄ và KHÔNG ĐỒNG ĐỀU: engine đã mới, policy.yaml còn cũ → bản LAI. Chờ CDN rồi chạy lại: 74/74 PASS. Không phải bug code → không revert. Bài học thành luật: /fdk-uat pha 2 phải poll sentinel trước khi đo (p-29).
- UAT hai pha PASS: canary (3 trụ 5/5, harness 74/74, /wayfinder tới tay, 23 skill tắt model-invocation tới global — cắt token thật) → main-URL smoke (đường mặc định 74/74). Bug lộ ra: sentinel CDN của /fdk-uat viết sai pattern → chờ vô ích 4 phút dù raw đã mới (p-32, đã ghi cảnh báo grep-verify). UAT hai pha PASS (150726).

## 2026-07-15 — hấp thụ hallmark làm nền design chung (T-260715-02, đóng p-23)
- Cài Nutlope/hallmark (Together AI, 106 file, provenance sha256) làm NỀN — 6 discipline + 57 cổng slop-test.
- concept design-foundation: sàn chung; 12 skill taste trỏ tới (flavour trên sàn). docs-site-macos = ngoại lệ artifact nội bộ.
- frontend-antipattern.py +4 cổng UNIVERSAL grep được (gradient-text/italic-header/fake-chrome/số-liệu-marketing), quét trong <style>. --self-test PASS. 0 false-positive trên 30+ seq.html.
- DOGFOOD lộ slop THẬT: overstack.html + index.html + health-dashboard có gradient-text (blue→purple headline) do generator sinh — sửa 3 generator dùng màu đặc.
- /propose fill-default từ catalog hallmark (tag default, ghi ## Assumptions). design-variety.py + .design-log.jsonl: cổng Variety travel-được (phơi bày mọi seq.html là một glass template — nợ đã biết).
- Nợ có sẵn lộ ra (KHÔNG sửa trong SPEC này): ~17 HTML cũ gradient-text + ligature debt.
- UAT hai pha PASS (hallmark): canary (3 trụ 5/5, harness 74/74, hallmark SKILL + 24 references travel tới tay incl slop-test.md) → main-URL smoke (đường mặc định, 74/74, reachable). Raise ledger issue 150726-legacy-html-slop-debt (ready-for-agent) cho nợ ~17 HTML cũ. p-23 đóng.
- /fdk-uat TOÀN DIỆN đường mặc định (curl từ orca, KHÔNG override): 3 trụ 5/5 · harness 74/74 · /wayfinder + /hallmark (129 references incl slop-test.md) tới tay · 23 skill tắt model-invocation · /plan+/propose+/orca-workflow là bản mới · 4 engine tất định ở global harness (frontend-antipattern --self-test PASS, frontier/skill-health/design-variety reachable) · R7-n + R18 CẮN THẬT trong dự án cài mới (exit 2), concept hợp lệ QUA (exit 0) · orchestration-ready 3/3 + orca UP · 86 skill global / 18 rule. UAT toàn diện đường mặc định (150726) PASS.

## 2026-07-15 — sổ nợ unknown: fill-first-find-out-later (T-260715-03)
- Tầng thứ ba giữa (default) và [CẦN LÀM RÕ]: default rủi ro điền để KHÔNG chặn việc, ghi thành nợ có sổ truy được.
- /propose: interview LUÔN có đáp án cuối "điền mặc định bây giờ, tìm hiểu sau"; tag (default, find-out-later → [[unknown-x]] U-NN). + luồng trả nợ.
- Folder llmwiki/wiki/draft/unknown/ + _template.md; harness/scripts/unknown-ledger.py (list/add/resolve/trace, --self-test PASS, audit giữ cả 2 giá trị); /lint 8c hiện nợ (báo cáo không chặn). p-33 solved 3/3.
- UAT hai pha PASS (unknown-ledger): canary (3 trụ 5/5, harness 74/74, /propose fill-first tới tay) → main-URL smoke (đường mặc định, 74/74, /propose reachable, unknown-ledger.py --self-test PASS ở global harness — engine travel thật). p-33 đóng 3/3.

## 2026-07-15 — skill /qc-code: senior review 4 mục + test tái hiện auto-hook (T-260715-04)
- /qc-code: review senior 4 mục (security/performance/naming/logic), điểm/10 + lỗi nặng nhất + fix, verdict PASS/CẦN SỬA. Mục logic sinh test tái hiện qc-*.
- Tách đắt/rẻ (HỎI user → option 3): LLM review gọi tay/workflow; test qc-* auto qua hook tất định 0-token (verify-before-commit 3b), KHÔNG gọi LLM trong hook.
- harness/scripts/qc-regression.py (--self-test PASS, tự phát hiện pytest/vitest/jest, fail-open). /orca-workflow 6b tùy chọn. Verdict advisory; test gác cứng. p-34 solved 3/3.
- UAT hai pha PASS (qc-code): canary (3 trụ 5/5, harness 74/74, /qc-code tới tay) → main-URL smoke (đường mặc định, 74/74, /qc-code reachable, qc-regression.py --self-test PASS ở global harness — engine travel thật). p-34 đóng 3/3.

## 2026-07-16 — skill /teach-me: giải thích 2 cấp + sơ đồ + grounded runtime (T-260716-01)
- /teach-me: giải thích MỘT thứ ở 4 phần cố định (cấp hệ thống +sơ đồ · cấp code +sơ đồ · bộ ba vấn-đề/workflow/chi-tiết os·cơ-chế·vai-trò · tóm tắt luồng +sơ đồ).
- Điểm phân biệt: CHỨNG "nó chạy thế nào" bằng runtime thật — chạy + instrument/breakpoint (pdb/debugpy/node-inspect/print/log) + quan sát state, KHÔNG đọc-rồi-đoán. Mượn triết lý /verify.
- Carve-out cứng: instrument tạm DỌN SẠCH sau (git diff xác nhận); không chạy được → khai "giải thích tĩnh" + ghi nợ unknown nếu khẳng định phụ thuộc runtime chưa thấy.
- Sơ đồ hai đường: mermaid inline (mặc định) / HTML explainer glass docs-site-macos (opt-in khi giữ/chia sẻ). KHÁC /onboard-codebase + /join-project (cả dự án).
- UAT hai pha PASS (teach-me): canary (3 trụ 5/5, harness 74/74, /teach-me tới tay + nội dung grounded-runtime) → main-URL smoke (đường mặc định, 74/74, reachable). Smoke dogfood trên frontier.py chứng bằng chạy thật. p-35 đóng 2/3 trụ (skill-only).

## 2026-07-17 — propose — gộp gitignored-check trùng lặp về canonical (T-260717-01)
- Nguồn: quét vấn đề tồn đọng → flywheel `spec-violation` đã tới ngưỡng 3 (harness-events.py m_stop, audit.py detect, okf-check.py content_files — cùng lỗi "quên skip file gitignored", mỗi lần vá bằng một bản copy logic riêng).
- Điều tra lộ: `harness-lint.py` đã có sẵn meta-guard `WIKI_TREE_SCANNERS` bắt được cả 3 và khiến chúng được vá trong ngày (2026-06-28) — cơ chế phòng-ngừa hệ thống đã chứng minh hoạt động. Phần còn thiếu chỉ là dọn trùng lặp implementation trong `harness/scripts/`.
- SPEC hẹp có chủ ý: chỉ trỏ `okf-check.py` về canonical `index_sync.gitignored()` qua pattern `_load()` mà `audit.py` đã dùng đúng — không file mới. `harness-events.py` giữ nguyên bản tự chứa vì nó là lõi PoC vendor-neutral (cài độc lập qua `curl | bash` vào project khác, không có `harness/scripts/` đi kèm) — Non-goal có lý do kiến trúc, không phải bỏ sót.
- Ghi chú follow-up ngoài phạm vi: `wiki-graph.py`/`wiki-health.py` có `local_only_stem()` trùng lặp verbatim giữa 2 file — khác class lỗi, để dành propose riêng nếu cần.
- Draft: `sources/draft/170726-gitignored-dedupe.md` + `html/170726-gitignored-dedupe-seq.html`. DỪNG chờ duyệt.

## 2026-07-17 — housekeeping — dọn run-council*/ + sửa root cause thói quen output sai chỗ
- Phát hiện: 6 thư mục `run-council`..`run-council6` untracked ở repo root (audit log xác nhận tạo rải từ 2026-07-05 20:10 đến 2026-07-06 11:28 — 6 phiên riêng biệt, mỗi phiên bump số để tránh đè bản trước).
- Root cause: `skills/council/SKILL.md` (canonical) ví dụ Stage 2a/2c dùng `--out run/` — path tương đối trần, không trỏ `scratchpad/`, nên mỗi phiên tự đặt tên khác nhau ở repo root thay vì theo quy ước scratchpad đã có (đối chiếu `scratchpad/co-council/`, `scratchpad/council-eval/` — nhiều lần council TRƯỚC đã làm đúng).
- Fix root: sửa 2 ví dụ lệnh trong canonical thành `--out scratchpad/council-<slug>/` + ghi rõ lý do (bài học 170726), sync ra mirror (`llmwiki/skills/orchestrate/council.md`) + installed (`~/.claude/skills/council/SKILL.md`) qua `fdk/tools/sync-skill.sh council`.
- Dọn: gom 6 thư mục vào `scratchpad/council-archive-170726/` (giữ transcript, không xoá — reversible), không còn xuất hiện trong `git status`.
- Ghi chú phụ, KHÔNG sửa trong lượt này: phát hiện 1 bản `council.md` lạc trong `llmwiki/wiki/skills/orchestrate/council.md` (nằm sai vị trí, wiki content chỉ nên ở concepts/entities/sources/draft/architecture/tours) — nêu ra, chưa dọn vì ngoài phạm vi việc đang làm.

## 2026-07-17 — lint — wiki-sync 11 ngày drift (false-positive) + pattern-health (1 manifest thừa)
- Bước 0 `wiki-sync.py --check`: exit 3, 264 file code/nguồn đổi kể từ neo `2067448d5d` (2026-07-06, 11 ngày). 63 trang wiki bị cờ code-drift (5 concept + 10 draft + 48 source).
- Spot-check 5 trang concept bị cờ (đọc toàn văn): CẢ 5 đều được viết CÙNG LÚC hoặc SAU file code kích hoạt cờ (vd `design-foundation.md` 2026-07-15 cùng ngày `frontend-antipattern.py` được tạo) — nội dung khớp thực tế, không sai. Kết luận: cờ drift ở đây là "chưa đóng vòng review" (11 ngày không ai `--mark-synced`), không phải nội dung sai. 58 trang draft/source còn lại là ghi chép lịch sử tại-thời-điểm-viết, không cần đồng bộ liên tục.
- Bước 1 (orphan, flag không sửa): 3 concept không được trang nào khác trỏ tới — `adapt-modes.md`, `design-foundation.md`, `skill-craft.md`.
- Bước 5 (index gaps): lệnh mẫu trong SKILL.md giả định link dạng `llmwiki/wiki/...` nhưng `index.md` dự án này dùng path tương đối (`concepts/...`) → chạy đúng định dạng thì chỉ có **1 gap thật**: `sources/170726-session-provenance.md` (auto-distill hôm nay) — đã thêm dòng vào index.
- Bước 6 (empty page, flag không sửa): `llmwiki/wiki/draft/orca/README.md` <5 dòng.
- Bước 7/8/8b/8c: 0 file thiếu `## Origin` (2 README loại trừ hợp lệ), 0 marker `shortcut:` thiếu trigger, skill-health 30 skill có cờ description/negation (báo cáo, không chặn — xem `[[skill-craft]]`), 0 nợ unknown mở.
- **Phát hiện mới ngoài checklist chuẩn**: `llmwiki/wiki/skills/` là một cây lạc **68 file** mirror toàn bộ skill docs, nằm sai vị trí (wiki content chỉ được phép ở concepts/entities/sources/draft/architecture/tours theo CLAUDE.md) — cùng gốc thời điểm với stray `council.md` đã ghi ở mục housekeeping trên (commit `0363f5d`, 2026-07-02). KHÔNG dọn trong lượt này (68 file, vượt soft-diff-budget) — khuyến nghị `/raise-issue` riêng.
- Pattern-health (`health-check.py`): 1 file "thiếu" (`llmwiki/skills/README.md`) hoá ra là bị XOÁ CÓ CHỦ Ý ở cùng commit `0363f5d` (33 dòng, thay bằng whiteboard) nhưng `.template-manifest.json` quên gỡ tên — xoá đúng 1 dòng thừa trong manifest (root-cause fix, không phục dựng file đã xoá chủ ý). Sau sửa: 75 pattern, 0 missing; 26 pattern "cũ hơn remote" lộ ra đúng thực chất sau khi bỏ entry ma — khớp `[[framework-multi-session-dev]]` (repo này local-ahead, KHÔNG sync/revert).
- Chốt neo: `wiki-sync.py --mark-synced` sau khi review xong.

## 2026-07-17 — propose — absorb-six-sources
Draft SPEC absorb HÒA TAN 6 nguồn GitHub (gstack review, awesome-skills code-review, everything-claude-code security-review, anthropics frontend-design, claude-mem portability, superpowers receiving-review+systematic-debugging) → nâng qc-code / orca-sec-scans / mem-rank / design-foundation / orca-issue. T-260717-02, chờ gate.

## 2026-07-17 — plan — absorb-six-sources-PLAN
PLAN 6 task thi hành cho T-260717-02 (FR-001..007 phủ đủ, R18 xanh). Executor: Claude in-session.

## 2026-07-18 — propose — capability-proof-map
SPEC checklist năng lực tự soi + tự cộng: proof-resolver 6 tầng trong build-capabilities, medic probe capproof (ratchet), guard fire-drill. T-260718-01, chờ gate.

## 2026-07-18 — plan — capability-proof-map-PLAN
PLAN 4 task (resolver 6 tầng / probe ratchet / guard 4 chiều / dups+mech). Executor: Claude in-session.

## 2026-07-18 — propose — archetype-tester
SPEC vai thứ 6 tester (/test): persona thiết kế test neo FR/SC + code qc-*. T-260718-02, chờ gate.

## 2026-07-18 — fdk-uat — batch grower+tester+maintainer lên orca
Canary 260718-1101 vòng 1: 10/12 — lens TESTER bắt 2 lỗi thật (persona không travel global; wikieval self-test không hermetic). Fix faf5918 → vòng 2: 12/12. PHA 2 main-URL smoke 0-override: 7/7. orca @ faf5918, canary đã xoá, stamp 1.3.24.

## 2026-07-18 — raise-issue — council-self-index-remaining-scope
Draft 020726-council-chon-de-thi-self-index verify chéo 6 nguồn: hạ tầng nền đã ship (d4d8b90), phần lõi (council tự chọn đề thi) chưa. Mở GH#81 giữ scope còn lại, priority P3 ready-for-human. Task T-260702-02 → superseded.

## 2026-07-18 — persona-beneficiary — chống miscontext lens
Feedback: dùng lens grower phân tích RedPlanetHQ/core, metric bị đo trên chính framework thay vì dự án đích (ngược ADR-004). Fix root-cause: thêm dòng **Beneficiary** vào cả 6 file `llmwiki/personas/*.md` — mặc định đo trên DỰ ÁN ĐÍCH, ngoại lệ duy nhất là phiên /fdk khai rõ. Memory máy-local `persona-lens-beneficiary` ghi kèm.

## 2026-07-18 — mem-rank-episodic-wire — bật 2/3 thí nghiệm mượn từ RedPlanetHQ/core
Sau khi mổ code CORE (temporal invalidation + hybrid recall) và đối chiếu với framework, wire 2/3 cải tiến đã đo metric/guardrail:
1. `llmwiki/.claude/hooks/stop.py` — `secondary_memory()` giờ gọi thêm `mem-rank.py episode` mỗi phiên có git-dirty (did=commit subject, files=đổi trong phiên). Trước bản vá này tầng episodic CHƯA từng tự ghi (`memory.jsonl` rỗng) — chỉ chạy tay qua `/record-episode`.
2. `llmwiki/skills/wiki-loop/lint.md` step 0b — thêm rubric 4 nhánh (contradiction/superseding/progression/equivalence) để phân loại code-drift trước khi sửa trang; nhánh `superseding` dùng frontmatter `invalid_at`/`invalidated_by` (đóng dấu, không xoá) thay vì sửa đè câm lặng — mượn ý bi-temporal của CORE, R9 không chặn khoá lạ nên an toàn thêm.
3. **Chưa làm** (item 1/3 — bật embedder semantic cho mem-rank): cần Ollama cài local, máy hiện không có (`which ollama` → not found). Adapter đã sẵn (`harness/mem-rank.config.yaml` + `embed-ollama.py`), chỉ còn bước hạ tầng ngoài phạm vi code — để lại nguyên trạng `verified:false`.
Verify: `mem-rank.py --self-test` PASS, dry-run episode ghi+retrieve đúng trong store tạm, `medic --ci` 14/14 + toàn bộ step CI repo-health (wiki-health/arch-scan/harness-lint/parity/dup-basename/7 test bash/harness-doctor/build-capabilities/adapt-registry) đều xanh trước khi push.

## 2026-07-19 — propose — travel-gap-forcing-functions
Draft T-260719-01: bịt 3 lỗ travel đường curl update (stamp surface thiếu 4 nhóm file · 34 skill trỏ path repo-relative chết ở downstream · fdk-uat/poc chỉ test dự án trống) — mỗi fix kèm forcing function (fdk-gate/medic · harness-lint · cổng /ship); T3 nâng thành fixture "dự án dang dở" dùng chung uat+poc theo góp ý user. Cặp: sources/draft/190726-travel-gap-forcing-functions.md + html/190726-travel-gap-forcing-functions-seq.html. STOP chờ duyệt.

## 2026-07-19 — propose — graph-lessons-grapuco
Draft T-260719-02: đọc thread cộng đồng Grapuco qua 3 lens persona (Grower/Prototyper/Maintainer) → 6 task chia theo độ chắc bằng chứng "sửa 2, đo 3, nháp 1". Phát hiện lõi: `/query` KHÔNG đọc `stale.json` (grep ra 0) — cờ code-drift do wiki-sync ghi chỉ tiêu thụ ở /lint, đường đọc mù → đúng kịch bản "graph là source-of-truth mà nội dung lệch" thread cảnh báo. Hở thứ 6 do user nêu: ranh giới persona là ngõ cụt (archetype.py không có handoff) → nối /raise-issue (hoãn) + council roster (gọi vào room ngay), cả hai nửa đã có sẵn. Loại phương án Context Hub vì thừa hưởng đúng 2 vết thương thread chỉ ra. Cặp: sources/draft/190726-graph-lessons-grapuco.md + html/190726-graph-lessons-grapuco-seq.html. STOP chờ duyệt.

## 2026-07-20 — thi hành T-260719-02 — graph-lessons-grapuco (6/6 task)
T1 wiki-sync `--flags-for` (fail-open, luôn exit 0) + query SKILL bước 3b — cờ code-drift cuối cùng tới ĐƯỜNG ĐỌC; test 11/11, chứng trên 3 trang drift thật. T3 sync-log.jsonl (137ms, 0 token). T4 đổi golden extract-site→newcomer-adr, giữ trần 30, HIT recall 1.0, hit@5 30/30, baseline chốt lại. T6 6 persona + 6 archetype vào council roster (case lifecycle, profile archetype, 3 cặp đối-trọng) — ranh giới persona hết là ngõ cụt. T2 ĐỔI KẾT LUẬN: code-graph MCP HỎNG (ghi/đọc lệch DB; reindex OK mà search `no such table`), A/B 37 vs 14 call cùng độ chính xác 5/5 — đo được chi phí tool hỏng, KHÔNG đo được giá trị code-graph; dừng ở số, handoff issue 200726-code-graph-index-broken cho maintainer. T5 NO-GO vì cùng nền hỏng. medic --ci 14 ok.

## 2026-07-20 — /fdk propose — orchestration-loop-closure
T-260720-01 Pha 1. Thử Orca trước theo yêu cầu: ĐO LIVE runtime — 59 task, 42 completed, 8 có deps, 18 terminal, 4 CLI khác vendor (claude/opencode/agy/copilot) ⇒ Orca LÀM ĐƯỢC, chưa cần herdr (điều kiện user không kích hoạt; herdr vẫn là ẩn số). Nhưng phép đo phơi ra 17 task treo (12 ready + 2 blocked + 3 failed) từ 22/05→17/07 — vòng phản hồi HỞ. dispatch-verify chỉ đóng vòng proposal↔đĩa, không chạm runtime state. Theo Meadows: thêm vòng phản hồi trước, không thêm tính năng. 3 task: orca-reconcile (chỉ báo cáo, fail-open, KHÔNG tự đóng) · probe medic thứ 15 mức warn · triage 17 task. Pha 2 (orchestrator tự học + ghim vai↔worktree↔CLI) chỉ mở khi SC-004 đạt. STOP chờ duyệt.

## 2026-07-20 — /fdk thi hành T-260720-01 — nguyên thuỷ "biết khi nào agent xong"
User phản biện "orca-workflow toàn tự làm" → ĐO LẠI: user ĐÚNG, tôi SAI. 59 task orchestration, chỉ 13 (22%) từng dispatch, 46 (78%) có dispatch:null; 14/14 task ready+blocked chưa từng giao. Nhưng gốc KHÔNG phải Orca không giao được: dispatch thật cho opencode chạy ngon, còn `terminal wait --for tui-idle` TIMEOUT 90s trên việc xong sau 9s (status vẫn "running" vì đó là shell). Orca không có agent_status ở đâu cả (soi terminal list 12 trường + worktree ps). Clone+đọc herdr (Rust 233k LOC, AGPL-3.0): nó có agent_status working/blocked/done vì QUAN SÁT pane thay vì tin worker tự khai. Mode HÒA TAN: lấy ý tưởng, cài bằng đồ Orca — sentinel `<cmd>; echo __ORCA_DONE__<id>:$?` + poll terminal read. T1 orca-dispatch.py (self-test 9/9). T2 chứng thật: opencode 9385ms exit=0 "Hà Nội" · agy 9088ms exit=0 "Tokyo" · nhánh lỗi 2337ms exit=127 → harness/metrics/dispatch-proof.json. T3 orca-reconcile.py (self-test 9/9, nhóm chính chưa-từng-dispatch) + probe medic thứ 15 mức WARN. T4 bản đối soát 17 task: 6 đóng được (bằng chứng cứng), 11 thuộc dự án khác → GIỮ, chờ user xác nhận (không xoá thứ mình không hiểu). medic --ci 0 fail 14 ok.

## 2026-07-20 — /fdk vá gap scope — sổ task Orca là runtime-global
User hỏi "HRIS/DMS/email-viewer là gì sao có trong này" → truy ra: sổ orchestration của Orca RUNTIME-GLOBAL (guide Orca nói thẳng), 18 terminal của nhiều dự án cùng ghi MỘT sổ. 11/17 task treo thuộc bonbon-ai · HRIS/payroll · DMS Coteccons · 5 sân test framework — không phải nợ của repo này; tôi đã trình bày sai chỗ đó. Nguy hiểm hơn báo cáo nhiễu: orchestrator ở dự án A claim được task dự án B, phá đúng mục tiêu tách-bias-tầng-vật-lý. Orca không có trường dự án (task-create không tag, task-list không lọc — đã kiểm). Vá ở tầng ta: (ghi) orca-reconcile.py --stamp đóng dấu repo root lúc task-create, đúng vĩnh viễn kể cả khi terminal chết (0/17 terminal cũ còn sống); (đọc) --scope current|all, thứ tự tin cậy stamp > map người-xác-nhận > dò path > unknown; fail-safe CHỈ loại task chứng minh được là của dự án khác, unknown thì GIỮ (vứt đi sẽ báo "0 treo" trong khi 3 task của mình đang nằm đó — đã dính bug này, test khoá lại). harness/orca-project-map.json backfill 11 task user xác nhận. Đóng 6 task của chính repo (3 có bằng chứng đã ship + 3 thí nghiệm chết). Kết quả: scope current 0 treo, medic 0 fail 0 warn 15 ok.

## 2026-07-20 — /fdk sửa code-graph MCP (issue P1)
Đọc code server (workspace/graph, 2087 LOC) thay vì đoán từ triệu chứng → chẩn đoán cũ của tôi SAI ("đường ghi/đọc lệch DB"). Thật ra 2 bug: (1) _each_db/get_stats fan-out qua MỌI DB registry mà get_all_db_paths chỉ kiểm .exists() → ĐÚNG MỘT db thiếu bảng symbols (payroll-frontend-develop) ném lỗi giết cả truy vấn, dù 16 DB kia lành — giải thích vì sao reindex báo thành công mà search vẫn hỏng; (2) list_projects dùng basename.rsplit("-") tàn dư layout cũ → mọi repo hiện thành "index.db". Đính chính số liệu: tôi từng báo "11 DB hỏng" — sai, do ổ ngoài chưa sẵn sàng lúc đo; thật là 1. Sửa tại HÀM DÙNG CHUNG (is_usable_db trong get_all_db_paths) thay vì vá từng caller. Commit 2727ede repo graph. Sau sửa: 17→16 DB, list_projects trả tên repo thật, search_symbols("flag_stale") trả 8 kết quả, 53.208 symbol query được. CÒN: phải restart MCP server (process giữ code cũ — vừa kiểm, vẫn trả 17x index.db).

## 2026-07-20 — /fdk đóng issue code-graph + đo lại A/B trên tool đã lành
Sau restart, verify từ client: list_projects trả 16 tên repo thật (trước 17x "index.db"), get_stats 16 project/5963 file/53208 symbol/550651 edge (trước "no such table"), search_symbols("flag_stale") ra đúng wiki-sync.py:138. Chạy lại A/B 5 task x 2 nhánh: lần 1 (tool hỏng) 37-vs-14 = 2.64x đắt; lần 2 (tool lành) 24-vs-16 = 1.50x. Tách theo LOẠI TRA CỨU mới ra kết luận thật: tra HÀM/LỚP/METHOD 11-vs-11 HOÀ; tra HẰNG SỐ 13-vs-5 THUA 2.6x — vì code-graph CHỈ index function/class/method, search_symbols("CONTENT_DIRS") trả rỗng, agent thử rồi phải quay về grep nên trả phí hai lần. Sửa dòng orientation trong session_start.py khai rõ phạm vi (hàm/lớp/method + get_callers; hằng số·config·chuỗi thì grep thẳng) — một dòng biến khoản thua thành hoà. Trả lời thread Grapuco: với ca định-vị-hàm ở repo cỡ này, "model đã đủ giỏi đọc repo" là ĐÚNG; giá trị còn lại của code-graph nằm ở get_callers/quan hệ gọi (550k cạnh) mà grep không làm được — CHƯA đo. medic 0 fail 15 ok.

## 2026-07-20 — /fdk vá lớp lỗi "TỒN TẠI ≠ DÙNG ĐƯỢC"
User hỏi: tool cứ chết ngang thì kiểm kiểu gì. Truy ra lỗi CẤU TRÚC: orientation quảng cáo code-graph dựa trên đúng một câu `(root/".graph-agent"/"index.db").is_file()` — tức "file có tồn tại không". DB 0 byte, DB thiếu schema, server chết, server chạy code cũ đều lọt. Đó là lý do code-graph hỏng nhiều tuần mà mọi phiên vẫn bị lùa vào (đo 37 tool-call vs 14). Nguyên tắc mới: QUẢNG CÁO MỘT NĂNG LỰC = PHẢI THĂM DÒ NÓ, không phải kiểm sự tồn tại của nó. dep-health.py (probe code-graph: DB có schema + tiến trình server sống; orca: CLI + runtime ready), self-test 8/8 không cần dependency nào. session_start đảo thành fail-CLOSED: không chứng minh được là chạy thì KHÔNG quảng cáo (fail-open ở tầng hook, fail-closed ở tầng quảng cáo). medic probe thứ 16 "deps" mức warn. Test dep-health-gate khoá 3 bất biến 5/5. TRẦN ĐÃ BIẾT ghi thẳng docstring: không bắt được ca "server chạy code CŨ" — hook không nói được giao thức MCP.

## 2026-07-20 — /fdk quét + vá TOÀN BỘ lớp lỗi "TỒN TẠI ≠ DÙNG ĐƯỢC"
User: "xem có đứa nào tương tự nữa không, fix luôn tất cả 1 cách hệ thống". Audit toàn repo (hooks/harness/fdk-tools/skills) tìm được 8 chỗ THẬT SỰ SAI (và xác nhận nhiều chỗ KHÔNG sao — file tĩnh thì tồn tại đúng là dùng được, không báo nhầm). Đã vá theo mức nguy hiểm:
T1 hook auto-chạy — code_graph_keeper.py: cùng predicate index.db.is_file(), nặng hơn session_start vì nó GHI vào registry global ~/.graph-agent/repos.txt và DẬP TẮT cảnh báo "chưa index"; nay đòi DB dùng được, dùng chung định nghĩa db_has_schema của dep-health (import theo path, fallback tại chỗ, hook không bao giờ chết).
T2 cổng sức khoẻ nói dối — harness-doctor probe_precommit_installed TỰ THU bằng chứng ngược ("binary NOT on PATH") rồi vẫn return True; nay installed AND binary. medic p_backstop docstring hỏi "còn sống" mà trả lời bằng .exists(); nay kiểm cả binary trên PATH.
T3 hệ PROOF nói dối ở quy mô danh mục — build-capabilities: ĐO ĐƯỢC 200/200 "bằng chứng" KHÔNG thực thi gì (tests/selftest/golden/rule-map/dir-exists đều là tồn-tại-file hoặc trùng-chuỗi; "thư mục tồn tại" bán thành proof liveness). Mà CAPABILITIES.md — file CLAUDE.md dặn agent tin — in tiêu đề "năng lực còn SỐNG". Nay gọi đúng tên: "Neo bằng chứng — N/M có neo KHAI BÁO" + đoạn giải thích rõ nó bắt được gì (năng lực không neo vào test/golden nào) và KHÔNG bắt được gì (test đỏ, engine chết), trỏ sang dep-health cho câu hỏi liveness. medic capproof đổi "proven" → "có NEO khai báo (tĩnh, chưa thực thi)". medic p_narrative khai rõ live_probe chỉ kiểm đường dẫn tồn tại. Để lại shortcut marker: nâng lên chạy thật khi có ngân sách CI, rẻ nhất là tier selftest.
T4 code-state: "index có (0KB)" là FACT sai lên overstack.html; nay "index dùng được (22335 symbol)" / "index HỎNG (thiếu bảng)".
T5 skill prose orca-onboard: gate "server đang khai báo" → đòi dep-health status ok; và mô tả keeper khớp hành vi mới.
medic 0 fail 16 ok · dep-health-gate 5/5 · capability-stamp 1.3.37→1.3.38.

## 2026-07-20 — /fdk 5-Why thành mặc định + trả lời "thẻ ghi-tạm có đóng không"
User hỏi: ghi tạm xong có đóng không → ĐO: 20 thẻ p-auto, 19 MỞ 1 đóng. Hook session_end sinh thẻ tự động nhưng KHÔNG có gì đóng chúng — xác nhận root đã nêu: bắt nợ có, trả nợ không.
5-Why lập kế hoạch sửa chữa 8 mục, phát hiện HỘI TỤ: 5/8 (thẻ ghi-tạm 19/20 · issue mở 24 · pattern lệch 15 · file chưa rà wiki 39 · task treo 17) chung MỘT root — hệ giỏi PHÁT HIỆN nợ, không có nhịp TRẢ nợ. Đòn bẩy Meadows: thêm MỘT đường trả nợ, không thêm bộ phát hiện thứ sáu.
Phát hiện ngoài dự kiến trong lúc lập kế hoạch: 10 tiến trình code-graph server orphan (cũ nhất 15/07, mỗi phiên spawn một, không ai dọn) ⇒ _proc_alive("graph/server.py") của dep-health khớp BẤT KỲ cái nào, kể cả orphan chạy code cũ — tôi vừa mắc lại chính lớp lỗi mình đi sửa, mức nhẹ. Phát hiện được từ ngoài: so ps -o lstart của process với git log -1 của repo server.
Ghi 5-Why thành MẶC ĐỊNH vào llmwiki/CLAUDE.md + AGENT.md (đặt TRƯỚC cái thang: hiểu đã rồi mới lười đúng chỗ): viết chuỗi ra không nghĩ thầm · dừng ở cấu trúc không dừng ở "vì người ta quên" · tìm hội tụ trước khi sửa · nghi ngờ chẩn đoán đầu tiên của chính mình (ca code-graph) · ngoại lệ duy nhất là việc không chứa chẩn đoán. Parity AGENT↔CLAUDE xanh. medic 0 fail 16 ok.

## 2026-07-20 — /fdk truy tận gốc vụ "10 con server cùng sống"
User: "10 con cùng sống là lỗi to vl rồi còn gì" — đúng, tôi đã đánh giá nhẹ. 5-Why + đo thật, ra CHUỖI lỗi chứ không phải một lỗi:
1. RÒ RỈ CONNECTION (repo graph, commit 2c2653a): indexer.py:154 `get_stats(get_conn(db_path))` mở connection inline không đóng — nằm trên đường index nên mỗi lượt reindex rò 1 fd. Đo: 1 server sống 3 ngày giữ 369 fd tới CÙNG 1 file (712 fd, chỉ 3 file riêng biệt). Chưa sập vì trần fd máy này là 1.048.576, KHÔNG phóng đại thành nguyên nhân "chết ngang".
2. ORPHAN: 10 tiến trình, mỗi phiên spawn 1, không ai dọn. RAM chỉ 152MB, CPU 0
## 2026-07-20 — /fdk truy tận gốc vụ "10 con server cùng sống"
User: "10 con cùng sống là lỗi to vl rồi còn gì" — đúng, tôi đánh giá nhẹ. Đo thật ra một CHUỖI lỗi:
1. RÒ RỈ (repo graph 2c2653a) indexer.py:154 mở connection inline không đóng; 1 server 3 ngày giữ 369 fd tới CÙNG 1 file. Chưa sập vì trần fd = 1.048.576.
2. ORPHAN 10 tiến trình, mỗi phiên spawn 1, không ai dọn. Nhưng 152MB/0% CPU — không phải vấn đề tài nguyên.
3. LỖI CỦA TÔI #1: _proc_alive hỏi "có tiến trình nào không". Sửa: so ps -o lstart với git log -1 repo server, BẮT ĐƯỢC ca "server chạy code cũ" mà bản trước tự khai là giới hạn kiến trúc.
4. LỖI CỦA TÔI #2 (hỏng thật): reap định nghĩa orphan = "không phải cái mới nhất", kill 9 con, TỰ CẮT MCP phiên này; con sống sót thuộc phiên Claude khác. Sửa: is_orphan = CHA ĐÃ CHẾT.
5. LỖI CỦA TÔI #3 (nặng nhất): db_has_schema dùng mode=ro. WAL cần -shm; server tắt thì mode=ro báo hỏng trên DB LÀNH. Lời giải cho lần đo đầu "11 DB hỏng" — tôi đổ oan cho ổ ngoài. Vá 4 chỗ gồm db.py server (801651b) nơi nó lọc get_all_db_paths.

## 2026-07-20 — /fdk kiểm kê graph + centralize #2/#3
Trả lời 4 câu của user. TẠO: #1 code-graph do reindex_repo; #2 wiki-whiteboard + #4 memory-map do stop.py::regen_docs cuối phiên; #3 wiki-graph.py dựng trong RAM mỗi lần gọi; #5 skill-whiteboard thủ công, 17 ngày không ai gọi. DELIVER: travel-policy cho #2/#3/#4 đi xuống (nhóm memory_query), #5 framework_only ở lại, còn #1 code-graph KHÔNG có trong travel-policy lẫn template-manifest — nó là MCP server riêng ở workspace/graph, downstream curl-cài KHÔNG hề có. UPDATE: #2/#4 tự sinh lại cuối phiên khi git-status có diff wiki/ hoặc code; #1 watcher debounce 2s nhưng chỉ trên máy có server.
KIỂM KÊ: 5 graph THẬT gộp về 3 mô hình. #1 code-graph (22.213 symbol, 272.529 cạnh: 253.969 CALLS + 18.560 IMPORTS) là cái DUY NHẤT agent truy vấn theo quan hệ lúc chạy; #2/#4/#5 để NGƯỜI nhìn; #3 là CLI thủ công. #4 và #5 chỉ importlib renderer của #2 — lười đúng cách. CHẾT: graph.db ở gốc repo (xác minh 0 file/0 symbol/0 cạnh), wiki-graph-static.html, skill-whiteboard drift 17 ngày. KHÔNG phải graph: mem-rank (danh sách xếp hạng), ledger.jsonl (chuỗi), stale.json (dict phẳng), fdk-problem-tree (CÂY, mỗi node 1 cha).
CENTRALIZE #2+#3 (user chốt): hai bản cài trả lời cùng câu hỏi "cái gì link tới cái gì" bằng hai regex độc lập, LỆCH THẬT 208 vs 164 cạnh, mỗi bên sai một kiểu nên không chọn bừa bên nào làm chuẩn — #3 không bỏ code-fence (đếm [[...]] trong ví dụ code), #2 giữ nguyên [[trang#anchor]] (sinh cạnh trỏ vào hư không). Nay một nguồn: wikilink_targets()/mdlink_targets() ở wiki-graph.py, build-wiki-graph.py import qua importlib có fail-open về regex local. #3 giảm 208→194 (loại 14 cạnh giả). Test wikigraph-single-source 4/4 khoá cả ba bất biến.

## 2026-07-20 — /fdk (a) nhúng graph vào overstack + (c) touches tự suy
User: "touch không tự update là vấn đề hệ thống" — đúng, và cùng root với 19/20 thẻ ghi-tạm, 24 issue mở, 15 pattern lệch.
5-Why touches: cũ vì wiki-relations.py chạy 1 lần 02/07 → nó là MIGRATOR không phải MAINTAINER → không ai nối vào nhịp → vì được đóng khung "dập quan hệ vào frontmatter" → ROOT: một sự thật SUY RA ĐƯỢC bị cất như sự thật ĐƯỢC KHAI; cất rồi thì đóng băng. wikilink không bao giờ cũ vì suy lại mỗi lần dựng.
(c) Chuyển logic suy touches từ writer sang ENGINE: wiki-graph.py thêm touches_targets(text, repo_root) — path trong backtick, có "/", TỒN TẠI trên đĩa. Lưu ý ngược với wikilink_targets: KHÔNG strip_code vì path nằm chính trong inline-code. build-wiki-graph.scan() suy sống mỗi lần dựng, frontmatter vẫn thắng (không nhân đôi). KẾT QUẢ: touches 21 → 283 cạnh, và 283/283 đích tồn tại thật (zero false-positive vì điều kiện bắt buộc có trên đĩa). Cầu nối concept↔code từ 0,8% lên ~10% tổng cạnh, và không thể cũ nữa.
(a) Nhúng #4 memory-map + #5 skill-whiteboard vào overstack.html bằng iframe srcdoc. Lý do chọn iframe thay vì tách fragment renderer: iframe cô lập JS/id nên KHÔNG phải mổ template 350 dòng của build-wiki-graph.py — engine đó đang travel. overstack.html 145KB → 412KB, 2 iframe, unescape ra tài liệu hợp lệ. Vì overstack.html là "output travel" nên #4/#5 giờ đi xuống máy user mà không cần đổi travel-policy.
Kiểm kê trả lời user: #1 code-graph (symbol→symbol) và #3 wiki-link (trang→trang) KHÔNG giải chung bài toán — khác node, khác câu hỏi. Cầu nối concept→code là #2 touches, và trước hôm nay nó gần rỗng.

## 2026-07-20 — /fdk chốt khung: MỘT bài toán graph, ghi thành concept
User chốt khung: "cả 3 cái đều để giải 1 bài toán thôi — artifact liên quan gì đến nhau và liên quan gì đến code; code liên quan gì đến nhau là sản phẩm phụ", và "grep lời không không giải quyết được".
ĐO ĐỂ CHỨNG: wiki-sync.map_suspects CHÍNH LÀ touches đảo chiều, cài bằng grep. Trên cùng 8 file code đổi — grep nghi 36 trang, graph có cạnh thật 25, trùng 21 ⇒ grep báo THỪA 15 và BỎ SÓT 4. Hỏng cả hai chiều, dù docstring tự nhận "thiên về recall". Cờ drift toàn hệ đang do phép đoán quyết định trong khi cạnh thật nằm sẵn trong graph.
Ghi wiki/concepts/graph-model.md: bài toán thật · 5 bản cài = 3 lát cắt (artifact↔artifact, artifact↔code là lý do tồn tại, code↔code là sản phẩm phụ) · bằng chứng grep hỏng · bài học gốc "sự thật SUY RA ĐƯỢC thì phải SUY đừng CẤT" · vì sao từng có 2 scanner · code-graph KHÔNG travel · 3 việc còn nợ theo thứ tự · và END STATE.
END STATE (trả lời "sau merge còn gì"): MỘT engine wiki-graph.py giữ model; nhiều view không view nào tự dựng model (build-wiki-graph = renderer, memory-map/skill-whiteboard đã là renderer, wiki-sync ĐỌC graph thay grep, /lint /query tiêu thụ cờ); BIẾN MẤT HẲN: wiki-relations.py (cả 2 việc của nó — derives-from từ ## Origin, touches từ backtick — đều suy ra được, nên writer hết lý do tồn tại, và mất luôn khái niệm "dập quan hệ vào frontmatter" tức mất nguồn gốc việc quan hệ bị đóng băng), graph.db gốc repo (0/0/0), wiki-graph-static.html; NGOÀI HỆ tuỳ chọn: code-graph MCP gác bằng dep-health.

## 2026-07-20 — /fdk cài i-have-adhd + hook vào đầu phiên + file bàn giao
Cài skill i-have-adhd (github.com/ayghri/i-have-adhd) đúng quy trình: canonical skills/ → LOOP_MAP utils → sync mirror → bảng Skills ở CLAUDE.md + AGENT.md (parity 82/82) → provenance ghi nguồn+sha → npx skills add --global.
FRESH-INSTALL BẮT ĐÚNG TÔI: sau khi đăng ký bảng mà chưa cài global, medic báo "SKILL RỚT — doc hứa nhưng user KHÔNG nhận được: i-have-adhd". Chính lớp lỗi "documented ≠ delivered" truy cả phiên, và harness bắt được người truy nó. Sửa bằng npx skills add . --global --all.
Hook output_style() vào session_start, gọi TRƯỚC orient(). Chỉ in khi skill thật sự có mặt trên đĩa (thăm dò, không đoán — theo đúng luật đã học). Khai rõ ranh giới vì hai luật kéo ngược nhau: i-have-adhd cắt ngắn CHAT, còn CLAUDE.md bắt tài liệu-người-đọc phải văn xuôi đầy đủ ⇒ phân xử: skill áp cho CHAT, file tài liệu (ADR/proposal/README/report/HTML) giữ luật cũ.
File bàn giao wiki/sources/draft/200726-graph-foundation-handoff.md: 6 việc theo thứ tự (bước 0 travel-policy vs installer là CHẶN, rồi --also, bỏ imports, wiki-sync đọc graph, merge, CAPABILITIES sinh từ graph), 4 việc dọn nhỏ, nợ mở, và 5 cạm bẫy phải đọc trước khi sửa code.

## 2026-07-20 — /fdk skill /orca-handover + thư mục sources/handover/
Pre-flight #3: grep ra KHÔNG có skill nào làm việc này. Ba cái gần nhất và ranh giới đã khai vào description để router không chọn nhầm — record-episode ghi cho MÁY truy hồi ngữ nghĩa (mem-rank); plan là brief thi hành cho task ĐÃ duyệt và đã rõ; orca-cli 'full handoff' là chuyển quyền sở hữu worktree. Khoảng giữa — việc CÒN DỞ và CÒN MƠ HỒ — không ai giữ, nên phiên này phải viết tay file bàn giao.
Skill quy định 7 mục bắt buộc (đọc trước · việc tiếp theo có ⏱ và cái CHẶN · dọn nhỏ · nợ mở · cạm bẫy · ĐÃ THỬ VÀ BỎ · origin) + 3 nguyên tắc: số đo thay tính từ, thứ tự phải có lý do và chỉ rõ cái chặn, cạm bẫy là phần đắt nhất. Rule cấm chép transcript (>200 dòng là dấu hiệu chép thay vì chắt).
Thư mục RIÊNG llmwiki/wiki/sources/handover/ theo yêu cầu user, không trộn vào sources/draft/ — draft là đề xuất chờ duyệt, handover là việc đang chạy dở; hai vòng đời khác nhau. R5 chỉ kiểm subfolder cấp một nên hợp lệ. Đã chuyển 200726-graph-foundation-handoff.md sang.
Đăng ký đủ: canonical → LOOP_MAP orchestrate → mirror → bảng Skills CLAUDE+AGENT (parity 83/83) → provenance → global. medic 0 fail 16 ok. problem-tree +p-41 (travel-policy nói ngược installer) +p-42 (CAPABILITIES là kiểm kê không phải bản đồ) +p-43 (solved).

## 2026-07-20 — /fdk sửa travel-policy phân loại sai medic.py
Stop hook báo fresh-install ĐỎ: "engine global THIẾU: fdk/tools/medic.py". Truy ra mâu thuẫn BA NGUỒN: downstream-contract.yaml:54 khai medic.py trong must_reach_global_engines (BẮT BUỘC tới global) · travel-policy.yaml xếp nó framework_only · install-harness.sh:154-175 đọc travel-policy để XOÁ nhóm đó khỏi global. Installer xoá đúng thứ hợp đồng nghiệm thu đòi ⇒ cổng đỏ tất định. Chú thích của chính travel-policy tự khai "stop.py gọi có guard fail-open ở downstream" — tác giả biết downstream cần mà vẫn xếp nhầm tầng. Sửa: medic.py → global_shared/engine_core. Sau sửa: install giữ lại medic (29 file .py ở global), fresh-install PASS, medic --ci 0 fail 16 ok.
BÀI HỌC CÔNG CỤ (đã dính 2 lần trong ngày): output `ls` bị RTK nén làm tôi chẩn đoán nhầm hai lần — lần đầu đếm fdk/tools ra "19 vs 27, không thiếu gì" (thật ra thiếu 8), lần sau tưởng medic.py có sẵn. Phải kiểm sự tồn tại file bằng python pathlib hoặc `test -e`, KHÔNG dựa vào `ls | grep` khi đang chẩn đoán.
Kèm p-44 vào problem-tree (con của p-41 — cùng lớp "hai nguồn chân lý nói ngược nhau").

## 2026-07-20 — /propose vệ sinh nền + trần ngân sách context (T-260720-02)
Đo trước, đề xuất sau. Số nền: code-graph 16 project / 5.970 file / 546.133 cạnh; get_callers("save") ~65 kết quả ~2.000 token, hỏng 4 cách (không tách project · index cả node_modules và .next · trùng lặp thô · khớp tên chứ không khớp symbol). Kho skill: 83 mô tả = 10.686 token nạp mỗi phiên, nhưng chỉ 26/83 skill từng được gọi trên 46 phiên. BA HƯỚNG THỬ RỒI BỎ, đều bác bằng số: BM25 chấm prompt để auto-inject (điểm trôi theo độ dài — log Jenkins 3.159 điểm vs trung vị 11.61; margin nổ ở đuôi thưa nên "tiếp tục"/"ok" đạt margin vô cực); head+tail scoring (74% prompt dài đổi kết luận); min-cut/Ncut (sai hình dạng bài — bài đúng là PCST, chưa tới ngưỡng). Bằng chứng phản diện mạnh nhất từ repo code-review-graph 22k sao: eval của chính họ cho 195.653 token cho một commit sửa docstring, thất bại ở BUDGET chứ không ở thuật toán. Kết luận hội tụ: chặn nằm ở vệ sinh dữ liệu và cưỡng chế ngân sách, không ở thuật toán chọn. Chọn phương án lọc nguồn + trần cưỡng chế; PCST giữ lại kèm điều kiện kích hoạt đo được (FR-007).
BÀI HỌC PHƯƠNG PHÁP: tập "prompt thật" ban đầu lẫn 22.863 tool-result + 4.412 message subagent — kết luận đầu tiên rút ra từ dữ liệu bẩn và đã phải rút lại. Lọc bằng cờ transcript (isSidechain/toolUseResult/isMeta), không lọc bằng khớp chuỗi.

## 2026-07-20 — /failure-flywheel distill session này
Ghi 3 failure vào missing-verification (fnmatch glob vượt "/", travel-policy đọc runtime, kết luận BM25 từ transcript bẩn). Report: missing-verification 5x + spec-violation 3x, cả hai chạm threshold=3. Draft --date 260720 (DDMMYY quen dùng cho tên file wiki) ra file SAI NGÀY 290626 — flywheel.py:_ddmmyy() nuốt exception khi --date không đúng ISO YYYY-MM-DD, rơi về DEFAULT_DATE 2026-06-29 không cảnh báo. Bug này chính nó là instance thứ 6 của missing-verification, xảy ra NGAY TRONG LÚC distill loại lỗi đó — đã ghi thêm vào sổ. Xoá file sai, draft lại đúng ISO date → 200726-failure-missing-verification.md, 5 failure, STOP cho người duyệt (skill từ chối tự viết rule vào TODO — đúng thiết kế "never auto-promote").

## 2026-07-21 — /propose code-graph → KÉO NGOÀI (T-260721-01)
Sau khi T1-T4 (context-hygiene) thi hành xong, lộ ra code-graph không nằm trong travel-policy — chỉ có code_graph_keeper.py giữ registry bền, không ai cài server. User hỏi: curl không tự cài nếu quan trọng thì phải từ bỏ, viết lại, hay giữ 1 bản ổn định để kéo về? Ánh xạ đúng 3 lựa chọn vào [[adapt-modes]]: "từ bỏ+distill riêng"=HÒA TAN, "1 bản lưu đơn để kéo về"=nghe giống NHÚNG nhưng đúng là KÉO NGOÀI. Quyết định bằng dữ kiện: git log repo graph thật cho 2 tác giả (rheinmir + Trần Bùi Hoàng Gia), remote Rheinmir/graph-kit — CÙNG org sở hữu rheinmir/setup (framework này). Không phải bên thứ ba như last30days/agent-reach mà là repo khác của cùng tác giả. Loại HÒA TAN (viết lại thứ đã có+chạy tốt), loại NHÚNG (vendor sẽ trôi khỏi bản gốc ngay từ commit sau). Chọn KÉO NGOÀI theo đúng khuôn research_reach đã có tiền lệ. Draft: FR-001..006, pin theo sha (chưa có tag), bootstrap trong install-harness.sh --global, verify bằng thăm dò thật (nguyên tắc dep-health.py) chứ không chỉ kiểm tồn tại file. R7 xanh, CHƯA được duyệt — khác draft context-hygiene đã "thi hành đi thôi", draft này đụng install-harness.sh (mã dùng chung mọi máy) nên dừng đúng ở bước hỏi duyệt.

## 2026-07-21 — /fdk giải cây vấn đề
Triage 36 node open/partial, KHÔNG giải hết (Meadows: đừng bắn một phát) — chỉ đóng sổ node có bằng chứng thật hoặc làm được ngay với chi phí thấp. Kết quả: 36 → 14 còn mở.

**Đóng sổ có verify lại (không phải suy từ trí nhớ):**
- p-39 (code-graph 2 DB lệch) — chẩn đoán gốc SAI, đã tự sửa trong CLAUDE.md 5-Why; verify lại: list_projects 0/16 trùng tên, 16/16 DB lành 0 lỗi no-such-table.
- p-41 (travel-policy nói ngược install-harness.sh) — travel_policy_sync.py exit 0, khớp commit 882ec92 đã có sẵn từ trước phiên này.

**Giải mới trong phiên — debounce Stop hook (p-45):** đo lại build-wiki-graph.py 49.0s + medic.py --ci 26.1s, hai bước ăn ~75-90s MỖI LƯỢT vì cổng kích hoạt quá lỏng. Thêm debounce theo thời gian (window 180s, harness/metrics/.stop-debounce.json). Nhánh trang trí (wiki-graph) debounce vô điều kiện; nhánh GATE (medic --ci) debounce CÓ ĐIỀU KIỆN — chỉ bỏ qua nếu lần trước ĐÃ healthy, một FAIL luôn chạy lại ngay, test 5 assert xác nhận không bao giờ bị giấu. KHÔNG rewrite build-wiki-graph.py (generator dùng chung, để dành /propose riêng nếu cần incremental thật).

**Triage 15 thẻ p-auto-*** (flush card tồn 19 ngày, 02/07→21/07, chưa ai chưng lọc): đọc lại toàn bộ, không thẻ nào có nội dung vấn đề riêng biệt ngoài "bề mặt bị chạm" (toàn artifact tự sinh). Đóng sổ, gộp làm bằng chứng cho p-10 (nhịp ship/triage chậm) thay vì để trôi vô thời hạn.

**Nợ mở, không giải trong phiên này (đúng chủ đích — đừng chồng fix chưa kịp phát tác):** p-07/08/09/10 (harness governance cũ), p-12/13/15/17 (partial, cần đo thêm), p-32 (fdk-uat sentinel), p-36/37/38 (orchestration), p-42 (CAPABILITIES.md kiểm kê vs bản đồ — liên quan trực tiếp draft 200726-context-hygiene-budget nhưng chưa thi hành T5-T7 nên chưa đủ đóng).

**Phát hiện phụ, chưa sửa:** hai node cùng id "p-07" (một từ 02/07, một từ 08/07) — bug id-trùng có sẵn trong cây từ trước, ngoài phạm vi lượt này.

## 2026-07-21 — docs-site-macos capability-map
Dựng llmwiki/html/210726-capability-map.html — đối chiếu 3 nguồn thật (travel-policy.yaml, LOOP_GROUPS, fdk-problem-tree.html #tree-data) trả lời "các năng lực có cô lập không". Số đo: 61% (25/41) vấn đề có scope chạm ≥2 trụ, 12/41 chạm cả 3; stop.py orchestrate 10 tool tuần tự (điểm hội tụ vật lý); 7/83 skill rơi ngoài LOOP_GROUPS vì CLAUDE.md khai "wiki-loop" mà code không biết. Verdict: chưa đủ cô lập — ranh giới có trên giấy nhưng rò ở chỗ quan trọng nhất.

## 2026-07-21 — /propose migration code-là-source-of-truth (T-260721-02)
User đọc bài RDD (goonnguyen.substack) và yêu cầu chuyển kiến trúc: code là sự thật, quan hệ suy ra được, merge so sánh A-B tự động. Đối chiếu trung thực: bài viết là Revenue-DD, KHÔNG chứa luận điểm merge A-B — phần đó là của user và là phần mạnh nhất. Phần áp dụng được của bài (SDD chết vì 135 plan + 40 ADR = distractor interference) khớp bệnh đã đo của ta: p-41 (đọc travel-policy 3 lần tin nhầm cả 3 — distractor interference xảy ra thật trong phiên 20/07), p-10 (15 draft tồn), p-42 (CAPABILITIES từ os.listdir), 7/83 skill rơi khỏi mind map vì LOOP_GROUPS viết tay. Nền đã đi nửa đường: touches tự suy 21→283 (bc39047), log.md render từ events.jsonl, STRIP_TIER3+travel_policy_sync (bước 0), khuôn --check. SPEC: 3 lớp artifact AUTHORED/DERIVED/STATE + ledger một chỗ (FR-001), mọi DERIVED có --check nối medic (FR-002), quan hệ CHỈ suy từ nguồn — khai tử wiki-relations.py (FR-003), LOOP_GROUPS → frontmatter SKILL.md, wiki-loop thành giá trị hợp lệ (FR-004), CAPABILITIES từ graph trả p-42 (FR-005), merge protocol regen + diff A-B thử trên merge thật (FR-006), draft-age vào lint trả p-10 (FR-007), hạ vai wiki thành "nguồn chân lý của WHY" (FR-008). Điểm nghẽn chốt ở cổng: travel-policy Tầng 2 đang khai wiki là "nguồn chân lý" — mâu thuẫn trực diện, giải bằng tách WHY (wiki giữ) / WHAT-quan-hệ (code sinh). 7 task, phân công theo cost table (3 OpenCode, 3 Claude, 1 kép). CHỜ DUYỆT.

## 2026-07-21 — hoàn nguyên move-lạc harness-local (medic narrative fail)
Stop hook báo "manifest NÓI DỐI: live_probe harness-local không tồn tại". Truy: harness-local/ (gốc, tracked HEAD, hợp đồng cứng ADR-011) bị xoá khỏi working tree, xuất hiện bản lạc llmwiki/harness-local/ (mtime 17/07, byte giống hệt HEAD, 0 consumer). Grep chứng minh harness-local PHẢI ở gốc: wired vào pre-commit:65, gen-converters CI:170 ($PWD/harness-local/run.py), install-harness:319 (scaffold $ROOT/harness-local), harness-local-test.sh + downstream-firedrill-test.sh, mechanisms.yaml, scoped-hooks. harness-local-test.sh:73 còn assert PHẢI ngoài manifest + ở gốc. Kết luận: move sang llmwiki/ là NHẦM, không phải relocation chủ đích. Hoàn nguyên: git checkout -- harness-local/ + rm bản lạc. Medic 0 fail 16 ok. KHÔNG phải việc phiên này tạo ra — có thể phiên song song; ghi lại để không tưởng mất việc.

## 2026-07-21 — /propose decision-anchoring (T-260721-03)
Sau chuỗi hỏi "từ code tìm WHY thế nào / code đổi doc biết ra sao / neo theo symbol là gì / adapt đứa ngoài hạ tầng thế nào", viết SPEC. Phát hiện quan trọng lúc grounding: harness/mechanisms.yaml (ADR-001, council-025) ĐÃ LÀ tiền lệ chạy sống của đúng ý tưởng này — id+desc(WHY)+live_probe(anchor path) + medic probe "narrative" tự bắt khi live_probe biến mất. Bằng chứng sống ngay trong phiên: probe đó vừa bắt được harness-local/ bị git-mv, chặn medic tới khi hoàn nguyên. Giới hạn của tiền lệ: neo mức FILE, không phải SYMBOL — sửa nội bộ hàm không kích hoạt xác nhận lại; chỉ phủ 1 loại quyết định (mechanism), không phủ ADR/feedback khác. SPEC = tổng quát hoá pattern đã chứng minh, không phát minh mới: thêm anchor_symbol+confirmed cạnh live_probe cũ, dùng code-graph (vừa vệ sinh xong phiên trước) resolve, 3 trạng thái LIVE/STALE/ORPHAN, lệnh why <symbol>, /lint báo cáo không chặn. Kiểm chéo vercel-labs/zerolang (agent-first, graph NẰM TRONG compiler) — đọc thẳng README: graph chứa symbols/types/effects/ownership/calls, 0 trường rationale. Ngay lab đi xa nhất cũng không giải WHY — củng cố đây là lỗ thật của cả ngành, không phải fantasy riêng. FR-007 chốt ranh giới trung thực: liveness chỉ cấu trúc (tồn tại/đổi tên/xoá), KHÔNG semantic — phán đoán ý nghĩa ở lại người. T8 (promote concepts/decision-anchoring.md) đặt CUỐI cùng, sau khi T1-T7 xanh — đúng luật "wiki entries chỉ tạo sau khi code commit". CHỜ DUYỆT.

## 2026-07-21 — vá 2 lỗ hổng decision-anchoring (feedback trực tiếp)
User hỏi liên tiếp 2 câu, cả hai đều bắt trúng chỗ SPEC thiếu:

1. "case delete và edit thì sao đủ CRUD chứ" — lộ ra tôi chỉ nghĩ CRUD trên 1 trục (code), bỏ sót trục thứ 2 (chính mục quyết định/neo). Xoá VẬT LÝ một mục mechanisms.yaml có anchor_symbol thì liveness KHÔNG CÒN GÌ ĐỂ KIỂM — không ORPHAN, không STALE, WHY biến mất không dấu vết. Đúng chính bệnh "docs rot" mà cả cơ chế sinh ra để chống, xảy ra ngay trong chính cơ chế. Vá: FR-009 (CRUD phía decision — update tự do, delete CẤM vật lý, bắt buộc status: retired theo đúng kỷ luật append-only đã chạy sống ở fdk-problem-tree.html) + SC-006 + task mới T8 (validator so git-diff bắt xoá-lén). Số task 8→9, promote-concept đổi từ T8→T9.

2. "phụ thuộc vào cái gì hay input, dependency là gì" — lộ ra dependency chain của liveness chưa viết ra, và có đúng 1 case UNAVAILABLE (code-graph MCP không tới được) mà FR-002 (3 trạng thái) không xử lý — sẽ rơi nhầm xuống ORPHAN, gây bão báo-động-giả. KHÔNG PHẢI rủi ro lý thuyết: code-graph MCP của chính phiên này đang disconnect thật (kill để restart nạp code T1-T4 hygiene trước đó, không tự respawn) — dùng ngay sự kiện đang xảy ra làm bằng chứng. Vá: FR-002 mở rộng 4 trạng thái (thêm UNAVAILABLE) + SC-007 + Global constraints ghi rõ dependency chain (git → code-graph THĂM DÒ được, nguyên tắc dep-health.py → project reindex → mới tin kết quả) + T1 Plan/verify mở rộng.

Cả 2 vá xong, R7 xanh (exit 0), 9/9 diagram-box khớp 9 task. Bài học chung: câu hỏi "còn thiếu gì" hiệu quả hơn nhiều so với tự rà — cả hai lỗ hổng đều tồn tại từ bản đầu tiên và R7/self-review không bắt được vì chúng không phải placeholder hay thiếu nhất-quán-tên, mà là thiếu HẲN một góc nhìn.

## 2026-07-21 — persona-lens grower/tester soi decision-anchoring
User gọi 2 lens (llmwiki/personas/grower.md + tester.md), khai beneficiary = chính framework (ngoại lệ /fdk theo ADR-004). 

Tester: bắt 3 lỗ — (1) race trên T8 (so nguyên file thay vì theo id, đúng câu hỏi đã ghi nợ U-03 — nay nâng thành FR-010 bắt buộc, đóng U-03), (2) chưa test hồi phục UNAVAILABLE→LIVE khi code-graph sống lại, (3) T9 promote-concept không có gate xác minh trích dẫn khớp output thật (LLM trust boundary, 1/13 nhóm lỗi qc-code). Cả 3 vá NGAY vào SPEC (FR-010, SC-008), mở rộng trong task có sẵn T1/T8/T9 — không phình thêm task, giữ 9/9 diagram-box khớp R7.

Grower: bắt 1 lỗ — 8 SC toàn correctness, không SC nào đo adoption, không kill-switch nếu không ai dùng anchor_symbol/why — trong khi chính SPEC tự trích bài học touches (chết vì không ai tiêu thụ) mà không tự áp cho mình. KHÔNG vá ngay — đúng ranh giới persona (grower đòi "đã dựng xong" mà T1-T9 còn pending) — raise-issue đúng quy trình ghi trong chính grower.md ("chạm ranh giới → /raise-issue assignee: <persona>"): GH#83, ledger 210721-decision-anchoring-adoption-metric.md, ISSUES.md đã đăng ký.

Bài học phương pháp: cả 3 phiên liên tiếp (CRUD, dependency, persona-lens) đều tìm ra lỗ hổng THẬT bằng cách đổi góc nhìn thay vì tự rà lại cùng một góc — không cái nào là placeholder hay lỗi chính tả mà R7/self-review bắt được.

## 2026-07-21 — plan — decision-anchoring-PLAN

`/plan` mở rộng SPEC `210721-decision-anchoring.md` (đã duyệt ngầm: user "rồi làm đi" + "trong chiều này xong cả 3 v0.1-0.3") thành `210721-decision-anchoring-PLAN.md` — 9 task (T1-T9, phát hiện lại T9 nằm TRONG v0.3, không tách rời như tóm tắt phiên trước ghi nhầm). Quyết định kiến trúc quan trọng: engine liveness đọc TRỰC TIẾP `.graph-agent/index.db` (sqlite) thay vì gọi MCP `search_symbols`/`get_symbol_context` — vì script CLI chạy ngoài context Claude không gọi được MCP tool (chỉ Claude-agent gọi được); đây là biến thể thi hành của "thăm dò code-graph" (Global constraints), verify bằng checksum sha256[:16] khớp cột `checksum` của bảng `files` (proxy cho "project đã reindex"). Khảo sát thật trước khi viết PLAN: DB hiện có 108 file/984 symbol nhưng KHÔNG index `llmwiki/.claude/hooks/stop.py` (chỉ 4/10 file trong `hooks/`) — bằng chứng sống cho nhánh UNAVAILABLE, không phải giả định. R7 (`proposal_complete.py`) chặn 2 lần trước khi xanh: thiếu `### Task N` (dùng nhầm `##`), và tự nhắc "TBD"/"TODO"/"điền sau" trong Self-review khi nói KHÔNG còn — cùng bẫy đã gặp ở SPEC gốc.

## 2026-07-21 — decision-anchoring — T1-T9 thi hành xong (v0.1+v0.2+v0.3)

Thi hành đầy đủ PLAN `210721-decision-anchoring-PLAN.md`, không dừng ở SPEC: `harness/scripts/decision-liveness.py` (T1: schema `anchor_symbol`/`confirmed` + engine 4 trạng thái, đọc trực tiếp `.graph-agent/index.db` thay vì MCP vì script CLI không gọi được MCP tool), 2 mục pilot trong `mechanisms.yaml` (T2 `stop-debounce` neo `_debounced`/stop.py, T6 `code-graph-probe-boundary` neo `probe_code_graph`/dep-health.py — 25 mục tổng, 2 anchored), lệnh `why <symbol>` (T3), self-test bao đủ 3 nhánh code-side sửa-thân/đổi-tên/xoá trên sandbox git (T4, SC-003) + mô phỏng drift kiểu harness-local (T5, SC-002), `/lint` bước 8e báo ORPHAN/STALE (T7), `harness/scripts/decision-guard.py` khoá xoá-vật-lý theo từng id (T8, SC-006 + race FR-010 đóng U-03), và `llmwiki/wiki/concepts/decision-anchoring.md` promote kèm `decision-anchoring-crosscheck.py` đối chiếu 4 FACT với output thật (T9, FR-010 trust boundary — script tự FAIL nếu concept trích sai số, không dựa lời tự khai).

Bằng chứng thật quan trọng nhất: pilot `_debounced` resolve ra UNAVAILABLE (không phải LIVE) vì `.graph-agent/index.db` thật KHÔNG index `stop.py` — xác nhận nhánh UNAVAILABLE hoạt động đúng trên dữ liệu thật, không phải giả lập; `why` vẫn trả đủ nội dung WHY (SC-001 không đòi trạng thái phải LIVE, chỉ đòi đọc được lý do). Regen `overstack.html` từ manifest để giữ probe `narrative` của `medic` xanh (25 cơ chế khớp). R7 (`proposal_complete.py`) chặn PLAN 2 lần trước khi xanh — thiếu `### Task N` (dùng nhầm `##`) và tự nhắc "TBD"/"TODO"/"điền sau" trong Self-review khi nói KHÔNG còn (bẫy lặp lại từ SPEC gốc). Một bug thật phát hiện qua self-test: `confirmed: YYYY-MM-DD` chỉ có độ phân giải NGÀY — nếu commit xác nhận và commit sửa cùng ngày, `git log --until=<ngày>` trả về HEAD thay vì baseline; self-test phải backdate commit init để mô phỏng đúng use-case thật (không phải bug của thuật toán diff, mà là hạn chế granularity đã biết trước ở FR-004).

## 2026-07-21 — fdk — bỏ disable-model-invocation của fdk-uat

User yêu cầu tường minh (xác nhận 2 lần: "tôi cho phép" rồi gọi `/fdk sửa đi cho tôi`) gỡ cờ `disable-model-invocation: true` khỏi `skills/fdk-uat/SKILL.md`, để agent tự gọi được `/fdk-uat` qua Skill tool thay vì bắt buộc user tự gõ. Lý do đồng ý sửa: đây là skill trong chính repo/framework của user (không phải guard nền tảng bên ngoài), user có toàn quyền trên chính cấu hình của mình, và đã xác nhận rõ ràng qua đúng kênh dành cho thay đổi framework (`/fdk`). Đồng bộ qua `fdk/tools/sync-skill.sh fdk-uat` (canonical → mirror llmwiki → bản cài `~/.claude`), cả 3 bản đã gỡ cờ.

## 2026-07-21 — decision-anchoring — fdk-uat bắt lỗi thật T7, đã vá

`/fdk-uat` (main-URL smoke, curl thật từ nhánh `orca`) phát hiện T7 sai vị trí sửa: bước 8e đã chèn vào `llmwiki/skills/wiki-loop/lint.md` (mirror) thay vì `skills/lint/SKILL.md` (canonical, nguồn thật cho gói npx phân phối) — nên bước 8e chưa từng tới tay người dùng thật qua đường cài remote, dù mọi test nội bộ trong repo đều xanh (vì test chạy trên bản mirror, không phải bản thật được ship). Đây đúng lớp lỗi eval 020726 mà `fdk/tools/sync-skill.sh` sinh ra để chặn ("ĐỪNG cp tay từng bản — nguồn drift"). Vá bằng cách chèn 8e vào `skills/lint/SKILL.md` rồi chạy `sync-skill.sh lint` để đồng bộ đúng chiều canonical→mirror→installed (parity xác nhận bằng `diff`, cả 3 bản khớp).

Kết quả UAT còn lại: 3 trụ có mặt sau curl bootstrap thật (không override biến); `harness/scripts/decision-liveness.py`/`decision-guard.py` tới tay qua tầng `global_shared` (`~/.claude/harness/harness/scripts/`), self-test ALL PASS chạy từ bản vừa cài, không phải bản dev; `why _debounced` trên dự án UAT trống trả đúng WHY + UNAVAILABLE trung thực (dự án mới chưa có `.graph-agent/index.db`); `test-broad.sh` 74/74 PASS.

## 2026-07-21 — decision-anchoring — UAT dựng workspace Orca thật (thấy được bằng mắt)

Lần UAT trước chỉ chạy filesystem-level (`/tmp`, xoá sau khi verify) — user chỉ ra không thấy gì trong app Orca. Dựng lại: curl bootstrap thật vào `~/orca/workspaces/uat-decision-anchoring-260721-1707`, `orca repo add` + `orca worktree create --name uat-verify --activate` — hiện đủ 2 worktree (`main` + `uat-verify`) trong `orca worktree list`, giữ lại (không xoá) để mở được trong app. Verify lại decision-anchoring trong chính worktree đó: `why _debounced` đúng WHY + UNAVAILABLE trung thực, self-test ALL PASS, skill `lint` global đã có bước 8e.

`/fdk-poc` bị hoãn: tool `fdk/tools/fdk-poc.py` chỉ tồn tại trên nhánh `Rheinmir/issue-15-br-k` (chưa merge `orca`, lệch ~127-281 commit mỗi chiều) — không có trên `orca` nên không chạy thật được, đúng luật "không bịa bước" của chính skill đó. User chọn bỏ qua.

## 2026-07-21 — decision-anchoring — 2 agent thật test độc lập trong workspace Orca

Spawn 2 phiên Claude Code THẬT (không phải tôi tự gõ lệnh) trong worktree `uat-verify`, mỗi phiên nhận một nhiệm vụ mơ hồ có chủ ý (không mách lệnh) để xem agent có tự khám phá cơ chế decision-anchoring không.

**Agent 1 (tra WHY):** tự grep `~/.claude`, tìm đúng bộ 3 script, tự chạy `decision-liveness.py why _debounced`, trả đúng WHY. Thành công không cần gợi ý thêm.

**Agent 2 (test ORPHAN):** tự bắt lỗi trong chính đề bài (tôi ra đề đổi tên `_debounce_mark`, nhưng symbol neo thật là `_debounced`) và tự sửa lại test cho đúng. Kết quả baseline thật trên `~/.claude/harness`: `path_state=ORPHAN` (không có `llmwiki/.claude/hooks/stop.py`, harness home chỉ mirror `llmwiki/personas/`), `symbol_state=UNAVAILABLE` (`.graph-agent/index.db` không tồn tại). Agent giải thích đúng: đây không phải bug logic (self-test sandbox đã pass) mà vì 2 tầng hạ tầng cần (file thật + index tươi) đang gãy sẵn trong bản cài — đúng thiết kế FR-002 "không bao giờ báo ORPHAN/STALE giả khi hạ tầng đứt".

**Phát hiện phụ, NGOÀI phạm vi (chưa xử lý):** MCP code-graph có một project "setup" khác trỏ `~/harness/setup` báo sai `_debounced` tồn tại dòng 49-60 trong khi file thật ở đó chỉ 46 dòng — index cũ lệch từ trước, không liên quan decision-liveness.py (script không lọc theo field "project", chỉ đọc DB riêng theo ROOT của chính nó). Agent 2 đúng đắn không đụng vào — cần `/raise-issue` riêng nếu muốn xử lý sau.

Không file nào bị agent ghi/sửa trong cả 2 phiên — sạch.

## 2026-07-21 — decision-anchoring — happy path LIVE xác nhận qua code-graph MCP thật

Agent 2 (tiếp tục phiên trước) dùng code-graph MCP THẬT: `reindex_repo("/Users/giatran/orca/setup/setup")` → 107 file scan, 1 reindex (stop.py dirty), 0 lỗi; `search_symbols`/`get_symbol_context` xác nhận `_debounce_mark` (38-46), `_debounce_state` (30-35), `_debounced` (49-60, callers: regen_docs, framework_medic_mirror) khớp 100% file thật. Chạy `decision-liveness.py check/why` từ đúng bản trong repo dev (không phải mirror `~/.claude/harness` — DB_PATH tự resolve theo `Path(__file__).parents[2]`, không cần sửa biến môi trường):

```
[stop-debounce]              → LIVE (resolve stop.py:49-60, không đổi kể từ 2026-07-21)
[code-graph-probe-boundary]  → LIVE (resolve dep-health.py:151-195, không đổi kể từ 2026-07-21)
```

Đây là lần đầu tiên cơ chế thật ra khỏi UNAVAILABLE — đóng nốt case còn thiếu trong toàn bộ chuỗi verify (trước đó chỉ có UNAVAILABLE thật + STALE/ORPHAN/LIVE trên sandbox). Xác nhận: mọi lần UNAVAILABLE trước đó là ĐÚNG hành vi (hạ tầng thật sự gãy — thiếu file hoặc index cũ), không phải lỗi logic của `resolve_symbol`/`compute_state`. Agent không sửa file mã nguồn nào, chỉ ghi `.graph-agent/index.db` (index cache, không phải nguồn code).

## 2026-07-21 — decision-anchoring — 5-Why "trỏ nhầm root" + vá thông điệp UNAVAILABLE

User yêu cầu 5-Why cho hiện tượng "trỏ nhầm root" mà 2 agent test gặp phải (UNAVAILABLE ở mirror `~/.claude/harness`, ORPHAN-giả ở index cũ `~/harness/setup`, chỉ LIVE khi chạy đúng repo dev thật). Chuỗi:

1. Script tự suy `ROOT = Path(__file__).parents[2]` — có 3+ bản cùng tên script nằm ở 3 root khác nhau, không lệnh nào tự báo đang ở world nào.
2. Nhiều bản phân tán là CỐ Ý — travel-policy tầng `global_shared` chủ động nhân bản script dùng-chung ra global harness home.
3. Nhân bản (cố ý) gây trỏ nhầm vì bản nhân ra KHÔNG đồng bộ toàn vẹn — có `mechanisms.yaml`/`decision-liveness.py` nhưng thiếu `llmwiki/.claude/hooks/stop.py` (chính file nó trỏ tới) và thiếu `.graph-agent/index.db`.
4. Không có kiểm tra toàn vẹn này vì travel-policy phân loại THEO TỪNG FILE độc lập, không mô hình hoá quan hệ tham chiếu CHÉO TẦNG (một mục ở `harness/` trỏ symbol ở `llmwiki/`).
5. Góc mù này chưa lộ trước đó vì mọi `live_probe` cũ đều trỏ file NẰM TRONG CHÍNH `harness/`/`fdk/` (cùng tầng) — decision-anchoring là cơ chế ĐẦU TIÊN neo chéo tầng.

**Root cause:** `global_shared` "hứa" là *"dùng chung mọi phiên"* nhưng chỉ đồng bộ đúng cái được khai `global_shared`, không đồng bộ theo-nhu-cầu những gì nó tham chiếu chéo sang tầng khác.

**Fix đòn-bẩy-thấp đã áp** (không sửa cả travel-policy — để dành nếu tái diễn nhiều hơn): `resolve_symbol()` trong `decision-liveness.py` giờ tự phân biệt UNAVAILABLE "chưa reindex" (tạm) khỏi "file/DB không tồn tại ở ROOT này — có thể đang chạy nhầm bản global_shared, thử repo dev thật hoặc reindex_repo qua code-graph MCP" (cấu trúc). Verify thật trên đúng 2 root gây nhầm trước đó: mirror `~/.claude/harness` giờ in gợi ý rõ ràng, repo dev thật vẫn LIVE đúng như trước. Self-test vẫn ALL PASS.

## 2026-07-21 — decision-anchoring — 5-Why xuôi cho "vì sao agent phải tự reindex" + giảm ma sát

User hỏi tiếp: nếu wiring agent-tự-reindex thì giải được bài toán gì (5-Why xuôi, chứng minh giá trị). Chuỗi: (1) xoá vòng lặp "hỏi→UNAVAILABLE→mò→reindex→hỏi lại" trong 1 lượt; (2) đo được thật hôm nay — agent 2 tốn thêm 1 lượt mới ra LIVE; (3) đúng lời hứa gốc "từ code tìm WHY, không cần nhớ tay"; (4) UNAVAILABLE-lượt-đầu dễ hiểu nhầm "cơ chế hỏng" — đúng nguyên nhân giết `touches` ("không ai tiêu thụ thì không ai nuôi"); (5) chi phí đo được NGAY (khác GH#83 phải chờ dữ liệu dài hạn) nên đáng sửa ngay, đòn bẩy rẻ (đổi luồng thông tin, không đổi kiến trúc MCP).

Vá: thêm đoạn hướng dẫn tường minh vào docstring đầu `decision-liveness.py` ("AGENT ĐANG ĐỌC FILE NÀY... trước tiên hãy tự gọi reindex_repo qua code-graph MCP") + thêm mục "Trỏ nhầm root, và vì sao reindex vẫn phải do agent chủ động" vào concept — giải thích rõ 2 ràng buộc cứng khiến máy không tự reindex được (MCP chỉ agent gọi; cố ý không để máy tự sửa lặng lẽ, theo tiền sử code-graph server hỏng-mà-không-ai-biết của `dep-health.py`). Verify: self-test ALL PASS, crosscheck 4 FACT khớp, `medic --ci` 0 fail.

## 2026-07-21 — decision-anchoring — UAT thật kiểm CRUD phía code + đa luồng, vá 2 lỗ

User hỏi trực tiếp: "CRUD phía code có thực sự handle hết chưa, có xử lý đa luồng không". Trả lời bằng test thật, không đoán:

**CRUD phía code:** đủ 4 sự kiện vòng đời (read=`why`, update-body→STALE, update-rename→ORPHAN, delete-file/symbol→ORPHAN) đều đã verify thật. Phát hiện thật khi đọc lại code: DB thật CÓ 10 cặp (file, tên symbol) trùng nhau — nguyên nhân là code-graph indexer APPEND dòng mới mỗi lần reindex thay vì thay thế (tự gây ra bởi 3 lần reindex liên tiếp `decision-liveness.py` trong phiên hôm nay). Query `symbols` cũ không có `ORDER BY` — `.fetchone()` lấy dòng nào cũng được, không xác định.

**Đa luồng:** thử tái hiện crash bằng writer giữ WAL lock + reader đọc cùng lúc — **KHÔNG crash** (tự phản chứng giả thuyết ban đầu, WAL mode cho phép đọc-ghi đồng thời an toàn). Thử ép DB corrupt sau khi qua `db_status()` check — bị bắt sớm ở chính `db_status()`, không lọt xuống dưới. Nhưng phát hiện thật khác: khối `conn.execute()` thứ 2 (query bảng `symbols`) KHÔNG có `except` bọc quanh, chỉ có `finally: conn.close()` — lỗi sqlite thoáng qua (thiếu cột do reindex nửa chừng, disk I/O) sẽ **crash cả script** thay vì trả UNAVAILABLE. Tái hiện thật bằng DB có đủ tên bảng (qua được schema check) nhưng thiếu cột `line_start`/`line_end` → xác nhận crash trước khi vá.

**Vá cả 2:** (1) `ORDER BY id DESC LIMIT 1` khi query symbols — ưu tiên dòng mới nhất, không đọc phải dòng ma từ lần index cũ; (2) bọc `except sqlite3.Error` quanh cả 2 khối query trong `resolve_symbol()`, đúng ethos fail-open đã dùng ở `dep-health.py`. Verify lại: self-test ALL PASS, ca thiếu-cột giờ trả UNAVAILABLE gracefully thay vì crash, crosscheck 4 FACT khớp, `medic --ci` 0 fail.

## 2026-07-22 — propose — artifact-provenance-eventlog

`/propose` cho event log theo pattern Kafka git-native (`T-260722-01`), nối tiếp trực tiếp mạch decision-anchoring hôm qua. Tự đánh giá ban đầu ("Kafka thừa, git+events.jsonl đủ") sai ở 2 điểm user chỉ ra và tôi tự kiểm chứng lại: `events.jsonl` bị gitignore (không merge qua nhánh/máy), chỉ actor {agent,system} qua hook Claude Code (không multi-vendor). CAP/AP framing của user (mỗi lãnh địa local độc lập, hợp nhất chỉ ở merge) trở thành luận điểm chính của Approach A: file JSONL git-tracked, hash-chain THEO TỪNG writer (không phải 1 chuỗi toàn cục), merge bằng driver `merge=union` có sẵn trong git (không tự viết consensus). Thêm FR-007 (adapter 3 hàm duy nhất) theo yêu cầu bổ sung giữa lượt: chừa slot migrate sang broker thật sau này mà không sửa mọi call site. R7 chặn 1 lần (thiếu `class="desc"` — dùng nhầm `class="prose"`), đã sửa. SPEC+HTML (`docs-site-macos`, draggable diagram + mind map + theme toggle) đã xanh, dừng chờ duyệt.

## 2026-07-22 — propose — artifact-provenance-eventlog: vòng phản biện /fable5, chốt FR-005

User bật `/fable5` thách 2 luận điểm về SPEC `220722-artifact-provenance-eventlog.md`: ẩn dụ cờ vua ("tăng trưởng vô hạn nhưng thực tế bounded") và câu hỏi "outlines có giúp được không" (kèm ảnh một hội thoại khác về constrained-decoding). Kết quả chạy đủ Floor+5 Move: ẩn dụ cờ vua SAI CƠ CHẾ khi soi kỹ (cờ vua pruning bằng cách vĩnh viễn không thăm phần cây luỹ thừa; log của mình append-only, tăng TUYẾN TÍNH — không cùng loại tăng trưởng) nhưng kết luận thực dụng của user vẫn đúng bằng lý do khác đơn giản hơn (log tuyến tính cùng bậc tăng trưởng với chính git history, chỉ thêm hằng số nhân — không cần ẩn dụ). Điểm "log hỗn loạn thứ tự vẫn dùng làm clue truy origin được" của user ĐÚNG và hạ mức nghiêm trọng của rủi ro merge=union-timeline-skew đã nêu trước đó xuống thấp hơn (chỉ hại use-case cần replay đúng thứ tự, không hại use-case lookup mà `/lint` bước 0b đã chạy sống). "outlines" không áp trực tiếp cho Claude API (không lộ logits) nhưng đúng ý tưởng của nó áp được qua tool-use/structured-output built-in của Claude cho nhánh "cần agent phán đoán" của `correlate()`.

Vá vào SPEC: FR-005 thêm yêu cầu cứng — nhánh fallback PHẢI trả lời qua tool-use schema `{is_related, confidence, reasoning}`, không phải free-text. Đồng bộ vào Task T4 (Plan), `## Origin` (ghi lại toàn bộ vòng phản biện), và HTML companion (thêm đoạn desc T4). R7 vẫn xanh sau mọi sửa.

## 2026-07-22 — concept mới — log-model + đơn giản hoá SPEC provenance-log

User chỉ đúng chỗ over-engineering: SPEC `220722-artifact-provenance-eventlog.md` đang cố cho `correlate()` (FR-005) tự suy quan hệ NỘI DUNG "wiki nói về code nào" — trong khi `touches_targets` (`wiki-graph.py:88`, content-based, tất định, chạy sống 21→283 cạnh) đã giải xong câu hỏi đó, mạnh hơn nhiều. Bài học rộng hơn: repo có 5 cơ chế "ghi lại chuyện đã xảy ra" (`events.jsonl`/`scratch-log.jsonl`/`memory.jsonl`/`touches`/`provenance-log` đề xuất) — cố ép chúng phối hợp/hợp nhất làm hệ MỎNG MANH hơn, không bền hơn; mỗi cái giữ đúng phạm vi hẹp thì độc lập, dễ tin.

Tạo `llmwiki/wiki/concepts/log-model.md` — bản đồ 1 file cho agent bất kỳ đọc một lần là định vị (bảng tra nhanh theo câu hỏi, sơ đồ ASCII độc lập, không mũi tên nối ngang). Thêm note 2 dòng vào docstring 4 file liên quan (`code-logger.py`, `scratch-log.py`, `mem-rank.py`, `wiki-graph.py::touches_targets`) trỏ về trang này. Sửa SPEC: FR-005 thu hẹp phạm vi `correlate()` chỉ còn "cùng phiên/mạch công việc theo thời gian" (không suy nội dung), thêm dòng Non-goals nói rõ ranh giới với `touches`. R7 vẫn xanh, `py_compile` sạch cả 4 file đã note.

## 2026-07-23 — skill-maintenance — gộp trùng lặp web-clone vs extract-site

Phát hiện `skills/extract-site/SKILL.md` Mode 3 và `skills/web-clone/SKILL.md` Mode B mô tả
CÙNG một pipeline reconstruct (distill từ `ai-website-cloner-template`) ở 2 nơi độc lập — rủi ro
drift khi sửa 1 bên quên bên kia. Gộp: `web-clone` là nhà canonical duy nhất cho pipeline này,
`extract-site` Mode 3 rút còn 1 đoạn trỏ sang. Sync mirror + bản cài máy qua `sync-skill.sh`,
cập nhật bảng skill `AGENT.md`/`CLAUDE.md` (2 dòng), regen `fdk/CAPABILITIES.md`. Giữ nguyên phần
không trùng: extract-site vẫn là nhà cho design-token extraction (DESIGN.md/tokens.json/css),
web-clone vẫn là nhà cho Mode A (snapshot offline byte-exact).

## 2026-07-23 — propose — provenance-log: chốt lý do KHÔNG gộp vào scratch-log.jsonl

User hỏi tiếp "5 log này có bỏ được cái nào không, hay mỗi cái giải bài toán riêng" — trả lời bằng bảng ánh xạ 5 log → 5 bài toán cụ thể (đều có ví dụ thật đã xảy ra trong phiên), rồi tự Attack chính đề xuất `provenance-log` mới: có thể gộp vào `scratch-log.jsonl` (đã git-tracked sẵn) thay vì đẻ file mới không? Kết luận: KHÔNG gộp, nhưng lý do đúng không phải "khác chủ đề" (yếu) mà là hai HỢP ĐỒNG TIN CẬY khác nhau — `scratch-log` optional/curated ("why OPTIONAL — không ép agent", tự khai trong chính docstring), `provenance-log` cần mandatory/automatic (FR-006 hứa lịch sử ĐẦY ĐỦ, thiếu 1 dòng phải là bug chứ không phải lựa chọn). Gộp chung sẽ tái tạo đúng loại nhầm lẫn đã tốn công sửa trong phiên (UNAVAILABLE 2 nguyên nhân bị lẫn ở decision-liveness.py, mirror-drift ở /lint 8e). Đã sửa vào Non-goals của SPEC, R7 vẫn xanh.

## 2026-07-23 — plan — artifact-provenance-eventlog-PLAN

`/plan` mở rộng SPEC `220722-artifact-provenance-eventlog.md` (duyệt qua "chạy /plan đi") thành PLAN thi hành T1-T5. T6 (rotate, v0.3/COULD) loại khỏi PLAN có chủ ý — ngưỡng rotate chưa trả nợ (U-05), viết task cho nó sẽ là placeholder giả trang, đúng điều khoản "cổng ngược" của /plan. Trước khi viết PLAN, verify thật claim kỹ thuật cốt lõi của SPEC (FR-004, merge=union) trên sandbox git — 3 dòng từ 2 branch độc lập đều còn sau merge, KHÔNG cần config thêm gì ngoài dòng `.gitattributes` — xác nhận Approach A khả thi, không cần quay lại /propose. R7 chặn 1 lần (Self-review tự nhắc TBD/TODO literal khi nói KHÔNG còn — bẫy đã gặp nhiều lần trong phiên), đã sửa.

## 2026-07-24 — decision-anchoring/provenance-log — T1-T5 thi hành xong, đánh dấu implemented

Thi hành đầy đủ PLAN `220722-artifact-provenance-eventlog-PLAN.md` (T1-T5, T6 hoãn chờ trả nợ U-05): `harness/scripts/provenance-log.py` (adapter `append_event`/`read_events`/`correlate`/`classify_topic`, hash-chain theo writer_id, `.gitattributes merge=union` verify thật trên sandbox 2 branch — 2 sự kiện đều còn sau merge, không mất dòng); `decision-liveness.py confirm <id>` (T3, bump `confirmed:` + phát event `decision.confirm`, verify thật trên `stop-debounce`); `correlate()` phạm vi hẹp temporal-only (T4, FR-005 đã thu hẹp sau phản biện trước đó); wiring `stop.py::regen_docs()` gọi `record-changed` phân loại theo path-prefix (T5, verify thật — file `.py` → `code.change`).

Một bug thật bắt được qua self-test: `classify_topic()` ban đầu kỳ vọng `SKILL.md`/`README.md` → `code.change`, nhưng `_CODE_RE` (mượn từ `stop.py`) cố ý KHÔNG chứa `.md` — sửa bằng cách thêm nhánh `p.endswith(".md")` riêng cho `.md` ngoài `llmwiki/wiki/`. Đồng bộ mirror global (`~/.claude/harness`), bump `capability-stamp` (178 mục), `medic --ci` 0 fail. SPEC + PLAN đổi `status: implemented`, đánh dấu T1-T5 done trong Plan.

## 2026-07-24 — provenance-log — /fable5 bắt lỗi thật: sai tên biến môi trường session

User gọi `/fable5` hỏi "tiếp tục chưa" — verify lại thật (Move 2 GROUND) thay vì trả lời từ trí nhớ, phát hiện T5's wiring ĐÃ tự bắn thật qua Stop hook giữa các lượt (38 event mới, gồm cả file không phải tôi sửa — bằng chứng hook tự động hoạt động đúng thiết kế). Nhưng Attack (Move 4) lộ lỗ thật: mọi event đều mang `writer_id` chứa `unknown-session` — `_writer_id()` đọc sai tên biến môi trường (`CLAUDE_SESSION_ID`, không tồn tại) thay vì biến thật `CLAUDE_CODE_SESSION_ID` (xác nhận qua `env` thật trong hook context, có UUID thật của phiên). Self-test không bắt được vì luôn override `writer_id` tay, chưa từng test qua nhánh đọc biến môi trường mặc định.

Vá `_writer_id()` đọc đúng `CLAUDE_CODE_SESSION_ID` (fallback `CLAUDE_SESSION_ID`/`SESSION_ID` cho vendor khác), thêm self-test case phủ đúng nhánh mặc định (không override tay) — bài học ghi thẳng vào comment code để không lặp lại. Verify thật: `_writer_id()` giờ trả đúng UUID phiên thật (`765fc26c-...`, khớp chính phiên này). `medic --ci` 0 fail.

## 2026-07-24 — provenance-log — nối /lint (8f) + promote concept, đóng vòng consumer

`/fable5` hỏi "check tình trạng, what next" — verify lại thật (grep `read_events`/`correlate` toàn repo) lộ ra: T1-T5 build xong nhưng KHÔNG có consumer thật nào ngoài self-test — hạ tầng ghi chạy sống (98 event thật đã tích luỹ) nhưng chưa ai đọc. User chọn cả 2 hướng: nối `/lint` + promote concept.

Thêm bước 8f vào `skills/lint/SKILL.md` (canonical — nhớ đúng bài học mirror-drift đã bắt qua UAT trước đó, sửa canonical trước rồi `sync-skill.sh lint`, verify parity 3 bản khớp nhau bằng `diff`). Bước 8f tra `provenance-log.jsonl` như nguồn "vì sao đổi" THỨ HAI cạnh `events.jsonl`/`scratch-log.jsonl` ở bước 0b, khác biệt: git-tracked, đi theo được qua máy khác. Verify grep thật hoạt động trên dữ liệu thật.

Tạo `llmwiki/wiki/concepts/provenance-log.md` — concept đầy đủ (CAP/AP, ranh giới với `touches`/`correlate()`, bài học `/fable5` writer_id, bằng chứng thật 98 event/53 code.change/44 docs.change/1 decision.confirm đo lúc viết). `medic --ci` 0 fail sau khi regen `build-overstack-docs.py` (docs drift từ skill-listing đổi, không liên quan trực tiếp).

## 2026-07-24 — fdk-uat/fdk-poc — gate cứng bắt buộc tạo workspace Orca thật

User nhắc lần thứ 2 (2026-07-21 → 2026-07-24, cùng lỗi tái diễn ở cả /fdk-uat lẫn /fdk-poc): agent tự ý chạy filesystem-only (curl vào thư mục tạm, test CLI thuần) rồi báo hoàn tất, bỏ qua việc dựng workspace Orca thật — "không visual = không dùng được". Root cause: bước dựng workspace trong `skills/fdk-uat/SKILL.md` được đánh dấu "(tuỳ chọn)" — nhớ tay đã fail 2 lần liền, đúng dấu hiệu cần đổi cấu trúc thay vì nhắc thêm.

Vá `skills/fdk-uat/SKILL.md` (canonical, sync mirror+installed, parity xác nhận `diff`): bỏ chữ "tuỳ chọn", thêm block assert chạy `orca worktree list` verify đúng tên worktree vừa tạo có mặt — fail thì DỪNG, không được báo PASS. Vá tương tự bản CÀI của `fdk-poc` (`~/.claude/skills/fdk-poc/SKILL.md`) — nhưng canonical thật của skill này nằm trên nhánh `Rheinmir/issue-15-br-k`, không sửa được sạch từ `orca`; ghi rõ giới hạn này để không tưởng nhầm đã vá triệt để (bản cài sẽ mất vá nếu `npx skills add` cài lại từ nguồn gốc).

## 2026-07-28 — orca-onboard — onboard-setup

Onboard chính repo overstack (853 file tracked, commit 9032ae4). Pipeline distill: static parse 0-token cho graph, Claude main thread cho layers/tour/domain, opencode+DeepSeek cho wiki/HTML render.

## 2026-07-29 — docs-site-macos — overstack-source-map

Sinh `llmwiki/html/290726-overstack-source-map.html` (138,7 KB, 7 section, self-contained) bằng generator python đọc thẳng knowledge-graph.json + domain-graph.json + policy.yaml. Kiểm chứng bằng cách mở thật trong Chrome: console sạch, 0 request ngoài, mind map/sơ đồ kéo-thả/master-detail/toggle theme đều chạy.

Phát hiện và sửa một bug rò CSS dark sang light: prefix `html[data-theme=dark]` chỉ dán vào selector đầu của danh sách phẩy nên `.steps li` ăn nền tối ở cả light mode. Bản vá đầu cũng sai (nối liền thành `html[data-theme=dark].card`, và `split(",")` xé selector chứa `rgba()`); cách sửa cuối là giữ selector dạng list rồi prefix từng phần tử.

## 2026-07-29 — docs-site-macos — spec-vs-overstack

Đối chiếu overstack (commit 9032ae4) với `graph-engineering-implementation-spec.md` v0.1 trên 67 mục thuộc 8 trục, sinh trang so sánh `llmwiki/html/290726-spec-vs-overstack.html` (94 KB, self-contained).

Kết quả: 15 đủ · 36 một phần · 15 thiếu · 1 khác-thiết-kế. 15 chỗ thiếu quy về ba gốc — (1) loop-runner không ratchet theo điểm số (grep `git reset` ra 0 kết quả, không có bản ghi Trial); (2) cạnh wiki vô danh và không có edge ID, kéo theo 5/11 loại cạnh spec và mắt xích 5 của bài nghiệm thu §10; (3) không có dịch vụ commit-DAG nên không giữ nhiều lineage thí nghiệm sống song song.

Chiều ngược lại, bảy thứ overstack có mà spec không nhắc: chặn trước hành động 0 token, fire-drill chứng minh luật còn cắn, nguyên tắc "tồn tại ≠ dùng được", chống drift ba bản skill, capproof, claim-receipts, hạ tầng bằng không.

## 2026-07-29 — gap-check — pdf-goc-graph-engineering

Đọc PDF gốc `Graph-Engineering-Athropic-Karpathy-Loop.pdf` (11 trang) — nguồn mà spec md derive ra. Không lật kết luận nào của bản đối chiếu 67 mục; bổ sung GỐC THIẾU THỨ 4: graph của overstack là DOCS-graph (chỉ xem/lint/vẽ), PDF đòi RUNTIME-graph (TABLE I: gate signal / classifier input / shared surface / shared memory / grounding layer trong từng workflow pattern). Kèm 2 món rẻ: grounding feedback có schema `required_evidence[]`, và message-board cho giả thuyết đã bỏ. Điểm mạnh nhất theo PDF: persistent world model 7/9 tick ("the agent forgets, the wiki does not"); thiếu temporal facts. Vị trí build path: ~Week 2 + mảnh Month 1. Cập nhật vào draft 290726-spec-vs-overstack.

## 2026-07-29 — docs-site-macos — pdf-gap-html

Sinh trang riêng `llmwiki/html/290726-pdf-gap-overstack.html` (81 KB, 7 section, self-contained) giải thích bằng HTML phần đối chiếu PDF gốc Graph Engineering: tiến trình vibe→agentic→graph với vị trí overstack, 5 cơ chế externalize bottleneck, 4 gốc thiếu kèm bằng chứng file thật, TABLE I runtime-graph (4/6 vai trò chưa có) + diagram DOCS-graph vs RUNTIME-graph, TABLE VI checklist (3✅ 4🟡 2🔴) + 14 bước chuẩn (thiếu 5 bước graph), persistent world model 6✅/2🟡/1🔴, build path ~Week 2, và 3 chỗ chính PDF khuyên ĐỪNG. Generator `.orca-onboard/tmp/build_pdf_gap.py` tái dùng shell build_source_map. Kiểm trong Chrome: console sạch, 0 request ngoài. Footer có đường dẫn tuyệt đối (R16).

## 2026-07-29 — plan — graph-engineering-PLAN

Checkout nhánh `graph-engineering` (từ orca @ 9032ae4, sửa typo "graph-engiering" của user thành tên đúng). Viết `sources/draft/290726-graph-engineering-PLAN.md` — 6 task đóng gap theo PDF: T1 ratchet điểm số cho loop-runner (metric-cmd + direction + git keep/revert + Trial, PDF R-1.1/1.3/1.4) · T2 edge ID sha1 + typed edges đọc frontmatter relations (thêm supports/contradicts/supersedes) · T3 /query đính mục Evidence trích eid · T4 grounding-check.py schema {decision, claim, reason, required_evidence[]} wire vào /qc-code · T5 bốn trần budget mới trong token-budget (model calls, sub-agents, workers, graph-writes) · T6 provenance-log post-hypothesis/read-hypotheses. Mỗi task TDD self-test-trước, mọi cờ optional giữ backward-compat, ngưỡng mới đều ASSUMPTION trong config adapter. Ngoài phạm vi CÓ TRIGGER: commit-DAG hub (chờ đau thật ≥2 lineage), KG extraction LLM (PDF §VIII.C tự khuyên đừng), temporal facts, verification-wave khác vai. R7 plan-executable cắn 3 lần lúc viết (Task 2/5/6 thiếu code block) — bổ sung đủ code thật mới qua.

## 2026-07-30 — docs-site-macos — pr92-flow
Trang HTML giải thích PR #92 (graph-engineering → orca): 3 gốc thiếu, luồng 7 tính năng T1–T7 (ratchet/edge-id/grounding-gate/token-budget/hypothesis-log/commit-dag-hub), và bảng "gọi ra ntn / khi nào kích hoạt" xác nhận bằng grep thật trên hooks — chỉ T2 (edge ID, qua stop.py) và T3 (/query) tự động, 5/7 còn lại là opt-in gọi tay không hook nào đụng tới. Nối tiếp phiên qc-code review PR #92 (verdict CẦN SỬA, 4 mục blocking).

## 2026-07-30 — cursor-animated-sites — hook-skill-layers
Walkthrough tương tác giải thích lifecycle thật của Claude Code + overstack khi user gõ 1 câu: SessionStart(1 lần/phiên) → UserPromptSubmit(mỗi câu) → Claude quyết định → nạp Skill(văn bản, không tự chạy) → PreToolUse(validators, CÓ THỂ CHẶN) → code thật(harness/scripts, tất định) → PostToolUse → lặp lại → Stop(medic --ci, CÓ THỂ CHẶN dừng) → SessionEnd. Cursor lề-trái đi qua cây file đúng thứ tự, màu theo vai trò (đọc/ghi/chặn/qua), kèm 2 ví dụ THẬT đã xảy ra ngay trong hội thoại (R16 report-show-path chặn 1 lần Write; medic --ci FAIL vì overstack.html cũ).

## 2026-08-01 — fdk — teach-me: khung bảy bước
Feedback Rhein: "học cái gì cũng phải có cấu trúc [Tên gọi→Nguồn gốc→Lý do tồn tại→Cơ chế hoạt động→Trade-off→Giới hạn→Vị trí trong hệ thống] để hiểu sâu". Đổi skill teach-me từ khung "bốn phần" (2 cấp + bộ ba + tóm tắt) sang khung bảy bước cố định, đúng thứ tự — dồn nội dung runtime-driven (2 sơ đồ hệ thống/code) vào bước 4, sơ đồ tóm tắt luồng vào bước 7, thêm mới Trade-off (bước 5) và Giới hạn (bước 6) — hai góc trước đây không có chỗ đứng riêng. Sync canonical→mirror→global install (parity 3 bản byte-identical), regen skill-search index, bump capability-stamp 1.3.60→1.3.61, cập nhật fdk-problem-tree.html (node p-45, solved, scope=[skills]). fdk-gate 21/21 PASS.

## 2026-08-03 — propose — evidence-terminal-chain
- SPEC `030826-evidence-terminal-chain-harness.md` + trang seq `030826-evidence-terminal-chain-seq.html` (8 diagram / 8 task), task `T-260803-01`, trạng thái **proposed** — chờ duyệt, chưa viết code.
- Luật đề xuất R19 `evidence-terminal`: mọi đường đi từ kết luận xuống lá phải kết thúc ở nút chứng cứ. Taxonomy 6 loại điểm cuối; `web` đòi link tới đúng chỗ tìm + ngày truy cập + trích nguyên văn; `parametric` (kiến thức từ training model) phải khai `origin` + cờ chưa kiểm chứng và bị cấm làm điểm cuối duy nhất.
- Prior art đã grep, không dẫm: `claim-receipts.py` (gán nhãn + resolve reference), `grounding-check.py` (schema verdict), issue `110726-anti-fabrication-observed-metrics` (trục số đo).

## 2026-08-03 — plan — evidence-terminal-chain
- SPEC được duyệt, bổ sung giữa chừng yêu cầu bật/tắt → SPEC vá thêm FR-011, FR-012, SC-005, Task 9 và mục "Công tắc bật/tắt ba tầng" (9 task / 9 diagram).
- `030826-evidence-terminal-chain-PLAN.md`: 9 task thi hành, 12/12 FR có task nhận, R18 rc=0.
- Công tắc theo khuôn kill-switch sẵn có của repo: cờ `--no-evidence-chain` > env `OVERSTACK_EVIDENCE_TERMINAL` > `enabled` trong config; tắt ở bất kỳ tầng nào vẫn in dòng báo lên stderr (chống cổng câm).

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-08-03 06:40:04 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=b8afb386 · actor=agent · prev=be6620d90361d49866fca121a029e7c5b439a5a5530374 |
| 2026-08-03 06:40:04 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=b8afb386 · actor=agent · prev=180165ce379567d2ac973f0595eb10eda47c369f414b09 |
| 2026-08-03 13:07:31 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=0 · prev=92dfbe3aa34dd47d8ef7ac1f49d4809971fa54bb90229020f60f45b21d86b8d3 · h=a0d6 |
| 2026-08-03 13:07:59 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/sources/030826-session-provenance.md', 'llmwiki/wiki/inde |
| 2026-08-03 13:07:59 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=fa4b97ee5c3958cc0c038679c8ee5cc32116c0278 |
| 2026-08-03 16:11:37 | `task.new` |  · task=T-260803-01 · title=evidence-terminal-chain · state=proposed · actor=agent · prev=784dba4bd0eb571944bd3d37a83bd0 |
| 2026-08-03 16:14:55 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Write · session=b8afb386 · actor=agent · pre |
| 2026-08-03 16:14:55 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Write · session=b8afb386 · actor=agent · pre |
| 2026-08-03 16:18:45 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Write · session=b8afb386 · actor=agent · prev=57029686163895 |
| 2026-08-03 16:18:45 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Write · session=b8afb386 · actor=agent · prev=310421dd303d42 |
| 2026-08-03 16:19:15 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:19:15 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:19:24 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=871a82fc2a8e8e0 |
| 2026-08-03 16:19:24 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=ec6a387a2c362ff |
| 2026-08-03 16:19:29 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=2f9bad82f311ada |
| 2026-08-03 16:19:29 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=e6a024e1c70e138 |
| 2026-08-03 16:19:59 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=b8afb386 · actor=agent · prev=965e98a687935309febdaf66805685c5f1a86d4038775e |
| 2026-08-03 16:19:59 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=b8afb386 · actor=agent · prev=d7e8f43e4e44544d281a42b30bb569b71a61e48678c2d6 |
| 2026-08-03 16:23:59 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:23:59 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:08 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:08 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:20 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:20 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:27 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:27 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:24:51 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=32c19c4cc7dad6e |
| 2026-08-03 16:24:51 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=341cfd861988170 |
| 2026-08-03 16:24:59 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=b1c6d6c5d2a5fff |
| 2026-08-03 16:24:59 | `file.write` | llmwiki/html/030826-evidence-terminal-chain-seq.html · tool=Edit · session=b8afb386 · actor=agent · prev=f4478b0f46f3be0 |
| 2026-08-03 16:25:07 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:25:07 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:25:19 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:25:19 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:25:27 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:25:27 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md · tool=Edit · session=b8afb386 · actor=agent · prev |
| 2026-08-03 16:31:22 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-PLAN.md · tool=Write · session=b8afb386 · actor=agent · prev=7 |
| 2026-08-03 16:31:22 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-PLAN.md · tool=Write · session=b8afb386 · actor=agent · prev=9 |
| 2026-08-03 16:31:53 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-PLAN.md · tool=Edit · session=b8afb386 · actor=agent · prev=c1 |
| 2026-08-03 16:31:53 | `file.write` | llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-PLAN.md · tool=Edit · session=b8afb386 · actor=agent · prev=ea |

<!-- log:auto:end -->
