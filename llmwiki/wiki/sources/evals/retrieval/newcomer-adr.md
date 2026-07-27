---
type: eval
id: newcomer-adr
question: "Tôi muốn thêm hook tự in trạng thái framework mỗi lần mở phiên cho tiện, làm sao?"
expected_pages: [ADR-004-framework-dev-context-opt-in, fdk]
---

# Retrieval golden: newcomer-adr

Golden truy-hồi (mảnh 2). `question` vào pipeline, `expected_pages` là TẬP trang chấp nhận được (case xấu #4). Chấm hit@k + token, không model.

**Vì sao golden này khác 29 golden còn lại.** Cả 29 golden kia hỏi bằng ĐÚNG thuật ngữ của wiki ("Vì sao framework-dev context là opt-in?", "Skill X dùng để làm gì?") — chúng đo truy hồi khi người hỏi *đã biết* mình đang tìm gì. Golden này mô phỏng **người mới**: hỏi bằng lời của người chưa đọc wiki, không có chữ "opt-in", không có chữ "ADR", chỉ có ý định. Và ý định đó **vi phạm một quyết định kiến trúc đã chốt** — ADR-004 cấm auto-bơm context nội-bộ-framework vào mọi phiên.

Bài thi vì vậy là: wiki có nổi được đúng quyết định chi phối lên **trước khi** người mới phá nó không? Trượt golden này nghĩa là người mới sẽ viết hook, hài lòng vì nó chạy, và không ai biết một ADR vừa bị vi phạm cho tới lúc review.

Đây là dạng câu hỏi mà thread cộng đồng Grapuco đồng thanh cho là phần khó thật — không phải "code nằm đâu" mà "luật nào đang chi phối và vì sao". Xem `[[190726-graph-lessons-grapuco]]`.

## Origin
- **Source:** proposal `wiki/sources/draft/190726-graph-lessons-grapuco.md` task T4 (FR-005) — sinh từ câu hỏi kiểm chứng của thread Grapuco: *"thành viên mới vào dự án có nắm được toàn bộ kiến thức đó không?"*
- **Đổi chỗ:** thay golden `extract-site` ("Skill extract-site dùng để làm gì?") để giữ trần cứng 30 (case xấu #1, chống mạ-vàng-eval) — đổi một câu tra-cứu nông lấy một bài đo business-rule. Quyết định do user chốt 2026-07-19.
- **Task:** `T-260719-02`
