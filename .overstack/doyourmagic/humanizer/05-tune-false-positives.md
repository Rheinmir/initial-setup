# 05 — Chặn sửa quá tay: false positive và chi tiết người cần giữ

**Vì sao dùng:** rủi ro lớn nhất của Humanizer không phải sửa thiếu, mà **sửa quá tay** — bào mất giọng thật, gỡ mất một disclaimer pháp lý, hay viết lại một câu trích dẫn. `SKILL.md` có sẵn hai hàng rào cho việc này; file này chỉ ra cách gọi thẳng chúng.

**Sinh ra cái gì:** một lượt chạy có phạm vi hẹp hơn, giữ được thứ đáng giữ.

> Lệnh trong file này gõ trong **khung chat của agent**.

## Danh sách "không được gắn cờ"

`SKILL.md` → "Check for false positives" liệt kê những thứ **tự nó không phải bằng chứng AI**. Đáng nhớ nhất:

- **Ngữ pháp chuẩn, style nhất quán.** Nhiều người viết là dân chuyên hoặc đã qua biên tập.
- **Từ trang trọng, học thuật.** §7 chỉ nhắm một danh sách từ cụ thể, không phải mọi từ trang trọng.
- **Curly quote đứng một mình.** macOS, Word, Google Docs tự bo nháy theo mặc định.
- **Em dash đứng một mình.** Nhiều biên tập viên và nhà báo dùng thường xuyên. Chỉ tính là dấu hiệu khi đi kèm nhịp văn quảng cáo sáo.
- **Một câu ngắn để nhấn.** Chỉ gắn cờ khi nhiều mảnh câu kịch tính nối nhau.
- **Mở đoạn lặp có chủ ý.** "She came. She saw. She conquered." là nhịp, không phải lỗi.
- **"Honestly" hay "look" giữa câu.** Dấu hiệu là cái mở bài kịch, không phải bản thân từ đó.
- **Giới hạn và disclaimer có ích.** Giữ nguyên tuyên bố phạm vi, cảnh báo pháp lý và an toàn, đính chính thật, phản biện có nêu nguồn, câu trả lời FAQ.
- **Phương án thật.** Trong design doc hay tutorial, giữ các lựa chọn người đọc có thể cân nhắc. Chỉ bỏ phương án viển vông bị gạt rồi không bao giờ nhắc lại.
- **Văn dẫn lại.** Không viết lại cụm bị theo dõi khi nó nằm trong ngoặc kép, tiêu đề, tên riêng, hoặc ví dụ đang được đem ra bàn.
- **Bản sửa trước 30/11/2022.** Mốc ChatGPT ra công chúng.

Luật chung: *"When unsure, look for several patterns together. One em dash proves nothing."*

## Chi tiết người cần giữ

`SKILL.md` → "Human details to keep" — những thứ chở giọng người, phải giữ trừ khi làm hỏng nghĩa: chi tiết lạ và cụ thể, cảm xúc lẫn lộn chưa ngã ngũ, tiếng lóng gắn năm tháng, lựa chọn ngôi thứ nhất có chủ ý, độ dài câu không đều, và những câu tự ngắt lời mình trong ngoặc đơn.

## Cách gọi hàng rào đó ra một cách rõ ràng

Khi bản trả về nghe nhạt hơn bản gốc:

```text
Bản viết lại đã bào mất giọng. Chạy lại và bám mục "Human details to keep" —
giữ các asides, câu tự sửa mình, và nhịp câu dài ngắn không đều của bản gốc.
```

Khi nó gỡ mất thứ phải giữ:

```text
Bạn đã bỏ đoạn giới hạn phạm vi ở cuối. Theo mục "Check for false positives",
disclaimer có ích phải giữ nguyên. Trả lại đoạn đó rồi đưa lại bản cuối.
```

Khi nó viết lại một câu trích dẫn:

```text
Đoạn trong ngoặc kép là trích dẫn nguyên văn, thuộc mục "Secondhand text" —
không được sửa. Chỉ chữa phần văn xuôi quanh nó.
```

## Khoá phạm vi ngay từ đầu

Rẻ hơn là chặn trước thay vì sửa sau:

```text
/humanizer

Văn kỹ thuật, giữ trung tính, không thêm cá tính.
Không đụng gì trong ngoặc kép và trong code block.
Chỉ sửa §7, §14, §23.

[văn bản]
```

## Kiểm bằng mắt: có mất claim nào không

Bước 3 trong quy trình bắt skill tự hỏi có thêm hoặc mất fact nào không. Bạn nên kiểm lại độc lập, nhất là ở chế độ file:

```bash
git diff --word-diff -- docs/launch-post.md
```

Đọc riêng các cụm bị xoá. Mỗi tên, số, ngày, citation bị mất là một lỗi theo đúng luật của skill — báo lại và bắt nó khôi phục.
