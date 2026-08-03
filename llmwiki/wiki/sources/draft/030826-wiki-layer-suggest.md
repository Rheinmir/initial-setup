---
type: draft
title: "wiki-layer-suggest — heuristic report gợi ý layer: cho dự án cũ, không tự ghi"
status: implemented
tags: [wiki-core, taxonomy, layer, migration, operationalizes, heuristic]
timestamp: 2026-08-03
task: T-260803-01
---

# 030826-wiki-layer-suggest — heuristic report gợi ý `layer:`, không tự ghi

**Status:** implemented (T1-T3 committed 2026-08-03)

**Sequence diagram:** [030826-wiki-layer-suggest-seq.html](../../../html/030826-wiki-layer-suggest-seq.html)

## What
Nối tiếp GH#93 (`[[010826-wiki-mental-model-taxonomy]]`): field `layer: fact|mental-model` hiện là opt-in thuần tuý — dự án cũ có wiki lớn (~2.500 node) không có cách nào biết node nào NÊN gắn layer gì mà không đọc tay từng file. User hỏi trực tiếp: có script nào tự cào wiki cũ và gợi ý migrate sang chuẩn mới không? Câu trả lời hiện tại là KHÔNG — đây là SPEC cho công cụ đó, dạng **report-only** (không tự ghi frontmatter), vì phân loại fact/mental-model là phán đoán ngữ nghĩa, không phải sự thật suy được chắc chắn như `touches` (path tồn tại trên đĩa).

## Context
- **`[[010826-wiki-mental-model-taxonomy]]`** (SPEC GH#93 vừa merge) — Non-goals của SPEC đó nói rõ "KHÔNG backfill toàn bộ ~2.500+ node" nhưng KHÔNG cấm một công cụ GỢI Ý (report), chỉ cấm auto-ghi hàng loạt. SPEC này lấp đúng khoảng trống đó, không mâu thuẫn với quyết định trước.
- **`[[wiki-core-relations]]`** — bài học "suy đừng cất": `touches` dập tay 1 lần rồi đóng băng vì đó là suy diễn CHẮC CHẮN bị đối xử như phán đoán CON NGƯỜI. Layer thì NGƯỢC LẠI — nó vốn dĩ LÀ phán đoán con người (không có "đúng" duy nhất fact hay mental-model cho một trang mơ hồ), nên báo cáo bắt buộc phải tách rõ "máy đoán" khỏi "người xác nhận" — không được để giá trị máy đoán trông giống hệt giá trị người đã duyệt.
- **Feedback trực tiếp trong phiên này (2026-08-03):** dữ liệu nào không tự-fill-chắc-chắn-bằng-code được thì phải đánh dấu ngày cập nhật + thẻ disclaimer "được điền bởi gì" ngay tại thời điểm điền, để sau này một vòng suy luận tốt hơn (người, hoặc agent khác) tìm thấy và ghi đè lại được. Đây là ràng buộc THIẾT KẾ chính của SPEC này, không phải chi tiết phụ.

## Global constraints
- Không tự ghi `layer:` vào bất kỳ file wiki nào — chỉ in báo cáo (stdout hoặc file report), người/agent quyết định chấp nhận gợi ý nào.
- Field nào do heuristic điền (không phải người tay gõ) PHẢI đi kèm `layer_source: heuristic` + `layer_date: YYYY-MM-DD` trong CHÍNH gợi ý in ra (để nếu người copy-paste vào frontmatter, 2 field kèm theo đi cùng, không tách rời).
- KHÔNG thêm dependency mới — Python 3 stdlib, mirror style của `wiki-graph.py`/`build-wiki-graph.py` đã có (đọc frontmatter bằng regex, không cần PyYAML).
- Tự dùng được ở dự án downstream (không phụ thuộc file chỉ có trong repo framework) — đặt trong `harness/scripts/` (tầng phân phối), không phải `fdk/tools/` (tầng chỉ-dev-framework, ADR-004).
- `llmwiki/CLAUDE.md`: `## Context` viết văn xuôi đầy đủ; mọi wiki file mới có `## Origin`; cập nhật `index.md`+`log.md`.

## Non-goals
- **Không** tự động ghi `layer:` vào file — mọi thay đổi frontmatter là hành động NGƯỜI/agent làm tay sau khi đọc report, script không có quyền write.
- **Không** dùng LLM/gọi API bên ngoài để phân loại — heuristic thuần dựa trên tín hiệu có sẵn (type:, tên section, độ dài, có/không tham chiếu skill) để chạy 0-token, tất định, offline. Phân loại bằng LLM (chính xác hơn) là hướng nâng cấp sau, có trigger riêng (xem Assumptions).
- **Không** đảm bảo heuristic đúng 100% — đây là gợi ý, sai một vài trang là chấp nhận được vì người review trước khi ghi, khác hẳn `touches` (suy sai = sai luôn, không ai review).
- **Không** sửa cơ chế `operationalizes_targets()`/build-wiki-graph.py đã có — công cụ này CHỈ tạo report giúp điền `layer:`, không đụng logic suy cạnh đã build ở GH#93.

## Approaches

**Phương án A — Heuristic tất định dựa trên tín hiệu có sẵn, in report kèm confidence (chọn).** Với mỗi node CHƯA có `layer:`: nếu `type: source` (thường là auto-distill log, ghi lại sự kiện đã xảy ra) → gợi ý `fact`, confidence=medium; nếu `type` in (`concept`,`draft`,`architecture`) VÀ thân bài có section `## Approaches`/`## Trade-off`/`## Non-goals` (dấu hiệu phân tích/diễn giải) → gợi ý `mental-model`, confidence=medium; còn lại → KHÔNG gợi ý (confidence=low, bỏ qua, không ép). Ưu điểm: 0-token, tất định, chạy được offline trên dự án downstream không cần API key. Nhược điểm: heuristic thô, bỏ sót nhiều trang mơ hồ (chấp nhận — đây là gợi ý, không phải phán quyết).

**Phương án B — Dùng LLM (agent) đọc từng trang, phân loại chính xác hơn.** Chính xác hơn A đáng kể, nhưng: (1) tốn token tuyến tính theo số node (~2.500 node = chi phí thật, không 0-token), (2) không chạy được offline/CI, (3) là bậc thang cao hơn Meadows-leverage không cần thiết khi heuristic rẻ đã đủ để KHỞI ĐỘNG việc gắn layer (mục tiêu là có điểm bắt đầu, không phải độ chính xác tối đa ngay từ v0.1). Giữ làm hướng nâng cấp — xem Assumptions.

**Phương án C — Không làm gì, để opt-in hoàn toàn thủ công (giữ nguyên hiện trạng).** Đây là trạng thái TRƯỚC SPEC này. Bác vì user đã hỏi thẳng và xác nhận muốn có công cụ — im lặng nghĩa là dự án cũ mãi mãi 0% node có layer, taxonomy GH#93 xây xong không ai dùng.

## Requirements (FR)

**FR-001**: Script `harness/scripts/wiki-layer-suggest.py` PHẢI quét mọi node wiki (6 `CONTENT_DIRS` chuẩn) CHƯA có `layer:` trong frontmatter, áp heuristic Phương án A, in ra report gồm: đường dẫn file, `type:` hiện có, layer gợi ý, confidence, lý do (1 câu).

**FR-002**: Script TUYỆT ĐỐI KHÔNG ghi file — chỉ in report ra stdout (mặc định) hoặc `--out <file>` (tuỳ chọn, vẫn chỉ là văn bản report, không phải frontmatter thật).

**FR-003**: Mỗi dòng gợi ý trong report PHẢI kèm sẵn snippet copy-paste được gồm cả 3 dòng: `layer: <giá trị>`, `layer_source: heuristic`, `layer_date: <ngày chạy script, thật, không placeholder>` — để nếu người chấp nhận gợi ý, dán cả 3 dòng thì bản ghi đã tự mang dấu "máy đoán, ngày nào" mà không cần nhớ thêm.

**FR-004**: `fdk/tools/build-wiki-graph.py` (hoặc script khác đọc `layer:`) KHÔNG được coi `layer_source`/`layer_date` là bắt buộc — node có `layer:` do NGƯỜI tự tay gõ (không qua script) vẫn hợp lệ, không cần 2 field kèm theo (chỉ bắt buộc khi giá trị TỪ heuristic).

**FR-005**: Script PHẢI chạy được ở dự án downstream chỉ có `harness/` + `llmwiki/` (không có `fdk/`) — không import bất kỳ module nào từ `fdk/`.

## Success criteria (SC)

**SC-001**: Chạy script trên wiki hiện có của repo này (~241 node) — report liệt kê được ít nhất một số node `type: source` (auto-distill) với gợi ý `fact`, và một số node `type: concept`/`draft` có section Approaches/Trade-off với gợi ý `mental-model` — người đọc report hiểu ngay "trang nào nên gắn gì" mà không cần tự đọc lại 241 file.

**SC-002**: Sau khi người copy 3 dòng gợi ý (layer/layer_source/layer_date) vào một file thật, build lại `wiki-graph.html` — badge layer hiện đúng (tái dùng cơ chế GH#93, không cần sửa gì thêm).

**SC-003**: 6 tháng sau, một người khác đọc frontmatter thấy `layer_source: heuristic` + `layer_date: 2026-08-03` trên một node — biết ngay giá trị này CHƯA được người xác nhận, có thể tự tin ghi đè nếu review thấy sai, không cần hỏi lại ai đã gõ dòng đó.

## Assumptions

- Heuristic set tín hiệu ban đầu chỉ 2 luật (source→fact, concept/draft+section-phân-tích→mental-model) — **(default, find-out-later)**: chưa đo trên dữ liệu thật tỷ lệ đúng/sai; mở rộng luật khi có phản hồi từ report thật đầu tiên.
- Nâng cấp Phương án B (LLM phân loại) — **(default, find-out-later → cần trigger cụ thể, ví dụ heuristic sai >30% trên report đầu)**: chưa build trong bản này, đúng Non-goals.
- File output mặc định là stdout, không phải file cố định trong wiki — **(default)**: người dùng tự `> report.txt` nếu muốn lưu, tránh sinh thêm 1 artefact cần track/gitignore.

## Plan

- [x] **T1 — Viết `harness/scripts/wiki-layer-suggest.py`: đọc frontmatter (mirror regex của `wiki-graph.py`), áp 2 luật heuristic, in report kèm 3-dòng snippet copy-paste + `layer_source`/`layer_date` thật.** Verify: SC-001, FR-001-003.
- [x] **T2 — Self-test tất định (`--self-test`, mirror style `wiki-graph.py`): wiki tạm có 1 node `type: source`, 1 node `type: concept` có `## Approaches`, 1 node mơ hồ (không heuristic nào khớp) — xác nhận đúng 2 gợi ý ra, 1 node bị bỏ qua.** Verify: FR-001, FR-002 (không file nào bị ghi trong quá trình test).
- [x] **T3 — Chạy thật trên `llmwiki/wiki` của repo này, đọc report, chấp nhận 1-2 gợi ý bằng tay (dán 3 dòng), build lại `wiki-graph.html` xác nhận badge hiện.** Verify: SC-002, SC-003.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Heuristic + format report cần đúng ngay, quyết định tín hiệu nào đáng tin cậy là phán đoán thiết kế | pending |
| T2 | Claude | Self-test cho logic có nhánh (3 case) cần đúng, không phải thao tác lặp mẫu | pending |
| T3 | Claude | Chạy thật + đọc report + tự quyết định chấp nhận gợi ý nào cần hiểu ngữ cảnh nội dung | pending |

## Self-review

**Phủ yêu cầu.** Câu hỏi gốc của user ("script tự cào và migrate") → FR-001 (cào/quét) + FR-002 (KHÔNG tự migrate, chỉ report) trả lời đúng bằng THIẾT KẾ, không phải bằng cách lờ đi nửa câu hỏi. Yêu cầu giữa phiên (ngày + disclaimer + ghi-đè-được) → FR-003 + FR-004 + SC-003.

**Quét placeholder.** Không còn việc để-đó-chưa-làm; heuristic cụ thể 2 luật, report format cụ thể 3 dòng.

**Nhất quán tên-kiểu.** `layer_source`/`layer_date` dùng đúng 2 tên xuyên suốt FR-003/FR-004/SC-003, không đổi thành `source_type`/`generated_at` hay biến thể khác giữa chừng.

## Notes
- [[010826-wiki-mental-model-taxonomy]] — SPEC gốc định nghĩa `layer:`/`operationalizes`, Non-goals của nó chừa đúng khoảng trống SPEC này lấp.
- [[wiki-core-relations]] — nguồn nguyên tắc "suy đừng cất", áp dụng NGƯỢC ở đây (layer là phán đoán người, không phải suy chắc chắn — nên phải đánh dấu rõ, khác touches).

## Origin
- **Source:** user hỏi trực tiếp trong phiên (2026-08-03) "tính tới trường hợp dự án cũ có script nào tự cào và migrate sang theo chuẩn mới không" + feedback giữa phiên về đánh dấu ngày/disclaimer cho dữ liệu heuristic.
- **Concept nền:** `[[010826-wiki-mental-model-taxonomy]]` · `[[wiki-core-relations]]`
- **Task:** `T-260803-01`
- **Draft:** `wiki/sources/draft/030826-wiki-layer-suggest.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
