---
type: draft
title: "Decision-anchoring: neo quyết định vào symbol, liveness suy từ code-graph"
status: implemented
tags: [decision-anchoring, code-graph, mechanisms-yaml, source-of-truth, why]
timestamp: 2026-07-21
task: T-260721-03
---

# Decision-anchoring: neo quyết định vào symbol, liveness suy từ code-graph

**Status:** implemented (T1-T9 committed 2026-07-21)

Yêu cầu gốc, một câu: từ một dòng code, phải tìm được WHY của nó; code đổi thì WHY phải tự báo cần xác nhận lại; toàn bộ chuyện đó phải suy ra được bằng máy, không phải nhớ tay.

**Sequence diagram:** [210721-decision-anchoring-seq.html](../../../html/210721-decision-anchoring-seq.html)

> Ghi chú phạm vi: draft này chưa promote thành `concepts/decision-anchoring.md` — đúng luật `llmwiki/CLAUDE.md`: *"Wiki entries are only created AFTER code is committed — never during proposal or planning."* Toàn bộ nguyên lý nằm ở `## Context`/`## Approaches` dưới đây; việc promote là chính task cuối của `## Plan`.

## Context

**Tiền lệ đã chạy sống — không phải ý tưởng mới, là tổng quát hoá.** `harness/mechanisms.yaml` (từ ADR-001, council-025) đã làm đúng hình dạng này ở mức thô: mỗi mục có `id` + `desc` (WHY, prose người viết) + `live_probe` (path repo-relative PHẢI tồn tại — anchor). `medic` chạy probe `narrative`: một cơ-chế LIVE mà `live_probe` biến mất khỏi đĩa → *"manifest NÓI DỐI"*. Đo được sống hôm nay: phiên này chính probe đó bắt được `harness-local/` bị dời đi (`live_probe: harness-local` trỏ vào chỗ trống), chặn medic, và chỉ đúng chỗ hỏng. 23 cơ-chế khác đang "LIVE đều có mặt" — verify chạy `medic --ci` ngay lúc viết draft này. Đây là bằng chứng chạy thật cho nguyên lý cốt lõi: *neo một câu WHY vào một đường dẫn tồn tại-được-kiểm, và để máy tự phát hiện khi neo gãy.*

Giới hạn của tiền lệ, đúng chỗ đề xuất này mở rộng: `live_probe` neo ở mức **file/dir**, không phải symbol — sửa bất kỳ dòng nào trong `session_start.py` không làm neo `orientation` gãy hay báo cần xác nhận lại, dù cơ chế bên trong đổi hoàn toàn. Và nó chỉ phủ một loại quyết định (runtime mechanism) — ADR, ghi chú feedback, quyết định thiết kế nằm ngoài `mechanisms.yaml` không có neo nào cả.

**Bốn cách ngành đang giải, đều dừng ở WHAT.** Khảo sát trong phiên (WebSearch, có trích dẫn): docs-as-code (sửa docs+code cùng PR — kỷ luật người, không cưỡng chế máy, im lặng với code cũ); sinh docs từ spec máy-đọc (OpenAPI → reference — chỉ sinh được thứ có hình dạng khai báo, không có khái niệm WHY); Live-Docs/event-driven (nghe code đổi → mở review — gần nhất, nhưng không phân biệt gãy-đúng với gãy-nhiễu, "mở review" không định nghĩa ai nhận); code knowledge graph (blast-radius từ code thật — trả lời "cái gì gọi cái gì", không trả lời "vì sao nên gọi vậy"). Kiểm cả hướng triệt để nhất — `vercel-labs/zerolang` (agent-first, graph nằm ngay trong compiler, không phải lớp phủ) — đọc thẳng README: graph của họ chứa *"symbols, node IDs, graph hashes, types, effects, ownership facts, capabilities, imports, call edges, and target facts"*, không một trường giữ lý do. Ngay cả lab đi xa nhất cũng dừng đúng chỗ bốn cách kia dừng.

Bài học ngành, trích gần nguyên văn từ khảo sát về ADR sống sót 5 năm: *"những kho ADR còn phục vụ team sau 5 năm có owner trên mỗi record, supersession links trỏ cả hai chiều, named drift triggers, và một review cadence có người thật sự giữ."* Đối chiếu: owner + supersession đã có (lớp AUTHORED, phán đoán người, xem [[adapt-modes]]); *"named drift trigger"* ngành đặt **tay**, đề xuất này suy **từ code-graph**; *"review cadence người giữ"* ngành làm **việc-nhớ**, đề xuất này biến thành **báo cáo tất định** qua `/lint`.

**Nền kỹ thuật đã sẵn, không xây engine mới.** `touches` (`build-wiki-graph.py:156`) đã suy quan hệ trang↔file từ path trong nội dung — mức file. `map_suspects` (`wiki-sync.py:114`) đã làm chiều code→wiki, thiên recall, chỉ cố vấn. Code-graph vừa được vệ sinh xong trong phiên trước (dedupe + nhãn project + trần) — tiền đề bắt buộc để neo mức-symbol không nhập nhằng tên trùng (`get_callers("save")` từng trả 65 kết quả lẫn lộn, giờ 5 kết quả sạch có nhãn project). `dep-health.py` đã có nguyên tắc *"quảng cáo một năng lực = phải THĂM DÒ, không phải kiểm tồn tại"* — áp thẳng vào cách xác định LIVE.

**Ba dạng biên cho "đứa ngoài hạ tầng"** (đã thảo luận trong phiên, chưa ghi thành văn bản): HÒA TAN (code trong repo, index được) → neo symbol trực tiếp; KÉO NGOÀI có version (research_reach, code-graph sau khi thành KÉO NGOÀI) → neo vào **pin** (`source+commit+sha`), gãy nghĩa là upstream vượt pin; KÉO NGOÀI không index được → neo vào **adapter** — `dep-health.py`/`code_graph_keeper.py` là ví dụ sống, chúng đã là biên nơi code-graph (ngoài) bước vào framework. Sàn trung thực: WHY thuần phán đoán người (không code nào), ở lại AUTHORED-không-neo, chỉ date-được không prune-tự-động-được.

## Global constraints

- `llmwiki/CLAUDE.md`: *"Wiki entries are only created AFTER code is committed — never during proposal or planning."* — áp dụng trực tiếp, xem ghi chú phạm vi ở đầu draft.
- `llmwiki/CLAUDE.md`, 5-Why: *"Tìm HỘI TỤ trước khi sửa... nhiều cái đổ về một root thì sửa root một lần."* — `harness-local` drift, `p-41`, và giới hạn mức-file của `mechanisms.yaml` đổ về cùng một root: neo tồn tại nhưng không đủ mịn.
- `dep-health.py` (nguyên tắc đã ghi trong code): *"quảng cáo một năng lực = phải THĂM DÒ nó, không phải kiểm sự tồn tại của nó."*
- Fail-open tuyệt đối ở hook; fail-CLOSED ở gate (`medic`, `/lint` báo cáo không chặn — khớp pattern draft-age, unknown-ledger đã có).
- `harness/travel-policy.yaml`: mọi engine mới phải khai đúng tầng; script liveness thuộc `global_shared` (dùng chung mọi phiên framework), không tạo tầng mới.
- Luật prose (CLAUDE.md 2026-06-27): `## Context` này và concept sẽ-promote phải viết văn xuôi đầy đủ, không caveman.
- **Dependency chain của liveness, thứ tự phải lành trước khi kết luận đáng tin:** git khả dụng → code-graph MCP resolve được (THĂM DÒ thật, đúng nguyên tắc `dep-health.py` — không chỉ kiểm "đã cài") → project đích đã reindex → schema `mechanisms.yaml`/ADR hợp lệ. Đứt bất kỳ tầng nào trong ba tầng đầu PHẢI rơi về UNAVAILABLE (FR-002), không được rơi xuống ORPHAN — ORPHAN chỉ dành cho "đã thăm dò được, symbol thật sự không còn". Bằng chứng đây không phải rủi ro lý thuyết: code-graph MCP của chính phiên viết SPEC này đang disconnect ngay lúc viết dòng này (bị kill để restart nạp code mới ở draft trước, không tự respawn giữa phiên).

## Non-goals

- **Không** semantic drift detection (LLM phán đoán ý nghĩa code có đổi không) — chỉ liveness cấu trúc (tồn tại/đổi tên/xoá) + cờ "code đổi kể từ lần confirm cuối". Phán đoán ý nghĩa ở lại người, đúng giới hạn trung thực đã thảo luận.
- **Không** backfill toàn bộ ADR/wiki hiện có trong đợt này — pilot trên tập nhỏ đã có bằng chứng thật (`mechanisms.yaml` mở rộng + 2-3 quyết định mới sinh trong chính phiên hôm nay) trước khi rollout rộng.
- **Không** tự động viết lại nội dung WHY khi STALE — máy chỉ flag, người xác nhận hoặc sửa.
- **Không** đổi cơ chế `live_probe` hiện có của `mechanisms.yaml` — mở rộng thêm trường mới (`anchor_symbol`), giữ nguyên tương thích ngược.
- **Không** giải bài toán multi-symbol-trùng-tên ngoài những gì code-graph đã giải ở phiên trước (project-scope, dedupe) — nếu vẫn nhập nhằng trong một project thì đó là nợ của code-graph, không phải của cơ chế này.
- **Không** xây UI riêng — tiêu thụ qua CLI (`why <symbol>`) + báo cáo trong `/lint`, khớp cách các cơ chế khác trong repo này hiển thị.

## Approaches

**Phương án A — mở rộng `mechanisms.yaml` pattern sang neo-symbol qua code-graph (chọn).** Thêm trường `anchor_symbol: <qualified-name>` cạnh `live_probe` hiện có (path-level) cho các mục muốn mịn hơn; thêm `confirmed: YYYY-MM-DD` để tách "code đổi" khỏi "code đổi mà chưa ai xác nhận lại"; viết script liveness dùng `search_symbols`/`get_symbol_context` để resolve; lệnh `why <symbol>` tra ngược. Ưu điểm: tận dụng nguyên xi hạ tầng đã chứng minh chạy (`medic` probe `narrative`, `/lint` report-không-chặn), rủi ro thấp vì `live_probe` cũ vẫn hoạt động song song. Nhược điểm: hai trường neo (path + symbol) tồn tại song song một thời gian — chấp nhận được, đúng nguyên tắc không đổi cơ chế cũ.

**Phương án B — comment-tag `@anchor: ID` nhúng trong code.** Sống sót qua rename (ID không đổi khi hàm đổi tên). Bác làm cơ chế CHÍNH: tái nhập một cache nhỏ vào code — đúng thứ "suy ra đừng cất" muốn tránh, và đã thảo luận: rename hiếm, đáng để flag-và-repoint (người xác nhận) hơn là nuôi một lớp ID phải đồng bộ tay. Giữ lại làm escape-hatch tuỳ chọn cho mục thật sự cần sống sót rename thường xuyên — không bắt buộc.

**Phương án C — semantic diffing bằng LLM mỗi lần code đổi.** Bắt được cả "trôi ngữ nghĩa" (tên hàm còn, hành vi đổi) mà kiểm-tồn-tại bỏ sót. Bác: chi phí mỗi lượt code đổi, độ tin cậy phán đoán LLM chưa kiểm chứng, và vi phạm thẳng giới hạn trung thực đã thống nhất trong phiên — phán đoán ý nghĩa là việc người, không phải máy.

## Requirements (FR)

**FR-001**: Mọi quyết định AUTHORED (ADR, mục `mechanisms.yaml`, ghi chú feedback có tác động code) PHẢI khai được một hoặc nhiều `anchor_symbol: <project>::<file>::<qualified-name>` (cho neo mức-symbol) bên cạnh `live_probe` hiện có (cho neo mức-file), cả hai đọc được bởi cùng một script liveness.

**FR-002**: Script liveness PHẢI resolve mỗi `anchor_symbol` qua `search_symbols`/`get_symbol_context` của code-graph, KHÔNG qua số dòng hay comment nhúng, và trả về đúng một trong BỐN trạng thái: LIVE (symbol tồn tại, không đổi kể từ `confirmed:`), STALE (symbol tồn tại, code trong vùng dòng của nó đã đổi kể từ `confirmed:` — bao gồm sửa thân hàm mà KHÔNG đổi tên), ORPHAN (symbol không còn resolve được — bao gồm cả đổi tên VÀ xoá hẳn, hai nguyên nhân khác nhau nhưng cùng một tín hiệu ra ngoài vì liveness không phân biệt được "đổi tên thành gì" khỏi "biến mất hẳn", chỉ biết "không resolve được nữa"), **UNAVAILABLE** (không kết luận được — code-graph MCP không tới được, hoặc project đích chưa reindex; PHẢI phân biệt tuyệt đối với ORPHAN vì nguyên nhân khác hẳn: "resolver không tới được" ≠ "symbol biến mất". Bắt buộc do dependency chain có thật: git khả dụng → code-graph MCP resolve được (thăm dò thật, đúng nguyên tắc `dep-health.py` — không chỉ kiểm "đã cài") → project đích đã reindex → LÚC ĐÓ liveness mới tin được. Đứt bất kỳ tầng nào PHẢI rơi về UNAVAILABLE, không được rơi xuống ORPHAN). Ba nhánh sửa-thân/đổi-tên/xoá-hẳn PHẢI đều được verify riêng — xem SC-003; UNAVAILABLE PHẢI verify riêng — xem SC-007.

**FR-003**: Hệ thống PHẢI cung cấp lệnh `why <symbol-hoặc-file>` — resolve qua code-graph rồi trả về mọi quyết định có `anchor_symbol`/`live_probe` khớp, đọc ngược từ code lên WHY.

**FR-004**: Mỗi quyết định có neo PHẢI mang trường `confirmed: YYYY-MM-DD`, chỉ người bump khi review một STALE và thấy vẫn đúng; script liveness PHẢI dùng ngày này (không phải ngày tạo file) để tính STALE.

**FR-005**: Neo vào code KÉO NGOÀI (không thuộc repo, không index được local) PHẢI trỏ vào adapter/boundary trong chính repo này (`dep-health.py`, `code_graph_keeper.py`, hoặc file provenance pin) — không trỏ thẳng vào symbol bên ngoài.

**FR-006**: `/lint` PHẢI báo cáo (không chặn) danh sách ORPHAN và STALE, theo đúng khuôn không-chặn đã dùng cho draft-age và unknown-ledger.

**FR-007**: Hệ thống KHÔNG được tự phán đoán ý nghĩa code đã đổi hay chưa (semantic) — chỉ cấu trúc (tồn tại/đổi-tên/xoá) và mốc thời gian (đổi-kể-từ-confirm). Vi phạm ranh giới này (vd một LLM tự động sửa WHY khi STALE) là bug, không phải feature.

**FR-008**: Sau khi mechanism verify được trên tập pilot thật (`mechanisms.yaml` mở rộng + các quyết định mới của chính phiên hôm nay), nguyên lý PHẢI được promote thành `llmwiki/wiki/concepts/decision-anchoring.md` — đúng luật commit-trước-wiki-sau.

**FR-009**: CRUD trên chính mục quyết định (không phải trên code nó neo vào) PHẢI được định nghĩa đủ, không chỉ CRUD trên code:
- **Update** — sửa `desc`, bump `confirmed`, hoặc re-point `anchor_symbol` sang symbol khác (dời neo có chủ ý, ví dụ sau refactor) là edit AUTHORED bình thường, không cần gate riêng ngoài schema (FR-001).
- **Delete** — **CẤM xoá vật lý** một mục đã có `anchor_symbol`/`live_probe`. Đây là lỗ hổng nghiêm trọng nhất nếu bỏ qua: liveness chỉ kiểm được những gì CÒN neo để kiểm — xoá hẳn mục thì code vẫn chạy bình thường (không ORPHAN, không STALE, vì không còn gì để phát hiện), và WHY biến mất không một dấu vết, đúng chính bệnh "docs rot"/"40 ADR mâu thuẫn" mà toàn bộ đề xuất này sinh ra để chống — chỉ khác là lần này xảy ra ngay trong cơ chế được thiết kế để ngăn nó. Bắt buộc theo đúng kỷ luật append-only đã chạy sống trong repo (`fdk-problem-tree.html`: *"không xoá node cũ; vấn đề được giải thì đổi status + ghi solvedBy"*) — đổi `status: retired` (+ `supersedes:` nếu có quyết định thay thế), không xoá dòng. Script liveness/`/lint` PHẢI cảnh báo nếu `git diff` cho thấy một mục có `anchor_symbol` biến mất khỏi `mechanisms.yaml`/ADR mà không đi qua đường `status: retired`.

**FR-010**: Ba lỗ hổng do lens Tester bắt được (không có nhóm race/concurrent, không test đường hồi phục, không gate xác minh trích dẫn) PHẢI được đóng trước khi thi hành:
- **Race** — validator T8 (bắt xoá-lén qua `git diff`) PHẢI so diff theo TỪNG MỤC (`id`), không so nguyên file, để hai người sửa hai mục khác nhau trong cùng file rồi merge không bị báo oan lẫn nhau. Đây chính là câu hỏi đã ghi nợ `U-03` — nay nâng thành yêu cầu bắt buộc, không còn là "để sau".
- **Recovery** — khi code-graph MCP sống lại sau một giai đoạn UNAVAILABLE, script liveness PHẢI tự resolve lại đúng về LIVE/STALE/ORPHAN ở lần gọi kế tiếp — KHÔNG được giữ trạng thái UNAVAILABLE cache lại, vì đó là một dạng "nói dối" khác (báo không xác định được trong khi giờ đã xác định được).
- **Trust boundary ở T9** — nội dung `concepts/decision-anchoring.md` khi promote PHẢI được một script đối chiếu tự động với output thật của T1-T8 (số cơ-chế LIVE, kết quả rename/xoá/sửa-thân, ca `harness-local`) trước khi coi là hợp lệ — không dựa vào lời tự khai của chính Claude khi viết concept đó.

## Success criteria (SC)

**SC-001**: Với quyết định thật đã neo (`_debounced`/`require_ok` trong `stop.py`, ghi trong phiên hôm nay), một người chạy `why _debounced` đọc được lý do thiết kế mà không phải grep tay hay nhớ nó nằm ở đâu.

**SC-002**: Nếu cơ chế này đã tồn tại lúc `harness-local/` bị dời (drift thật xảy ra trong phiên hôm nay), nó tự báo `live_probe`/`anchor_symbol` liên quan thành ORPHAN ngay lúc dời — không phải đợi `medic --ci` bắt được như một tác dụng phụ của probe `narrative` không chuyên biệt.

**SC-003**: Ba nhánh code-side đều tạo đúng tín hiệu tương ứng, không lẫn nhau và không lan sang symbol không liên quan — thử cả ba trên nhánh test, đo số cảnh báo sinh ra cho mỗi nhánh:
  - **sửa thân hàm, giữ tên** (`_debounced` đổi nội dung, tên không đổi) → STALE, không phải ORPHAN.
  - **đổi tên** (`_debounced` → `_should_skip`) → ORPHAN ở neo cũ, đúng MỘT tín hiệu.
  - **xoá hẳn** (`_debounced` bị xoá, không có hàm thay thế) → ORPHAN, cùng tín hiệu như đổi tên (liveness không phân biệt được nguyên nhân, chỉ biết "không resolve được").
  Cả ba: `_debounce_mark`/`_debounce_state` (không đụng tới) phải đứng yên LIVE.

**SC-004**: 100% neo trỏ vào code KÉO NGOÀI (ví dụ liên quan `code_graph_keeper.py`) trỏ vào file adapter trong repo, không trỏ thẳng vào file bên ngoài — xác nhận bằng quét toàn bộ `anchor_symbol`/`live_probe` hiện có.

**SC-005**: Người duyệt `/lint` phân biệt được ngay ORPHAN (cần sửa neo hoặc xoá quyết định) với STALE (cần đọc lại, có thể vẫn đúng) chỉ bằng nhãn — không phải đọc lại toàn bộ nội dung để tự suy trạng thái.

**SC-006**: Thử xoá vật lý một mục `mechanisms.yaml` có `anchor_symbol` trên nhánh test (không đi qua `status: retired`) PHẢI bị `/lint` cảnh báo ngay ở lượt chạy kế tiếp — bằng chứng rằng lỗ hổng "xoá neo = WHY biến mất không dấu vết" đã được khoá, không chỉ định nghĩa trên giấy.

**SC-007**: Ngắt kết nối code-graph MCP giữa phiên (đúng ca đã xảy ra thật trong chính phiên viết SPEC này — restart để nạp code mới, không tự respawn) rồi chạy liveness/`why` KHÔNG ĐƯỢC làm toàn bộ neo hiện có đổ về ORPHAN hàng loạt. Bằng chứng: giả lập lại đúng trạng thái này (code-graph không tới được), chạy liveness, đếm — phải toàn bộ UNAVAILABLE, không một ORPHAN giả nào sinh ra.

**SC-008**: Ba lỗ hổng do lens Tester bắt được đều đóng, đo được cụ thể: (a) hai người sửa hai mục khác nhau trong `mechanisms.yaml` cùng một merge — validator T8 không báo oan mục hợp lệ (đóng nợ `U-03`); (b) code-graph sống lại sau một giai đoạn UNAVAILABLE — lần gọi liveness kế tiếp tự resolve đúng, không kẹt cache; (c) `concepts/decision-anchoring.md` ở T9 bị script đối chiếu tự động FAIL nếu trích một con số không khớp output thật của T1-T8.

## Plan

Cắt theo MoSCoW (lens PM — không có persona `pm.md` trong repo, đây là phán đoán PM chuẩn, không phải đối chiếu hợp đồng persona như grower/tester). Sau 4 vòng phản biện (before/after · CRUD · dependency · persona-lens) SPEC phình từ ~8 FR/5 SC/7 task lên 10 FR/8 SC/9 task mà chưa ship dòng nào — đúng dấu hiệu "perfect is the enemy of shipped". Cắt ranh để có tín hiệu dùng thật sớm nhất, phục vụ trực tiếp GH#83 (không đo được adoption vì chưa có gì để đo).

**v0.1 — MUST, ship trước để có vòng lặp lõi chạy được:**

- [x] **T1 — Thêm trường `anchor_symbol`/`confirmed` vào schema `mechanisms.yaml`, viết script liveness trả đủ 4 trạng thái (LIVE/STALE/ORPHAN/UNAVAILABLE), thăm dò code-graph trước khi tin kết quả resolve.** Verify: chạy trên 23 mục hiện có, không mục nào đổi trạng thái ngoài ý muốn (tất cả vẫn LIVE ở mức `live_probe` cũ); SC-007 — giả lập code-graph MCP không tới được, chạy lại, toàn bộ phải UNAVAILABLE chứ không có ORPHAN giả nào; và test HỒI PHỤC (FR-010) — cho code-graph sống lại, gọi liveness lần kế tiếp phải tự resolve đúng về LIVE/STALE/ORPHAN, không kẹt ở UNAVAILABLE cache.
- [x] **T2 — Neo thật `_debounced`/`require_ok` (stop.py) làm pilot symbol-level đầu tiên.** Verify: SC-001 — `why _debounced` chạy thật, trả đúng nội dung.
- [x] **T3 — Lệnh `why <symbol>` (reverse lookup qua code-graph).** Verify: chạy trên pilot T2 và trên một `live_probe` cũ (ví dụ `orientation`), cả hai trả đúng.

**v0.2 — SHOULD, hardening trước khi rollout rộng (chưa cần cho pilot 1 symbol):**

- [x] **T4 — Test đủ 3 nhánh code-side trên nhánh thử: sửa thân hàm giữ tên, đổi tên `_debounced`, xoá hẳn một hàm khác không có thay thế.** Verify: SC-003 — sửa thân → STALE, đổi tên → đúng 1 ORPHAN, xoá hẳn → đúng 1 ORPHAN; cả ba không cảnh báo lan sang symbol khác.
- [x] **T5 — Test drift thật bằng cách mô phỏng lại ca `harness-local` (di chuyển một file có `live_probe`/`anchor_symbol` trỏ vào, trên sandbox).** Verify: SC-002 — phát hiện ngay, không cần đợi medic `narrative`.
- [x] **T6 — Neo boundary cho KÉO NGOÀI: gắn `anchor_symbol` vào `dep-health.py`/`code_graph_keeper.py` cho các quyết định liên quan code-graph đã ghi trong phiên trước.** Verify: SC-004 — quét không còn neo trỏ thẳng ra ngoài repo.
- [x] **T7 — Nối `/lint` báo cáo ORPHAN + STALE, phân nhãn rõ.** Verify: SC-005 — chạy `/lint` trên trạng thái sau T1-T6, đọc output không cần hỏi lại máy.

**v0.3 — COULD, hoãn thật sự (chỉ đáng làm khi nhiều người cùng sửa `mechanisms.yaml` thường xuyên):**

- [x] **T8 — Khoá lỗ hổng xoá-vật-lý: validator so `git diff` của `mechanisms.yaml`/ADR THEO TỪNG MỤC (`id`), không so nguyên file, cảnh báo khi một mục có `anchor_symbol` biến mất mà không đi qua `status: retired`.** Verify: SC-006 — xoá thử một mục có neo trên nhánh test (không qua `status: retired`), `/lint` bêu ngay lượt kế tiếp; và test RACE (FR-010, đóng nợ `U-03`) — hai mục KHÁC NHAU trong cùng file cùng đổi trong một merge (một thêm neo mới, một `status: retired` hợp lệ), validator không được báo oan mục hợp lệ.
- [x] **T9 — Promote `llmwiki/wiki/concepts/decision-anchoring.md` sau khi T1-T8 xanh, kèm script đối chiếu tự động nội dung concept với output thật của T1-T8 trước khi coi hợp lệ.** Verify: FR-008 + FR-010 (trust boundary) — concept file tồn tại, trích dẫn đúng bằng chứng pilot thật; script đối chiếu PHẢI FAIL nếu concept trích một con số không khớp log/output thật của T1-T8, không dựa vào lời tự khai của Claude khi viết.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Đổi schema `mechanisms.yaml` — file nguồn chân lý cho `medic`, sai một trường lan ra 23 mục hiện có | done |
| T2 | Claude | Neo pilot đầu tiên cần đúng — sai định dạng thì mọi neo sau chép theo cái sai | done |
| T3 | OpenCode (rẻ) | Reverse lookup là thao tác tra cứu cơ học một khi resolve-qua-code-graph đã viết xong ở T1/T2 | done |
| T4 | OpenCode (rẻ) | Ba nhánh (sửa/đổi-tên/xoá) + đếm cảnh báo là kịch bản test có quy trình rõ, không cần phán đoán | done |
| T5 | OpenCode (rẻ) | Mô phỏng lại đúng thao tác `git mv` + đo, quy trình đã biết từ ca thật hôm nay | done |
| T6 | Claude | Xác định đúng boundary/adapter cho từng quyết định cần phán đoán, sai thì neo lại trỏ ra ngoài | done |
| T7 | OpenCode (rẻ) | Nối report vào `/lint` theo khuôn draft-age/unknown-ledger đã có sẵn để chép | done |
| T8 | Claude | Xác định đúng "xoá hợp lệ" (qua status: retired) khỏi "xoá lén" cần phán đoán — sai ngưỡng thì hoặc bêu oan mọi lần retired hợp lệ, hoặc bỏ lọt đúng ca cần bắt | done |
| T9 | Claude | Viết concept — văn xuôi đầy đủ, tổng hợp toàn bộ nguyên lý phiên này, không phải việc cơ học | done |

## Assumptions

- `anchor_symbol` viết dạng `<project>::<file>::<qualified-name>` — **(default)**: khớp cách code-graph đã định danh sau khi thêm nhãn `project` (phiên trước), không phát minh cú pháp mới.
- Ngưỡng "code đổi kể từ confirm" tính bằng `git diff` chạm vùng dòng của symbol (không phải toàn file) — **(default, find-out-later)**: hợp lý về lý thuyết, cần đo thật trên T2/T5 xem `git blame`/diff theo symbol-span của code-graph đủ chính xác không.
- Pilot giới hạn ở `mechanisms.yaml` mở rộng + các quyết định sinh trong chính phiên hôm nay (không đụng ADR cũ) — **(default)**: giữ rủi ro nhỏ, đúng Non-goals; backfill rộng là việc khác, sau khi pilot chứng minh được.
- T9 (promote concept) đặt CUỐI, sau khi T1-T8 xanh — **(default)**: đúng luật repo, không đoán trước rằng thiết kế sẽ không đổi khi thi hành thật.
- ~~Ngưỡng phân biệt "xoá hợp lệ" khỏi "xoá lén" so nguyên file~~ — **đã đóng** (`U-03` resolved 2026-07-21, lens Tester): nâng thành yêu cầu cứng so theo TỪNG MỤC (`id`), xem `FR-010`/`T8`/`SC-008`, không còn là default.

## Render brief

Participant chung: `PERSON (viết WHY)`, `MECHANISMS.YAML / ADR (AUTHORED)`, `CODE-GRAPH (resolve)`, `LIVENESS SCRIPT`, `LINT/MEDIC (báo cáo)`.

- **T1**: [legacy] `mechanisms.yaml` 23 mục có `live_probe` → [add] thêm `anchor_symbol`+`confirmed` → [add] script liveness đọc cả hai trường, THĂM DÒ code-graph trước (nguyên tắc `dep-health.py`) → [block] hai nhánh chặn riêng biệt: (a) mục thiếu `confirmed` khi có `anchor_symbol` → cảnh báo, không tính LIVE; (b) code-graph không tới được hoặc project chưa reindex → UNAVAILABLE, KHÔNG được rơi xuống ORPHAN — đúng SC-007, và đúng thực tế đang xảy ra ngay lúc viết SPEC này.
- **T2**: [legacy] `_debounced` trong `stop.py`, quyết định đã viết trong phiên hôm nay → [add] neo `anchor_symbol: setup::stop.py::_debounced` → [add] code-graph resolve ra đúng file:line → [block] resolve rỗng (project chưa reindex) → không tính ORPHAN oan, báo "chưa index".
- **T3**: [add] lệnh `why <symbol>` → [legacy] tra ngược qua `mechanisms.yaml`/ADR có neo khớp → [add] trả cả hai loại (path-level cũ, symbol-level mới) → [block] symbol trùng tên nhiều project → bắt buộc `project::` để giải nhập nhằng (đã giải quyết ở phiên trước).
- **T4**: [add] ba nhánh trên nhánh thử — sửa thân `_debounced` (giữ tên), đổi tên `_debounced`→`_should_skip`, xoá hẳn một hàm khác không thay thế → [add] liveness chạy lại cho cả ba → [block] STALE cho nhánh sửa-thân, ORPHAN đúng 1 chỗ cho nhánh đổi-tên và nhánh xoá-hẳn, các symbol khác (`_debounce_mark`, `_debounce_state`) không bị ăn theo — chứng minh gãy-đúng khác gãy-nhiễu trên cả 3 kiểu gãy, không chỉ đổi tên.
- **T5**: [legacy] mô phỏng lại `harness-local` bị `git mv` sang chỗ khác trên sandbox → [add] liveness phát hiện `live_probe` gãy NGAY, không cần `medic --ci` chạy full suite → [block] so sánh thời điểm phát hiện: `narrative` probe cũ (broad, chậm phát hiện tới lượt medic chạy) vs liveness mới (chuyên biệt, phát hiện tức thời khi được gọi).
- **T6**: [legacy] quyết định về `dep-health.py`'s "thăm dò thay vì kiểm tồn tại" đã viết trong code, chưa neo hình thức → [add] gắn `anchor_symbol` trỏ vào chính `dep-health.py`/`code_graph_keeper.py` (adapter, không trỏ ra graph-kit ngoài repo) → [block] một neo thử trỏ thẳng vào `graph-kit` (ngoài repo) → script liveness từ chối, buộc trỏ lại vào adapter — đúng FR-005.
- **T7**: [legacy] `/lint` đã báo draft-age, unknown-ledger theo khuôn không-chặn → [add] thêm mục ORPHAN/STALE cùng khuôn → [block] không biến `/lint` thành gate chặn — chỉ báo cáo, người quyết sửa hay bỏ qua.
- **T8**: [legacy] `mechanisms.yaml`/ADR đã có mục với `anchor_symbol` — điểm mù: liveness chỉ kiểm được cái CÒN neo, xoá hẳn mục thì không còn gì để kiểm → [add] validator so `git diff` của file, cảnh báo khi một mục có `anchor_symbol` biến mất mà không đi qua `status: retired` → [block] xoá thử một mục có neo trên nhánh test (không qua `status: retired`) → `/lint` phải bêu ngay, đúng SC-006 — khoá đúng lỗ hổng "xoá neo = WHY biến mất không dấu vết".
- **T9**: [legacy] toàn bộ pilot T1-T8 đã chạy xanh, có bằng chứng thật → [add] viết `concepts/decision-anchoring.md`, trích số đo thật (không giả định) → [block] promote khi T1-T8 còn đỏ — vi phạm luật commit-trước-wiki-sau, phải chặn tới khi xanh hết.

## Self-review

**Phủ yêu cầu.** Ba vế của yêu cầu gốc trong lượt gọi `/propose` — viết concept (giải qua `## Context` + T9 promote sau), teach-me hình dạng code-level (Render brief mỗi task có participant CODE-GRAPH cụ thể, SC-001/SC-003 là ví dụ chạy thật không phải giả định), hoạt-họa khi code đổi trigger ra sao (T4/T5 là chính hai kịch bản đó, dựng thành diagram riêng) — đều về đúng chỗ, không rơi. Feedback "case delete và edit thì sao đủ CRUD chứ" lộ ra một trục thứ hai chưa phủ (CRUD trên chính mục quyết định, không chỉ trên code) — vá bằng FR-009/SC-006/T8, không phải mở rộng gượng vào task cũ.

**Quét chỗ bỏ ngỏ.** Đã rà toàn văn, mọi mục đều có nội dung cụ thể. Giá trị chưa chắc duy nhất (ngưỡng git-diff-theo-symbol-span) đã hạ xuống `(default, find-out-later)` thay vì giả định chắc chắn.

**Nhất quán tên-kiểu.** `anchor_symbol` dùng thống nhất cho neo mức-symbol, `live_probe` giữ nguyên tên cũ cho neo mức-file (không đổi tên trường đã chạy sống); ba trạng thái LIVE/STALE/ORPHAN viết hoa thống nhất xuyên suốt; "liveness script" là tên duy nhất cho cơ chế mới, không đặt tên khác ở chỗ khác.

## Origin
- **Source:** phiên 2026-07-21 — chuỗi hội thoại "code là source of truth" → "từ code tìm WHY thế nào" → "neo theo symbol là sao" → "adapt với đứa ngoài hạ tầng thế nào" → khảo sát 4 cách ngành đang giải (WebSearch) → kiểm chéo `vercel-labs/zerolang` → phát hiện `mechanisms.yaml` là tiền lệ đã chạy.
- **Concept nền:** [[adapt-modes]] (ba dạng biên) · [[graph-model]] · [[skill-craft]] · `ADR-001` (policy-as-source-of-truth, council-025 — nguồn gốc `mechanisms.yaml`)
- **Bằng chứng chạy thật trong phiên:** `medic --ci` bắt `harness-local` drift qua probe `narrative` (2026-07-21); code-graph vệ sinh xong (`get_callers("save")` 65→5) là tiền đề neo-symbol không nhập nhằng.
- **Task:** `T-260721-03`
