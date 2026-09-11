---
type: eval
id: teach-me-manager-syncskill
title: "teach-me cho manager — sync-skill.sh để làm gì, có đáng giữ không"
input: "Giải thích cho sếp (manager) của tôi: fdk/tools/sync-skill.sh để làm gì, có đáng giữ không?"
expected: "Người nghe là manager. Đủ bảy phần đúng thứ tự nhưng nói bằng tác động: một bản skill phải có mặt ở ba chỗ (bản gốc, bản gương trong llmwiki, bản cài trên máy); sửa tay dễ quên một chỗ khiến máy khác nhận bản cũ; script chép cả ba trong một lệnh rồi tự so khớp. Trade-off/Giới hạn nói bằng rủi ro, công sức. Không có khối code, không backtick. Chốt bằng một đề xuất rõ (giữ/bỏ) cho sếp."
asserts:
  - 'regex:(?s)Tên gọi.*Nguồn gốc.*Lý do tồn tại.*Cơ chế hoạt động.*Trade-off.*Giới hạn.*Vị trí'
  - 'regex:^(?![\s\S]*```(?:bash|sh|shell|console|python|py)\b)'
  - 'regex:^(?![\s\S]*`[^`\n]+`)'
  - 'regex:(?i)rủi ro|chi phí|thời gian|công sức'
  - 'regex:(?i)đề xuất|khuyến nghị|nên giữ|quyết định'
rubric: "ĐẠT nếu một manager không biết code đọc hiểu ngay: dẫn bằng tác động (máy khác nhận bản cũ → lỗi khó truy), phần chữ dưới khoảng 700 tiếng Việt (≈ 500 từ tiếng Anh, không tính sơ đồ), bằng chứng nén thành câu thường nhưng không nói quá điều đã quan sát, có đề xuất hành động. KHÔNG đạt nếu trình bày như tài liệu kỹ thuật, dán lệnh shell, hay liệt kê đường dẫn dạng code."
---

# Golden: teach-me-manager-syncskill

Ca người nghe kinh doanh. Bài học eli5 chép sang: bản có skill của eli5 vẫn trượt vì dùng backtick cho tên thư mục khi viết cho manager — hai assert phủ định ở đây bắt đúng lỗi đó (khối code shell/python và inline code).

## Origin
- Phiên 11/09/2026 — distill [dreambigou/eli5](https://github.com/dreambigou/eli5) (ca `explain-codebase-manager`, assert "no code blocks or inline code formatting") vào `skills/teach-me/SKILL.md`.
- A/B 11/09/2026: bản cũ trượt assert backtick và trượt giám khảo 3/4 (≈1.800 tiếng, sơ đồ có lệnh shell); bản mới qua 5/5 assert nhưng giám khảo vẫn đánh trượt vì dài (~718 tiếng) và một câu "màn hình chỉ toàn dấu tích xanh" nói quá lần tái hiện. Ngưỡng độ dài trong rubric đổi sang tính theo tiếng Việt cho khớp SKILL.md; kết quả đã ghi giữ nguyên, không chấm lại.
