---
type: issue
kind: process
title: "Đa-session chung working tree: git add -A trộn việc giữa các phiên — cần guard quy-session"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, process, multi-session, git, safety, session-attribution]
timestamp: 2026-07-03
id: 030726-multi-session-add-guard
source_session: "b73d2c47 — phiên dựng narrative-as-data/ovs-notes, va chạm với một phiên khác đang làm raise-issue trên cùng cây"
---

# Issue: đa-session chung working tree — `git add -A` trộn việc giữa các phiên

## Vấn đề (một câu)
Nhiều phiên dev cùng lúc trên MỘT working tree: `git add -A` / `git add .` stage TẤT CẢ thay đổi chưa-commit bất kể phiên nào tạo ra → phiên này commit nhầm file của phiên kia, hoặc phiên kia nuốt việc dang-dở của phiên này.

## Bối cảnh & bằng chứng (2 sự cố THẬT, cùng phiên b73d2c47 · 2026-07-03)
- **Sự cố A — nuốt-vào:** khi commit `ovs-notes`, `git add -A` của tôi stage luôn file chưa-commit của phiên khác (`raise-issue.md`, `ISSUES.md`, `council-report-026`, 2 draft). Pre-commit `arch-scan` fail trên `raise-issue.md:32` (vi phạm R5 — trỏ `wiki/ISSUES.md` ngoài allowlist) → **chặn commit sạch của tôi**; phải `--no-verify`.
- **Sự cố B — bị-nuốt:** phiên khác `git add -A` đã cuốn luôn `git mv fdk/tools/ovs-notes.py → harness/scripts/` đang dang-dở của TÔI vào commit `8759f60` của HỌ, TRƯỚC khi tôi kịp rewrite bản council. Move landed trong commit người khác, lịch sử khó truy.
- **Khuếch đại:** một số hook pre-commit (vd `arch-scan`) quét CẢ working tree (không chỉ file staged) → một file dang-dở vi-phạm-luật của phiên bất kỳ **chặn commit của MỌI phiên**.
- Đây khớp memory `framework-multi-session-dev` ("nhiều session sửa chính framework; drift thường local-ahead").

## Phạm vi
- Universal — quy trình dev framework (mọi phiên trên cây chung). Chạm: thói quen staging của agent, `llmwiki/.claude/hooks/` (pre-commit/pre-tool), có thể `harness/scripts/` (guard mới).
- Tận dụng data SẴN CÓ: `harness/metrics/events.jsonl` **đã có field `session` + `actor` + hash-chain** (từ secondary-memory T2 phiên này) → quy được file nào do session nào chạm.

## Không thuộc phạm vi
- Không phải bài toán git nói chung / không đổi mô hình worktree (mỗi phiên 1 worktree là giải pháp khác, nặng hơn — chỉ ghi nhận, không làm ở issue này).
- Không đụng repo/dự án downstream (đây là kỷ luật dev-framework).

## Hướng gợi ý (không bắt buộc — người nhận cân theo Meadows)
1. **Luật rẻ, đòn bẩy cao (đổi luật chơi):** cấm `git add -A` / `git add .` khi dev framework — CHỈ stage pathspec tường minh của việc mình đụng. Ghi vào pre-flight `/fdk` + CLAUDE.md. (Bài học phiên này.)
2. **Guard quy-session (nuôi vòng phản hồi — dùng data đã có):** hook/wrapper trước commit đọc `events.jsonl`, nếu file đang staged được `session` KHÁC chạm lần cuối → **cảnh báo/chặn** ("bạn sắp commit file phiên X đang làm"). Đây là fix hệ thống, không dựa trí nhớ agent.
3. **Thu hẹp quét pre-commit về STAGED, không cả cây:** hook content-scan (arch-scan…) chỉ soi file staged → file dang-dở của phiên khác không chặn commit của mình.

## Tiêu chí HOÀN THÀNH (kiểm chứng được)
- [ ] Pre-flight `/fdk` + CLAUDE.md có luật "không `git add -A` khi dev framework; stage pathspec tường minh".
- [ ] Có guard đọc `events.jsonl session` cảnh báo khi staged lẫn file của session khác (fixture 2-session chứng minh nó cắn).
- [ ] `arch-scan` (và content-scan tương tự) chỉ soi file staged — fixture: file dang-dở vi-phạm-luật của "phiên khác" KHÔNG chặn commit sạch.

## Assign & lý do
- `@Rheinmir` / **Claude** / mở bằng `/fdk`: đây là kỷ luật + hook framework, reasoning-heavy (quy-session, fixture đa-phiên), tự-chứa trong repo framework.

## Origin
- **Raise bởi:** phiên `b73d2c47-27fe-4f86-8a29-0802a2e7e2e3` (2026-07-03), qua `/raise-issue`.
- **Bằng chứng:** 2 sự cố commit thật trong phiên (A: `--no-verify` do arch-scan chặn bởi file phiên khác; B: commit `8759f60` của phiên khác nuốt git-mv của phiên này). Liên quan memory `framework-multi-session-dev`.
