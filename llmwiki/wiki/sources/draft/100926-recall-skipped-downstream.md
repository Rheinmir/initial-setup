---
type: issue
kind: tech-debt
title: "recall/okf-scan không chạy ở bản cài downstream thiếu .template-manifest.json"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, recall, okf-scan, session-start, downstream]
timestamp: 2026-09-10
id: 100926-recall-skipped-downstream
source_session: "phiên 95e2c1ee — xử lý GH#151"
---

# Issue: recall bị bỏ qua ở bản cài downstream

## Origin

`harness/scripts/self-report.py` tự mở [GH#151](https://github.com/Rheinmir/setup/issues/151)
với fingerprint `self-report:recall-never-ran`, mức high: "13 phiên có số đo, 0 phiên có biên
lai okf-scan".

## Tái hiện

- Trên repo `setup` **không** tái hiện được: `self-report --report` ra 36 biên lai / 12 phiên.
- Quét các bản cài trên máy thì ra `tester-kit`: có `llmwiki/wiki` và `.harness-stamp`,
  **không** có `.template-manifest.json`, không có `harness/version.json`.
  `self-report --report --root tester-kit` → "11 phiên có số đo, 0 phiên có biên lai" — cùng
  một phát hiện. `tester-kit/harness/metrics/self-report.jsonl` có ghi `recall-never-ran`.
- Bản sao cô lập (chỉ gồm wiki + stamp, không manifest) chạy `session_start.py` → 0 biên lai.

## Gốc

Ba hook đang dùng hai tiêu chí khác nhau cho câu hỏi "đây có phải bản cài overstack không":

- `user_prompt_submit.py` và Stop gác bằng `find_wiki_dir` → vẫn chạy, vẫn ghi số đo.
- `session_start.py` thoát ở `if not .template-manifest.json: sys.exit(0)`, **trước khi** gọi
  `recall()` → okf-scan không bao giờ chạy, không có biên lai.

Bản cài downstream (v4) không có manifest là chuyện bình thường — chính các hàm
`harness_integrity`, `wiki_drift`, `draft_threshold` đã được dời lên trước lệnh thoát này vì
lý do đó. `recall()` bị sót lại.

## Đã làm

- Ở nhánh thiếu manifest: nếu `find_wiki_dir` thấy wiki thì gọi `recall()` rồi mới thoát.
  Cùng một điều kiện cho cả ba hook.
- Fire-drill trên bản sao cô lập: trước vá **0** biên lai → sau vá **1**, hook in "Quét OKF
  (40 mục, có biên lai)".
- Chép `session_start.py` sang `~/.claude/harness/hooks/` (đúng thao tác dòng 141 của
  `install-harness.sh`), để các dự án dùng hook global nhận bản vá.

## Nợ mở, không chặn

- `output_style` và `orient` vẫn chỉ chạy cho project có manifest. Tôi cố ý giữ phạm vi ở
  `recall()`, là thứ issue này đo được.
- `tester-kit` sẽ có biên lai từ phiên kế tiếp; self-report dedupe theo fingerprint nên nếu đã
  xanh thì issue sẽ không bị mở lại.
