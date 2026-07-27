---
name: orca-handover
description: Sinh MỘT file .md bàn giao đủ dày để một phiên KHÁC (người hoặc agent, không có context nào của phiên này) mở ra là bắt đầu làm được ngay — việc còn dở, thứ tự ưu tiên có lý do, số đo làm bằng chứng, cạm bẫy đã trả giá, và nợ mở không chặn. Gọi khi user nói "bàn giao", "handover", "handoff", "viết lại để phiên sau làm tiếp", "context cho session khác", "tôi sắp hết phiên", "ghi lại để mai làm", "/orca-handover". KHÁC record-episode (ghi cho MÁY truy hồi ngữ nghĩa) và KHÁC plan (brief thi hành cho task ĐÃ duyệt, đã hiểu rõ) — orca-handover dành cho việc CÒN DỞ và CÒN MƠ HỒ, nơi thứ tự và lý do quan trọng hơn từng bước code.
---

# Skill: orca-handover

## When to use

- Phiên dài sắp kết thúc mà việc chưa xong, và phiên sau **không có context nào**.
- Vừa điều tra ra một chuỗi phát hiện, cần chốt lại **thứ tự giải** trước khi quên lý do.
- Chuyển việc cho người/agent khác mà việc còn **mơ hồ** (chưa có SPEC duyệt).

**KHÔNG dùng khi:**
- Task đã duyệt và đã rõ từng bước → dùng `plan` (brief thi hành cho agent headless).
- Chỉ cần máy truy hồi "phiên trước làm gì" → dùng `record-episode` (mem-rank).
- Chuyển quyền sở hữu worktree/terminal cho agent khác → dùng `orca-cli` (full handoff).

## Nguyên tắc — vì sao file này khác một bản tóm tắt

Người đọc nó **không có gì cả**: không transcript, không biết hôm qua đã thử gì và vì sao bỏ. Tóm tắt kể *đã làm gì*; bàn giao phải trả lời *làm gì tiếp và vì sao thứ tự đó*.

Ba thứ quyết định file này dùng được hay không:

1. **Mỗi claim phải có SỐ ĐO.** "Grep không đủ tốt" là ý kiến. "Trên 8 file đổi: grep nghi 36, graph 25, trùng 21 ⇒ thừa 15 sót 4" là bằng chứng — phiên sau kiểm lại được, và không phải tin lời ai.
2. **Thứ tự phải có LÝ DO, và phải chỉ rõ cái nào CHẶN cái nào.** Danh sách phẳng khiến phiên sau chọn việc dễ nhất trước rồi vấp cái chưa xong.
3. **Cạm bẫy là phần đắt nhất.** Mỗi lỗi đã trả giá mà không ghi lại thì phiên sau trả giá lần nữa.

## Steps

### 1. Thu bằng chứng TRƯỚC khi viết (đừng viết theo trí nhớ)

```bash
git log --oneline -15
git status --short
python3 fdk/tools/medic.py --ci 2>&1 | tail -5     # nếu repo có medic
```

Mọi con số trong file phải lấy từ lệnh chạy thật trong phiên, không ước lượng lại. Số nào không tái lập được thì **ghi rõ là chưa xác minh**, đừng làm tròn thành sự thật.

### 2. Xác định cái CHẶN

Với mỗi việc còn lại, hỏi: *làm việc B trước việc A thì hỏng gì?* Có câu trả lời cụ thể → A là **bước 0**, ghi kèm hậu quả nếu bỏ qua. Không có → thứ tự tự do, nói luôn là tự do.

### 3. Viết file `llmwiki/wiki/sources/handover/DDMMYY-<tên>.md`

Thư mục **riêng** `sources/handover/` — không trộn vào `sources/draft/`. Lý do: draft là *đề xuất chờ duyệt*, handover là *việc đang chạy dở*; hai loại có vòng đời khác nhau và người đọc khác nhau. Gom chung thì phiên sau phải lọc. (R5 chỉ kiểm subfolder cấp một nên `sources/handover/` hợp lệ.)

Bảy mục, đúng thứ tự này:

| Mục | Nội dung bắt buộc |
|---|---|
| **Đọc trước** | 1–2 link tới concept/ADR nền. File này chỉ nói *làm gì tiếp*, không lặp lại kiến trúc |
| **Việc tiếp theo** | Đánh số. Mỗi việc: bằng chứng · vì sao ở vị trí này · ⏱ ước lượng · rủi ro. Bước chặn ghi rõ **CHẶN** |
| **Việc dọn nhỏ** | Làm lúc nào cũng được, gộp ước lượng chung |
| **Nợ mở, không chặn** | Bảng: việc · trạng thái. Gồm cả thứ **đo chưa xong** |
| **Cạm bẫy** | Đánh số. Mỗi cái: hiện tượng → nguyên nhân → hậu quả nếu dính lại |
| **Đã thử và BỎ** | Hướng đã loại + **lý do**. Thiếu mục này phiên sau sẽ thử lại y hệt |
| **Origin** | Nguồn, commit trong phiên, concept liên quan |

### 4. Ước lượng thời gian bằng đơn vị cụ thể

`~30 phút` · `~2 giờ` · `nửa ngày` — không dùng "một chút", "khá nhanh". Ước sai còn hơn ước mơ hồ: phiên sau đọc "nửa ngày" thì biết không nhét vào 20 phút cuối ngày.

### 5. Kiểm file tự đứng được

Đọc lại và tự hỏi: **người chưa từng dự phiên này có bắt đầu được không?** Chỗ nào phải hỏi lại là chỗ thiếu. Đặc biệt kiểm:

- Đường dẫn file có **chính xác** không (copy-paste chạy được)
- Con số có nói rõ **đo trên cái gì** không ("trên 8 file đổi" chứ không phải "trên vài file")
- Có chỗ nào viết "như đã bàn ở trên" mà không có "trên" không

### 6. Đăng ký

Thêm dòng vào `llmwiki/wiki/index.md`, append `llmwiki/wiki/log.md`. Nếu repo có validator: chạy `index_sync` cho xanh.

## Rules

- **Số đo > tính từ.** Mọi phát biểu về mức độ ("chậm", "nhiều", "hỏng nặng") phải kèm số hoặc bị xoá.
- **Đường dẫn tuyệt đối hoặc repo-relative chính xác** — phiên sau copy-paste là chạy, không phải đoán thư mục.
- **Không lặp lại kiến trúc** — link tới concept đã có. File bàn giao phình lên vì chép lại nền là file không ai đọc hết.
- **Ghi cả cái CHƯA xác minh** — "chưa đo", "chưa kiểm chéo" là thông tin quý; giấu nó khiến phiên sau xây trên nền giả định.
- **Mục "Đã thử và BỎ" không được thiếu** — đây là mục dễ quên nhất và tốn nhất khi thiếu.
- **KHÔNG chép transcript.** Bàn giao là chắt lọc, không phải log. Dài quá 200 dòng là dấu hiệu đang chép thay vì chắt.
- Anti-pattern: viết "tiếp tục công việc dang dở" mà không nói **dang dở ở đâu, file nào, dòng nào**.

## Ví dụ mở đầu đạt yêu cầu

```markdown
### 0. `travel-policy.yaml` phải khớp `install-harness.sh` — CHẶN mọi việc dưới

Bằng chứng nó sai ngay lúc này:
    install-harness.sh:128   cp fdk/tools/build-capabilities.py → ~/.claude/hooks/
    travel-policy.yaml:71    build-capabilities.py → TẦNG 3 FRAMEWORK-ONLY

Installer copy xuống. Hợp đồng khai ở lại.
Hệ quả nếu bỏ qua: mọi câu trả lời "cái gì travel" đều chưa kiểm chéo.
⏱ ~1 giờ cho validator đối chiếu hai bên.
```

Đọc xong biết ngay: sai ở đâu, chứng minh thế nào, bỏ qua thì mất gì, tốn bao lâu.
