---
type: issue
kind: feature-gap
title: "Thống kê skill-usage thực tế → dashboard HTML báo cáo hàng tuần"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, analytics, skill-usage, dashboard, weekly-report, telemetry]
timestamp: 2026-07-03
id: 030726-skill-usage-dashboard
source_session: "Phiên 2026-07-03 — yêu cầu thống kê skill nào dùng nhiều + dashboard tuần"
---

# Issue: Thống kê skill-usage thực tế + dashboard HTML hàng tuần

## Vấn đề (một câu)
Dự án có ~70 skill nhưng **không biết skill nào thực sự được dùng, dùng bao nhiêu, khi nào** — thiếu số liệu để biết skill nào đáng giữ/gộp/bỏ, và không có báo cáo tuần cho sức khoẻ quy trình.

## Bối cảnh & bằng chứng
- **Hiện KHÔNG track skill-usage.** `post_tool_use.py` chỉ audit file-write (R4) + code-logger cho thay đổi file framework; `scratch-log.jsonl` log thay đổi file kèm "why". Không hook nào đếm lời gọi Skill.
- **Nguồn dữ liệu đã có, không cần thêm hạ tầng thu thập:** transcript phiên Claude Code `~/.claude/projects/-Users-giatran-orca-setup-setup/*.jsonl` chứa mọi lời gọi Skill tool (tên skill, timestamp, session). Đây chính là nguồn `caveman-stats` và `orca-eval` đang đọc.
- **Nơi xuất báo cáo đã có khuôn:** `llmwiki/html/` (convention `DDMMYY-slug.html`), render bằng `docs-site-macos`/`md-to-html`; `index.html` liệt kê report.
- Liên quan: `[[orca-eval]]` (quét N session gần nhất → report), `caveman-stats` (đọc session log), `[[ADR-005]]` (thứ cần travel đi theo harness — dashboard generator nên travel được).

## Phạm vi
- Một tool `fdk/tools/skill-usage.py` (hoặc `harness/scripts/`) đọc transcript `.jsonl`, parse các event Skill-tool, đếm theo skill + theo tuần (ISO week), xuất:
  - bảng xếp hạng skill dùng nhiều nhất (count, lần cuối dùng, số session chạm)
  - skill "chết" (0 lần trong N tuần) — đầu vào cho quyết định gộp/bỏ
  - xu hướng theo tuần
- Một **dashboard HTML hàng tuần** `llmwiki/html/weekly-<ISOweek>.html`: top skills (bar), skill chết, tổng phiên/tuần, so tuần trước.
- (Tuỳ) skill `/skill-report` gói lại: chạy tool → render dashboard → mở.
- (Tuỳ) tự động hoá tuần: cron/schedule hoặc gợi ý trong stop-hook cuối tuần.

## Không thuộc phạm vi
- KHÔNG thêm hook thu thập realtime mới (dữ liệu đã nằm trong transcript — chỉ đọc, tránh phình hook mọi phiên).
- KHÔNG gửi telemetry ra ngoài — đọc local, render local.
- KHÔNG đo chất-lượng-skill (đúng/sai), chỉ đo TẦN SUẤT dùng. (Chất lượng là việc của trace-grader/orca-eval.)

## Hướng gợi ý (không bắt buộc)
- Parse `.jsonl`: lọc message có `tool_use` name = `Skill` (và slash-invocation trong user text nếu muốn) → `{skill, ts, session}`.
- Gom theo `strftime('%G-W%V')`; cache kết quả để không parse lại transcript cũ (append-only).
- Render bằng `docs-site-macos` (glass) hoặc dataviz skill cho biểu đồ; một file HTML self-contained.
- Cẩn thận privacy: chỉ đọc project của repo này, không quét project khác.

## Tiêu chí HOÀN THÀNH
1. `python3 fdk/tools/skill-usage.py --weekly` in bảng xếp hạng skill + skill chết cho tuần hiện tại, số liệu khớp transcript thật (spot-check ≥3 skill đếm tay).
2. Sinh `llmwiki/html/weekly-<ISOweek>.html` self-contained, có top-N + skill-chết + so tuần trước.
3. Chạy lại cùng tuần → số liệu ổn định (deterministic trên cùng tập transcript).
4. Không đọc ngoài project repo này; không side-effect mạng.

## Assign & lý do
- **assignee @Rheinmir · dispatch Claude · entry /fdk**: framework tooling (thêm tool + có thể skill mới), cần hiểu nguồn transcript + convention html/. Phần render biểu đồ có thể sub opencode sau.
- **priority P2**: hữu ích cho quyết định gộp/bỏ skill (đúng tinh thần Lão Tử ở council-026: bỏ cái không dùng), nhưng không chặn vận hành.

## Origin
Raise bởi skill `/raise-issue` phiên 2026-07-03 theo yêu cầu user: thống kê skill dùng nhiều + dashboard HTML tuần. Bằng chứng nguồn dữ liệu: transcript `~/.claude/projects/-Users-giatran-orca-setup-setup/*.jsonl` (đã dùng bởi caveman-stats/orca-eval). Chưa thực hiện — defer cho phiên /fdk kế.
