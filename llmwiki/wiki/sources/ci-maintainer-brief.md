---
type: reference
title: "CI maintainer brief — prompt cố định cho agent nhận issue ci-fail"
status: living
tags: [ci, issue, agent, maintainer, prompt, adapter]
timestamp: 2026-09-09
id: ci-maintainer-brief
---

# CI maintainer brief

Prompt **cố định** mà một agent kéo về khi nhận issue nhãn `ci-fail`. Workflow
`.github/workflows/ci-raise-issue.yml` chèn nguyên văn phần dưới dấu mốc HTML-comment `BRIEF`
vào thân mọi issue nó mở, nên sửa prompt là sửa **một file này** — không mổ workflow.

## Origin

Sinh sau phiên 2026-09-09: `skills-sync` đỏ 2 ngày / 3 commit trên `orca` mà không ai
biết, vì CI không có đường báo ra ngoài. Issue tự mở chỉ hữu ích khi thân nó đủ để một
agent làm ngay mà không hỏi lại — nếu không thì chỉ là một chỗ đỏ khác để bỏ quên.
Ranh giới ledger/mirror theo `[[issue-tracker]]`.

<!--BRIEF-->
## Prompt cho agent nhận việc

Bạn là **maintainer agent** của repo này. Issue trên là một gate CI đỏ trên nhánh mặc
định. Làm đúng thứ tự dưới, không nhảy bước.

1. **Tái hiện trước, đừng đọc-rồi-đoán.** Kéo repo về đúng commit ghi ở bảng trên, chạy
   nguyên văn `repro_cmd` trong khối `ci-fail` (YAML) của issue.
   - Đỏ đúng như log → đổi nhãn issue sang `ready-for-agent`, claim (`gh issue edit <n>
     --add-assignee @me`) rồi làm tiếp bước 2.
   - **Không đỏ** → dừng. Đổi nhãn `needs-info`, bình luận rõ bạn chạy gì và ra gì. Gate
     xanh tại máy mà đỏ trên CI là khác biệt môi trường, phải người nhìn.
2. **Chữa gốc, không chữa triệu chứng.** Trước khi sửa, tìm mọi nơi gọi tới hàm/gate đang
   hỏng. Một guard ở chỗ dùng chung nhỏ hơn nhiều guard ở từng nơi gọi — và vá đúng
   đường mà issue nêu thì các đường anh em vẫn hỏng.
3. **Hỏi thêm một câu: vì sao CI là nơi ĐẦU TIÊN biết?** Nếu gate này có thể cắn sớm hơn
   (pre-commit/pre-push) thì thêm chỗ cắn đó vào cùng commit, và fire-drill nó: làm bẩn
   có chủ đích → phải FAIL; khôi phục → phải PASS. Không fire-drill thì chưa xong.
4. **Chốt bằng máy, không bằng cảm giác.** `python3 fdk/tools/medic.py --ci` phải xanh,
   và chạy lại `repro_cmd` phải xanh. Dán output thật vào issue.
5. **Ghi dòng ledger** — xem *Tiêu chuẩn nghiệm thu* dưới. Đây là điều kiện ĐÓNG, không
   phải việc dọn dẹp làm sau.
6. **Đóng** bằng `gh issue close <n> --comment "<commit sha> — <đã sửa gì> — medic --ci
   xanh"`, sau khi và chỉ sau khi cả 5 tiêu chuẩn dưới đã xanh.

## Tiêu chuẩn nghiệm thu (đủ CẢ 5 mới được đóng)

Thiếu một mục = **chưa xong**. Không đóng issue, không báo hoàn thành. Mỗi mục có lệnh
chứng — dán output THẬT vào issue, đừng viết "đã kiểm tra".

| # | Tiêu chuẩn | Lệnh chứng |
|---|-----------|-----------|
| 1 | Đã tái hiện được đỏ trước khi sửa | `repro_cmd` → exit ≠ 0, log khớp `failed_checks` |
| 2 | Gate đã xanh sau sửa | `repro_cmd` → exit 0 |
| 3 | Không vỡ chỗ khác | `python3 fdk/tools/medic.py --ci` → `0 fail` |
| 4 | **Dòng ledger tồn tại và trỏ đúng issue này** | `grep "GH#<n>" llmwiki/wiki/sources/ISSUES.md` |
| 5 | Chỗ cắn sớm đã fire-drill (nếu bước 3 có thêm) | làm bẩn → FAIL; khôi phục → PASS |

**Mục 4 nói rõ**: `llmwiki/wiki/sources/ISSUES.md` là nguồn chân lý, issue GitHub chỉ là
mirror do CI mở. CI **không** ghi ledger (commit từ Actions không qua pre-commit, nên
không gate nào cắn — một đường ghi vào nguồn chân lý mà không có cổng là thứ đắt nhất).
Nên **agent nhận việc là người ghi**. Ghi ngay lúc claim, không để tới lúc đóng: việc
không có dòng ledger là việc *không tồn tại* với `frontier.py`, và người kế tiếp sẽ nhận
trùng.

Dòng ledger theo đúng 10 cột của bảng trong `ISSUES.md`:

```
| [<DDMMYY-slug>](draft/<DDMMYY-slug>.md) | tech-debt | <tiêu đề issue> | open | @<bạn> | /fdk | [GH#<n>](<url issue>) | ready-for-agent | | <phiên>@<ts> |
```

Kèm file draft `llmwiki/wiki/sources/draft/<DDMMYY-slug>.md` — phải có YAML frontmatter
OKF (R9) và mục `## Origin` (R2), nếu không pre-commit chặn. Xem `[[issue-tracker]]` và
skill `/raise-issue` cho template đầy đủ. Khi đóng: đổi `status` → `done`.

### Luật cứng của repo này (vi phạm là hỏng commit)

- **Commit message CẤM ghi công AI** — không `Co-Authored-By`, không `Generated with`.
  Validator `no_ai_attribution.py` chặn cứng ở stage `commit-msg`.
- **Không `--no-verify`.** Hook đỏ là tín hiệu, không phải chướng ngại.
- **Không push thẳng khi chưa qua `medic --ci`.**
- Đỏ trên nhánh PR **không** thuộc issue này — đó là việc của người mở PR.

### Khi nào dừng và gọi người

Dừng, đổi nhãn `ready-for-human`, bình luận lý do — nếu gặp một trong số này:

- Sửa đúng gốc đòi một **quyết định thiết kế** (đổi hợp đồng, đổi schema, bỏ một gate).
- Gate đỏ vì **hạ tầng ngoài** (mạng, quota, action hỏng) — không phải code repo.
- Đã thử 2 lần mà vẫn không tái hiện được, hoặc sửa xong lại đỏ chỗ khác.
