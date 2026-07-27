---
type: draft
title: propose-plan-split-superpowers
status: proposed
tags: [propose, plan, r7, orca-workflow, superpowers]
timestamp: 2026-07-14
task: T-260714-01
r7_meta: true   # draft NÓI VỀ chính luật R7 → phải trích nguyên văn chuỗi bị cấm; miễn check (g)/(l)
---

# 140726-propose-plan-split-superpowers

**Status:** proposed

## What
Tách vòng đời đề xuất thành hai văn bản có hai người đọc khác nhau — `/propose` sinh **SPEC** (thiết kế, người duyệt) và một skill mới `/plan` sinh **PLAN** (kế hoạch thi hành, agent mù đọc) — rồi mở rộng R7 để cắn được cả hai, sao cho mọi thứ superpowers có thì ta có, và mọi ưu thế ta đang có thì giữ nguyên.

## Context
Đã query wiki trước khi soạn (force-query, R7-f):

- ``ADR-003-skill-as-single-source-of-truth`` — mọi yêu cầu về hành vi propose sống trong `skills/propose/SKILL.md`; `orca-workflow` chỉ *gọi* skill, không mô tả lại. Thay đổi này vì thế phải rơi vào skill, không rơi vào workflow.
- ``ADR-004`` — context nội-bộ-framework là opt-in; skill mới không được auto-fire đầu phiên.
- ``ADR-015`` (persona theo archetype) và bảng chi phí CLI trong `skills/orchestrate/orca-workflow.md` — dispatch hiện giao task cho CLI rẻ chạy headless (`opencode run` / `agy -p` / `kiro run`).
- Bài học **250626** ghi ngay trong `orca-workflow.md`: CLI agent headless **thực đo giao hàng ~1/5 task**. Đây là dữ kiện nền của toàn bộ đề xuất này.
- `harness/validators/proposal_complete.py` — R7 hiện có 6 check (a)–(f): bảng Agent Task Assignment, link sequence diagram, số `diagram-box` ≥ số task, cấm `.msg{opacity:0}`, prose `class="desc"` mỗi diagram, và `## Context` phải có nội dung.
- Nguồn đối chiếu ngoài: `fdk/docs/superpowers/` (10 cặp spec+plan thật) + repo `obra/superpowers` đã clone về `scratchpad/superpowers/` — đọc `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`, `skills/subagent-driven-development/{SKILL.md,implementer-prompt.md,task-reviewer-prompt.md}`.

**Kết luận từ đối chiếu:** plan của superpowers dày (673–2621 dòng, so với spec 82–511 dòng) không phải vì họ thích viết dài, mà vì mô hình thi hành của họ là *một subagent mới tinh cho mỗi task, không thừa hưởng context nào*. Cái gì không nằm trong file thì agent không có. Ta dispatch cho model **rẻ hơn và mù hơn** (CLI headless, không hỏi lại được, giao hàng 1/5) nhưng lại viết plan mỏng hơn họ. Đó là gốc của tỷ lệ giao hàng thấp, và là thứ đề xuất này sửa.

## Non-goals
- Không bê nguyên cây thư mục `docs/superpowers/{specs,plans}` vào repo. Wiki đã là nơi chứa; convention `-PLAN.md` trong `wiki/sources/draft/` đã tồn tại (`060726-ponytail-distill-PLAN.md`).
- Không thêm rule id mới (không R18). R7 đã được wire ở pre-commit, post-tool-use hook, harness-doctor, dispatch-verify và cả hai `policy.yaml` — thêm nhánh check vào chính file đó là điểm đòn bẩy rẻ nhất.
- Không thêm vòng hỏi-từng-câu kiểu `brainstorming` vào `/propose`. Ta đã có `/br interview` cho đường nặng đó; nhân đôi là nợ.
- Không đụng cơ chế dispatch/persona/archetype đang chạy.

## Global constraints
Ràng buộc bao trùm mọi task dưới đây, chép nguyên từ luật repo:

- **ADR-003:** hành vi propose/plan chỉ định nghĩa tại `skills/<tên>/SKILL.md` (canonical). Mirror `llmwiki/skills/**` và bản cài `~/.claude` sinh bằng `bash fdk/tools/sync-skill.sh <tên>` — cấm `cp` tay.
- **Không rule id mới:** mở rộng R7 tại `harness/validators/proposal_complete.py`. Hai file `harness/policy.yaml` và `harness/poc-vendor-neutral/policy.yaml` phải sửa **giống hệt nhau** (có gate `policy-converters-drift` trên CI).
- **Fail-closed đúng phạm vi:** check mới chỉ cắn file `wiki/sources/draft/**/*.md` còn `Status: proposed`. Draft đã `implemented`/`done` và output-report (không có `## Plan`) tiếp tục miễn — không được làm đỏ lịch sử.
- **Không ghi công AI** trong commit/PR/wiki (R15).
- **HTML cho người xem** phải có toggle sáng/tối (nút gạt có nhãn, `localStorage`, chống FOUC), thang chữ compact 13″, và in full path của chính file ở footer.
- **Trước push:** `python3 fdk/tools/medic.py --ci` xanh + chạy trọn job `repo health` của `.github/workflows/harness.yml` tại local.

## Approaches
Ba cách đạt mục tiêu, đã cân nhắc:

**(A) Nhồi chi tiết code-level vào chính draft `/propose` hiện tại.** Một file duy nhất, không skill mới, không split. Nhược điểm giết chết phương án: draft phình lên 700–800 dòng thì cái cổng `orca orchestration gate-create` mất tác dụng — user không đọc nổi thứ mình đang bấm duyệt. Superpowers tách hai văn bản chính vì lý do này.

**(B) Chỉ siết R7 (cấm placeholder, ép file path) rồi đo xem plan mỏng có thật làm agent hỏng không.** Rẻ nhất, nhưng ta *đã có* số đo: bài học 250626, 1/5. Đo lại một thứ đã biết là trì hoãn, không phải thận trọng.

**(C) — chọn.** Tách SPEC (gate cho người) / PLAN (nạp cho máy), mở rộng R7 cắn cả hai, dispatch bơm task brief trích từ PLAN thay vì mô tả suông. Đây là bậc "đổi luật chơi" của Meadows: agent rẻ không cần giỏi lên, chỉ cần cái nó đọc phải đủ. Đắt hơn (B) đúng một skill mới và một nhánh validator, nhưng đó là toàn bộ khoản chênh.

## Plan

- [ ] **T1 — `/propose` thành SPEC-grade.** Sửa `skills/propose/SKILL.md`: draft giữ nguyên `## Context` (force-query), `## Plan`, bảng phân công agent, cặp `.md`+`.html`; **thêm** `## Global constraints` (ràng buộc bao trùm, chép nguyên văn từ wiki/ADR — mỗi task ngầm mang theo), `## Non-goals`, `## Approaches` (2–3 phương án + tradeoff + phương án chọn, không được chọn thầm), và `## Self-review` (3 mắt lưới: phủ hết yêu cầu / quét placeholder / nhất quán tên-kiểu). Cuối skill: bàn giao sang `/plan` sau khi gate duyệt.

- [ ] **T2 — skill mới `/plan`.** Tạo `skills/plan/SKILL.md` (tương đương `writing-plans` của superpowers, viết cho *người thi hành không biết gì về codebase và gu thì đáng ngờ*). Input: draft SPEC đã duyệt. Output: `llmwiki/wiki/sources/draft/DDMMYY-<tên>-PLAN.md` gồm Goal / Architecture / Tech stack / `## Global constraints` (chép từ SPEC) / `## File structure` (file nào tạo–sửa, mỗi file một trách nhiệm) / `### Task N` × N / `## Self-review`. Mỗi Task N bắt buộc: **Files** (đường dẫn chính xác, kèm dải dòng khi sửa) · **Interfaces** (Consumes / Produces với chữ ký chính xác — agent chỉ thấy task của mình, đây là cách nó biết tên hàm hàng xóm) · các **Step 2–5 phút** dạng TDD (viết test fail → chạy cho thấy fail kèm chuỗi lỗi mong đợi → code tối thiểu → chạy pass → commit), step nào đổi code thì **phải có code**. Kèm danh mục **cấm placeholder** đích danh: `TBD`, `TODO`, "xử lý lỗi phù hợp", "handle edge cases", "tương tự Task N".

- [ ] **T3 — R7 mở rộng (không rule mới).** Sửa `harness/validators/proposal_complete.py`, thêm hai nhánh scope theo tên file. Nhánh SPEC (draft thường): **(g)** cấm token placeholder, **(h)** bắt buộc `## Global constraints` có nội dung. Nhánh PLAN (`*-PLAN.md`): **(i)** mỗi `### Task` phải có `**Files:**` với ≥1 đường dẫn thật, **(j)** mỗi Task có ≥1 code fence, **(k)** có ≥2 agent trong bảng thì mỗi Task bắt buộc `**Interfaces:**`, **(l)** cấm placeholder, **(m)** có `## Global constraints`. File PLAN không cần `.html` — miễn check (b)(c)(d)(e) cho nhánh này. **Kèm một fix đã lộ ra khi soạn chính draft này:** check (d) hiện quét toàn bộ text của trang HTML nên nó cắn nhầm cả *văn xuôi* nhắc tới chuỗi CSS bị cấm; phải giới hạn (d) chỉ quét trong các khối `<style>`.

- [ ] **T4 — đồng bộ policy.** Cập nhật statement R7 ở `harness/policy.yaml` **và** `harness/poc-vendor-neutral/policy.yaml` giống hệt nhau (gate `policy-converters-drift` sẽ đỏ nếu lệch), phản ánh đúng: R7 gác cả SPEC lẫn PLAN.

- [ ] **T5 — `orca-workflow` nối mắt xích.** Bước 4 ("Phân rã tasks") đổi thành: gate duyệt SPEC → **gọi skill `/plan`** sinh `-PLAN.md` → `task-create` mỗi `### Task` → `dispatch --inject` bơm **nguyên văn task brief** (Files + Interfaces + Steps + Global constraints) thay vì mô tả task suông. Giữ nguyên persona/archetype (ADR-015) và watchdog 60–90s.

- [ ] **T6 — register + parity.** `bash fdk/tools/sync-skill.sh propose` và `... plan` (canonical → mirror llmwiki → bản cài `~/.claude`); thêm dòng `plan` vào bảng Skills của `llmwiki/CLAUDE.md` + `llmwiki/AGENT.md` + LOOP_MAP; `python3 fdk/tools/build-capabilities.py`; append `wiki/index.md` + `wiki/log.md`; thêm node vào `llmwiki/html/fdk-problem-tree.html`.

- [ ] **T7 — cổng NGƯỢC cho `/plan` (thêm sau phản biện của user).** `/plan` được quyền **BÁC SPEC**: dừng lại, không viết PLAN nửa vời, khi một yêu cầu không quy được về task nào làm được / hai mục SPEC mâu thuẫn nhau hoặc mâu thuẫn `## Global constraints` / phương án đã chọn hoá ra bất khả thi / phải bịa ra hàm-file mà SPEC không hề nhắc. Gom mọi chỗ vỡ thành **một lần báo** (mỗi chỗ kèm đúng câu SPEC gây ra nó) → quay về `/propose` sửa rồi **duyệt lại**. Lý do: viết PLAN chính là cách phát hiện SPEC sai; nếu cổng đã cho qua rồi mới lòi ra thiết kế bất khả thi thì user đã duyệt một thứ không xây được — cổng coi như hỏng.


## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — /propose SPEC-grade | Claude | Sửa hợp đồng skill trung tâm, nuance cao, chạm R7 | pending |
| T2 — skill /plan | Claude | Văn bản định nghĩa chất lượng plan — không giao cho model rẻ | pending |
| T3 — R7 mở rộng | Claude | Validator fail-closed, sai một regex là chặn nhầm cả repo | pending |
| T4 — đồng bộ policy ×2 | Claude | Nhỏ nhưng có gate drift trên CI, làm cùng T3 cho khớp | pending |
| T5 — orca-workflow bước 4 | Claude | Chạm luồng dispatch đang chạy | pending |
| T6 — register + parity | OpenCode `big-pickle` (fallback Claude) | Cơ học thuần: chạy sync-skill.sh, build-capabilities.py, append index/log. Watchdog 60–90s, im lặng thì Claude tiếp quản (bài học 250626) | pending |
| T7 — cổng ngược cho `/plan` | Claude | Hợp đồng skill, nuance cao — sinh ra từ phản biện của user, không có trong bản đầu | pending |

**Sequence diagram:** [140726-propose-plan-split-seq.html](../../../html/140726-propose-plan-split-seq.html)

## Risks
- **Draft cũ còn `proposed` bị đỏ oan — đã kiểm chứng, rủi ro nhỏ hơn tưởng.** Repo còn 9 draft ở trạng thái `proposed`. Nhưng pre-commit chỉ chạy R7 trên file *staged* (`files: ^(fdk|llmwiki)/wiki/(draft|sources/draft)/.*\.md$`) và `harness-doctor` test bằng fixture tổng hợp chứ không quét draft thật. Vậy 9 draft cũ chỉ đỏ khi có người sửa chúng. Vẫn nên quét thử toàn bộ sau khi làm T3 để biết trước cái nào sẽ đỏ.
- **Regex `**Files:**` bắt hụt.** Nếu PLAN viết `**Files**` (thiếu dấu hai chấm) sẽ bị chặn nhầm. Giảm thiểu: regex chấp nhận cả hai dạng, và thông báo lỗi in ra đúng dòng sai.
- **PLAN phình → tốn token Claude.** Đây là chi phí có chủ đích: token đổ vào PLAN một lần, thay cho N lần agent rẻ giao hàng hỏng rồi Claude làm lại từ đầu.
- **Skill mới không được trigger.** `/plan` là danh từ chung, router có thể lẫn. Giảm thiểu: `description` nêu rõ "chỉ dùng SAU khi draft SPEC đã được duyệt", và `orca-workflow` gọi thẳng bằng Skill tool.

## Success criteria
- `python3 harness/validators/proposal_complete.py <draft cố tình thiếu Global constraints>` → exit 2, in đúng mã `(h)`.
- `python3 harness/validators/proposal_complete.py <PLAN cố tình có "TBD">` → exit 2, in đúng mã `(l)`.
- `python3 harness/validators/proposal_complete.py <PLAN đủ chuẩn>` → exit 0.
- Draft `140726-*.md` này (SPEC) và PLAN sinh ra từ nó đều qua R7 sạch — dogfood.
- `python3 fdk/tools/medic.py --ci` xanh; job `repo health` chạy local xanh.
- `grep -c "plan" CAPABILITIES.md` > 0 và `~/.claude/skills/plan/SKILL.md` tồn tại sau `sync-skill.sh`.

## Self-review
- **Phủ yêu cầu:** mọi thứ superpowers có (spec/plan split · Files chính xác · Interfaces Consumes/Produces · Global Constraints · step TDD có code + expected output · cấm placeholder · self-review · task right-sizing) đều có task tương ứng: T1, T2, T3. Mọi ưu thế đang có (wiki force-query, bảng agent + chi phí, HTML glass, task-id audit, R7 tất định) giữ nguyên trong T1 và không bị task nào gỡ.
- **Placeholder:** không có `TBD`/`TODO`/"xử lý lỗi phù hợp" trong văn bản này.
- **Nhất quán tên:** rule dùng xuyên suốt là **R7** (không R18); file validator là `harness/validators/proposal_complete.py`; skill mới tên **`plan`**, file `skills/plan/SKILL.md`, output hậu tố **`-PLAN.md`**.

## Notes
- Nguồn ngoài: `scratchpad/superpowers/` (clone `obra/superpowers`), `fdk/docs/superpowers/` (10 cặp spec+plan thật, tỷ lệ spec:plan ≈ 1:8).
- `ADR-003-skill-as-single-source-of-truth` · `ADR-004` · `ADR-015`

## Origin
- **Draft:** `wiki/sources/draft/140726-propose-plan-split-superpowers.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
