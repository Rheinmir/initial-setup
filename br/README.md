# 📁 br/ — nhà của dây chuyền Ralph (GH#15)

Folder này là **chỗ ở runtime** của dây chuyền: trống cho tới khi bạn chạy `/br`.
Các file dưới đây sẽ TỰ xuất hiện theo từng bước:

| File | Xuất hiện khi | Là gì |
|------|---------------|-------|
| `spec-filled.md` | `/br interview` | khung S1–S10 đã bóc từ tài liệu `llmwiki/raw/` |
| `interview/NNN-questions.html` + `NNN-answers.md` | `/br interview` | bộ câu hỏi (xem) + file điền trả lời |
| `BR.md` + `BR.clauses.json` | `/br compile` | bản yêu cầu (mỗi điều khoản có clause_id + provenance) |
| `frames/frame-NNN-*.md` + `frames/index.md` | `/br slice` | các khung việc nhỏ gắn code + registry truy ngược |
| **`prompts.md`** | `br-prompts.py sync` (sau slice) | **📒 SỔ PROMPT tổng — mỗi frame một mục `## <frame_id>`, SỬA TAY thoải mái, thắng mọi nguồn khác** |
| `queue.yaml` | bạn tạo (mẫu: `skills/br/assets/queue.example.yaml`) | hàng đợi chạy nhiều frame, resume được |
| `frames/<id>.run.json` | `/br run` | run-log: verdict · file thật đã đổi · scope_clean · commit |
| `line-status.{json,html}` | `/br status` | trang tổng quan + cây thư mục file↔frame |

## Bắt đầu
1. Bỏ tài liệu thô vào `llmwiki/raw/`
2. Gọi `/br interview` → điền trả lời → `/br compile` → `/br slice`
3. `python3 fdk/tools/br-prompts.py sync` → mở `br/prompts.md` sửa prompt tay nếu muốn
4. `python3 fdk/tools/br-run.py run br/frames/<frame>.md` (in-place — bật app xem liền)
5. Lỗi ở đâu? `python3 fdk/tools/br-find.py "<file hoặc từ khoá>"` → ra frame + mục prompt phụ trách

## Origin
Skeleton tạo 2026-07-06 (phiên GH#15) để chỉ đường — nội dung thật do các bước /br sinh ra.
