---
type: draft
title: 020726-audit-fdk-strategy — audit toàn dự án theo 8 nguyên tắc Mongol pattern
tags: [fdk, audit, output-report, strategy]
timestamp: 2026-07-02
id: 020726-audit-fdk-strategy
relations:
  - {rel: derives-from, path: fdk/wiki/concepts/fdk-dev-strategy.md}
---

# 020726-audit-fdk-strategy
**Type:** draft
**Status:** proposed
**Tags:** fdk, audit, output-report
**Proposed:** 2026-07-02

## What
Audit toàn bộ 3 trụ của dự án (harness / skills / llmwiki) đối chiếu kim chỉ nam `fdk-dev-strategy` (8 nguyên tắc "Mongol pattern") theo chuẩn pre-flight của `/fdk`, chạy bằng 3 agent song song.

## Kết quả theo trụ

### Trụ HARNESS — bề rộng tốt, chưa "một nguồn chân lý"
Điểm mạnh: 14 validator native + 1 vendor-neutral, 9 hook phủ đủ vòng đời, pre-commit 25+ hook, CI có retrieval-eval tất định (nguyên tắc #7 logistics vững).
Nợ (theo mức):
1. **[CAO — #3]** Policy chưa DRIVE enforcement: hook `pre_tool_use.py:44` hardcode danh sách validator thay vì đọc `policy.yaml`; policy tự ghi chú wiring thật ở `gen-converters.py`.
2. **[CAO — #3]** Drift thật 15 pattern (5 hook, 6 skill, AGENT/CLAUDE.md, overstack.html) nhưng version.json local = remote = 1.3.6 → drift bị che, không ai bị ép thu nợ.
3. **[CAO — #3/#7]** Validator mồ côi: `task_lifecycle.py` không được wire ở đâu; `code_health.py`, `agent_claude_parity.py`, `duplicate_basename.py` chạy ở CI nhưng không có rule R* trong policy → CI ≠ policy.
4. **[TRUNG — #7]** Feedback loop mỏng: `events.jsonl` 712 dòng nhưng `failures.jsonl` chỉ 3 — flywheel có ống nhưng tín hiệu chưa chảy.
5. **[TRUNG — #4]** Hai implement validate song song (native vs vendor-neutral) phải giữ đồng bộ bằng drift-test; enforcement phân mảnh 4 tầng không có ma trận rule×tầng.
6. **[THẤP]** `.claude/hooks/` gốc rỗng (hook thật ở `llmwiki/.claude/hooks/`); `harness-local/` là scaffold chết (`rules: []`, pre-commit `|| true`).

### Trụ SKILLS — lõi parity xuất sắc, mép đăng ký hụt
Điểm mạnh: **parity canonical ↔ mirror 66/66 byte-identical, 0 lệch**; AGENT.md/CLAUDE.md đủ 100%.
Nợ:
1. **[CAO — #3]** `fdk` — skill front-door — thiếu trong `marketplace.json` (65/66).
2. **[CAO — #6]** `extract-site` description sai bản chất (khai "site→markdown", body là design-token extraction) → dẫm chân `web-crawl`/design-taste; ứng viên merge/deprecate.
3. **[CAO — #3]** `ingest`/`propose`/`query` đăng ký 2 lần trong runtime list; bản cài `~/.claude/skills/query` lệch repo canonical (vi phạm ADR-003 skill-as-SoT).
4. **[TRUNG — #4]** design-taste v1/v2 treo không lịch deprecate; `last30days` 19.2k từ phình một file; họ onboard 4 skill ranh giới mờ.
5. **[THẤP — #3]** Header SKILL.md không đồng nhất (khó lint tự động) — nên chuẩn skeleton qua `new-skill`.

### Trụ LLMWIKI — rất khỏe, nợ nằm ở nhịp ship
Điểm mạnh: **0 vi phạm OKF, 0 index gap, 0 dead-link, 0 orphan** ở llmwiki/wiki; ADR-001..016 liên tục, không nợ ADR (cổng ADR-010 lành mạnh — nguyên tắc #1 đạt).
Nợ:
1. **[TRUNG — #8]** 15 draft `proposed` tồn (cũ nhất 25/06); 2 draft `done` chưa archive; 1 draft `promoted` chưa dọn → một lần `/docs-curate` + `/lint` giải quyết.
2. **[THẤP — #3]** 3 file fdk/wiki thiếu frontmatter (`active-context.md`, `decisions.md`, `010726-council-output.md`) — nên whitelist file log-type trong `okf_frontmatter.py` thay vì backfill.
3. **[THẤP — #5]** `llmwiki/raw/tech-pattern` chưa ingest; vocab `Status:` draft không đồng nhất (proposed/done/review/stub…).
4. **[TRUNG — #7]** 7 node ghi-tạm `p-auto-02..08` trong problem-tree còn open rỗng — phiên chạm framework nhưng chưa distill vào sổ.

## Chấm theo 8 nguyên tắc
| # | Nguyên tắc | Đánh giá |
|---|-----------|----------|
| 1 | Decision latency | ✅ Khỏe — mọi quyết định kiến trúc có ADR, không nợ |
| 2 | Meritocracy/leverage | ✅ Khỏe — 66 skill, flywheel/new-skill có mặt; nhưng flywheel chưa chảy |
| 3 | Tiêu chuẩn hóa | ⚠️ Nợ lớn nhất — policy chưa drive, drift bị che, đăng ký hụt mép |
| 4 | Modular army | ✅/⚠️ — mỗi skill một việc phần lớn đạt; 2 implement validate song song, vài skill phình |
| 5 | Intelligence trước combat | ✅ — wiki sạch, eval truy hồi có; 1 raw chưa ingest |
| 6 | Tích hợp, không dẫm | ⚠️ — extract-site dẫm web-crawl; họ onboard ranh giới mờ |
| 7 | Logistics | ⚠️ — hậu cần dày nhưng vòng phản hồi mỏng (3 failures/712 events, p-auto không distill) |
| 8 | Nhịp ship | ⚠️ — 15 draft tồn 7 ngày, done chưa archive |

## Top 5 hành động đề xuất (leverage cao nhất trước — thang Meadows)
1. Cho hook đọc `policy.yaml` sinh danh sách validator (đổi luật chơi, đóng gốc finding harness #1 + #3).
2. Buộc bump version khi pattern đổi để drift không im lặng (thêm vòng phản hồi).
3. Thêm `fdk` vào marketplace + sửa description `extract-site` + dedupe đăng ký ingest/propose/query.
4. Chạy `/docs-curate` để promote/archive 15 draft tồn; ingest `raw/tech-pattern`.
5. Nối flywheel: cơ chế flush p-auto phải kèm distill, để failures.jsonl thực sự nhận tín hiệu.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/fdk-problem-tree.html` | modified — thêm 4 node p-07..p-10 (open) |
| `llmwiki/wiki/sources/draft/020726-audit-fdk-strategy.md` | created |
| `llmwiki/html/020726-audit-fdk-strategy.html` | created — render docs site liquid-glass của báo cáo này |

## Tình báo bổ sung (02/07, sau audit)
User xác nhận dùng **nhiều session song song để sửa chính dự án này**. Diễn giải lại finding drift: 15 pattern lệch nhiều khả năng là **local đi trước remote** (cải tiến chưa upstream), không phải bản cũ — hướng xử lý là `/sync-template` upstream + bump version, KHÔNG revert. Đồng thời giải thích 7 node p-auto tích tụ (nhiều phiên chạm framework, khâu distill cuối phiên chưa chạy) → củng cố hành động #5.

## Notes
- Invoked via: `/fdk` (goal: audit theo kim chỉ nam fdk-dev-strategy)
- 3 agent Explore song song, mỗi trụ một agent; inventory LIVE: 66 skill / 14 validator / 17 rule.

## Origin
- **Draft:** `wiki/sources/draft/020726-audit-fdk-strategy.md`
- **Source:** `fdk/wiki/concepts/fdk-dev-strategy.md` + audit 3 trụ 2026-07-02
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
