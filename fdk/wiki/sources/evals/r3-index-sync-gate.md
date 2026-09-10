---
type: eval
id: r3-index-sync-gate
title: "Draft wiki mới quên dòng index — tầng nào chặn, chặn lúc nào"
input: "Một phiên thêm draft mới vào wiki nhưng quên thêm dòng vào index.md. Trong overstack, cái gì chặn lỗi này và chặn ở thời điểm nào? Vì sao máy tác giả có thể xanh mà CI đỏ?"
expected: "Hook pre-commit wiki-index-sync chạy index_sync.py cho fdk/wiki và llmwiki/wiki, CHỈ khi commit đụng file wiki (^(fdk|llmwiki)/wiki/.*\\.md$); CI job harness chạy lại R3 làm sàn. index_sync chỉ tính file đã git add (tracked), nên file chưa add không được đếm. Máy có thể xanh vì hook đã chèn dòng index trên đĩa mà chưa ai commit — phải so bản đã commit chứ không so đĩa. Pre-commit stash phần chưa stage nên hook thấy đúng trạng thái sẽ commit."
asserts:
  - 'regex:(?i)wiki-index-sync|pre-commit'
  - 'icontains:pre-commit'
  - 'regex:(?i)git add|tracked|đã commit'
  - 'icontains:index'
rubric: "ĐẠT nếu nêu được cả tầng cắn sớm (pre-commit, chỉ khi đổi file wiki) lẫn lý do xanh-ở-máy-đỏ-trên-CI (so đĩa thay vì so commit / file chưa add). KHÔNG đạt nếu chỉ nói 'CI bắt'."
---

# Golden: r3-index-sync-gate

Hỏi lại GH#150. Đáp án là hook thêm ở `6a1024d` và fire-drill hai chiều (bẩn → Failed rc=1; sạch → Passed rc=0).

## Origin
- Hiệu chỉnh 10/09/2026 sau lần chạy độc lập (agent trong worktree đã xoá thư mục evals): câu trả lời đúng bản chất — nêu R3, Stop hook tự vá, CI, pre-commit, file untracked — nhưng không gọi tên hook. Tên hook là chi tiết, không phải kiến thức cốt lõi; chuyển assert thành `wiki-index-sync|pre-commit`. Câu trả lời sai ("chỉ CI bắt") vẫn trượt vì thiếu pre-commit.
- Phiên 95e2c1ee, 10/09/2026 — xử lý [GH#150](https://github.com/Rheinmir/setup/issues/150); draft `llmwiki/wiki/sources/draft/100926-r3-index-sync-precommit.md`.
