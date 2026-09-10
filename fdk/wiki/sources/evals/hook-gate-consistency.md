---
type: eval
id: hook-gate-consistency
title: "Ba hook vòng đời phiên phải cùng một tiêu chí 'đây có phải bản cài'"
input: "self-report báo 'N phiên có số đo, 0 phiên có biên lai okf-scan' ở một bản cài downstream. Nguyên nhân gốc là gì?"
expected: "Hai hook dùng hai tiêu chí khác nhau. UserPromptSubmit và Stop gác bằng find_wiki_dir nên vẫn chạy và vẫn ghi số đo; session_start.py thoát ở kiểm .template-manifest.json TRƯỚC khi gọi recall(), nên okf-scan không bao giờ chạy và không có biên lai. Bản cài downstream (v4) thiếu manifest là chuyện bình thường. Sửa: thiếu manifest mà có wiki thì vẫn gọi recall() rồi mới thoát."
asserts:
  - 'icontains:template-manifest'
  - 'icontains:find_wiki_dir'
  - 'icontains:recall'
  - 'regex:(?i)session.?start'
rubric: "ĐẠT nếu chỉ ra được hai tiêu chí gác khác nhau giữa các hook và việc thoát sớm xảy ra TRƯỚC recall(). KHÔNG đạt nếu kết luận 'chạy lại installer' mà không nêu cơ chế."
---

# Golden: hook-gate-consistency

Hỏi lại GH#151. Đáp án đã tái hiện ở `tester-kit` (11 phiên, 0 biên lai) và fire-drill trên bản sao cô lập (0 → 1 biên lai), commit `6a1024d`.

## Origin
- Phiên 95e2c1ee, 10/09/2026 — xử lý [GH#151](https://github.com/Rheinmir/setup/issues/151); draft `llmwiki/wiki/sources/draft/100926-recall-skipped-downstream.md`.
