---
type: issue
kind: tech-debt
title: "Self-test harness chạy git commit LỒNG không tắt hook → nguy cơ tự-kích đệ quy"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, harness, self-test, pre-commit, recursion, git-hooks]
timestamp: 2026-07-04
id: 040726-selftest-nested-commit-unguarded
source_session: "Phiên 2026-07-04 — gặp treo commit thật khi ship GH#8, truy ra self-test commit lồng"
---

# Issue: Self-test harness chạy `git commit` lồng không tắt hook

## Vấn đề (một câu)
Ba self-test của harness (`decision-adr-gate-test.sh`, `r12-v3-workspace-test.sh`, `harness-update-test.sh`) tạo repo git tạm rồi chạy `git commit` LỒNG **mà không tắt hook** — nếu bất kỳ self-test nào bị nối lại vào một commit-time hook (`pre-commit`/`commit-msg`), commit lồng sẽ tự-kích lại chính hook đó → đệ quy bùng nổ tổ hợp.

## Bối cảnh & bằng chứng
- Phiên 2026-07-04 (ship GH#8): mọi `git commit` treo >2 phút rồi timeout. `ps` cho thấy **hàng chục** tiến trình `git commit -qm adr2` + `pre_commit hook-impl … COMMIT_EDITMSG` chồng nhau.
- Truy nguồn: `harness/tests/decision-adr-gate-test.sh` dòng 32 & 36 chạy `git commit -qm init` / `git commit -qm adr2` trong repo tạm. Vì commit lồng **không** tắt hook, mỗi commit tự-kích lại commit-msg hook → chạy lại self-test → lại 2 commit lồng. Nhánh 2 → `2^depth` tiến trình, không hội tụ.
- Hệ quả quan sát: (1) commit treo, buộc `--no-verify` (bỏ qua CẢ 17 rule); (2) bị kill giữa chừng để lại index bẩn (`ADR-002-new.md` trạng thái `AD` + phantom deletion); (3) pre-commit stash file unstaged, kill xong **không trả lại** → nguy cơ mất việc chưa lưu (đã thấy `.claude/settings.json` bị phẳng về `.bak`).
- Liên quan: `[[harness-enforcement-floor]]` (CI L4 mới là sàn thật, L2 chỉ tiện-nghi), GH#18 (`040726-precommit-slow-fragile-on-commit` — đã trim 25→12 hook, tháo self-test khỏi pre-commit). GH#18 chữa TRIỆU CHỨNG (gỡ self-test khỏi hook); issue này chữa GỐC (self-test tự nó không được phép tự-kích, dù tương lai ai đó nối lại vào hook).

## Phạm vi
- 3 file: `harness/tests/decision-adr-gate-test.sh`, `harness/tests/r12-v3-workspace-test.sh`, `harness/tests/harness-update-test.sh`.
- Mọi lời gọi `git commit` LỒNG trong self-test (tổng 5 điểm).

## Không thuộc phạm vi
- KHÔNG đụng nội dung logic test (chỉ làm commit lồng không-tự-kích-hook).
- KHÔNG thay lại kiến trúc pre-commit (đó là GH#18).

## Hướng gợi ý (không bắt buộc)
- Guard mọi commit lồng: `git -c core.hooksPath=/dev/null commit --no-verify …` (đai + nịt: `--no-verify` bỏ pre-commit/commit-msg; `core.hooksPath=/dev/null` chặn cả post-commit / hook kế thừa qua config global).
- Thêm một guard-test rà chính các file self-test: `grep 'git commit'` trong `harness/tests/` phải không còn dòng nào thiếu `no-verify|hooksPath` — biến bất-biến này thành rào tự-cắn.

## Tiêu chí HOÀN THÀNH
1. Mọi `git commit` lồng trong `harness/tests/*.sh` đều tắt hook (`--no-verify` + `core.hooksPath=/dev/null`).
2. Cả 3 self-test vẫn PASS như cũ (decision-adr-gate, r12-v3-workspace, harness-update).
3. Không còn khả năng tự-kích đệ quy dù self-test được nối lại vào commit-time hook.
4. grep-guard chống tái phát: git-op sinh-hook mới không guard → fail. **(ĐÃ LÀM — council report-028 chốt là bắt buộc, không tuỳ)**
5. Phủ CẢ `git push` (không chỉ commit) — cùng lớp nguy cơ `pre-push`. **(ĐÃ LÀM: r12:31,37 guarded)**

## Council (report-027/028) — đánh giá trước merge
Hội đồng feynman·linus·kahneman (case debug, cặp tension feynman↔linus). Winner **feynman**: fix đúng-gốc nhưng ban đầu chưa đủ (`git push` trần). Đồng thuận cả 3 ghế → **MERGE sau khi hoàn tất trong CHÍNH PR**: (a) guard 2 push, (b) thêm `harness/tests/hook-guard-invariant-test.sh` (rào tự-cắn, đã kiểm negative). Bất đồng duy nhất merge-now↔followup được giải: làm ngay tại chỗ, không PR-con.

## Assign & lý do
- **assignee @Rheinmir · dispatch Claude · entry /fdk**: sửa harness test (framework core), cần hiểu cơ chế hook + git worktree.
- **priority P2**: gốc-latent đã được GH#18 vô hiệu hoá bề mặt (tháo self-test khỏi hook), nhưng bất-biến an toàn nên chốt cứng để không tái phát khi tương lai nối lại.

## Origin
Raise bởi skill `/raise-issue` phiên 2026-07-04, sau khi gặp treo commit thật lúc ship GH#8 và truy ra self-test commit lồng. Bằng chứng: `ps` fork-storm `git commit -qm adr2`, `harness/tests/decision-adr-gate-test.sh:32,36`. Fix đã thực hiện trong CÙNG phiên (theo yêu cầu user chạy luồng raise→PR→council→merge) — xem PR liên kết.
