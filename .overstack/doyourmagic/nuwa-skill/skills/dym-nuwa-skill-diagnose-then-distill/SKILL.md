---
name: dym-nuwa-skill-diagnose-then-distill
description: "Chưa biết chắt lọc ai: đường chẩn đoán (chat-only). Vì sao dùng: bạn chỉ có một vấn đề ("hay ra quyết định sai", "viết không ai đọc"), chưa biết nên mượn đầu óc của ai."
disable-model-invocation: true
---

# Skill: dym-nuwa-skill-diagnose-then-distill — Chưa biết chắt lọc ai: đường chẩn đoán (chat-only)

**Vì sao dùng**: bạn chỉ có một vấn đề ("hay ra quyết định sai", "viết không ai đọc"), chưa biết nên mượn đầu óc của ai.
**Sinh ra cái gì**: 2–3 ứng viên có lý do, bạn chọn một rồi rơi thẳng vào luồng [02](02-distill-a-person.md).

> Đây là lệnh CHAT, không phải shell.

---

## Câu lệnh khởi động

```
我想提升决策质量
有没有一种思维方式能帮我看透商业本质
I need a thinking advisor
```

Nói tiếng Việt vẫn hiểu được nếu skill đã nạp, nhưng an toàn nhất là mở bằng một trong các câu trên rồi mô tả tiếp bằng tiếng Việt.

## Nhịp làm việc (Phase 0B)

Ba bước, **tối đa 2 vòng hỏi lại** — repo quy định thẳng "không được biến thành bảng khảo sát", và nếu bạn đã nói đủ rõ thì agent phải khuyến nghị luôn, không hỏi.

1. **Định vị nhu cầu** — agent ánh xạ vấn đề của bạn vào một trong 10 chiều dưới đây.
2. **Đề cử 2–3 ứng viên** — có thể là *người* hoặc *chủ đề*, kèm nhãn ⚡已有Skill (đã có sẵn trong `.claude/skills/`, dùng ngay) hoặc 🆕需要蒸馏 (phải chắt lọc mới).
3. **Bạn chọn** → chuyển sang Phase 0.5 của luồng 02.

| Chiều nhu cầu | Câu nói điển hình | Hướng khung tư duy |
|---|---|---|
| Quyết định & phán đoán | "hay chọn sai", "tê liệt vì phân tích" | đa mô hình tư duy, nghịch đảo, tư duy xác suất |
| Biểu đạt & viết | "nói mãi không rõ", "bài không ai đọc" | giản hoá kiểu Feynman, kể chuyện, năng lực ví von |
| Khởi nghiệp & kinh doanh | "muốn làm indie dev", "không tìm ra PMF" | nguyên lý đầu tiên, đòn bẩy, kiềm chế sản phẩm |
| Dạy & lan truyền | "giảng không ai nghe" | từ đã biết đến chưa biết, dạy bằng ẩn dụ |
| Tư duy phản biện | "hay bị dắt mũi" | tư duy phủ chứng, góc nhìn tiến hoá, nhận diện thiên kiến |
| Sáng tạo nội dung | "video không ai xem" | kỹ nghệ chú ý, test–lặp, tâm lý khán giả |
| Chiến lược đời người | "mơ hồ hướng nghề", "lo âu" | chủ nghĩa dài hạn, chọn đòn bẩy, lãi kép |
| Rủi ro & bất định | "sợ thiên nga đen", "đầu tư toàn lỗ" | phản mong manh, chiến lược lồi, quản trị rủi ro đuôi |
| Thiết kế & sản phẩm | "UX tệ", "không biết cắt bớt" | tối giản, mô hình tâm trí người dùng, ràng buộc là sáng tạo |
| Hài hước & sức biểu đạt | "nói chuyện nhạt" | tương phản phi lý, phá vỡ kỳ vọng, uy quyền tự trào |

## Người hay chủ đề?

- Nhu cầu trỏ tới **một lối nghĩ cụ thể** → *人物Skill* (chắt lọc khung tư duy một người).
- Nhu cầu trỏ tới **phương pháp luận của một lĩnh vực** → *主题Skill* (tổng hợp nhiều góc nhìn; mẫu duy nhất trong repo là `examples/x-mastery-mentor/`).
- Không chắc → agent phải đưa cả hai loại vào danh sách đề cử cho bạn chọn.

## Đường tắt: 15 skill đã có sẵn, không cần chắt lọc lại

Nếu ứng viên trùng danh sách này thì đừng tốn tiền chắt lọc — cài thẳng:

```bash
npx skills add alchaincyf/paul-graham-skill      # khởi nghiệp / viết / sản phẩm
npx skills add alchaincyf/munger-skill           # đầu tư / đa mô hình tư duy
npx skills add alchaincyf/feynman-skill          # học / dạy / tư duy khoa học
npx skills add alchaincyf/naval-skill            # tài sản / đòn bẩy / triết lý sống
npx skills add alchaincyf/taleb-skill            # rủi ro / phản mong manh
npx skills add alchaincyf/elon-musk-skill        # kỹ thuật / chi phí / nguyên lý đầu tiên
npx skills add alchaincyf/steve-jobs-skill       # sản phẩm / thiết kế / chiến lược
npx skills add alchaincyf/karpathy-skill         # AI / kỹ thuật / giáo dục
npx skills add alchaincyf/ilya-sutskever-skill   # an toàn AI / scaling
npx skills add alchaincyf/mrbeast-skill          # nội dung / phương pháp YouTube
npx skills add alchaincyf/trump-skill            # đàm phán / quyền lực / truyền thông
npx skills add alchaincyf/zhang-yiming-skill     # sản phẩm / tổ chức / toàn cầu hoá
npx skills add alchaincyf/zhangxuefeng-skill     # chọn ngành / hướng nghiệp
npx skills add alchaincyf/x-mentor-skill         # vận hành X/Twitter (chủ đề)
```

Riêng 孙宇晨 (Justin Sun) chưa có repo riêng — copy `examples/sun-yuchen-perspective/` vào thư mục skills.

Cả 15 skill này đều đã qua chấm mù hai agent độc lập và đạt hạng A (≥85): 97 điểm cho MrBeast/Naval/Taleb/Jobs/Karpathy/Paul Graham/Zhang Xuefeng · 96 cho Munger/Feynman/X-mentor · 95 Trump · 94 Ilya · 93 Zhang Yiming · 91 Sun Yuchen · 89 Musk. Chi tiết trong `FIDELITY.md` của từng skill.

## Cạm bẫy đã kiểm chứng

- Nếu bạn mô tả nhu cầu quá mơ hồ và agent hỏi tới vòng thứ ba, nó **đang chạy sai quy trình** — nhắc "đề cử luôn đi, đừng hỏi nữa".
- Đề cử nhãn ⚡已有Skill dựa trên việc quét thư mục `.claude/skills/` trên máy bạn. Máy chưa cài skill nào thì mọi ứng viên đều là 🆕 — không có nghĩa là chúng chưa tồn tại trên GitHub; đối chiếu danh sách trên trước khi đồng ý chắt lọc mới.
