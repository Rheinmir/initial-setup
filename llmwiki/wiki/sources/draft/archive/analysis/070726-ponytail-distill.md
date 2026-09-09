---
type: issue
kind: process
title: "Chưng cất Ponytail (anti-over-engineering ladder) vào overstack, bỏ phần bao bì thừa"
status: open
assignee: Rheinmir
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, yagni, anti-over-engineering, simplify, distill]
timestamp: 2026-07-07
id: 070726-ponytail-distill
source_session: phiên 2026-07-07 — user yêu cầu chưng cất repo ponytail + planning adapt
---

# Issue: Chưng cất Ponytail vào overstack

## Vấn đề (một câu)
Overstack chưa có luật chống over-engineering ÁP LÚC VIẾT code (chỉ có review sau khi viết qua /simplify), trong khi ponytail (76k ⭐) đã chứng minh một bộ luật ~25 dòng làm được việc này.

## Bối cảnh & bằng chứng
- Nguồn: https://github.com/DietrichGebert/ponytail (MIT) — lõi giá trị = "the ladder" 7 bậc (YAGNI → reuse codebase → stdlib → native → dep đã cài → 1 dòng → code tối thiểu) + carve-out an toàn + root-cause fix + marker nợ `ponytail: <ceiling>, <upgrade trigger>`.
- Bản thân repo ponytail over-engineered ở tầng phân phối (hooks JS 6 nền tảng, MCP server, 3 intensity level, benchmark suite) — fork `ponytail-lite` tồn tại chỉ để bỏ "plugin madness" → ta chỉ distill NỘI DUNG, không mang bao bì.
- Plan chi tiết đã viết: `llmwiki/wiki/sources/draft/060726-ponytail-distill-PLAN.md` (bảng đối chiếu với /simplify, /code-review, /caveman hiện có).

## Phạm vi
3 bước trong PLAN:
1. B1 — thêm khối "Ladder + carve-out + root-cause" (~25 dòng) vào tầng luật luôn-nạp (AGENT.md/rules) — mặc định, không opt-in.
2. B2 — chuẩn hoá marker nợ `shortcut: <ceiling>, <upgrade trigger>` + grep liệt kê marker thiếu trigger trong /lint hoặc medic.
3. B3 — nâng /simplify: format finding 1-dòng, 5 tag (delete/stdlib/native/yagni/shrink), chốt `net: -N lines` / "Lean already. Ship."

## Không thuộc phạm vi
- KHÔNG port hooks/MCP/statusline/intensity levels/skill đứng riêng của ponytail.
- KHÔNG đổi /caveman (ponytail tự nhận "pair with Caveman" — trùng phần prose, bỏ).

## Hướng gợi ý (không bắt buộc)
Bắt đầu từ `AGENTS.md` của ponytail (bản 32 dòng self-contained) làm nguồn distill cho B1 thay vì SKILL.md 120 dòng.

## Tiêu chí HOÀN THÀNH
- Luật ladder xuất hiện trong tầng luôn-nạp và selftest/medic không đỏ.
- `grep -rnE '(#|//) ?shortcut:'` được /lint nhận diện, marker thiếu trigger bị flag.
- /simplify xuất finding đúng format 1-dòng + tag + `net:` trên một diff mẫu.

## Assign & lý do
Assignee: Rheinmir (owner repo). Dispatch: Claude qua `/fdk` — đây là sửa chính framework (luật + skill), đúng cửa /fdk theo ADR-004.

## Origin
Raise bởi Claude, phiên 2026-07-07 theo yêu cầu user "chưng cất phần hay của repo ponytail". Bằng chứng: clone depth-1 DietrichGebert/ponytail, đọc `skills/ponytail/SKILL.md`, `AGENTS.md`, `skills/ponytail-{review,audit,debt}/SKILL.md`. Plan: [[060726-ponytail-distill-PLAN]].
