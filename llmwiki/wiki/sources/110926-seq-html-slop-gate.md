---
type: source
title: "Sự cố: seq html dạng danh sách lọt cổng R7/R11 dù không có sơ đồ nào"
status: shipped
tags: [incident, propose, r7, r11, diagram, archify, gate]
timestamp: 2026-09-11
---

# Sự cố: seq html dạng danh sách lọt cổng R7/R11 dù không có sơ đồ nào

## Triệu chứng

Ngày 10/09/2026 user mở trang `100926-ticket-composer-a-seq.html`, trang cặp đôi của proposal F6 lô a (Ticket Composer), chép từ một máy khác. Trang tự gọi mình là "sequence diagrams" nhưng không có sơ đồ nào. Mỗi task chỉ gồm một hàng chip tên thành phần (Owner, Dashboard, nginx, Gate), một danh sách bước có gắn nhãn ADD / BLOCK / LEGACY, và một đoạn văn xuôi. Vậy mà trang đi qua mọi cổng của overstack và tới tay người duyệt.

## Tái hiện

Dựng lại proposal 7 task trỏ tới đúng file html thật, rồi chạy hai cổng bằng code cũ: R7 (`proposal_complete.py`) trả mã 0 và R11 (`llmwiki-validate.py files`) cũng trả mã 0. Nói cách khác, một trang không có sơ đồ nào vẫn được coi là đủ chuẩn để hỏi duyệt.

## Nguyên nhân gốc (5-Why)

1. Trang không có sơ đồ vì agent làm đúng lời dặn ở bước 7 của `/propose`: "clone an existing `llmwiki/html/*-seq.html`".
2. Khung được clone vốn đã không phải sequence diagram. Class `.lifeline` chỉ là một thẻ `<span>` hiện thành chip, còn `.msg` là một dòng chữ có mũi tên "→" viết trong văn bản. Tên class hứa nhiều hơn những gì trang thật sự vẽ ra, và mọi seq html cũ trong repo (trừ một trang archify) đều theo khung này.
3. Cổng không bắt được vì cả hai chỉ kiểm hình thức. R7(c) đếm chuỗi `<div class="diagram-box"` (trang có 7, đủ cho 7 task), R7(e) đếm `class="desc"`, còn R11 chỉ soi các marker CSS của phong cách kính (`backdrop-filter`, gradient `#f7fbff`, bóng `inset`), và chỉ khi trang có chứa `diagram-box`.
4. Không có cổng nào soi hình học vì cổng hình học duy nhất của framework (9 phép kiểm của archify cộng `visual-check`) chỉ chạy khi sơ đồ đi qua `/diagram`. `/propose` giữ một định dạng vẽ tay riêng, chạy song song với engine đã có cổng.
5. Cấu trúc sinh ra lỗi là như vậy: một cổng mang tên "sơ đồ" xác nhận đúng hình thức của một khung tự chế, trong khi khung đó không phải sơ đồ. Đây là cùng một gốc với bài học đã ghi trước đó rằng mọi sơ đồ phải đi qua `/diagram` thay vì để model tự dựng hình.

## Cách sửa

Commit `bda0fc6` sửa ba chỗ. R7(c) giờ chỉ tính sơ đồ thật đối với draft đặt tên từ 10/09/2026: mỗi task phải có một artifact archify mà trang seq nhúng hoặc trỏ tới (qua `iframe`, `a` hay `embed`), và artifact đó phải tồn tại trên đĩa, mang chữ ký archify và có `<svg>`. Draft cũ hơn giữ luật cũ để không đỏ hồi tố, còn draft không đọc được ngày thì bị áp luật mới. Bước 7 của `/propose` (bản canonical và bản mirror) giờ yêu cầu viết một spec archify `sequence` cho mỗi task và render qua `/diagram`. Fixture GOOD của R7 trong `harness-doctor` được đổi sang chuẩn mới.

Vì user hỏi về chi phí, bước 7 kèm thêm hai ràng buộc chống đốt token. Thứ nhất, `deliver` và `visual-check` của mọi task phải gộp vào một lệnh shell để N sơ đồ chỉ tốn một lượt model. Thứ hai, spec chỉ được sửa tối đa hai vòng, còn đỏ thì dừng lại hỏi user. Số đo làm căn cứ: bản thân archify tốn 0 token (`deliver` 0,13 giây, `visual-check` 6,3 giây), nhưng một phiên vẽ sơ đồ trước đó đã gọi `validate` 57 lần ở mức context khoảng 430 nghìn token mỗi lượt, tức khoảng 44 triệu token đọc lại cho một trang.

## Kiểm chứng

Trên đúng file thật, R7 chuyển từ mã 0 sang mã 2 với lỗi (c). Self-test của R7 đạt 8/8 (có hai ca đỏ, một ca draft cũ, một ca trang nhúng đủ artifact), `auto-index-and-grounding-test.sh` đạt 4/4, 47 draft hiện có không đổi kết quả so với trước khi sửa, `harness-doctor` báo 19/19 rail còn cắn, và `medic --ci` không còn mục đỏ.

## Còn mở

R11 vẫn chỉ áp khi trang có `diagram-box`. Trang seq theo chuẩn mới nhúng sơ đồ bằng `iframe` nên sẽ không còn chuỗi đó, và phần vỏ trang sẽ không bị soi phong cách kính. Lỗi này không làm lọt trang thiếu sơ đồ, nhưng cần xử lý nếu muốn giữ phong cách thống nhất. Bản global `~/.claude/harness` chỉ nhận R7 mới khi chạy lại bootstrap.

## Origin

- Commit sửa: `bda0fc6` trên nhánh `orca` (`harness/validators/proposal_complete.py`, `skills/propose/SKILL.md`, `harness/scripts/harness-doctor.py`).
- Repro: file `llmwiki/html/100926-ticket-composer-a-seq.html` do user chép từ máy khác ngày 10/09/2026, cùng ảnh chụp màn hình user gửi trong phiên 667058a4.
- Failure-flywheel: class `gate-checks-form-not-substance`.
- Liên quan: [[080926-archify-fork-pin]].
