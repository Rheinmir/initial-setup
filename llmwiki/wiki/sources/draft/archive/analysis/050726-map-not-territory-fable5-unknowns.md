---
type: issue
kind: process
title: "Map-is-not-Territory (Thariq/Fable 5): kỹ thuật tìm unknowns → đối chiếu & vá overstack (skills/CLAUDE.md/context)"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, process, context-engineering, fable5, unknowns, skills]
timestamp: 2026-07-05
id: 050726-map-not-territory-fable5-unknowns
source_session: "Phiên 2026-07-05 — user gửi bài explainx.ai về 'map is not territory' của Thariq, yêu cầu tạo issue + tổng hợp tài liệu 30 ngày."
---

# Issue: Map-is-not-Territory (Thariq/Fable 5) → đối chiếu & vá overstack

## Vấn đề (một câu)
Với model mạnh hơn (Fable 5), khoảng cách "bản đồ" (prompts/skills/CLAUDE.md/context ta đưa) so với "lãnh thổ" (codebase + ý định ngầm thực tế) KHÔNG thu hẹp mà NỚI RỘNG — model giải quyết mơ hồ một cách tự tin, lỗi lan qua nhiều file và lộ ra muộn; overstack cần cơ chế chủ động "tìm unknowns" trước khi prompt, và audit lại skill/bản-đồ khi đổi model.

## Bối cảnh & bằng chứng
Nguồn gốc: [Map Is Not the Territory — explainx.ai](https://explainx.ai/blog/map-is-not-territory-fable-5-thariq-unknowns-2026) diễn giải chuỗi bài của Thariq Shihipar (Anthropic).

**Luận điểm cốt lõi (Thariq):**
- Prompts + skills + context = *bản đồ* của việc, không phải *việc* (lãnh thổ = codebase thực, ý định ngầm, ràng buộc không ghi chép).
- Model càng mạnh, **chi phí của bản đồ SAI càng tăng**: model yếu lỗi lộ sớm/dễ thấy; Fable 5 lấp mơ hồ tự tin → lỗi lan rộng, phát hiện muộn.
- "Phần quan trọng nhất khi làm với Fable là phát hiện *unknowns của chính mình* để prompt tốt hơn."

**Kỹ thuật Thariq đề xuất (bằng chứng để đối chiếu):**
1. PR hai phần: phần cho người (ảnh/GIF/diff), phần cho agent (ý định, ràng buộc, edge case).
2. Quyết định dùng skill: skill cho tác vụ lặp có failure-mode rõ; CLAUDE.md cho quy ước dự án; **audit skill cũ sau khi nâng model**.
3. Tìm unknowns: yêu cầu agent **paraphrase kế hoạch trước khi chạy**; coi mọi output bất ngờ là tín hiệu lệch map/territory; dồn reasoning effort vào phần thực sự mơ hồ; verify lại bản đồ khi đổi model.
4. Cho model biết *điểm xuất phát* của mình (mình đang nghĩ tới đâu, kinh nghiệm với bài toán).

**Tổng hợp tài liệu ~30 ngày (Fable 5 ra 2026-06-09):**
- [Thariq @trq212 — chuỗi X](https://x.com/trq212/status/2073101078145724589): "discovering my own unknowns"; brainstorm có mục tiêu, phỏng vấn qua-lại có cấu trúc, ghi implementation-notes khi code.
- [the-decoder — tips tìm blind-spot trước](https://the-decoder.com/anthropic-developer-shares-prompting-tips-for-fable-5-that-focus-on-finding-your-own-blind-spots-first/): bottleneck chuyển từ model → blind-spot của người.
- [Anthropic — Introducing Fable 5 & Mythos 5](https://www.anthropic.com/news/claude-fable-5-mythos-5) + [Platform docs](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5): bền quyết-định qua chuỗi task dài.
- [codewithmukesh — CLAUDE.md là bước setup đòn bẩy cao nhất](https://codewithmukesh.com/blog/claude-code-for-beginners/).
- [productcompass — Fable 5 guide for PMs](https://www.productcompass.pm/p/claude-fable-5-guide); [MindStudio — long-running agentic real-world](https://www.mindstudio.ai/blog/claude-fable-5-agentic-coding-real-world-results); [awesome-claude-fable-5](https://github.com/Anil-matcha/awesome-claude-fable-5).

Liên quan wiki nội bộ: [[030726-self-evolving-skills]] (audit/tiến hoá skill), [[030726-skill-usage-dashboard]] (đo skill dùng thật → biết skill nào là bản-đồ-cũ), [[030726-observability-runtime]] (bắt output bất ngờ = tín hiệu lệch), council-029 (probe/escape harden).

## Phạm vi
- Universal (đụng cách overstack thiết kế skills + CLAUDE.md + luồng propose/gate).
- Cụ thể: (a) một checklist/skill "find-unknowns" (paraphrase-plan gate trước khi dispatch), (b) quy trình audit skill sau khi đổi model (skill = bản-đồ có hạn dùng), (c) mẫu PR hai phần (human-view + agent-intent) trong luồng ship.

## Không thuộc phạm vi
- Không viết lại engine skill hiện có; không đổi policy.yaml.
- Không build feature model-dispatch mới (đã có issue riêng); chỉ đề cập nếu chạm.
- Không tổng hợp thành bài blog public.

## Hướng gợi ý (không bắt buộc)
- Thêm bước "paraphrase-plan" tùy chọn vào `/propose` hoặc `/orca-workflow`: agent thuật lại kế hoạch + liệt kê giả định/unknown → user xác nhận trước khi code (bắt lệch map/territory sớm).
- Trường "map-freshness" cho skill: đánh dấu skill cần re-audit khi model đổi mốc (nối [[030726-skill-usage-dashboard]]).
- Ô "Giả định đang gánh" (đã có trong /br compile) nhân rộng làm khối chuẩn cho mọi propose.

## Tiêu chí HOÀN THÀNH
- [ ] Một trang wiki concept "map-not-territory / find-unknowns" chưng cất luận điểm + kỹ thuật, có Origin + link nguồn.
- [ ] Ít nhất 1 thay đổi quy trình cụ thể được đề xuất & gate (paraphrase-plan gate HOẶC skill map-freshness audit).
- [ ] Đối chiếu rõ: overstack ĐÃ có gì (br "Giả định đang gánh", propose gate) vs THIẾU gì.
- [ ] Ghi index + (đã) mirror GitHub.

## Assign & lý do
- **assignee @Rheinmir / dispatch Claude / entry /fdk**: đây là việc framework (chạm skills + CLAUDE.md + luồng propose), cùng chủ sở hữu các issue frontier khác; mở bằng `/fdk` để có context nội-bộ-framework.

## Origin
Raise bởi `/raise-issue` trong phiên 2026-07-05 theo yêu cầu user (gửi link explainx.ai + "last 30 days tổng hợp tài liệu"). Bằng chứng: bài explainx.ai đã fetch, 2 vòng WebSearch (X/Thariq, the-decoder, Anthropic docs, các guide Fable 5) — liệt kê ở mục Bối cảnh.
