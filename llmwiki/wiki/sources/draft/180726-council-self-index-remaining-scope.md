---
type: issue
kind: architecture
title: "Council tự chọn đề thi + app mẫu ngoài-khuôn + harass 8 loại vector — phần lõi chưa ship"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P3
tags: [issue, council, self-index, wiki-core-relations, harass-test]
timestamp: 2026-07-18
id: 180726-council-self-index-remaining-scope
source_session: "phiên 2026-07-18 — rà 8 draft ⏱ TREO qua JOIN task↔docs-curate; ca này verify bằng 6 nguồn chéo (task-store, council.py, wiki cross-ref, git log, report archive, validator tồn tại)"
---

# Issue: Council tự chọn đề thi + app mẫu ngoài-khuôn + harass 8 loại vector — phần lõi chưa ship

## Vấn đề (một câu)

Proposal gốc `020726-council-chon-de-thi-self-index` đã ship **hạ tầng nền** (ledger sự kiện + relations có kiểu, commit `d4d8b90`) nhưng **phần lõi ý tưởng** — để council TỰ CHỌN đề thi (app mẫu ngoài-khuôn + bộ harass 8 loại vector), thay vì người tự chọn — chưa từng thực hiện; task `T-260702-02` đứng yên `proposed` từ 2026-07-02 tới nay.

## Bối cảnh & bằng chứng

Verify bằng 6 nguồn độc lập (không chỉ 1 lần grep), tất cả khớp nhau:

1. **Task-store**: `harness/metrics/tasks.json` → `T-260702-02` state=`proposed`, `history` chỉ có 1 entry duy nhất từ 2026-07-02 — chưa từng advance.
2. **`harness/scripts/council.py`**: 0 hit cho "harass / self-index / 8 loại vector / ludic fallacy" — cơ chế "council tự chọn đề thi" không nằm trong script chính.
3. **Wiki cross-ref**: [[wiki-core-relations]] trỏ ngược `[[020726-council-chon-de-thi-self-index]]` làm Proposal nguồn — xác nhận nó là **con** của proposal gốc, không phải toàn bộ scope.
4. **Git log**: commit `d4d8b90` ("feat(wiki-core): ledger sự kiện + relations có kiểu + validator R-rel bước 1+2&3") có thật — phần hạ tầng nền đã ship.
5. **Report tự nhận dở dang**: `llmwiki/html/archive/reports/030726-self-index-benchmark-report.html` (còn nguyên, đã archive không mất) kết luận nguyên văn: *"xác nhận engine robust ở mặt thiết kế, chưa anti-fragile ở đuôi ngoài-mẫu. Phạm vi: mới test build-wiki-graph.py đơn lẻ; hook auto-touches + validator rel_integrity + code-graph MCP chưa exercise — cần run tích hợp mới kết luận toàn hệ."*
6. **Validator được report tự nhắc chưa exercise**: `rel_integrity` — không tồn tại trên đĩa (chỉ có `fdk/tools/wiki-relations.py`, khác tên khác việc) — khớp đúng lời report tự thú.

Overlap một phần với `/fdk-poc` (đã cài global, thật): nó phủ "dự án thật + curl-cài + ghi log thật", nhưng **không có** phần "council tự chọn đề thi" — nên không thay thế được scope còn lại của issue này.

## Phạm vi

- Dựng một app mẫu **ngoài khuôn** (không phải wiki của chính framework) để test không bị quen tay/ludic fallacy.
- Cơ chế để **council** (nhiều persona/model) tự chọn app mẫu + bộ harass, thay vì người chọn sẵn.
- Chạy đủ harass 8 loại vector quan hệ (hiện chỉ mới test `build-wiki-graph.py` đơn lẻ).
- Exercise `hook auto-touches` + một validator kiểu `rel_integrity` (report gọi tên này nhưng chưa hiện thực) + `code-graph` MCP trong cùng một vòng tích hợp.

## Không thuộc phạm vi

- Không đụng lại phần đã ship (ledger sự kiện, relations có kiểu — giữ nguyên, đã proven qua `d4d8b90`).
- Không thay thế `/fdk-poc` — hai việc khác lớp (fdk-poc = chạy /br thật; issue này = council tự chọn đề thi để chống ludic fallacy của chính framework).
- Không bắt buộc làm ngay — priority P3, độ rủi ro nếu bỏ là thấp (hạ tầng nền vẫn hoạt động tốt mà không cần phần này).

## Hướng gợi ý (không bắt buộc)

- Bước 1 nhỏ nhất: hiện thực validator `rel_integrity` mà report `030726-self-index-benchmark-report.html` đã giả định tồn tại — đối chiếu với `fdk/tools/wiki-relations.py` xem có tái dùng được không.
- Bước 2: mở `/wayfinder` nếu scope thấy vẫn còn mù mờ (việc quá lớn một phiên) trước khi `/propose` chi tiết.

## Tiêu chí HOÀN THÀNH

- Council (không phải người) tự chọn được app mẫu + bộ đề harass, có ghi log quyết định.
- Hook auto-touches + validator quan hệ (rel_integrity hoặc tương đương) + code-graph MCP đều được exercise trong một vòng tích hợp, không còn "test đơn lẻ".
- Kết luận benchmark mới (kế thừa `030726-self-index-benchmark-report.html`) trả lời được câu report cũ bỏ ngỏ: hệ có anti-fragile ở đuôi ngoài-mẫu không.

## Assign & lý do

- **Assignee**: @Rheinmir (chủ repo, quyết định độ ưu tiên).
- **Dispatch**: Claude — cần phán đoán thiết kế (chọn app mẫu, cơ chế council-chọn), không phải việc boilerplate.
- **Entry**: `/fdk` — đây là việc phát triển framework, không phải feature dự án downstream.
- **Priority P3**: hạ tầng nền đã chạy tốt mà không cần phần này; đây là nợ làm-cho-chắc, không phải nợ chặn đường.

## Origin

- **Tracker:** [GH#81](https://github.com/Rheinmir/setup/issues/81) (mirror, label `ready-for-human`) — ledger này vẫn là nguồn chân lý.
- Raised bởi phiên 2026-07-18, sau khi rà 8 draft ⏱ TREO (JOIN `task:` frontmatter ↔ `harness/metrics/tasks.json` state, wired vào `docs-curate.py` cùng phiên).
- Nguồn gốc thật: draft `020726-council-chon-de-thi-self-index.md` (task `T-260702-02`, 2026-07-02) — draft đó nay archive, phần scope còn lại chuyển hẳn về issue này để không mất dấu.
- Bằng chứng: xem mục "Bối cảnh & bằng chứng" ở trên — 6 nguồn tra chéo, không phải suy đoán từ 1 lần grep.
