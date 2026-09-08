---
name: dym-humanizer-humanize-pasted-text
description: "Chữa văn bản dán trực tiếp (chế độ mặc định). đây là đường chính. Bạn dán văn bản nghe "mùi AI", Humanizer trả lại bản viết như người viết mà không đổi nội dung."
disable-model-invocation: true
---

# Skill: dym-humanizer-humanize-pasted-text — Chữa văn bản dán trực tiếp (chế độ mặc định)

**Vì sao dùng:** đây là đường chính. Bạn dán văn bản nghe "mùi AI", Humanizer trả lại bản viết như người viết mà **không đổi nội dung**.

**Sinh ra cái gì:** ba phần trong một lượt trả lời — bản nháp, danh sách ngắn các pattern AI còn sót, và bản cuối.

> Mọi lệnh trong file này gõ trong **khung chat của agent**, không phải terminal.

## Cách gọi

```text
/humanizer

[dán văn bản vào đây]
```

Nếu cài theo đường plugin (workflow `02`), gọi `/humanizer:humanizer`.

Hoặc nói tự nhiên, không cần slash:

```text
Humanize đoạn này giúp tôi: [văn bản]
```

## Cái bạn nhận lại

`SKILL.md` mục "How to return the result" quy định chế độ mặc định (văn bản dán) trả về **ba phần**:

1. **Bản nháp** — lượt viết lại đầu tiên, không coi cấu trúc gốc là bất biến.
2. **Phần soi lại** — danh sách ngắn chỗ nào vẫn còn nghe máy.
3. **Bản cuối** — bản đã viết lại sau khi soi.

Thấy đủ ba phần nghĩa là skill đã chạy đúng quy trình. Chỉ nhận được một khối văn bản trơn thì hoặc agent đang chạy chế độ khác (xem `04`), hoặc skill chưa được nạp.

## Quy trình bên trong (4 bước, trích `SKILL.md` → "Rewrite process")

1. Đọc nguồn và đánh dấu từng pattern AI.
2. Viết nháp. Đọc to lên. Soi nhịp câu, chi tiết, động từ đơn giản (*is*, *has*), mức trang trọng.
3. Tự hỏi hai câu: **"Chỗ nào vẫn nghe như AI?"** và **"Bản viết lại có thêm hay mất fact, tên, số, ngày, trích dẫn, citation, thứ hạng nào không?"** Thêm hoặc mất đều tính là lỗi.
4. Viết bản cuối theo ý, không vá từng cụm bị gắn cờ.

## Khớp giọng của bạn

Đưa mẫu văn của chính bạn thì kết quả bám giọng đó thay vì luật style mặc định:

```text
/humanizer

Đây là mẫu văn của tôi để khớp giọng:
[dán 2-3 đoạn bạn tự viết]

Giờ humanize đoạn này:
[dán văn bản AI]
```

Mẫu văn **đè lên** luật style, kể cả luật gạch ngang §14 ("Em and en dashes"). Nguyên văn trong `SKILL.md`: *"A writing sample takes priority over these style rules. If the sample uses em dashes, keep them at about the same rate. Do not apply §14 as a ban."*

Skill sẽ bám nhịp câu, cách chọn từ, cách mở đoạn, dấu câu và cả tật viết cố ý trong mẫu.

## Ranh giới cứng: không bịa

Skill bị cấm thêm fact, tên, số, ngày, trích dẫn hay citation không có trong nguồn hoặc không do bạn cung cấp. Nếu một câu cần chi tiết còn thiếu, nó phải **hỏi bạn** hoặc viết câu đơn giản hơn. Nó được phép thêm ý kiến hoặc phản ứng khi giọng người viết cho phép — nhưng không được thêm claim mang tính sự kiện. Truyện hư cấu là ngoại lệ.

Nên khi Humanizer hỏi lại "tháng mấy?", "khu nào?" thay vì trả bài luôn, đó là hành vi đúng, không phải nó lười. Ví dụ đầy đủ trong `README.md` ghi rõ điều này ngay dưới tiêu đề "Full example".

## Khi nào nó được thêm cá tính

- **Có cá tính:** blog, tiểu luận, bài quan điểm, viết cá nhân.
- **Giữ trung tính:** văn tham khảo, kỹ thuật, pháp lý, văn nêu sự kiện.

Nếu bạn nhận lại một trang tài liệu API bỗng có giọng đùa, đó là lỗi — nói rõ "đây là văn kỹ thuật, giữ trung tính" rồi chạy lại.

## 35 pattern nó rà

Sáu nhóm, đánh số 1–35 trong `SKILL.md`, bảng đối chiếu before/after nằm trong `README.md`:

| Nhóm | Số hiệu | Ví dụ đại diện |
|---|---|---|
| Content | 1–6 | thổi phồng tầm quan trọng, nguồn mơ hồ, mục "thách thức và triển vọng" |
| Language & grammar | 7–13 | từ AI hay dùng, né *is/are*, "not X but Y", bộ ba gượng |
| Style | 14–19, 26–35 | gạch ngang, bold quá tay, emoji, punchline giả, mở bài giả-thật-lòng |
| Chatbot | 20–22 | "I hope this helps!", rào đón giới hạn kiến thức, giọng nịnh |
| Filler & hedging | 23–25 | "in order to", chồng qualifier, kết bài lạc quan sáo |

Muốn nhắm một pattern cụ thể thì nêu số hiệu:

```text
/humanizer

Chỉ sửa §14 và §18 trong đoạn này, giữ nguyên phần còn lại:
[văn bản]
```
