---
type: issue
kind: feature-gap
title: "Self-evolving skills: vòng CoEvoSkills nội bộ (sinh → eval tự động → merge khi xanh)"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, skills, self-evolving, eval, frontier-gap, failure-flywheel]
timestamp: 2026-07-03
id: 030726-self-evolving-skills
source_session: "frontier-gap-scan baseline 03/07/2026 — trục THUA #2"
---

# Issue: Skill chưa tự tiến hoá & thiếu eval-per-skill

## Vấn đề (một câu)
Thế giới có agent tự sinh + tiến hoá skill đa-file qua verify vòng lặp (CoEvoSkills/SkillForge/SkillClaw), còn overstack skill vẫn viết tay và không có eval riêng cho từng skill.

## Bối cảnh & bằng chứng
- Trục Self-evolving skills = **Thua**. Nguồn: frontier-gap-scan, report overstack-vs-world-30d.
- Thế giới: CoEvoSkills (arXiv 2604.01687) sinh skill package đa-file, tiến hoá qua iterative verification; SkillForge (2604.08618) skill tự-tiến-hoá theo domain; Self-Harness (arXiv 08/06/2026) weakness-mining → propose → validate, +52% Terminal-Bench.
- overstack hiện: `new-skill` scaffold + `fdk` + `failure-flywheel` (đề xuất rule khi lỗi lặp) — có phôi thai nhưng còn người-trong-vòng-lặp toàn phần, chưa có vòng sinh→eval→giữ/loại tự động.

## Phạm vi
- `failure-flywheel`, `new-skill`, `fdk`, `wikieval`/`medic eval`. Universal.

## Không thuộc phạm vi
- KHÔNG tự-merge skill không qua duyệt người (giữ gate người ở bước cuối — an toàn hơn tốc độ).
- Không rời marketplace nội bộ.

## Hướng gợi ý (không bắt buộc)
- Tiền đề: mỗi skill 1 golden case (xem issue `030726-observability-runtime` phần eval-per-skill).
- Vòng: `failure-flywheel`/`fdk` đề xuất skill/patch → chạy eval tự động → chỉ đưa vào PR khi xanh → người duyệt merge.
- Dùng `Workflow` để fan-out sinh N biến thể → judge panel → chọn.

## Tiêu chí HOÀN THÀNH
- Có 1 lần chạy thật: một gap → sinh candidate skill/patch → eval tự chạy → tạo PR-draft, người duyệt.
- Quy trình ghi lại thành runbook trong `fdk/wiki`.

## Assign & lý do
- @Rheinmir chủ; Claude dispatch (đụng nhiều skill lõi). Mở `/fdk`.

## Repo/paper tham khảo
- CoEvoSkills — arXiv 2604.01687 (sinh skill đa-file + tiến hoá qua iterative verification).
- SkillForge — arXiv 2604.08618 (skill tự-tiến-hoá theo domain).
- Self-Harness — arXiv 08/06/2026 (explainx.ai/blog/self-harness-agents-improve-themselves-arxiv-2026): weakness-mining → propose → validate, +52% Terminal-Bench.
- `VoltAgent/awesome-ai-agent-papers` — tuyển tập paper agent 2026 (memory/eval/workflows).
- `muratcankoylan/agent-skills-for-context-engineering` — skill package đa-file mẫu.

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03. Bằng chứng: report overstack-vs-world-30d + frontier-gap-scan.
