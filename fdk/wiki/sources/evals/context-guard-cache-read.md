---
type: eval
id: context-guard-cache-read
title: "Gác đầy context — vì sao đo input_tokens là sai khi có prompt cache"
input: "Cơ chế 'đầy context thì tự xoay phiên' của overstack từng không bao giờ kích hoạt dù phiên rất dài. Vì sao, và độ đầy context phải đo thế nào?"
expected: "Trigger cũ chỉ cộng input_tokens (phần KHÔNG cache) nên phiên 367 lượt chỉ ra 3 866, luôn quanh 15% trần 2 000 000. Với prompt cache, độ đầy context nằm gần hết ở cache_read_input_tokens. Phải đo usage của LƯỢT CUỐI trong transcript: input_tokens + cache_read_input_tokens + cache_creation_input_tokens (phiên đo được 613 246), rồi so với context_window_tokens × ngưỡng 0.85. Bỏ cache_read chỉ đúng khi TÍNH TIỀN."
asserts:
  - 'icontains:cache_read'
  - 'icontains:input_tokens'
  - 'regex:(?i)context_window|cửa sổ context'
  - 'icontains:cache_creation'
rubric: "ĐẠT nếu chỉ ra được trigger cũ đếm sai trường (input_tokens thay vì tổng context) VÀ nêu công thức đo đúng trên lượt cuối. KHÔNG đạt nếu chỉ nói 'tăng ngưỡng' hay 'hạ trần'."
---

# Golden: context-guard-cache-read

Hỏi lại đúng câu user báo 10/09/2026 ("sáng giờ chưa gặp lúc nào cơ chế gác đầy context tự đóng phiên cũ mở phiên mới"). Đáp án là số đo thật trên phiên 95e2c1ee và bản sửa `7803210`.

## Origin
- Hiệu chỉnh 10/09/2026 sau lần chạy độc lập: câu trả lời đúng bản chất (nêu `_context_now`, cộng input + cache_read + cache_creation từ transcript) nhưng không dùng cụm "lượt cuối". Điểm phân biệt thật là CỘNG ĐỦ ba trường chứ không phải cách diễn đạt, nên thay assert cụm từ bằng `icontains:cache_creation`. Câu trả lời sai ("tăng ngưỡng", "hạ trần") vẫn trượt.
- Phiên 95e2c1ee, 10/09/2026: đo transcript (usage lượt cuối) so với `session-continue.py near`; sửa ở commit `7803210` (phiên song song setup-e7).
