---
name: dym-browser-use-qa
disable-model-invocation: true
description: "Chấm điểm 1–5 một site/app kèm bằng chứng — không phải bãi ảnh chụp. Bám điểm vào HOÀN THÀNH TÁC VỤ trước, rồi trừ theo lỗi console/network và độ thô ráp. Dùng khi user hỏi 'trang này ổn chưa', 'QA giúp cái flow này', 'chấm điểm UI', hoặc khi /br qc cần một verdict có thể cãi lại được."
---

# dym-browser-use-qa

Chắt từ `skills/qa/references/methodology.md` của browser-use (đọc 09/2026). Phần
đáng lấy nhất KHÔNG phải cách lái trình duyệt — mà là **kỷ luật ra verdict**.

## When to use
- Cần một câu trả lời "tốt/xấu mức nào" có số, không phải "đây là ảnh chụp, anh xem đi".
- `/br qc` hoặc `/qc-uiux` cần một mục chấm UI/UX đứng vững trước phản biện.

## Steps
1. **Diễn lại yêu cầu thành một tác vụ người dùng cụ thể** — "test signup" → "tạo tài khoản
   bằng email mới → tới được dashboard". Định nghĩa thành công TRƯỚC khi chạm trình duyệt.
   Yêu cầu mơ hồ → chọn happy path hiển nhiên nhất và **ghi rõ đã chọn gì** trong báo cáo.
2. **Lái như người dùng thật** — `/dym-browser-use repl` cho luồng nhiều bước. Chụp ảnh sau
   MỖI hành động có ý nghĩa và **kiểm chứng trang đổi đúng như kỳ vọng** — đừng giả định
   cú bấm đã ăn.
3. **Moi lỗi ảnh chụp không thấy** sau mỗi bước — `drain_events()` lọc
   `Runtime.exceptionThrown`, `Runtime.consoleAPICalled type=="error"`, `Network.loadingFailed`,
   `Network.responseReceived status>=400`. *Một trang trông đẹp nhưng ném lỗi ở mọi cú bấm
   không phải điểm 5.*
4. **Thăm dò quá happy path một nhịp** — submit trường bắt buộc để trống, email sai định dạng,
   nút back. Sản phẩm tốt xử lý êm; sản phẩm hỏng rò stack trace hoặc im lặng không phản hồi.
5. **Chấm, kèm dẫn chứng.**

## Thang điểm
| Điểm | Nghĩa |
|---|---|
| **5** | Tác vụ xong sạch. Không lỗi, không vướng, phản hồi nhanh, chỉn chu. |
| **4** | Tác vụ xong. Vướng vặt về thẩm mỹ/UX (tải chậm, chữ khó hiểu, một console warning) nhưng không chặn. |
| **3** | Tác vụ xong nhưng có ma sát thật — một bước rối, phải lách, một lỗi không chặn. Dùng được, không tốt. |
| **2** | Chỉ xong một phần. Một bug đáng kể chặn mất một đoạn, hoặc phải thử lại mới qua. |
| **1** | Không xong được. Nút chết, crash, spinner vô tận, trang không tải, mất dữ liệu. |

**Neo điểm vào HOÀN THÀNH TÁC VỤ trước, rồi mới chỉnh theo lỗi và độ chỉn chu.**
"Chạy được nhưng ném 3 lỗi console" là 3–4, không phải 5. "Đẹp nhưng nút submit không làm gì"
là 1, không phải 4 — đẹp không cứu được luồng gãy.

Hỏi nhiều thứ (vd "test search VÀ filter") → chấm từng mục, rồi **điểm tổng phản ánh đường
tới hạn YẾU NHẤT**. Không được bình quân một luồng gãy lên vì trang chủ đẹp.

## Định dạng đầu ra
```
Score: 3/5

Task: Đăng ký bằng email mới và tới dashboard.
Result: Xong, nhưng có ma sát.

Chạy được:
- Form nhận input hợp lệ, tạo tài khoản, chuyển hướng dashboard.

Vấn đề:
- [chặn?] không — lỗi "Email already in use" render thành "[object Object]" (thấy khi thử lại).
- [console] TypeError trong analytics.js ở mọi trang (Runtime.exceptionThrown, xem /tmp/qa-03.png).
- [ux] submit không có chỉ báo tải; đứng hình ~4s.

Edge đã thử: email trống (xử lý, có lỗi inline ✓), submit chậm 8s (không spinner ✗).
Evidence: /tmp/qa-01-landing.png, /tmp/qa-03-error.png
```

## Rules
- **Đừng tin một ảnh chụp sạch.** Luôn `drain_events()` — analytics crash, API 4xx/5xx,
  promise rejection không hiện lên pixel nào.
- **Reset state giữa các lần chạy** với luồng một-lần (đăng ký bằng email đã dùng) — dùng giá trị
  mới hoặc tab sạch, để cái sai là lỗi của site chứ không phải state cũ.
- **Đo thời gian những thứ đáng đo.** Tải 12 giây hoặc spinner không bao giờ dứt là một dữ kiện
  chấm điểm, không phải chú thích cuối trang.
- **Dừng ở tường auth/thanh toán không vượt qua được một cách chính đáng.** Chấm phần đã kiểm
  được, nói thẳng phần nào không tới được và vì sao.
- **Cẩn thận với hành động thật, bị tính tiền, hoặc phá huỷ.** App tự cấp phát tài nguyên
  (dựng VM, gửi email, quẹt thẻ) → chạy TỐI THIỂU một cái, không loạt; tránh nút "xoá tất cả"/
  "dừng tất cả" có thể phá state không phải của mình. Chỉ dọn thứ mình tạo.
- **Chép lại được.** Ghi đúng URL, đúng các bước, đúng input đã dùng.
- Touch only what the task requires — no opportunistic changes.
