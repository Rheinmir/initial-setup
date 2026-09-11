---
type: eval
id: teach-me-eli5-merge-conflict
title: "teach-me ELI5 — git merge conflict cho trẻ 5 tuổi"
input: "ELI5: git merge conflict là gì? Giải thích cho con tôi 5 tuổi."
expected: "Người nghe là trẻ 5 tuổi. Đủ bảy phần đúng thứ tự (được thêm phụ đề đời thường), kể như câu chuyện với một phép so sánh quen với trẻ (hai bạn cùng tô một bức tranh / cùng viết một trang). Có chạy thật một conflict nhỏ để chứng, nhưng không dán log thô hay dấu <<<<<<< cho trẻ. Không thuật ngữ git trần (rebase, HEAD, SHA). Câu ngắn, giọng vui."
asserts:
  - 'regex:(?s)Tên gọi.*Nguồn gốc.*Lý do tồn tại.*Cơ chế hoạt động.*Trade-off.*Giới hạn.*Vị trí'
  - 'regex:(?i)tưởng tượng|giống như|giống hệt|cũng như'
  - 'not-contains:<<<<<<<'
  - 'regex:^(?![\s\S]*\b(?:rebase|HEAD|SHA)\b)'
rubric: "ĐẠT nếu trẻ 5 tuổi (qua lời bố mẹ đọc) hiểu được: câu ngắn, giọng vui không bề trên, một phép so sánh đồ chơi/tranh vẽ/bạn bè xuyên suốt; bảy phần có mặt nhưng không nặng nề. KHÔNG đạt nếu viết như cho người lớn, hay dán output git."
---

# Golden: teach-me-eli5-merge-conflict

Ca người nghe đơn giản nhất. Khung bảy phần vẫn giữ — đây là chỗ dễ vỡ nhất vì "Trade-off", "Giới hạn" là từ người lớn; skill cho phép phụ đề đời thường mà vẫn giữ tên tiêu đề.

## Origin
- Phiên 11/09/2026 — distill [dreambigou/eli5](https://github.com/dreambigou/eli5) (ca `explain-db-index-age5` và `explain-git-merge-5th-grader`) vào `skills/teach-me/SKILL.md`.
