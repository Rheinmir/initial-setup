---
type: draft
title: "Wiki mental-model taxonomy — quan hệ operationalizes nối Fact/Mental-Model tới Protocol"
status: proposed
tags: [wiki-core, taxonomy, relations, operationalizes, graph-model, visualize]
timestamp: 2026-08-01
task: T-260801-01
---

# 010826-wiki-mental-model-taxonomy — quan hệ `operationalizes` nối Fact/Mental-Model tới Protocol

**Status:** implemented (T1-T4 committed 2026-08-01)

**Sequence diagram:** [010826-wiki-mental-model-taxonomy-seq.html](../../../html/010826-wiki-mental-model-taxonomy-seq.html)

## What
Issue [#93](https://github.com/Rheinmir/setup/issues/93) đòi phân loại nội dung wiki theo **độ trừu tượng nhận thức** (Fact → Mental Model → Protocol), khác với cách phân loại theo *nơi lưu* hiện có (`concepts/entities/sources/draft/architecture/tours`); và cần một cách **visualize** cho người học mới thấy được chuỗi này. Hai comment cập nhật của tác giả issue (2026-08-01) đã thu hẹp phạm vi thật xuống còn: (1) lớp Protocol **đã tồn tại sẵn** dưới tên `SKILL.md` + rule-registry, không cần xây lại; (2) việc cần làm là **link tường minh** một node Fact hoặc Mental-Model tới Protocol mà nó tạo ra, qua một quan hệ đồ thị mới tên `operationalizes`; (3) đường này KHÔNG bắt buộc — cho phép đường tắt Fact → Protocol thẳng, không phải luôn qua Mental-Model trung gian, để tránh chính taxonomy này gây phình hệ thống (cảnh báo Munger tác giả issue tự trích dẫn và áp ngược lại chính đề xuất của mình).

## Context
Query `llmwiki/wiki/` trước khi viết SPEC này, 3 nguồn liên quan trực tiếp:

- **[[wiki-core-relations]]** (`llmwiki/wiki/concepts/wiki-core-relations.md`) — thiết kế lõi quan hệ hiện tại của wiki: `relations:` khai trong frontmatter theo cú pháp `{rel: X, to: Y}`, và bài học lịch sử **"suy đừng cất"** — quan hệ `touches` (wiki→code) từng bị `fdk/tools/wiki-relations.py` dập tay một lần (2026-07-02), đóng băng ở 21/2.559 cạnh (0,8%), rồi được thay bằng suy-sống mỗi lần dựng đồ thị, tăng lên 283 cạnh. Đây là bài học trực tiếp áp dụng cho thiết kế `operationalizes` bên dưới.
- **[[graph-model]]** (`llmwiki/wiki/concepts/graph-model.md`) — xác nhận trường `type:` hiện có trên mỗi node wiki (`concept`/`entity`/`source`/`draft`/…) là phân loại theo **thư mục lưu trữ**, một chiều hoàn toàn khác với "độ trừu tượng nhận thức" mà issue #93 đòi — đúng như nhận định gốc của issue, không phải suy diễn của tôi.
- **`harness/scripts/wiki-graph.py`** (đọc trực tiếp code, không phải wiki) — `ALLOWED_RELS = {derives-from, depends-on, implements, supports, contradicts, supersedes}` (dòng 134-135) chỉ cho cạnh `to:` kiểu **wiki→wiki**; cạnh `touches` (wiki→code, dòng 104 `touches_targets()`) đứng **NGOÀI** whitelist này vì nó được suy từ thân bài (backtick path + tồn tại thật trên đĩa), không khai tay trong `relations:`. `operationalizes` (wiki→skill/rule) có hình dạng giống `touches` hệt — cả hai đều nối một wiki node tới một artifact NGOÀI 6 thư mục nội dung — nên nên theo đúng cơ chế suy, không theo cơ chế `ALLOWED_RELS`.

**Phát hiện phụ, ghi vào Non-goals:** `touches` hiện chỉ được wire vào MỘT nơi tiêu thụ (`fdk/tools/build-wiki-graph.py::scan()`, dòng 156-159, dùng cho visualization) — KHÔNG được wire vào graph builder nội bộ của chính `wiki-graph.py` (CLI `backlinks`/`neighbors`/`cite`/`export` dùng cho agent). `operationalizes` sẽ theo đúng hiện trạng này để nhất quán (không tự ý mở rộng phạm vi ra CLI agent — đó là việc khác, chưa ai yêu cầu).

## Global constraints
- `llmwiki/CLAUDE.md` 5-Why: đã chạy — hỏi "vì sao chưa phân loại theo abstraction" chạm đúng cấu trúc: `type:` hiện tại đo *nơi lưu*, chưa từng có field nào đo *tầng nhận thức*; đây là khoảng trống cấu trúc thật, không phải thiếu sót vá được bằng cách gắn nhãn thủ công một lần.
- Nguyên tắc "suy đừng cất" (`[[wiki-core-relations]]`, `[[graph-model]]`): field/quan hệ nào suy được từ nội dung + xác minh tồn tại thật thì SUY LẠI mỗi lần dựng, không cất một lần rồi đóng băng.
- `llmwiki/CLAUDE.md`: mọi file wiki mới phải có `## Origin`; không ghi `raw/`; đúng subfolder; cập nhật `index.md` + `log.md`.
- Validator R7 (`proposal_complete`, `harness/poc-vendor-neutral/policy.yaml:49-62`): SPEC này phải có `## Agent Task Assignment` + link Sequence diagram tồn tại trên đĩa + `## Global constraints`; cấm còn câu hỏi làm rõ chưa trả lời lúc ra cổng duyệt.
- `fdk.md` Rules: HTML sinh cho người xem phải có toggle sáng/tối (`localStorage` + chống FOUC), cỡ chữ compact cho màn 13″, show full path, và giải nghĩa thuật ngữ chuyên ngành lần xuất hiện đầu.
- `llmwiki/CLAUDE.md` prose rule: `## Context` viết văn xuôi đầy đủ, không caveman.

## Non-goals
- **Không** backfill trường phân loại mới cho toàn bộ ~2.500+ node wiki hiện có — opt-in, gắn dần khi cần, đúng cảnh báo Munger mà chính tác giả issue rút lại ở comment #2 (taxonomy ép buộc toàn diện tự nó gây phình hệ thống).
- **Không** xây 2 mức giữa/trên của bảng 5-mức gốc trong mô tả issue ban đầu (`Concept`, `Framework`) — comment #1 đã xác nhận bảng đó "chỉ là bối cảnh, không phải nền tảng cần build"; chỉ giữ 2 nhãn `fact` / `mental-model` cộng thêm lớp Protocol đã có sẵn dưới tên khác.
- **Không** wire `operationalizes` vào CLI truy vấn agent (`wiki-graph.py` subcommand `backlinks`/`neighbors`/`cite`/`export`) trong bản này — hiện trạng `touches` cũng chưa được wire vào đó; mở rộng đồng thời cả hai là việc khác, ngoài yêu cầu gốc (chỉ đòi "visualize cho người học mới", tức tầng hiển thị `fdk/tools/build-wiki-graph.py`).
- **Không** thêm validator ép buộc mọi Protocol (skill/rule) phải có ít nhất một cạnh `operationalizes` trỏ tới — nợ mở, chấp nhận; một Protocol chưa có Fact/Mental-Model nào tham chiếu tới nó không phải lỗi.
- **Không** đổi hay xoá field `type:` hiện có — `layer:` (xem FR-001) là field độc lập, cộng thêm bên cạnh, không thay thế.

## Approaches

**Phương án A — Suy sống (infer-at-build), field `layer:` tuỳ chọn 2 giá trị (chọn).** Thêm frontmatter tuỳ chọn `layer: fact | mental-model` trên node wiki (không bắt buộc, node cũ không có coi là "chưa phân loại"). Quan hệ `operationalizes` KHÔNG khai tay trong `relations:` — suy từ thân bài: một node có `layer:` mà thân bài nhắc tới tên skill/rule trong backtick (vd `` `propose` ``, `` `R7` ``) VÀ tên/id đó xác minh tồn tại thật (`skills/<tên>/SKILL.md` có mặt, hoặc `id: <ID>` có trong `harness/poc-vendor-neutral/policy.yaml`) thì sinh cạnh. Ưu điểm: đúng nguyên tắc "suy đừng cất" đã trả giá một lần với `touches`, 0 backfill bắt buộc, tự cập nhật khi thân bài đổi. Nhược điểm: phụ thuộc đúng convention backtick trong thân bài — nhưng đây là nhược điểm CHUNG đã chấp nhận với `touches`, không phải rủi ro mới.

**Phương án B — Khai tay trong `relations:`, thêm `operationalizes` vào `ALLOWED_RELS`.** Tường minh hơn (không phụ thuộc heuristic quét text), nhưng lặp lại NGUYÊN VĂN bug lịch sử đã ghi trong `[[wiki-core-relations]]`: `touches` dập tay một lần rồi đóng băng ở 0,8% coverage, không tự cập nhật khi nội dung đổi. Bác — đây là bài học đã trả giá, không phải giả thuyết.

**Phương án C — Backfill taxonomy 4 mức (Fact/Concept/Mental-Model/Framework) toàn diện ngay lập tức.** Đúng sát tiêu đề issue gốc nhất, nhưng chính là thứ mà comment #2 của tác giả issue tự cảnh báo và rút lại (taxonomy ép buộc toàn diện = tự phình hệ thống, trích Munger). Bác theo yêu cầu mới nhất, đã ghi thành comment cập nhật chính thức trên issue.

## Requirements (FR)

**FR-001**: Wiki node frontmatter PHẢI hỗ trợ trường tuỳ chọn mới `layer: fact | mental-model` — phân loại độ trừu tượng nhận thức, ĐỘC LẬP hoàn toàn với `type:` hiện có (nơi lưu). Node không khai `layer:` vẫn hợp lệ, không lỗi, coi là "chưa phân loại".

**FR-002**: Hệ thống PHẢI suy ra (không khai tay trong `relations:`) một quan hệ đồ thị mới `operationalizes`, nối node có `layer: fact` hoặc `layer: mental-model` tới Protocol (skill hoặc rule) mà thân bài nhắc tới bằng backtick — hàm `operationalizes_targets(text, repo_root)` đặt cạnh `touches_targets()` trong `harness/scripts/wiki-graph.py`, cùng chữ ký, cùng nguyên tắc "phải tồn tại thật trên đĩa" mới sinh cạnh (skill: `skills/<tên>/SKILL.md` tồn tại; rule: `id: <ID>` có mặt trong `harness/poc-vendor-neutral/policy.yaml`).

**FR-003**: `operationalizes` PHẢI cho phép cạnh xuất phát từ CẢ hai loại node (`layer: fact` hoặc `layer: mental-model`) bằng cùng một cơ chế suy — hiện thực hoá đúng yêu cầu "đường tắt Fact → Protocol trực tiếp, chỉ khác điểm xuất phát" (comment #2 của issue).

**FR-004**: Tầng hiển thị `fdk/tools/build-wiki-graph.py` PHẢI vẽ cạnh `operationalizes` mới — thêm entry vào `REL_COLORS`/`REL_VI` (dòng 107-117) theo đúng pattern các rel khác đã có, và gọi `operationalizes_targets()` trong `scan()` cạnh lời gọi `touches_targets()` hiện có (dòng 155-159).

**FR-005**: Node đích của `operationalizes` (skill/rule) PHẢI hiện ra như node lá trong đồ thị — mở rộng đúng cơ chế đã có cho `touches` ở dòng 341 (`fdk/tools/build-wiki-graph.py`, thêm node lá cho path code), không đòi hỏi skill/rule phải nằm trong 6 thư mục nội dung wiki (`CONTENT_DIRS`).

**FR-006**: Node có `layer:` PHẢI có màu/badge riêng trong đồ thị (khác node "chưa phân loại"), để người xem phân biệt ngay Fact vs Mental-Model bằng mắt — đây là phần "visualize cho người học mới" mà issue #93 đòi ở tiêu đề.

## Success criteria (SC)

**SC-001**: Một người MỚI mở `llmwiki/html/wiki-graph.html`, nhìn vào một node đã gắn `layer: mental-model` có tham chiếu một skill hợp lệ trong thân bài — thấy ngay cạnh `operationalizes` nối tới đúng skill đó, không cần đọc code hay hỏi ai để hiểu "cái wiki này sinh ra cái skill nào".

**SC-002**: Gắn `layer: fact` cho một node Fact có tham chiếu trực tiếp một skill (không qua Mental-Model trung gian) — đồ thị vẫn vẽ đúng cạnh `operationalizes` từ Fact thẳng tới Protocol, xác nhận đường tắt hoạt động thật (không chỉ trên giấy).

**SC-003**: Sửa một node đã gắn `layer:` — đổi tên skill được tham chiếu trong thân bài (vd từ `` `propose` `` sang `` `plan` ``) rồi build lại đồ thị — cạnh `operationalizes` TỰ cập nhật theo giá trị mới, không cần chạy script "dập" thủ công nào (bằng chứng cho "suy đừng cất" chạy đúng, không lặp lại bug `touches` cũ).

**SC-004**: 100% node wiki hiện có (không sửa gì) build lại đồ thị vẫn chạy được bình thường, không lỗi, không crash — xác nhận backward-compatible, `layer:` là opt-in thật, không ép buộc migrate.

## Assumptions

- Cú pháp tham chiếu skill/rule trong thân bài là backtick trần, khớp CHÍNH XÁC tên (`` `propose` ``, `` `R7` ``), không hỗ trợ alias — **(default)**: nhất quán với cách `touches_targets()` đã dùng backtick cho code path.
- `layer:` chỉ nhận đúng 2 giá trị `fact` | `mental-model` — **(default)**: Protocol (lớp 3) đã có nhà riêng (skill/rule), không cần nhãn lại nó trong wiki; `concept`/`framework` bị loại khỏi scope theo comment #1 của issue.
- Gắn `layer:` cho node nào là quyết định của người viết wiki tại thời điểm viết/sửa trang đó — **(default)**: không có script tự động phân loại retroactively trong bản này (khớp Non-goals, tránh backfill toàn diện).
- Rule tham chiếu bằng `id:` (vd `R7`), không phải `name:` (policy.yaml không có field `name` ngắn cho mọi rule) — **(default, find-out-later)**: cần xác nhận lại nếu sau này policy.yaml đổi schema id.

## Plan

- [x] **T1 — Thêm `operationalizes_targets(text, repo_root)` vào `harness/scripts/wiki-graph.py`, đặt cạnh `touches_targets()` (dòng ~113).** Regex bắt backtick token, verify tồn tại thật: `skills/<tên>/SKILL.md` HOẶC `id: <ID>` trong `harness/poc-vendor-neutral/policy.yaml`. Verify: SC-002, SC-003.
- [x] **T2 — Wire vào `fdk/tools/build-wiki-graph.py::scan()`: gọi `operationalizes_targets()` cạnh `touches_targets()` (dòng 155-159), sinh `edges.append({"from": pid, "rel": "operationalizes", "to": target, "kind": "path"})`. Thêm entry `REL_COLORS`/`REL_VI` (dòng 107-117). Thêm node lá cho target (mirror dòng 341). Đọc `layer:` frontmatter, gán màu/badge node.** Verify: SC-001, SC-004.
- [x] **T3 — Gắn `layer: fact` hoặc `layer: mental-model` mẫu cho 3-5 node wiki hiện có** (ví dụ minh hoạ, KHÔNG backfill toàn bộ — đúng Non-goals) — chọn node đã có tham chiếu skill/rule sẵn trong thân bài để chuỗi hiện ra thật ngay, không giả lập. Verify: SC-001, SC-002. **Kết quả thật khác ước lượng:** grep toàn bộ `llmwiki/wiki/concepts/` chỉ tìm ra ĐÚNG 1 node (`wiki-core-relations.md`) có backtick tham chiếu skill thật (`query`, `verify-before-commit`) — không có node "fact" nào tham chiếu skill/rule để minh hoạ đường tắt (SC-002 do đó chỉ được chứng minh ở mức đơn vị trong Task 1, không ở mức wiki thật). Không bịa thêm nội dung để đủ số — đúng nhánh "DỪNG, chọn node khác/không ép" đã lường trước trong PLAN.
- [x] **T4 — Test tất định tối thiểu cho `operationalizes_targets()`** (assert-based `demo()`/`__main__` self-check, theo carve-out `llmwiki/CLAUDE.md`: logic non-trivial phải để lại đúng 1 check chạy được) — case skill hợp lệ, rule hợp lệ, tên không tồn tại (không sinh cạnh). Verify: SC-003 (đổi tham chiếu → cạnh đổi theo).

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Hàm suy + điều kiện xác minh tồn tại là logic bảo toàn tính đúng của cả đồ thị — sai một chi tiết (regex quá rộng, thiếu check tồn tại) tái sinh đúng bug `touches` cũ, cần đúng ngay từ đầu | pending |
| T2 | Claude | Chạm engine hiển thị chính (`build-wiki-graph.py`) đang phục vụ `wiki-graph.html` sống — cần nhất quán tuyệt đối với cách `touches` đã được wire, không lệch pattern | pending |
| T3 | OpenCode (rẻ) | Thêm 1 dòng frontmatter `layer:` theo mẫu đã có sẵn trên node đã chọn — thao tác cơ học, không cần thiết kế | pending |
| T4 | Claude | Test cho logic có nhánh (skill/rule/không-tồn-tại) cần đúng ngay, không phải thao tác lặp lại theo mẫu | pending |

## Self-review

**Phủ yêu cầu.** Toàn bộ yêu cầu trong issue #93 (bao gồm 2 comment cập nhật) đã về đúng task: quan hệ `operationalizes` (T1+T2/FR-002), đường tắt Fact→Protocol (FR-003/SC-002), visualize cho người mới (FR-004-006/SC-001), không phình hệ thống (Non-goals + T3 chỉ gắn mẫu không backfill toàn bộ).

**Quét placeholder.** Rà toàn văn — không còn cụm việc-để-đó-chưa-làm hay câu chép-nguyên-task-khác kiểu "tương tự Task N". Mỗi task đều có hành động cụ thể + verify cụ thể.

**Nhất quán tên-kiểu.** `operationalizes` là tên quan hệ DUY NHẤT xuyên suốt draft (không lẫn `operationalize`/`operationalise`); `layer:` là tên field DUY NHẤT (không lẫn `abstraction:`/`tier:`); `operationalizes_targets()` là tên hàm DUY NHẤT dùng từ FR-002 tới Plan tới Agent Task Assignment.

## Notes
- [[wiki-core-relations]] — nguồn của nguyên tắc "suy đừng cất" áp dụng xuyên suốt SPEC này.
- [[graph-model]] — xác nhận `type:` hiện có là phân loại theo nơi lưu, không phải abstraction level.

## Origin
- **Source:** GitHub issue [Rheinmir/setup#93](https://github.com/Rheinmir/setup/issues/93) + 2 comment cập nhật (2026-08-01) của tác giả issue. Ledger gốc mà issue trích dẫn (`llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md`) KHÔNG có mặt ở bất kỳ branch/commit nào trong repo tại thời điểm nhận issue — đã hỏi lại người dùng qua `AskUserQuestion`, được xác nhận dựng SPEC này từ issue + comment (không có ledger gốc nào khác để đối chiếu).
- **Concept nền:** `[[wiki-core-relations]]` (bài học "suy đừng cất") · `[[graph-model]]` (phân biệt `type:` = nơi lưu).
- **Bằng chứng chạy thật trong phiên:** đọc trực tiếp `harness/scripts/wiki-graph.py` (dòng 104-150, `touches_targets`/`ALLOWED_RELS`), `fdk/tools/build-wiki-graph.py` (dòng 107-168, 341), `git log --all` xác nhận ledger gốc không tồn tại (0 kết quả mọi branch).
- **Task:** `T-260801-01`
- **Draft:** `wiki/sources/draft/010826-wiki-mental-model-taxonomy.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
