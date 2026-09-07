---
type: eval
id: artifact-selfpath-relative
title: "Artifact sinh ra nhúng đường dẫn TƯƠNG ĐỐI — path tuyệt đối làm file đã commit drift theo máy"
input: "Artifact HTML do generator sinh ra rồi commit vào git có được nhúng đường dẫn tuyệt đối của chính nó không, và nếu có thì hỏng ở đâu?"
expected: "Không. R16 đòi người xem biết file nằm ĐÂU — đường tương đối theo repo (llmwiki/html/wiki-graph.html) trả lời đủ; đường tuyệt đối trả lời thừa (máy nào) và làm artifact ĐÃ COMMIT drift: mỗi phiên regen ở worktree của nó lại đổi footer, và với trang gom nhiều nguồn thì path CỘNG DỒN chứ không thay thế. Đo 2026-09-07 trên orca: 5 artifact mang 11 path tuyệt đối, fdk-problem-tree.html gom 6 path từ 6 worktree, overstack.html trỏ vào một scratchpad đã bị xoá. Vá ở tầng SO SÁNH (--check bỏ qua self-path) chỉ chữa gate, không chữa git; sửa gốc là ghi tương đối lúc RENDER, một chỗ trong build-wiki-graph.py phủ cả 5 artifact."
asserts:
  - 'icontains:tương đối'
  - 'regex:(?i)(drift|cộng dồn|tích lu)'
  - 'regex:(?i)(r16|footer|self-?path)'
rubric: "ĐẠT nếu nêu được: (1) tương đối theo repo là đủ cho R16, (2) tuyệt đối gây drift trên file ĐÃ COMMIT và có thể cộng dồn, (3) sửa ở chỗ RENDER chứ không chỉ ở chỗ SO SÁNH. KHÔNG đạt nếu chỉ nói 'nên dùng path tương đối' mà không nêu được drift là hỏng ở tầng git chứ không phải tầng gate."
---

# Golden: artifact-selfpath-relative

Rút từ sự cố thật 2026-09-07. `fdk-gate` trên `orca` đỏ 20/21 với bất kỳ ai clone về, step `overstack-docs current`: `--check` so nguyên văn hai bản HTML, mà footer mang đường dẫn tuyệt đối của máy sinh ra file (R16) — gate so **máy** chứ không so **nội dung**. Bằng chứng: regen xong `diff` = 0 dòng nội dung, chỉ 2 dòng path khác.

PR #129 vá ở tầng so sánh (`_strip_selfpath` chuẩn hoá footer trước khi diff). Gate hết nói dối, nhưng git thì vẫn drift — vá tầng so sánh không chạm tầng ghi. Đo sau đó: 5 artifact đã commit mang 11 path tuyệt đối; `fdk-problem-tree.html` gom 6 path từ 6 worktree khác nhau, tức mỗi phiên regen **cộng thêm** một dòng chứ không ghi đè.

Sửa gốc: `_repo_rel()` trong `fdk/tools/build-wiki-graph.py` — generator duy nhất phát ra `<div class="foot"><code>…`, nên một chỗ phủ cả 5 artifact. Khoá bằng `--self-test` (fdk-gate tự chạy mọi script có cờ này), gồm cả nhánh ngoài-repo: `relative_to("/")` vẫn rò nguyên cây thư mục nên phải fallback về tên file.

## Origin
- Distill từ phiên 2026-09-07 (PR #129 vá `--check`, PR kế sửa gốc `_repo_rel`) — golden neo bài học "vá chỗ SO SÁNH không thay được sửa chỗ GHI" vào eval hồi quy.
