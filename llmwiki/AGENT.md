FILE FIRST — đọc trang này trước, rồi merge với rule + skill của framework bên dưới.

# Behavioral guidelines — distilled from Karpathy's CLAUDE.md
Giảm lỗi LLM-coding phổ biến. Thiên về cẩn trọng hơn tốc độ; task tầm thường thì dùng phán đoán.

1. **Think before coding.** Đừng đoán, đừng giấu chỗ mơ hồ. Khai assumption; nhiều cách hiểu → trình ra, đừng tự chọn; có cách đơn giản hơn → nói + push back; chưa rõ → dừng, hỏi.
2. **Simplicity first.** Code tối thiểu giải đúng vấn đề, không suy diễn — không thêm feature/abstraction/"flexibility"/error-handling cho ca bất khả. 200 dòng mà 50 đủ → viết lại. "Senior có chê overcomplicated không?" → đơn giản hoá.
3. **Surgical changes.** Chỉ chạm cái buộc phải chạm. Đừng "cải thiện"/refactor code lân cận; giữ style cũ; dead-code lạ thì nêu, đừng xoá. Chỉ dọn orphan do CHÍNH thay đổi của bạn tạo ra. Mỗi dòng đổi phải truy về đúng yêu cầu.
4. **Goal-driven execution.** Biến task thành mục tiêu kiểm chứng được ("add validation" → viết test fail rồi làm pass). Việc nhiều bước → nêu plan ngắn, mỗi bước kèm cách verify. Success criteria mạnh giúp loop độc lập; criteria yếu ("làm cho chạy") thì phải hỏi liên tục.

Đạt khi: diff bớt thừa, bớt viết-lại do overcomplicate, câu hỏi làm rõ đến TRƯỚC khi sai — không phải sau.

(Nguồn: 4 nguyên tắc của Karpathy CLAUDE.md, bản distill của Forrest Chang — `multica-ai/andrej-karpathy-skills`. Bối cảnh framework: rule + skill cụ thể nằm ngay dưới.)

## 5-Why — chạy TRƯỚC mọi việc, không phải tuỳ chọn

Trước khi sửa hay xây bất cứ thứ gì, hỏi **"vì sao"** cho tới khi chạm **cấu trúc** sinh ra nó — thường là năm tầng. Bỏ qua bước này là cách nhanh nhất để vá triệu chứng, và bug sẽ tái sinh dưới một cái tên khác.

- **Viết chuỗi ra, đừng nghĩ thầm.** Chuỗi viết ra thì người khác kiểm được; chuỗi nghĩ trong đầu luôn "hợp lý" với chính người nghĩ.
- **Dừng đúng chỗ.** Chạm cấu trúc thì dừng: một vòng phản hồi thiếu, một cái tên hứa nhiều hơn hành vi, một cổng chỉ báo mà không chặn. Dừng ở *"vì người ta quên"* là chưa tới đáy — quên là hằng số của con người, không phải nguyên nhân.
- **Tìm HỘI TỤ trước khi sửa.** Chạy 5-Why cho vài triệu chứng đang có cùng lúc; nhiều cái đổ về một root thì sửa root **một lần**, đừng vá N chỗ. Đo 2026-07-20: thẻ ghi-tạm tồn **19/20**, issue mở **24**, pattern lệch upstream **15**, file chưa rà wiki **39**, task orchestration treo **17** — năm cái sổ khác nhau, **một** root: hệ rất giỏi PHÁT HIỆN nợ và không có nhịp TRẢ nợ. Lúc đó phản xạ sai là thêm bộ phát hiện thứ sáu.
- **Nghi ngờ chẩn đoán đầu tiên của chính mình.** Nó thường là suy luận từ triệu chứng chứ chưa đọc code. Cùng ngày: tôi kết luận code-graph "ghi và đọc trỏ hai DB khác nhau" — sai; đọc code thì ra *một* DB thiếu schema giết cả fan-out. Chẩn đoán chỉ được tin sau khi **tái hiện** được.
- **Ngoại lệ duy nhất:** việc không chứa chẩn đoán nào — đổi tên, format, regen artifact, chép nguyên văn. Việc nào có chữ "sửa", "hỏng", "vì sao", "sao lại thế" thì luôn chạy.

## Chứng cứ trong CHAT — opt-in qua `/graph-mode`, không auto-bơm mỗi phiên

Luật chuỗi-lập-luận-phải-chạm-chứng-cứ (6 loại điểm cuối, chi tiết [[evidence-terminal-chain]])
GIỜ nằm ở `skills/graph-mode/SKILL.md`, không còn bơm mặc định vào mọi phiên — kỷ luật này buộc
trích dẫn/mở file nhiều hơn mỗi câu trả lời (nặng token), nên chỉ bật khi thật cần độ tin cậy cao
(audit, ADR, chẩn đoán lan rộng). Gọi `/graph-mode` để bật, "tắt graph mode"/"normal mode" để tắt.
Validator máy trên tài liệu ```evidence-chain (R19, `harness/validators/evidence_terminal.py`) KHÔNG
phụ thuộc skill này — luôn chạy qua `harness/policy.yaml` bất kể graph-mode bật hay tắt.

## Cái thang chống over-engineering — chạy khi VIẾT/SỬA code
Karpathy ở trên là "vì sao"; đây là "làm sao". (Chưng cất từ ponytail, MIT — nguồn `060726-ponytail-distill`.)

**Hiểu bài trước, leo thang sau.** Đọc code, trace flow end-to-end rồi mới sửa. Diff nhỏ ĐẶT SAI CHỖ = bug thứ hai.

**Cái thang — dừng ở bậc đầu tiên đứng vững:** (1) YAGNI — thứ này có cần tồn tại không? bậc rẻ nhất là xoá → (2) codebase đã có chưa? tái dùng → (3) stdlib giải được không? → (4) native platform? CSS thay JS, DB constraint thay app-code → (5) dependency đã cài rồi? → (6) 1 dòng được không? → (7) cuối cùng mới viết code tối thiểu.

**Bug = root cause, không vá triệu chứng.** Grep mọi caller, sửa 1 lần ở hàm chung — fix root-cause thường diff NHỎ HƠN vá từng caller.

**Marker nợ có kỷ luật** — shortcut cố ý phải để lại comment `shortcut: <trần hiện tại>, <trigger nâng cấp>` (vd `# shortcut: global lock, đổi per-account nếu throughput thành vấn đề`). Grep được → nợ có hạn, không thành "never". Marker thiếu trigger bị `/lint` cắn.

**Carve-out — KHÔNG lười ở:** validation tại trust boundary, error-handling chống mất data, security, a11y, calibration phần cứng, và bất cứ thứ gì user YÊU CẦU rõ. Logic non-trivial phải để lại ĐÚNG 1 check chạy được (assert demo / 1 test nhỏ) — YAGNI áp cho cả test, nhưng không phải 0 test.

**Format báo cáo rút gọn (vd khi chạy `/simplify`):** mỗi finding 1 dòng `L<line>: <tag>: <trước> → <sau>`, tag ∈ {delete, stdlib, native, yagni, shrink}; chốt `net: -N dòng`. Không có gì để cắt → "Lean already. Ship."

**Output:** code trước, tối đa 3 dòng "skipped X, add when Y". Giải thích dài hơn code → xoá giải thích.

## Rules
- 🧰 **Đồ nghề bạn CÓ — đừng làm lại thứ đã tồn tại:** bản đồ năng lực sinh-bằng-code, luôn-mới (ADR-005): repo framework → `fdk/CAPABILITIES.md` (skill+rule+tool); dự án downstream → `CAPABILITIES.md` ở gốc (build-capabilities deploy cạnh hooks, đọc global skills + rule đã cài). Không chắc có gì cho việc đang làm → ĐỌC nó, hoặc `find-skills "<việc>"`. Sinh lại: `python3 fdk/tools/build-capabilities.py` (downstream tự nhận bối cảnh khi chạy với `--root`).
- **Đang phát triển CHÍNH framework này (skill/rule/validator/script/hook/wiki)? Gọi `/fdk`** — on-demand front-door: pre-flight + không miss rule + không dẫm module cũ. KHÔNG auto-bơm đầu phiên vì phần lớn phiên là dùng framework để dev DỰ ÁN KHÁC (xem `ADR-004`).
- **Design rule (feedback 2026-06-27):** thứ gì auto-fire/tự-bơm context vào MỌI phiên (hook SessionStart/UserPromptSubmit, dòng auto-load) chỉ được phục vụ *dự án hiện tại*; context *nội-bộ-framework* (FDK, inventory, runbook sửa rule) phải **opt-in** qua skill gọi chủ động. Luật này nằm ở đây (theo repo) vì memory cá nhân là máy-local, kéo repo máy khác sẽ mất. Xem `ADR-004`.
- FOLLOW the instructions in README.md in wiki folder
- EVERY wiki file must have an `## Origin` section — source is always traceable
- NEVER write to `raw/`
- ALWAYS update `wiki/index.md` when adding or removing a wiki file
- ALWAYS append to `wiki/log.md` after every operation
- Use `[[wikilinks]]` to cross-reference entries in `wiki/`
- Wiki files live in `concepts/`, `entities/`, `sources/`, `draft/`, `architecture/`, or `tours/` — never in `wiki/` root (enforced by R5 validator)
- Wiki entries are only created AFTER code is committed — never during proposal or planning

## Skills

| Skill | Invoke when | File | Loop |
|-------|------------|------|------|
| `ingest` | A new file appears in `raw/` | `skills/wiki-loop/ingest.md` | wiki-loop |
| `query` | User asks a question requiring wiki synthesis | `skills/wiki-loop/query.md` | wiki-loop |
| `wiki-room` | Context phiên chính rot — mở room 1 tầng nạp chi tiết wiki (budget cứng) | `skills/wiki-loop/wiki-room.md` | wiki-loop |
| `record-episode` | Chốt phiên vào tầng nhớ episodic (mem-rank store) để phiên sau truy hồi "phiên trước làm gì" theo nghĩa | `skills/wiki-loop/record-episode.md` | wiki-loop |
| `lint` | After every 10 ingests, or wiki feels stale | `skills/wiki-loop/lint.md` | wiki-loop |
| `playwright-verify` | Verify code nhanh bằng Playwright standalone `.mjs` (không qua test runner): chụp ảnh `localhost`/`file://`, đọc console/pageerror, đo `getBoundingClientRect` khi phần tử "không thấy/không bấm được", auth bypass dev-login. Dùng khi claude-in-chrome bị chặn localhost. | `skills/dev-loop/playwright-verify.md` | dev-loop |
| `propose` | Any new feature or change is requested | `skills/dev-loop/propose.md` | dev-loop |
| `qc-code` | Review code phong cách senior 10 năm — 4 mục (security/performance/naming/logic) điểm/10 + lỗi nặng nhất + fix + verdict PASS/CẦN SỬA; sinh test tái hiện qc-* auto-chạy tất định. KHÁC /orca-sec-scans (Trivy tĩnh) | `skills/dev-loop/qc-code.md` | dev-loop |
| `teach-me` | Giải thích MỘT thứ ở 2 cấp (hệ thống + code) + bộ ba (vấn đề/workflow/chi tiết os·cơ chế·vai trò) + tóm tắt luồng, mỗi phần có sơ đồ; CHỨNG bằng runtime thật (chạy + breakpoint/debugger), không đoán tĩnh. KHÁC /onboard-codebase (cả dự án→wiki) | `skills/dev-loop/teach-me.md` | dev-loop |
| `plan` | SPEC đã DUYỆT → mở rộng thành `-PLAN.md` thi hành được (Files chính xác + Interfaces + code từng bước) TRƯỚC khi dispatch cho agent | `skills/dev-loop/plan.md` | dev-loop |
| `impact-check` | Before modifying any shared symbol | `skills/dev-loop/impact-check.md` | dev-loop |
| `safe-change` | Editing code called from more than one place | `skills/dev-loop/safe-change.md` | dev-loop |
| `verify-before-commit` | Before every commit | `skills/dev-loop/verify-before-commit.md` | dev-loop |
| `ship` | User nhắc release/push/ship — checklist điều kiện trước push & release (medic gate/git sạch/version x.x.x+1/patch note trung thực) | `skills/dev-loop/ship.md` | dev-loop |
| `ovs-notes` | Xem release notes/changelog — liệt kê các bản (tag/GH release) newest-first để chọn & đọc, read-only (khác /ship = cắt release) | `skills/utils/ovs-notes.md` | utils |
| `onboard-codebase` | Deep analysis of legacy code to populate Wiki | `skills/dev-loop/onboard-codebase.md` | dev-loop |
| `doyourmagic` | Freshly-cloned external repo/tool → clone→explore→analysis→write-workflows, sinh bộ `.overstack/doyourmagic/<repo-name>/workflows.md` + `index.html` chạy được ngay. KHÁC `onboard-codebase` (phân tích DỰ ÁN CHÍNH → wiki nội bộ, không phải tool ngoài) | `skills/dev-loop/doyourmagic.md` | dev-loop |
| `orca-workflow` | Daily propose → gate → dispatch with Orca | `skills/orchestrate/orca-workflow.md` | orchestrate |
| `orca-onboard` | Parallel codebase onboarding with Orca | `skills/orchestrate/orca-onboard.md` | orchestrate |
| `orca-handover` | Sinh MỘT file .md bàn giao đủ dày để phiên KHÁC (không có context nào) mở ra là làm được ngay — việc dở + thứ tự có lý do + số đo làm bằng chứng + cạm bẫy đã trả giá + hướng đã thử và BỎ. KHÁC record-episode (ghi cho MÁY) và plan (task ĐÃ duyệt, đã rõ) | `skills/orchestrate/orca-handover.md` | orchestrate |
| `orca-issue` | Sự cố/bug/regression — vòng repro-first → fix red→green → distill kép | `skills/orchestrate/orca-issue.md` | orchestrate |
| `wayfinder` | Việc QUÁ LỚN một phiên & còn mù mờ — bản đồ ticket QUYẾT ĐỊNH (fog of war/frontier/out-of-scope), giải từng cái tới khi đường rõ. TRƯỚC /propose. Chỉ-gọi-tay | `skills/orchestrate/wayfinder.md` | orchestrate |
| `sync-template` | Upstreaming template improvements to master repo | `skills/utils/sync-template.md` | utils |
| `md-to-html` | User wants to render a professional HTML report | `skills/utils/md-to-html.md` | utils |
| `docs-site-macos` | User wants macOS-style documentation site | `skills/utils/docs-site-macos.md` | utils |
| `web-crawl` | Crawl/scrape a URL or site into LLM-ready markdown | `skills/utils/web-crawl.md` | utils |
| `web-clone` | Clone a website — snapshot (1-file offline copy) or reconstruct (rebuild as editable Next.js code, canonical home for the full-clone pipeline) | `skills/utils/web-clone.md` | utils |
| `fdk` | Đang phát triển CHÍNH framework (skill/rule/validator/hook/wiki) | `skills/utils/fdk.md` | utils |
| `fdk-uat` | UAT thật một bản sắp phát hành — dựng dự án TRỐNG, cài bằng curl từ remote (đường người-mới), kiểm năng lực MỚI có tới tay không; không pass thì GỠ commit khỏi remote | `skills/utils/fdk-uat.md` | utils |
| `medic` | Cổng sức khoẻ tổng — 1 lệnh chứng minh hệ còn khoẻ (luật cắn/drift/docs/code/eval); trước commit, sau pull, nghi rule không chặn | `skills/utils/medic.md` | utils |
| `new-skill` | Scaffold một skill mới (canonical+mirror+lệnh register) | `skills/dev-loop/new-skill.md` | dev-loop |
| `skill-provenance` | Ghi/kiểm provenance (nguồn + sha256) khi cài skill ngoài — audit supply-chain, phát hiện skill bị sửa lén | `skills/dev-loop/skill-provenance.md` | dev-loop |
| `loop-runner` | Vòng lặp agent có guardrail (propose→verify→revise, termination) | `skills/dev-loop/loop-runner.md` | dev-loop |
| `failure-flywheel` | Gom lỗi lặp → đề xuất rule/skill mới (error-analysis) | `skills/dev-loop/failure-flywheel.md` | dev-loop |
| `council` | Hội đồng nhiều model đánh giá → câu trả lời tốt nhất (Karpathy) | `skills/orchestrate/council.md` | orchestrate |
| `trace-grader` | Chấm ĐƯỜNG ĐI của agent (tool/thứ tự/pass^k), không chỉ kết quả | `skills/orchestrate/trace-grader.md` | orchestrate |
| `wikieval` | Bộ eval hồi quy từ wiki goldens (cascade assert + baseline, CI gate) | `skills/dev-loop/wikieval.md` | dev-loop |
| `tidy` | Dọn kho nháp/render (ex docs-curate): `check` ngưỡng >10 draft → hỏi đầu phiên; plan → promote bản chất→wiki → apply (git mv vào archive/ tracked, không giết draft sống) | `skills/utils/tidy.md` | utils |
| `raise-issue` | Raise issue đầy đủ bối cảnh vào ledger local (draft) để dev khác pull về xử lý qua /fdk — feature-gap/tech-debt/foundation (KHÁC orca-issue = bug repro-first) | `skills/utils/raise-issue.md` | utils |
| `frontier-scan` | Quét đối thủ + đối chiếu overstack 8 trục (gọi instant) — "frontier scan", "chúng ta thua gì" | `skills/utils/frontier-scan.md` | utils |
| `brandkit` | Premium brand-kit image generation skill for creating high-end… | `skills/utils/brandkit.md` | utils |
| `hallmark` | **NỀN design mặc định** (Together AI) — 6 discipline + 57 cổng slop-test, từ chối trông AI-generated. Mọi UI đứng trên nó; skill taste khác là flavour. 4 verb: build/audit/redesign/study. Xem [[design-foundation]] | `skills/utils/hallmark.md` | utils |
| `prd-grade-fe` | Pipeline MỘT CỬA ra frontend chuẩn production có cổng máy gác: interview nguồn theme (A macOS glass · B tài liệu · C URL) → khoá vào `design.md` (hallmark + impeccable đọc chung) → build token-only → `fe-gate.sh` (impeccable detect + 4 viewport) + rubric audit/harden/polish → mới giao. Đứng TRÊN hallmark, thêm gate | `skills/utils/prd-grade-fe.md` | utils |
| `diagram` | Vẽ SƠ ĐỒ (hộp+mũi tên) và BIỂU ĐỒ (số liệu) bằng máy — router tới `archify` cho sơ đồ, `dataviz` + kỷ luật lieflat cho biểu đồ; model điền tờ khai, code dựng hình, cổng soi hình học rồi mới giao | `skills/utils/diagram.md` | utils |
| `build-now-adapt-later` | When a task is blocked by missing or unverified information (an… | `skills/dev-loop/build-now-adapt-later.md` | dev-loop |
| `cavecrew` | Decision guide for delegating to caveman-style subagents. | `skills/utils/cavecrew.md` | utils |
| `i-have-adhd` | Định hình OUTPUT cho người đọc ADHD — hành động trước, đánh số bước, nêu lại state mỗi lượt, chặn lạc đề, ước lượng thời gian cụ thể, không mở bài/kết bài xã giao. Áp cho phần CHAT; tài liệu người đọc vẫn theo luật văn xuôi đầy đủ | `skills/utils/i-have-adhd.md` | utils |
| `caveman` | Ultra-compressed communication mode. | `skills/utils/caveman.md` | utils |
| `caveman-commit` | Ultra-compressed commit message generator. | `skills/utils/caveman-commit.md` | utils |
| `caveman-compress` | Compress natural language memory files (CLAUDE.md, todos, preferences)… | `skills/utils/caveman-compress.md` | utils |
| `caveman-help` | Quick-reference card for all caveman modes, skills, and commands. | `skills/utils/caveman-help.md` | utils |
| `caveman-review` | Ultra-compressed code review comments. | `skills/utils/caveman-review.md` | utils |
| `caveman-stats` | Show real token usage and estimated savings for the current session. | `skills/utils/caveman-stats.md` | utils |
| `check-approve` | Sinh sẵn 1-liner để trace 1 lệnh approve/return/reject của DMS trên log BE… | `skills/utils/check-approve.md` | utils |
| `computer-use` | Use Orca's computer-use CLI to inspect and operate local desktop app… | `skills/utils/computer-use.md` | utils |
| `cursor-animated-sites` | Build an interactive "cursor-animated walkthrough" page on top of the… | `skills/utils/cursor-animated-sites.md` | utils |
| `design-taste-frontend` | Anti-slop frontend skill for landing pages, portfolios, and redesigns. | `skills/utils/design-taste-frontend.md` | utils |
| `design-taste-frontend-v1` | The original v1 taste-skill, preserved for projects depending on its exact… | `skills/utils/design-taste-frontend-v1.md` | utils |
| `extract-site` | Extract and convert a website or docs site into clean markdown (full-code clone → see `web-clone`) | `skills/utils/extract-site.md` | utils |
| `fable5` | Reasoning protocol distilled from Claude Fable 5 — Floor check, multi-hypothesis diagnosis, adversarial self-review, Constraint Loop. Persists for the session like `/caveman` once invoked | `skills/utils/fable5.md` | utils |
| `graph-mode` | Bật luật chứng cứ evidence-chain (R19) cho CHAT — mọi kết luận phải chạm điểm cuối xem được (observed/tool-record/graph-edge/web/parametric/absence). Nặng token nên opt-in, không auto-bơm mỗi phiên; tắt bằng "tắt graph mode"/"normal mode" | `skills/utils/graph-mode.md` | utils |
| `find-skills` | Helps users discover and install agent skills when they ask questions like… | `skills/utils/find-skills.md` | utils |
| `full-output-enforcement` | Overrides default LLM truncation behavior. | `skills/utils/full-output-enforcement.md` | utils |
| `gpt-taste` | Elite UX/UI & Advanced GSAP Motion Engineer. | `skills/utils/gpt-taste.md` | utils |
| `harness-tour` | Tour — Claude tự diễn cho user xem harness chặn mình theo thời gian thực… | `skills/utils/harness-tour.md` | utils |
| `harness-update` | TỰ BẢO TRÌ framework overstack trên máy user (self-maintain) — migrate… | `skills/utils/harness-update.md` | utils |
| `health-check` | Kiểm tra sức khỏe "pattern chuẩn" của template — pattern đã đủ chưa, có… | `skills/utils/health-check.md` | utils |
| `high-end-visual-design` | Teaches the AI to design like a high-end agency. | `skills/utils/high-end-visual-design.md` | utils |
| `image-to-code` | Elite website image-to-code skill for Codex. | `skills/utils/image-to-code.md` | utils |
| `imagegen-frontend-mobile` | Elite mobile app image-generation skill for creating premium, app-native… | `skills/utils/imagegen-frontend-mobile.md` | utils |
| `imagegen-frontend-web` | Elite frontend image-direction skill for generating premium,… | `skills/utils/imagegen-frontend-web.md` | utils |
| `industrial-brutalist-ui` | Raw mechanical interfaces fusing Swiss typographic print with military… | `skills/utils/industrial-brutalist-ui.md` | utils |
| `jenkins-agent-l3-deploy` | Deploy a docker-compose app via a Jenkins INBOUND AGENT running on the… | `skills/orchestrate/jenkins-agent-l3-deploy.md` | orchestrate |
| `join-project` | Orient nhanh vào dự án đang chạy đã có llmwiki — read-only, không ghi wiki | `skills/utils/join-project.md` | utils |
| `last30days` | Research what people actually say about any topic in the last 30 days. | `skills/utils/last30days.md` | utils |
| `agent-reach` | Với-tới internet 15 nền (X/Reddit/YT/GitHub/Bilibili/XHS…), zero-API-fee, doctor self-heal — external-pull | `skills/utils/agent-reach.md` | utils |
| `minimalist-ui` | Clean editorial-style interfaces. | `skills/utils/minimalist-ui.md` | utils |
| `new-project-setup` | Deploy llmwiki từ đầu vào project mới — template pull, skill install, RTK,… | `skills/dev-loop/new-project-setup.md` | dev-loop |
| `orca-cli` | Use the public `orca` CLI to operate Orca-managed worktrees/workspaces,… | `skills/orchestrate/orca-cli.md` | orchestrate |
| `orca-dispatch-reference` | Reference for Antigravity/OpenCode dispatch, skill installation,… | `skills/orchestrate/orca-dispatch-reference.md` | orchestrate |
| `orca-eval` | Quét N session Claude Code gần nhất, distill best practices thành report… | `skills/orchestrate/orca-eval.md` | orchestrate |
| `orca-sec-scans` | Quét bảo mật mã nguồn bằng Trivy — tự check/cài Trivy nếu chưa có, quét… | `skills/orchestrate/orca-sec-scans.md` | orchestrate |
| `orchestration` | Use Orca orchestration for structured multi-agent coordination: threaded… | `skills/orchestrate/orchestration.md` | orchestrate |
| `redesign-existing-projects` | Upgrades existing websites and apps to premium quality. | `skills/utils/redesign-existing-projects.md` | utils |
| `snapshot-push` | Push bonbon-ai outer repo as full snapshot, including be/ and fe/ content | `skills/utils/snapshot-push.md` | utils |
| `stitch-design-taste` | Semantic Design System Skill for Google Stitch. | `skills/utils/stitch-design-taste.md` | utils |
| `tour-guide` | Thêm một in-app product tour (spotlight onboarding overlay) tự viết, KHÔNG… | `skills/utils/tour-guide.md` | utils |
| `tour-guide-supademo` | Style thiết kế Supademo cho in-app product tour (dùng kèm skill tour-guide… | `skills/utils/tour-guide-supademo.md` | utils |
| `uat-nonit-testcase` | Tạo bộ test case / checklist UAT cho người dùng nghiệp vụ NON-IT (C&B, kế… | `skills/utils/uat-nonit-testcase.md` | utils |

## Invocation rules
- New file in `raw/` → invoke `ingest` immediately
- New feature request → invoke `propose` first, stop, wait for approval
- Edit to shared code → invoke `impact-check` then `safe-change`
- Orca available → invoke `orca-workflow` cho feature (propose → gate → dispatch)
- Nhiều codebase cần onboard → invoke `orca-onboard` (parallel analysis)
