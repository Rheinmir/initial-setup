---
type: unknown-ledger
title: "unknown — <source-slug>"
status: open
source_task: T-YYMMDD-NN
source_spec: wiki/sources/draft/DDMMYY-<source>.md
timestamp: YYYY-MM-DD
---

# Unknown ledger — <source-slug>

> **Nợ unknown** — model đã *fill-first* (điền default để không chặn việc), *find-out-later* (chờ thông tin thật để trả nợ). KHÔNG chặn cổng; hiện ra ở `/lint` để không chìm. Đóng khoảng hở giữa `(default)` và `[CẦN LÀM RÕ]`. Xem `[[150726-unknown-ledger]]`.
>
> Thêm/đóng mục bằng `python3 harness/scripts/unknown-ledger.py` — đừng sửa số U-NN bằng tay.

## U-01 — <câu hỏi / điều chưa biết>
- **Trace:** FR-<NNN> · SPEC `wiki/sources/draft/DDMMYY-<source>.md` · task `T-YYMMDD-NN`
- **Đã fill (default):** <giá trị model tự chọn để việc chạy tiếp>
- **Cần verify:** <thông tin thật phải lấy để biết default đúng hay sai>
- **Rủi ro nếu default sai:** <điều gì hỏng nếu đoán sai>
- **Status:** open
- **Resolved:** _(khi có thông tin thật: giá trị đúng · đã fix ở đâu · ngày · nếu code đã sai thì link issue)_

## U-02 — Trần mặc định cho số kết quả code-graph trả về nên là bao nhiêu?
- **Trace:**  · SPEC `200726-context-hygiene-budget` · task `T-260720-02`
- **Đã fill (default):** 20
- **Cần verify:** đo phân bố số caller thật ở 3 dự án khách sau vài phiên dùng
- **Rủi ro nếu default sai:** trần thấp quá thì mất caller thật; cao quá thì context phình
- **Status:** open
- **Resolved:** _(chưa)_

## U-03 — So git-diff toàn file hay theo từng mục (id) để phân biệt xoá-hợp-lệ khỏi xoá-lén khi 2 người sửa cùng file mechanisms.yaml trong 1 merge?
- **Trace:**  · SPEC `210721-decision-anchoring` · task `T-260721-03`
- **Đã fill (default):** so nguyên file trong cùng commit/PR
- **Cần verify:** thử case 2 người sửa 2 mục khác nhau trong cùng file, cùng PR — xem so-nguyên-file có báo oan không
- **Rủi ro nếu default sai:** so nguyên file có thể báo oan (false positive) khi merge nhiều thay đổi hợp lệ cùng lúc, làm /lint mất tín nhiệm
- **Status:** resolved
- **Resolved:** So diff theo TỪNG MỤC (id), không so nguyên file — nâng thành FR-010/SC-008/T8, không còn là default nữa · fix: llmwiki/wiki/sources/draft/210721-decision-anchoring.md FR-010 + T8 + SC-008 · 2026-07-21

## Origin
- Sinh bởi `/propose` khi user chọn "fill-first, find-out-later" cho một unknown của SPEC nguồn.
- Trả nợ: `unknown-ledger.py --resolve <file> <U-id> --value … --fixed … --date …`.
- **Commit:** _(verify-before-commit điền)_
