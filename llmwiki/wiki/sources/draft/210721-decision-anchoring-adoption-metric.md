---
type: issue
kind: process
title: "decision-anchoring: chưa có metric adoption, chưa có kill-switch nếu không ai dùng"
status: open
assignee: grower
dispatch: Claude
entry: /fdk
priority: P3
tags: [issue, decision-anchoring, adoption, telemetry, grower]
timestamp: 2026-07-21
id: 210721-decision-anchoring-adoption-metric
source_session: "phiên /fdk 2026-07-21 — soi SPEC 210721-decision-anchoring.md bằng lens persona grower/tester (`persona-lens-beneficiary`)"
---

# Issue: decision-anchoring chưa có metric adoption, chưa có kill-switch

## Vấn đề (một câu)
`llmwiki/wiki/sources/draft/210721-decision-anchoring.md` (task `T-260721-03`) có 8 success criteria (`SC-001`..`SC-008`), toàn bộ đo correctness (cơ chế chạy đúng hay sai) — không cái nào đo adoption (có ai thực sự dùng `anchor_symbol`/`why` sau khi dựng xong hay không), và không có ngưỡng kill-switch nếu adoption thấp.

## Bối cảnh & bằng chứng
Soi bằng lens `[[grower]]` (`llmwiki/personas/grower.md`) — DO đầu tiên của persona này: *"mỗi thay đổi nêu metric mục tiêu + guardrail metric (đừng để win cục bộ hại retention/cost)"*. SPEC hiện không có metric mục tiêu nào cho adoption, chỉ có metric cho correctness.

Đáng chú ý: chính `## Context` của SPEC đó tự trích dẫn root-cause đã từng xảy ra thật trong repo này — quan hệ `touches` từng bị khai tay trong frontmatter, đóng băng ở 21 cạnh suốt 18 ngày, đúng vì *"thứ không ai tiêu thụ thì không ai nuôi"* (xem bàn giao `200726-graph-foundation-handoff`). SPEC dùng bài học đó để biện minh cho thiết kế suy-ra-đừng-cất, nhưng không tự áp lại bài học đó cho chính cơ chế mới của nó — không có gì đảm bảo `anchor_symbol` sẽ không lặp lại đúng số phận của `touches`.

Chưa vá NGAY trong SPEC gốc vì đúng ranh giới persona: `grower.md` đòi *"sản phẩm đã dựng xong → lặp dựa trên dữ liệu dùng thật"* — decision-anchoring chưa dựng (`T1`-`T9` toàn `pending` tại thời điểm raise issue này), nên đo adoption thật chỉ có ý nghĩa SAU khi build xong và có dữ liệu dùng thật, không phải lúc propose. Đây là quyết định "chạm ranh giới ≠ vứt ý" theo đúng điều khoản ghi trong chính `grower.md`.

## Phạm vi
Chỉ `decision-anchoring` (`mechanisms.yaml`/ADR `anchor_symbol`) sau khi `T1`-`T9` của `210721-decision-anchoring.md` đã xanh. Không đụng SPEC gốc trong đợt raise-issue này.

## Không thuộc phạm vi
- Không tự ý thêm metric vào SPEC đang chờ duyệt (đó là việc của `grower` khi tới lượt, không phải việc của người raise issue).
- Không thiết kế lại telemetry — tái dùng nguyên `fdk/tools/skill-usage.py` (đã có pattern đo tần suất: count/sessions/last_used/this_week/prev_week), không xây engine đo mới.

## Hướng gợi ý (không bắt buộc)
- Metric mục tiêu: % mục `mechanisms.yaml`/ADR mới có `anchor_symbol` trong 30 ngày kể từ khi viết; số lần gọi `why` mỗi tuần.
- Guardrail: nếu adoption dưới ngưỡng X sau N tuần → xét lại có nên giữ cơ chế hay để nó chết như `touches` từng chết (`success-flywheel`-style: chỉ giữ thứ thắng trên holdout, không overfit theo cảm tính).
- Ngưỡng X/N cụ thể để `grower` tự quyết khi có dữ liệu thật — không đoán trước ở đây.

## Tiêu chí HOÀN THÀNH
- `decision-anchoring` có ít nhất một SC đo adoption (không phải correctness) + một ngưỡng kill-switch bằng số, không phải "sẽ xem xét sau".
- Ngưỡng đó neo được vào dữ liệu telemetry thật (tái dùng `skill-usage.py` pattern hoặc tương đương), không phải cảm tính.

## Assign & lý do
`assignee: grower` — đúng phase iterate-PMF của persona này; việc chỉ có ý nghĩa sau khi `decision-anchoring` đã dựng xong và có dữ liệu dùng thật, khớp DO đầu tiên của `grower.md` ("đo trước khi đổi, có baseline").

## Origin
- Raise bởi: phiên `/fdk` 2026-07-21, ngay sau khi soi `210721-decision-anchoring.md` bằng lens `grower`+`tester` (persona-lens-beneficiary).
- Nguồn: `[[grower]]`, `llmwiki/wiki/sources/draft/210721-decision-anchoring.md`, bàn giao `200726-graph-foundation-handoff` (bài học `touches`).
