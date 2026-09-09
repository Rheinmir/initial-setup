---
type: issue
kind: architecture
title: "Orchestration scale: DAG + file-bus, nâng orca lên hàng-trăm-subagent song song có verify"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, orchestration, orca, dag, scale, frontier-chom]
timestamp: 2026-07-03
id: 030726-orchestration-scale
source_session: "frontier-gap-scan baseline 03/07/2026 — trục CHỚM #1"
---

# Issue: Orchestration mới ở mức CHỚM về quy mô

## Vấn đề (một câu)
Claude Code dynamic workflows chạy hàng trăm subagent song song với verify built-in + saved progress; orca/`council`/`loop-runner` cùng tư tưởng nhưng quy mô nhỏ hơn nhiều.

## Bối cảnh & bằng chứng
- Trục Deterministic orchestration = **Chớm**. Nguồn: [[frontier-gap-scan]], report overstack-vs-world-30d.
- Thế giới: DAG + file-bus handoff, node Generator/Reviewer/Gate; Claude dynamic workflows (research preview) — orchestration script tự-viết, hàng trăm subagent, verify trước khi trả về, progress lưu qua CLI/Desktop/VS Code.
- overstack hiện: `orca` orchestration, `council` (blind peer-rank), `loop-runner`, `Workflow` (đã có pipeline/parallel + journal). Nền tảng đúng, cần scale + saved-progress/resume mạnh hơn.

## Phạm vi
- orca orchestration + `Workflow` resume/journal. Universal.

## Không thuộc phạm vi
- Không chạy đua "số subagent" mù quáng — scale phải kèm verify + resume, không thì bỏ.

## Hướng gợi ý (không bắt buộc)
- Chuẩn hoá node type Generator/Reviewer/Gate trên orca (đã gần khớp `loop-runner`).
- File-bus handoff thay vì nhồi context — dùng saved-dir/journal làm bus.
- Tận dụng `Workflow` resumeFromRunId cho saved-progress.

## Tiêu chí HOÀN THÀNH
- 1 orca run chạy ≥ vài chục subagent với verify-per-node + resume được sau ngắt.

## Assign & lý do
- @Rheinmir chủ; Claude dispatch. Mở `/fdk`. P2 (chớm, nền tảng đã có).

## Repo/paper tham khảo
- `langchain-ai/langgraph` — stateful cyclic multi-agent, checkpointing/persist state (chuẩn DAG + state).
- LangChain Deep Agents — harness long-running: planning + context mgmt + multi-agent orchestration.
- Claude Code dynamic workflows (releasebot.io/updates/anthropic/claude-code) — hàng trăm subagent song song + verify + saved progress (tham chiếu thiết kế).
- `wshobson/agents` — multi-harness agentic plugin marketplace (Claude Code/Codex/Cursor/OpenCode…).
- AgentCo-op — arXiv 2605.20425 (retrieval-based synthesis of interoperable multi-agent workflows).

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03. Bằng chứng: report overstack-vs-world-30d + [[frontier-gap-scan]].
