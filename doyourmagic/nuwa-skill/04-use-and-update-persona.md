# 04 — Dùng và cập nhật một persona skill (chat-only)

**Vì sao dùng**: skill đã chắt lọc xong nằm im thì vô dụng — file này nói cách gọi nó ra làm việc, cách kéo nó ra khỏi vai, và cách làm mới nó khi tư liệu đã cũ.
**Sinh ra cái gì**: các phiên tư vấn đúng vai; và với luồng cập nhật là một `SKILL.md` được vá tăng dần (không viết lại).

> Lệnh CHAT, không phải shell.

---

## Gọi persona ra làm việc

```
用芒格的视角帮我分析这个投资决策
费曼会怎么解释量子计算？
切换到Naval，我在纠结三件事
```

Tiếng Việt cũng chạy khi skill đã nạp: *"Dùng góc nhìn Munger phân tích thương vụ này giúp tôi"*.

## Persona sẽ cư xử ra sao (theo `references/skill-template.md`)

Đây là hợp đồng hành vi mà mọi skill do nüwa sinh ra đều mang:

- Xưng **「我」**, nói thẳng bằng giọng nhân vật — không phải "Munger có lẽ sẽ nghĩ rằng…".
- **Miễn trừ trách nhiệm chỉ nói một lần** ở lượt kích hoạt đầu ("tôi trò chuyện với bạn bằng góc nhìn X, suy luận từ phát ngôn công khai, không phải quan điểm của chính người đó"), sau đó không lặp lại.
- Gặp chủ đề nhân vật **chưa từng công khai bày tỏ** → phải nói rõ "đây là suy luận từ khung, không phải lập trường bản thân người đó" trước khi triển khai. Nếu thái độ thật của người đó là **im lặng có cấu trúc** (không bàn loại chủ đề này), skill phải trình bày trung thực sự im lặng đó, không được bịa ra một phương án dung hoà khéo léo.
- Khi trích câu tủ hoặc dữ kiện then chốt phải kèm xuất xứ tối giản, để trong bài phân biệt được **nguyên văn của người đó vs. suy luận của khung** (ít nhất một lần mỗi bài).
- **Thoát vai**: gõ 「退出」「切回正常」「不用扮演了」 — hoặc "thoát vai", "quay lại bình thường".

## Agentic Protocol: vì sao persona đôi khi đi tìm thông tin trước

Mỗi skill sinh ra đều có mục **回答工作流** ba bước, để persona "làm bài tập trước khi phát biểu" thay vì bịa từ tư liệu huấn luyện:

| Loại câu hỏi | Đặc điểm | Persona làm gì |
|---|---|---|
| Cần dữ kiện | dính công ty/người/sự kiện/sản phẩm/thị trường cụ thể | **tìm kiếm thật trước** (Step 2) rồi mới trả lời |
| Thuần khung | giá trị trừu tượng, lối tư duy, lời khuyên sống | trả lời thẳng bằng mô hình tâm trí (nhảy tới Step 3) |
| Hỗn hợp | dùng case cụ thể để bàn đạo lý trừu tượng | lấy dữ kiện case trước, rồi phân tích bằng khung |

Các chiều tìm kiếm ở Step 2 **được suy ra từ chính mô hình tâm trí của nhân vật**, không phải "tìm thông tin liên quan" chung chung. Ví dụ trong repo: Munger → xem hào kinh tế, xem cấu trúc khuyến khích của ban lãnh đạo, xem rủi ro lớn nhất (nghịch đảo), xem loại suy lịch sử. Taleb → xem tình huống cực đoan, xem ai đang gánh rủi ro đuôi, xem lịch sử dự báo của giới chuyên gia. Bạn sẽ **không thấy báo cáo khảo cứu** — chỉ thấy phán đoán của nhân vật dựa trên thông tin thật.

## Cập nhật skill khi tư liệu cũ

```
更新芒格的skill
张一鸣最近有新动态，更新一下
```

Luồng cập nhật là **tăng dần, không viết lại**:

1. Đọc `SKILL.md` hiện có, lấy 「调研时间」 trong mục ranh giới trung thực, tính khoảng cách tới hôm nay.
2. Chỉ bung **3 agent**: Agent 2 (đối thoại mới) + Agent 5 (quyết định mới) + Agent 6 (cập nhật dòng thời gian) — rẻ hơn hẳn một lần chắt lọc đủ.
3. Đối chiếu thông tin mới với nội dung cũ:
   - củng cố mô hình sẵn có → bổ sung case;
   - mâu thuẫn với mô hình sẵn có → ghi nhận thay đổi, sửa mô hình;
   - xuất hiện mô thức tư duy mới → cân nhắc thêm mô hình mới.
4. Cập nhật mục 「最新动态」 và mốc thời gian khảo cứu.

## Cạm bẫy đã kiểm chứng

- **Persona không tự nhận mình lỗi thời.** Ranh giới trung thực có ghi 「调研时间」 nhưng persona không cảnh báo khi ngày đó đã xa. Nếu đang hỏi chuyện thời sự, mở `SKILL.md` xem ngày khảo cứu trước, hoặc chạy luồng cập nhật ở trên.
- **Ranh giới trung thực là mục quan trọng nhất để đọc trước khi tin.** Ba giới hạn mà repo tuyên bố cho mọi skill: không chắt lọc được trực giác (khung thì trích được, cảm hứng thì không); không bắt được đột biến (chỉ là ảnh chụp tới thời điểm khảo cứu); phát ngôn công khai ≠ suy nghĩ thật.
- **Đừng dùng cho lĩnh vực trách nhiệm cao** — y tế, pháp lý, đầu tư — nếu skill không kèm tuyên bố miễn trừ rõ ràng và ranh giới "không thay thế chuyên gia". Đây là lằn ranh đạo đức được ghi thẳng trong `CONTRIBUTING.md`.
