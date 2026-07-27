---
type: issue
kind: architecture
title: "Auto-wire loop chống-lạc-quan: grader/anti-fabrication tự-kích qua hook, không đợi gọi skill tay"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, orchestration, hooks, evaluation, closed-loop, council, wikieval, trace-grader, failure-flywheel]
timestamp: 2026-07-11
id: 110726-auto-wire-eval-loop
source_session: phản biện của user — overstack có đủ component nhưng không có luồng tự động nối chúng
---

# Issue: Các guard chống-lạc-quan là skill gọi TAY — thiếu loop tự đóng

## Vấn đề (một câu)
Overstack có đủ mảnh (`council`, `wikieval`, `trace-grader`, `claim-receipts`, `failure-flywheel`) nhưng KHÔNG có luồng tự động nối chúng: mọi guard đều là **skill user phải nhớ gọi** — mà đúng lúc lạc quan/vội nhất thì không ai gọi, nên guard rỗng tác dụng khi cần nhất.

## Bối cảnh & bằng chứng
- Bằng chứng trực tiếp: 2 issue vừa raise ([[110726-eval-blinding-grader-context]], [[110726-anti-fabrication-observed-metrics]]) đều đặt vấn đề ở **tầng component**. User phản biện đúng: giá trị đắt nhất của nguồn tham khảo KHÔNG phải từng component (mình có đủ) mà là **wire tự động thành loop khép kín** — grader tự chấm sau *mỗi* lần worker sinh output, scheduler tự nhắc khi mở app, luật cấm-bịa chạy trong mạch, người dùng chỉ thấy 3 lệnh.
- Hiện trạng overstack: `council`/`wikieval`/`trace-grader`/`failure-flywheel` = skill gọi tay. `claim-receipts` đã là gate (gần tự động nhất) nhưng chưa nối với các guard còn lại.
- Infra ĐÃ CÓ để tự-kích nhưng chưa dùng cho eval: SessionStart hook đang chạy `wiki-sync`/`orientation`; `harness/hooklib.py`, `post_tool_use.py`, `pre_tool_use.py` tồn tại — mới dùng cho nhắc-nhở/lint, CHƯA dùng để tự-kích chuỗi eval/anti-fabrication.
- Nguyên tắc: một guard chống lạc quan chỉ có giá trị khi **tự chạy**; guard phải-nhớ-gọi bị bỏ qua đúng lúc cần nhất.

## Phạm vi
- Lớp orchestration/hook: `harness/hooklib.py`, `post_tool_use.py`, SessionStart hook, và điểm nối tới `council.py`/wikieval/trace-grader/claim-receipts.
- Universal (kỷ luật framework).

## Không thuộc phạm vi
- Không xây lại từng component (blinding schema, claim class là 2 issue con riêng).
- Không tự-chạy MỌI thứ vô tội vạ — phải chọn trigger đúng + có ngắt (chi phí token, đệ quy hook như R13 đã từng nổ — xem `precommit-r13-recursion-bug`).

## Hướng gợi ý (không bắt buộc)
- Định nghĩa 1-2 **trigger tự động** cụ thể thay vì "tự động hoá mọi thứ":
  - post-produce: sau khi một skill/worker sinh artifact "đáng chấm" → tự kích grader mù (dùng schema của #71).
  - claim-receipts mở rộng (#72) chạy sẵn trong mạch commit/produce.
- Loop phải có **phanh**: opt-in per-loại-artifact, ngân sách token, chống đệ quy hook.
- Đây là orchestration — cân nhắc để `/orca-workflow` hoặc loop-runner cầm nhịp thay vì nhồi vào hook thô.

## Tiêu chí HOÀN THÀNH
- Ít nhất 1 chuỗi guard chạy KHÔNG cần user gọi skill (vd grader mù tự kích sau một loại produce), có phanh + tắt được.
- Tài liệu 1 sơ đồ: trigger → guard nào → kết quả đi đâu.

## Assign & lý do
- @Rheinmir / Claude / `/fdk`, P1: đây là gap kiến trúc bao trùm 2 issue con; quyết trigger + phanh là việc người giữ harness/hook.

## Origin
Raised bởi `/raise-issue` (phiên 2026-07-11) từ phản biện của user: "workflow gọi bằng skill thì sao? làm gì có luồng tự động nối mấy cái này với nhau?". Distill từ một plugin học-tập cộng đồng có loop tự đóng (grader tự chấm mọi buổi + scheduler tự nhắc); nguồn chỉ tham khảo, không kèm tác giả/repo.
