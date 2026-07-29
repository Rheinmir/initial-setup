---
type: issue
kind: feature-gap
title: "Observability runtime: tracing + eval-per-skill + simulation cho orca (không chỉ eval tĩnh CI)"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, observability, tracing, eval, orca, frontier-gap]
timestamp: 2026-07-03
id: 030726-observability-runtime
source_session: "frontier-gap-scan baseline 03/07/2026 — trục THUA #3"
---

# Issue: Thiếu observability/eval lúc chạy

## Vấn đề (một câu)
Khi orca chạy nhiều agent, không có tracing/simulation/guardrail-runtime để truy vết vì sao một nhánh sai — overstack chỉ có eval tĩnh CI (`wikieval`, `medic eval`), thấy kết quả cuối chứ không thấy quá trình.

## Bối cảnh & bằng chứng
- Trục Eval/observability = **Thua**. Nguồn: frontier-gap-scan, report overstack-vs-world-30d.
- Thế giới: Galileo Agent Control (Apache 2.0, control plane governance), future-agi (tracing·evals·simulations·datasets·gateway·guardrails, self-hostable). "Harness engineering" nhấn observability là cột.
- overstack hiện: `wikieval`, `medic eval`, `trace-grader` — chủ yếu tĩnh/CI. `Workflow` đã ghi `journal.jsonl` per-agent (nguyên liệu sẵn có nhưng chưa có view).

## Phạm vi
- orca orchestration, `Workflow` journal, `trace-grader`, `medic`. Universal.

## Không thuộc phạm vi
- Không kéo SaaS observability ngoài (giữ self-hostable/local).
- Không làm full APM — bắt đầu tối thiểu: timeline truy vết.

## Hướng gợi ý (không bắt buộc)
- Tối thiểu: parse `journal.jsonl` mỗi subagent → 1 view HTML timeline (nhánh nào, input/output, verdict) để truy vết nhánh sai.
- eval-per-skill: mỗi skill 1 golden assertion; CI chặn nếu regress (tiền đề cho `030726-self-evolving-skills`).
- Sau: simulation — replay một task qua nhiều seed để đo ổn định.

## Tiêu chí HOÀN THÀNH
- 1 view HTML timeline dựng được từ `journal.jsonl` của một run orca/Workflow thật.
- ≥3 skill có golden assertion gắn vào `medic`/`wikieval`.

## Assign & lý do
- @Rheinmir chủ; Claude dispatch. Mở `/fdk`.

## Repo/paper tham khảo
- `future-agi/future-agi` — open-source, end-to-end: tracing·evals·simulations·datasets·gateway·guardrails, self-hostable (Apache 2.0). Mẫu gần nhất với thứ ta cần.
- Galileo Agent Control (Apache 2.0, 03/2026) — control plane governance agent ở scale.
- `ai-boost/awesome-harness-engineering` — tuyển tập tool eval/observability/permissions/orchestration.
- dev.to "Harness Engineering: The Emerging Discipline" — bối cảnh vì sao observability là cột.

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03. Bằng chứng: report overstack-vs-world-30d + frontier-gap-scan.
