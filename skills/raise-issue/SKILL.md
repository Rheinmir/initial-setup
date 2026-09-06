---
name: raise-issue
description: "Raise một ISSUE đầy đủ bối cảnh vào ledger local (draft) để dev khác pull về xử lý ở BẤT KỲ đâu qua /fdk mà không đụng nhánh/dự án khác; TỰ mirror lên tracker remote nếu có (GitHub qua gh / GitLab qua glab / Gitea qua tea) — ledger là nguồn chân lý. Dùng cho feature-gap, tech-debt, foundation, câu hỏi kiến trúc (KHÁC orca-issue = sự cố/bug repro-first). Gồm template context + assign owner + dispatch agent. Trigger: 'raise issue', 'tạo issue', 'ghi issue', 'mở issue', 'log gap này', 'issue để dev khác làm', '/raise-issue'."
---

# Skill: raise-issue

## When to use
- Phiên ĐỂ HỎI/thiết kế, phát hiện một GAP hoặc nợ nhưng CHƯA thực hiện — cần ghi lại đủ bối cảnh để phiên/dev khác kéo về làm.
- "raise issue", "tạo issue", "mở issue cho việc này", "log gap này để sau làm", "issue để dev khác pull về".
- Feature-gap, tech-debt, câu hỏi kiến trúc, cải tiến quy trình, Plan-B/optionality.
- **KHÔNG dùng** cho: bug/sự cố runtime/regression đang cháy → đó là `orca-issue` (repro-first gate). Việc đã sẵn sàng làm ngay trong phiên → đó là `propose` rồi code.

## Ranh giới với skill khác (đọc trước khi trùng)
- `orca-issue` = vòng xử lý SỰ CỐ (bug), bắt buộc tái hiện đỏ→xanh. raise-issue = ghi việc TIẾN VỀ PHÍA TRƯỚC (gap/nợ), không repro.
- `propose` = plan để LÀM NGAY trong phiên này. raise-issue = HANDOFF, cố ý defer, travel được sang phiên/máy/dự án khác.
- raise-issue chỉ GHI + ASSIGN. Không code, không sửa nhánh khác. Người nhận sau này mở bằng `/fdk` (nếu là framework) hoặc `/propose` (nếu là feature dự án).

## Nơi lưu — ledger local là NGUỒN CHÂN LÝ, tracker remote là mirror
- Issue = một file draft: `llmwiki/wiki/sources/draft/DDMMYY-<slug>.md` (cùng chỗ propose, đi theo repo khi clone — travel-được, không phụ thuộc tracker ngoài). **Đây luôn là nguồn chân lý.**
- Index tập trung: `llmwiki/wiki/sources/ISSUES.md` — một dòng/issue (id · tiêu đề · status · assignee · **tracker**), giống MEMORY.md. (Lưu ở `sources/` chứ KHÔNG ở `wiki/` root — R5 folder-structure chặn root.)
- **Mirror lên tracker remote NẾU CÓ** (để hiện ở tab Issues, assign người thật, có notification): tự phát hiện theo `git remote get-url origin` + CLI sẵn có, mirror rồi ghi link vào cột `tracker`. Ledger vẫn là nguồn chân lý; tracker chỉ là bản sao để phối hợp.

## Tracker — đọc HỢP ĐỒNG của repo, đừng hardcode CLI ở đây
Cách publish/fetch/label/close/claim ở repo này sống trong **một file hợp đồng theo repo** — `llmwiki/wiki/sources/issue-tracker.md` (adapter boundary). Skill này chỉ nói *ý định*; hợp đồng nói *cách làm*. Đổi tracker (thêm Jira, đổi GitLab) là sửa hợp đồng đó, KHÔNG sửa skill này. Xem `[[issue-tracker]]`.
- Chưa có file hợp đồng → tạo từ mẫu (mặc định **local-markdown**: ledger là gốc, không cần mạng); có remote GitHub → đề xuất thêm mirror `gh`.
- Body issue remote PHẢI link ngược về file ledger (nguồn chân lý). Ghi URL vào cột `tracker`.
- **5 nhãn chuẩn** (cột `labels`, mặc định `needs-triage`): `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix`. Chỉ `ready-for-agent` mới được dispatch cho CLI headless; `ready-for-human` là việc phải người.

## Hook wiki sẽ cắn — thoả ngay từ đầu (đỡ 3 lần bật lại)
Mọi file trong `llmwiki/wiki/` phải có: **(R9)** YAML frontmatter OKF ở đầu (`type/title/status/tags/timestamp/id`) · **(R2)** section `## Origin` truy nguồn · **(R5)** nằm trong folder hợp lệ (`sources/draft/` cho issue, `sources/` cho index). Template dưới đã gồm sẵn cả ba.

## Steps
1. **Phân loại** issue: `foundation` | `feature-gap` | `tech-debt` | `architecture` | `process`. Nếu là bug → dừng, chuyển sang `orca-issue`.
2. **Query wiki trước khi viết** (R7-f): tìm ADR/concept/draft liên quan để không trùng và để nêu bối cảnh chính xác. Ghi các link `[[...]]` vào phần Bối cảnh.
3. **Viết draft** `llmwiki/wiki/sources/draft/DDMMYY-<slug>.md` theo template dưới — bối cảnh phải ĐỦ để người chưa dự phiên này pull về là hiểu ngay (vì sao issue tồn tại, bằng chứng, phạm vi, tiêu chí xong).
4. **Assign**: điền `assignee` (người/agent chịu trách nhiệm) + `dispatch` (đề xuất Claude/opencode/human) + `entry` (mở bằng `/fdk` hay `/propose`). Nêu lý do chọn.
5. **Đăng ký vào index**: thêm một dòng vào `llmwiki/wiki/sources/ISSUES.md` (tạo file nếu chưa có, header `# Issues — ledger local`).
6. **Mirror lên tracker remote (nếu có)**: phát hiện host + CLI (bảng trên); nếu có → tạo issue remote (body link ngược file ledger), ghi URL vào cột `tracker`. Không có → bỏ qua, ledger-only. Hỏi assignee (username) nếu chưa rõ.
7. **Commit ledger** (GH#99): `git add llmwiki/wiki/sources/draft/<DDMMYY-slug>.md llmwiki/wiki/sources/ISSUES.md && git commit -m "issue: <DDMMYY-slug> — <tiêu đề>"`. Ledger chỉ là nguồn chân lý khi nó **travel theo repo** — file untracked thì người pull về không thấy, `git log --all` rỗng, tức issue chưa tồn tại. Không push ở bước này (đó là việc của `/ship`); nếu đang ở nhánh chính và không được commit thẳng → tạo nhánh `issue/<DDMMYY-slug>` rồi commit vào đó và nói rõ.
8. **Xác nhận, KHÔNG thực hiện**: báo lại issue id + đường dẫn ledger + link tracker + assignee. Dừng ở đây — việc thực thi là của phiên nhận.

## Template issue (frontmatter + thân)
```markdown
---
type: issue
kind: foundation | feature-gap | tech-debt | architecture | process
title: "<một câu>"
status: open            # open | claimed | in-progress | done | wontfix
assignee: <tên/agent>   # ai chịu trách nhiệm
dispatch: <Claude | opencode:<model> | human>
entry: /fdk | /propose  # người nhận mở bằng skill nào
priority: P1 | P2 | P3
tags: [issue, <...>]    # R9 OKF
timestamp: <YYYY-MM-DD>
id: <DDMMYY-slug>
source_session: <mô tả ngắn phiên phát hiện>
---

# Issue: <tiêu đề>

## Vấn đề (một câu)
## Bối cảnh & bằng chứng   (vì sao issue tồn tại; link [[ADR]]/[[concept]]/report/council)
## Phạm vi                 (đụng file/module/dự án nào; universal hay local)
## Không thuộc phạm vi     (chống scope-creep)
## Hướng gợi ý (không bắt buộc)
## Tiêu chí HOÀN THÀNH     (kiểm chứng được)
## Assign & lý do
## Origin                  (R2 — raise bởi ai/phiên nào, nguồn bằng chứng)
```

## Rules
- CHỈ ghi + assign. Tuyệt đối không code, không sửa nhánh/dự án khác — issue phải travel sạch.
- Bối cảnh đủ cho người-chưa-dự-phiên: nêu bằng chứng (report/council/ADR), không giả định trí nhớ chung.
- Query wiki trước (R7-f) để không raise trùng issue đã có.
- Mỗi issue một file + một dòng index. Không nhét nhiều issue vào một file.
- Không tự nâng status quá `open`/`claimed` — chuyển `in-progress`/`done` là việc của phiên nhận.
- Touch only what the task requires — no opportunistic changes.
