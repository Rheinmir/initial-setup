Version 1.1.0:

- Added **capproof — checklist năng lực tự soi**: mọi năng lực (skill/rule/tool/cơ-chế) được resolver đa tầng map sang một bằng chứng chạy được; `medic` gác kiểu ratchet (năng lực mới thiếu proof hoặc tụt proof → đỏ). Tại bản này: **197/197 năng lực có proof, 0 nợ**; `fdk-gate` 20/20 step xanh.
- Added **engines-smoke**: 20 engine + 2 cơ chế từng thiếu bằng chứng giờ được CHẠY THẬT trong sandbox ở mỗi lần CI — execute với input thật, assert exit-code + output thật, không phải danh sách tên cho có.
- Added vai thứ 6 **TESTER (`/test`)** — đủ bộ 6 archetype (prototyper/builder/sweeper/grower/maintainer/tester); persona travel xuống global khi cài.
- Added **hòa tan 6 nguồn ngoài**: review code 13 nhóm + severity (`qc-code`), security-review, frontend-design (hallmark + kỷ luật giao diện xuyên màn hình), memory import/export, receiving-review + systematic-debugging.
- Added **ledger-snapshot**: cuối phiên tự gom các ledger (flywheel/memory/events/audit/tasks) thành tarball có prune + round-trip dedupe — ký ức máy-local sống sót mất máy.
- Added **flywheel auto-capture**: rule cắn tự vào ledger bằng code, không chờ ai nhớ gõ.
- Added lint mở rộng: nhịp docs-sprawl (`/docs-curate`), claim-receipts trên draft active (ref chết → bêu tất định), JOIN trạng thái task ↔ draft để biết proposal nào outdated, cờ ⚑ kèm hồ sơ từng file drift.
- Added **provenance re-verify scope hẹp**: chỉ skill NGOÀI (external-pull) bị sửa lén sau khi pin mới đỏ — skill local sửa hằng ngày không còn cries-wolf.
- Changed **3 cơ chế đo bật luôn** (wikieval / retrieval-eval / failure-flywheel) — không cần kích hoạt tay; wikieval từ chối ghi baseline thiếu outputs.
- Changed **harness travel đầy đủ xuống downstream**: installer clone theo đúng ref đang cài, harness-doctor fire-drill chạy ở CI downstream, rule riêng dự án (harness-local) có fire-drill luôn-mới.
- Changed CI: **mọi test trong `harness/tests/` đều được wire** + guard `tests-wired` — test mới quên wire là CI đỏ; probe medic mới chưa khai map cơ-chế cũng đỏ (PROBE_MECH_MAP).

Known limitations:
- GH#81 (phần còn lại của council-self-index) ở trạng thái ready-for-human — đã ghi đủ bối cảnh, chưa thực hiện.
- Một số draft cũ còn treo trạng thái task (7 ca TREO) — đã có hồ sơ trong lint, chờ chốt cách đóng.
- Grounded-audit (đưa LLM + vector vào lint để thẩm nội dung propose) mới ở mức đề xuất, chưa build.
