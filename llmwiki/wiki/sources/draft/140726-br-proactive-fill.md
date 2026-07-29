---
type: draft
title: "br proactive fill — interview tự nhận documents, tự điền field thiếu theo thang default → spec-kit → lens, slice ra DAG frame (ATG mảnh 1)"
status: proposed
tags: [br, interview, proactive, defaults, spec-kit, atg, dag, issue-15]
timestamp: 2026-07-14
task: T-260714-01
---

# 140726-br-proactive-fill

**Status:** proposed
**Task:** T-260714-01 · **Issue:** GH#15 (dây chuyền br) · liên quan [[140726-atomic-task-graph-distill]]

## Restate (một câu)

Thêm mode `--proactive` cho `/br interview`: khi user thả documents + yêu cầu vào `raw/`, dây chuyền tự extract → gap-diff S1–S10 rồi **tự điền các field còn thiếu** theo thang ưu tiên (default của loop → convention github/spec-kit → lens-fill), chỉ hỏi user tối đa 5 câu trọng yếu; đồng thời `/br slice` sinh frame có `depends_on` (DAG, mảnh 1 của Atomic Task Graph) để chuỗi frame không còn là danh sách phẳng.

## Context

Query wiki trước khi draft — các trang đã đọc và điểm ăn khớp:

- [[050726-ralph-interview-pipeline]] — entity map E1–E9 của dây chuyền. Interview hiện tại **dừng chờ user điền toàn bộ** answers.md (E4→E5); lens-fill đã có nhưng là bước user phải chủ động bật. Ý tưởng proactive fill là mở rộng đúng chỗ E4→E5 này, không đổi entity nào.
- [[120726-pipeline-friction]] — xương thật đã ghi nhận: lệnh dài phải gõ tay, user phải điền nhiều, rào chắn dày ngày đầu. Proactive fill đánh trực tiếp vào friction "user phải điền" — thứ nặng nhất với người không phải dev.
- [[120726-pipeline-gaps-raised]] — 3 gap khi clone-ngược; G2 (reverse BR) không thuộc phạm vi này nhưng defaults registry sinh ra ở đây sẽ dùng lại được cho G2.
- `llmwiki/html/140726-br-dieu-kien-day-chuyen.html` (commit c9dc13d) — **bảng 26 điều kiện mặc định** của dây chuyền, kèm phán quyết council: vá G1 phải là **checksum hợp đồng** (mọi field S1–S10 có clause đối ứng). Bảng này hiện chỉ là HTML người đọc — chưa máy nào ăn được; proposal này chuyển nó thành registry máy-đọc-được.
- [[140726-atomic-task-graph-distill]] — issue distill paper ATG (arXiv 2607.01942): plan = DAG atomic task; issue đã khuyến nghị "mảnh 1 (DAG hoá frame) gần như chắc chắn đáng làm, mảnh 2–3 cân với limitations". Proposal này lấy đúng mảnh 1.
- Nguồn ngoài đã tra trong phiên: [GitHub spec-kit](https://github.com/github/spec-kit) — flow constitution → specify → plan → tasks; mỗi phase một artifact Markdown nuôi phase sau; constitution = bộ nguyên tắc bất biến của project. Ăn khớp 1:1 với chuỗi spec-template → BR → PLAN → frames của ta; thứ đáng KÉO là **convention field chuẩn** của họ, không phải CLI của họ.

## Global constraints

Chép nguyên văn từ wiki/ADR/policy — mọi task bên dưới ngầm mang theo section này:

- **ADR-004 (file-first, opt-in):** "thứ gì auto-fire/tự-bơm context vào MỌI phiên chỉ được phục vụ dự án hiện tại; context nội-bộ-framework phải opt-in qua skill gọi chủ động." → `--proactive` là **flag của lệnh user gọi**, tuyệt đối không watcher/daemon/hook trên `raw/`.
- **Kỷ luật lens-fill ([[050726-ralph-interview-pipeline]] · Rủi ro):** "mọi mục lens điền BẮT BUỘC `verified: false` + hiện trong bảng 'Giả định đang gánh'; không bao giờ trộn lẫn với câu trả lời thật của user." → áp cho CẢ ba tầng fill mới (default / spec-kit / lens).
- **Carve-out KHÔNG được tự điền (CLAUDE.md + propose R7-n):** cơ chế xác thực/phân quyền · lưu trữ dữ liệu (lưu gì, ở đâu, bao lâu, ai đọc) · tiền/thanh toán/hạn mức · hệ quả pháp lý/tuân thủ · ranh giới tin cậy. Field S1–S10 rơi vào nhóm này luôn thành **câu hỏi thật** cho user.
- **Trần 5 câu hỏi** khi interview chạy, chọn theo Impact × Uncertainty (skill propose, mục "Tự điền hay hỏi").
- **Frame schema v0 (council 031/032):** tái dùng `frame-template` + `frame-lint`, KHÔNG tạo schema mới — thêm field vào frontmatter frame phải qua frame-lint.
- **R15:** commit không có AI-attribution. **Prose rule (CLAUDE.md 2026-06-27):** file người đọc viết văn xuôi đầy đủ. **PATH:** máy chỉ có `python3`, không có `python`.

## Non-goals

- **Không watcher/daemon tự chạy khi file xuất hiện trong `raw/`** — "proactive" nghĩa là *tự điền thay vì hỏi*, không phải *tự khởi động không ai gọi* (vi phạm ADR-004).
- **Không cài specify CLI của spec-kit** — chỉ distill convention của họ vào registry của ta (kiểu absorb: KÉO NGOÀI tri thức, không kéo tool).
- **Không làm ATG mảnh 2–3** (localized repair, subgraph reuse) — đã có issue riêng [[140726-atomic-task-graph-distill]] với tiêu chí hoàn thành riêng; mảnh 1 ở đây là nền cho chúng.
- **Không đụng orca orchestration**, không tái hiện benchmark của paper.
- **Không auto-approve BR** — gate người duyệt ở cuối compile vẫn nguyên (proactive fill giảm số câu hỏi, không bỏ cổng duyệt).

## Approaches

Ba phương án khác nhau về bản chất — chọn A:

**A — HÒA TAN: flag `--proactive` trên `/br interview` hiện có + fill-chain 4 tầng (CHỌN).**
Gap-diff xong, mỗi required field `missing` đi qua chuỗi: ① default của loop (`br/defaults.yaml` — machine-hoá bảng 26 điều kiện) → ② convention spec-kit (cùng registry, nguồn `spec-kit`) → ③ lens-fill sẵn có → ④ không tầng nào điền được HOẶC field thuộc carve-out → thành câu hỏi thật (trần 5). Mỗi field điền ghi `filled_by` + `verified: false`.
*Được:* tái dùng toàn bộ E1–E6, không schema mới, không hook, kỷ luật provenance sẵn có gánh luôn tầng mới. *Mất:* vẫn cần user gọi lệnh (đúng ADR-004 nên coi là feature, không phải mất).

**B — Watcher tự động trên `raw/`** (proactive theo nghĩa đen: thả file là pipeline tự chạy đến BR).
*Được:* trải nghiệm "zero lệnh". *Mất:* vi phạm thẳng ADR-004 (auto-fire); lỗi giữa chừng không ai đứng cạnh; chi phí chạy ngầm không kiểm soát. **Loại.**

**C — KÉO NGOÀI toàn phần: dùng spec-kit thật làm engine** (map S1–S10 sang spec.md của specify CLI, để spec-kit sinh plan/tasks).
*Được:* đứng trên vai tool được maintain. *Mất:* mất provenance từng field (thứ cả dây chuyền đứng trên), mất frame-lint/6 phanh, lock schema ngoài, thêm dependency nặng. **Loại — chỉ kéo convention của họ (đã nằm trong A).**

## Plan

- [ ] **Task 1 — Registry mặc định `br/defaults.yaml`:** chuyển bảng 26 điều kiện (HTML c9dc13d) thành YAML máy-đọc: mỗi entry `{field: S*.*, value, source: loop-26|spec-kit, note}`; distill thêm convention field chuẩn từ spec-kit (constitution principles → S7/S8, spec template fields → S4/S9/S10); `schema_version: 0`.
- [ ] **Task 2 — Fill-chain trong `/br interview --proactive`:** sau gap-diff, chạy chuỗi default → spec-kit → lens cho field missing; carve-out và field không tầng nào điền được → câu hỏi thật (chọn top-5 theo Impact × Uncertainty); answers.md ghi `filled_by: default:<id>|spec-kit:<id>|lens-<tên>` + `verified: false` từng mục; STOP cho user duyệt trang câu hỏi rút gọn.
- [ ] **Task 3 — Compile nhận provenance mới + checksum hợp đồng (vá G1):** bảng "Giả định đang gánh" trong BR.md nhóm theo nguồn fill (default / spec-kit / lens); compile **FAIL** nếu một required field S1–S10 không có clause đối ứng trong BR (checksum hợp đồng theo phán quyết council c9dc13d).
- [ ] **Task 4 — DAG hoá frame (ATG mảnh 1):** `/br slice` sinh `depends_on: [frame-id,…]` trong frontmatter từng frame; `frame-lint` reject chu trình + depends_on trỏ frame không tồn tại; `/br status` (line-status.html) vẽ quan hệ phụ thuộc thay vì danh sách phẳng.
- [ ] **Task 5 — Chạy thật end-to-end + register:** chạy trên `br/memos` (raw sẵn có): đo số câu hỏi user phải trả lời trước/sau khi bật `--proactive`, đối chứng không field carve-out nào bị auto-fill; register (mirror + LOOP_MAP + CAPABILITIES) + `medic --ci` + cập nhật ledger GH#15.

## Requirements (FR)

- **FR-001**: `/br interview --proactive` PHẢI tự điền mọi required field `missing` theo đúng thứ tự thang raw-extract → default (loop-26) → spec-kit → lens, và ghi provenance (`filled_by`, `verified: false`) cho từng field được điền.
- **FR-002**: Field thuộc nhóm carve-out (xác thực/phân quyền, lưu trữ dữ liệu, tiền, pháp lý, ranh giới tin cậy) KHÔNG BAO GIỜ được auto-fill — luôn xuất hiện thành câu hỏi thật cho user, bất kể registry có giá trị default hay không.
- **FR-003**: Số câu hỏi thật gửi user mỗi vòng interview PHẢI ≤ 5, chọn theo Impact × Uncertainty; các field bị cắt khỏi top-5 rơi về fill-chain và được đánh dấu assumed.
- **FR-004**: `br/defaults.yaml` PHẢI versioned (`schema_version`), mỗi entry có `source`; cả interview lẫn compile đọc cùng một registry này.
- **FR-005**: `/br compile` PHẢI fail (exit ≠ 0, thông báo field nào) khi một required field S1–S10 không có clause đối ứng trong BR.md; bảng "Giả định đang gánh" nhóm theo nguồn fill.
- **FR-006**: Frame sinh từ `/br slice` PHẢI có `depends_on` tường minh; `frame-lint` PHẢI reject đồ thị có chu trình hoặc cạnh trỏ frame không tồn tại; `/br status` PHẢI hiển thị được quan hệ đó.

## Success criteria (SC)

- **SC-001**: Từ một folder raw thật, user đi từ "thả tài liệu" đến BR.md sẵn-duyệt mà chỉ phải trả lời **tối đa 5 câu hỏi** (hiện tại: điền tay toàn bộ answers.md). Bằng chứng: log lần chạy `br/memos` ở Task 5, đếm câu hỏi trước/sau.
- **SC-002**: Người duyệt nhìn BR.md phân biệt được **trong dưới 1 phút** đâu là lời user, đâu là máy điền và điền từ nguồn nào (default / spec-kit / lens). Bằng chứng: bảng "Giả định đang gánh" nhóm theo nguồn, kiểm bằng mắt trên BR mẫu.
- **SC-003**: Khi một frame fail giữa chuỗi, người vận hành nhìn `/br status` biết ngay những frame nào bị ảnh hưởng theo cạnh phụ thuộc mà không phải đọc code. Bằng chứng: screenshot line-status.html có DAG trên lần chạy mẫu.
- **SC-004**: Không một field carve-out nào bị auto-fill trong lần chạy mẫu. Bằng chứng: grep log fill-chain đối chứng danh sách carve-out — 0 khớp.

## Assumptions

- (default) Tên flag là `--proactive`; không đổi tên mode hiện có.
- (default) Registry đặt tại `br/defaults.yaml`, `schema_version: 0`; project khác dùng qua template pull như các file `br/` khác.
- (default) Spec-kit chỉ được distill convention (một lần, vào registry) — không thêm dependency, không theo dõi upstream tự động; khi spec-kit đổi, cập nhật registry tay.
- (default) ATG chỉ lấy mảnh 1 (DAG hoá), theo đúng khuyến nghị trong [[140726-atomic-task-graph-distill]]; mảnh 2–3 để issue đó quyết sau khi mảnh 1 chạy thật.
- (default) Project mẫu để chạy thật là `br/memos` (đã có raw + frames từ các phiên trước).
- Không có mục `[CẦN LÀM RÕ]` — yêu cầu không chạm auth/tiền/pháp lý ở tầng thiết kế dây chuyền; carve-out ở đây là **luật chặn fill**, không phải quyết định cần user trả lời trước.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| Task 1 — defaults.yaml registry | Claude Code | Chắt lọc 26 điều kiện + spec-kit cần phán đoán (điều kiện nào máy ăn được), không phải copy cơ học | pending |
| Task 2 — fill-chain interview | Claude Code | Architectural decision (thang ưu tiên, carve-out, Impact × Uncertainty) | pending |
| Task 3 — compile + checksum G1 | Claude Code | Đụng kỷ luật provenance — sai ở đây là xanh giả cấp specs | pending |
| Task 4 — slice DAG + frame-lint | Claude Code | Sửa validator dùng chung (frame-lint) — cross-cutting | pending |
| Task 5 — chạy thật + register | Claude Code | Cần đọc kết quả và phán quyết đạt/không | pending |
| Render HTML companion | OpenCode `big-pickle` | Render cơ học từ Render brief — theo bảng chi phí; watchdog 90s, fallback Claude | pending |

Tất cả task chính dồn về Claude vì cả 5 đều đụng kỷ luật provenance hoặc validator dùng chung — đúng tiêu chí "architectural decisions → Claude" trong bảng phân công chi phí; phần boilerplate thuần (render HTML) đã tách cho CLI rẻ.

**Sequence diagram:** [140726-br-proactive-fill-seq.html](../../../html/140726-br-proactive-fill-seq.html)

## Render brief

Mỗi task một diagram; lifelines chung: `User` · `br CLI` · `raw/` · `defaults.yaml` · `spec-filled/answers` · `BR.md` · `frames/`.

**Task 1 — defaults.yaml registry**
Steps: ① [legacy] Bảng 26 điều kiện tồn tại dạng HTML người đọc (c9dc13d) → ② [add] Distill thành `br/defaults.yaml` entry `{field, value, source: loop-26}` → ③ [add] Bổ sung convention spec-kit (constitution→S7/S8, spec fields→S4/S9/S10, source: spec-kit) → ④ [add] `schema_version: 0` + selftest đọc lại được.
Prose: Bảng 26 điều kiện mặc định hiện chỉ tồn tại trong một trang HTML mà con người đọc — không máy nào trong dây chuyền ăn được nó, nên mỗi lần agent cần một giá trị mặc định là một lần đoán lại từ đầu. Task này chuyển bảng đó thành một registry YAML có version, mỗi entry ghi rõ nó áp cho field nào của spec S1–S10 và đến từ nguồn nào (bảng 26 của loop hay convention của GitHub spec-kit). Rủi ro chính là distill sai ngữ nghĩa một điều kiện — vì vậy mỗi entry giữ `note` trỏ ngược về nguồn để người review đối chiếu được.

**Task 2 — fill-chain interview --proactive**
Steps: ① [legacy] `/br interview` extract raw → spec-filled, gap-diff ra field missing → ② [add] Với mỗi field missing: tra defaults.yaml (loop-26) → ③ [add] miss thì tra convention spec-kit → ④ [add] miss nữa thì lens-fill → ⑤ [block] field carve-out (auth/dữ liệu/tiền/pháp lý/trust) KHÔNG vào fill-chain — thành câu hỏi thật → ⑥ [add] chọn top-5 câu hỏi theo Impact × Uncertainty, STOP chờ user.
Prose: Đây là trái tim của proposal. Thay vì sinh một bộ câu hỏi dài bắt user điền toàn bộ, mode proactive chỉ hỏi những gì thật sự phải hỏi: mỗi field thiếu đi qua thang bốn tầng, và chỉ những field không tầng nào trả lời được — hoặc thuộc nhóm carve-out mà một mặc định sai là hỏng kiến trúc — mới đến tay user, tối đa năm câu. Mọi giá trị máy điền đều mang `filled_by` và `verified: false`, không bao giờ trộn lẫn với lời user thật. Nhánh chặn quan trọng nhất là carve-out: dù registry có sẵn giá trị, field xác thực hay lưu trữ dữ liệu vẫn bị đẩy thành câu hỏi thật, vì đó là chỗ ảo giác an toàn đắt nhất.

**Task 3 — compile + checksum hợp đồng**
Steps: ① [legacy] `/br compile` đọc answers.md → BR.md có clause_id → ② [add] Bảng "Giả định đang gánh" nhóm theo nguồn fill (default / spec-kit / lens) → ③ [block] Checksum hợp đồng: required field S1–S10 nào không có clause đối ứng → compile FAIL, in tên field → ④ [add] pass thì BR sẵn-duyệt.
Prose: Council c9dc13d đã phán tầng báo cáo của dây chuyền "đang bán ảo giác an toàn" và yêu cầu vá G1 bằng checksum hợp đồng. Khi máy được quyền tự điền field, rủi ro field rơi lặng lẽ giữa đường còn cao hơn — vì vậy compile giờ là cổng cứng: mọi required field của spec phải truy được về một clause trong BR, thiếu một field là fail kèm tên field, không có chuyện "compile xong mà hợp đồng thủng". Bảng giả định nhóm theo nguồn để người duyệt thấy ngay mình đang gánh bao nhiêu cược từ máy, cược nào từ default của loop, cược nào từ chuẩn ngoài, cược nào từ lens.

**Task 4 — slice DAG (ATG mảnh 1)**
Steps: ① [legacy] `/br slice` cắt BR thành frames danh sách phẳng → ② [add] Sinh `depends_on: [frame-id,…]` từ quan hệ clause (frame đọc output frame khác → cạnh phụ thuộc) → ③ [block] `frame-lint` reject chu trình / cạnh trỏ frame không tồn tại → ④ [add] `/br status` vẽ DAG: frame fail thì highlight vùng hạ nguồn bị ảnh hưởng.
Prose: Đây là mảnh rẻ nhất của paper Atomic Task Graph và là mảnh issue distill đã đánh giá "gần như chắc chắn đáng làm": phụ thuộc giữa frame đang nằm ẩn trong đầu người slice, giờ được mã hoá tường minh vào frontmatter. Cái lợi tức thì không phải chạy song song (quy mô chục frame chưa cần) mà là khoanh vùng: một frame fail, nhìn đồ thị biết ngay những frame hạ nguồn nào không nên chạy tiếp và frame nào vô can. frame-lint gác để đồ thị luôn là DAG hợp lệ — chu trình hay cạnh mồ côi bị chặn từ lúc slice, không đợi đến lúc run.

**Task 5 — chạy thật end-to-end**
Steps: ① [add] Chạy `--proactive` trên `br/memos` (raw sẵn) → ② [add] Đo: số câu hỏi user phải trả lời trước/sau → ③ [block] Đối chứng log: field carve-out bị auto-fill = 0, khác 0 là fail → ④ [add] Register skill + medic --ci + ledger GH#15.
Prose: Lần chạy thật là bằng chứng cho cả bốn SC: đếm được số câu hỏi giảm còn bao nhiêu, nhìn được bảng giả định trên BR thật, thấy được DAG trên line-status, và grep được log để chứng minh không field nhạy cảm nào bị máy điền trộm. Chạy trên br/memos vì project này đã có tài liệu thô lẫn frames từ các phiên trước — so sánh trước/sau có đối chứng thật thay vì demo dựng sẵn.

## Self-review

1. **Phủ yêu cầu:** "tự nhận documents" → Task 2 (extract raw vẫn là đầu vào, proactive là flag chủ động — ADR-004 ghi rõ ở Non-goals); "tự bổ sung bằng default của loop" → Task 1+2 (bảng 26 → registry → fill-chain); "fill theo chuẩn github/spec-kit" → Task 1 (distill convention) + Non-goals (không cài CLI); "quy trình Atomic Task Graph" → Task 4 (mảnh 1) + Non-goals (mảnh 2–3 ở issue riêng). Đủ, không yêu cầu nào về hai task.
2. **Quét placeholder:** không còn TBD/TODO/"xử lý phù hợp"; giá trị nào chưa chốt đều nằm ở `## Assumptions` với tag `(default)`.
3. **Nhất quán tên-kiểu:** thống nhất `br/defaults.yaml` (không lúc registry.yaml lúc defaults.yml), `--proactive`, `depends_on`, `filled_by`, `verified: false` xuyên suốt draft và render brief.

## Origin

- **Draft:** `wiki/sources/draft/140726-br-proactive-fill.md`
- **Nguồn:** phiên 2026-07-14, user hỏi qua `/orca-workflow`: proactive loop tự nhận documents, tự fill bằng default của loop / chuẩn spec-kit / quy trình ATG. Wiki đã query: [[050726-ralph-interview-pipeline]] · [[120726-pipeline-friction]] · [[120726-pipeline-gaps-raised]] · [[140726-atomic-task-graph-distill]] · bảng 26 điều kiện (c9dc13d). Nguồn ngoài: arXiv 2607.01942 · github.com/github/spec-kit.
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
