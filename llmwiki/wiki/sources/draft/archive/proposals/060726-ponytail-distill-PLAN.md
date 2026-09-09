---
type: plan
issue: 060726-ponytail-distill
title: "PLAN — Chưng cất Ponytail (anti-over-engineering) vào overstack"
status: draft
timestamp: 2026-07-07
tags: [plan, yagni, anti-over-engineering, simplify, distill]
---

# PLAN — Chưng cất Ponytail (DietrichGebert/ponytail) vào overstack

## Origin

- Nguồn: https://github.com/DietrichGebert/ponytail (clone depth-1, đọc 2026-07-07) — file lõi: `skills/ponytail/SKILL.md`, `AGENTS.md`, `skills/ponytail-{review,audit,debt}/SKILL.md`.
- Yêu cầu user (phiên 2026-07-07): "chưng cất phần hay của repo ponytail, giảm thiểu over-engineering, planning cách adapt, raise issue GH".

Ngày: 2026-07-07 · Nguồn: https://github.com/DietrichGebert/ponytail (76k ⭐, MIT)
Trạng thái: draft — chờ duyệt

## 1. Ponytail là gì

Skill "lazy senior dev" chống over-engineering cho AI agent. Lõi giá trị nằm gọn trong ~5 khối text; phần còn lại của repo (hooks JS đa nền tảng, MCP server, plugin cho 6 harness, benchmark suite, statusline) là bao bì phân phối — chính là thứ ta KHÔNG cần (bằng chứng: fork `ponytail-lite` 130⭐ tồn tại chỉ để bỏ "plugin madness").

## 2. Phần đáng chưng cất (giữ)

1. **The Ladder — 7 bậc, dừng ở bậc đầu tiên đứng vững**:
   YAGNI (có cần tồn tại không?) → đã có trong codebase? → stdlib? → native platform (CSS thay JS, DB constraint thay app code)? → dependency đã cài? → 1 dòng được không? → cuối cùng mới viết code tối thiểu.
2. **"Ladder chạy SAU khi hiểu bài, không thay cho hiểu bài"** — đọc code, trace flow end-to-end trước, rồi mới leo thang. Diff nhỏ ở chỗ sai = bug thứ hai.
3. **Bug fix = root cause, không vá triệu chứng** — grep mọi caller, sửa 1 lần ở hàm chung; fix lazy ĐÚNG là fix root-cause vì diff nhỏ hơn vá từng caller.
4. **Marker nợ có kỷ luật**: shortcut cố ý đánh dấu `ponytail:` comment ghi rõ *ceiling* + *upgrade trigger* (`# ponytail: global lock, per-account locks nếu throughput thành vấn đề`) → grep được thành ledger, deferral không mục thành "never".
5. **Carve-out an toàn (When NOT to be lazy)**: không giản lược validation ở trust boundary, error handling chống mất data, security, a11y, calibration phần cứng; logic non-trivial phải để lại ĐÚNG 1 check chạy được (assert demo / 1 test file nhỏ) — YAGNI áp cho cả test.
6. **Format review 1 dòng/finding** của ponytail-review/audit: `L12: stdlib: validator 27 dòng → "@" in email, 1 dòng.` + tag (`delete/stdlib/native/yagni/shrink`) + chốt `net: -N lines`. Nothing to cut → "Lean already. Ship."
7. **Output contract**: code trước, tối đa 3 dòng "skipped X, add when Y". Giải thích dài hơn code = xoá giải thích.

## 3. Phần over-engineered (bỏ, không mang theo)

- Hooks runtime JS (~20KB) + mode-tracker + statusline cho Claude/Codex/Copilot/Gemini/Hermes/OpenClaw — harness ta đã có cơ chế skill riêng.
- MCP server ponytail-mcp — chỉ để bơm instructions, thừa.
- 3 intensity level (lite/full/ultra) + persistence state — giữ 1 mức mặc định là đủ; ai cần "lite" thì nói bằng lời.
- 11 test file + benchmark arms — test cho bao bì, không cho nội dung.
- 5 skill tách rời (ponytail/review/audit/debt/gain/help) — ta gộp còn ~2 điểm chạm.

## 4. Đối chiếu cái đã có trong overstack (tránh trùng)

| Ponytail | Overstack hiện có | Gap |
|---|---|---|
| ladder khi VIẾT code | — (chỉ có review sau khi viết) | ✅ gap chính |
| ponytail-review/audit | `/simplify`, `/code-review` | format 1-dòng + tag + `net: -N` là nâng cấp nhỏ |
| ponytail-debt ledger | — | ✅ gap: chưa có convention marker nợ grep-được |
| output terse | `/caveman` | trùng — không mang theo, ponytail tự nói "pair with Caveman" |

## 5. Kế hoạch adapt (3 bước, nhỏ nhất chạy được)

- **B1 — Luật viết-code**: thêm khối "Ladder + carve-out an toàn + root-cause" (~25 dòng, cỡ AGENTS.md của ponytail-lite) vào tầng luật luôn-nạp của framework (AGENT.md/rules), KHÔNG làm skill riêng phải nhớ gọi — chống over-engineering phải là mặc định, không phải opt-in.
- **B2 — Marker nợ**: chuẩn hoá comment `shortcut:` (tên trung lập thay `ponytail:`) với format `<ceiling>, <upgrade trigger>`; thêm 1 lệnh grep vào /lint hoặc medic để liệt kê marker thiếu trigger. Không viết skill ledger riêng.
- **B3 — Nâng /simplify**: bổ sung format finding 1-dòng + 5 tag + chốt `net: -N lines` / "Lean already. Ship." vào skill simplify hiện có, thay vì tạo ponytail-review song song.

Không làm: hooks, MCP, intensity levels, statusline, skill mới đứng riêng.

## 6. Rủi ro

- Luật luôn-nạp tăng ~25 dòng context mỗi phiên — đổi lại giảm diff thừa, chấp nhận.
- Xung đột với task "build đầy đủ theo spec": carve-out "anything explicitly requested" đã xử lý.
- License MIT — trích ý tưởng + ghi nguồn là đủ.
