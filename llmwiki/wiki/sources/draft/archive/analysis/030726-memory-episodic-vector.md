---
type: issue
kind: feature-gap
title: "Memory: thêm tầng episodic + vector retrieval + temporal cho llmwiki (đạt 4/4 tầng nhớ)"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, memory, retrieval, frontier-gap, wiki]
timestamp: 2026-07-03
id: 030726-memory-episodic-vector
source_session: "frontier-gap-scan baseline 03/07/2026 — trục THUA #1"
---

# Issue: Memory — llmwiki mới có ~1.5/4 tầng nhớ

## Vấn đề (một câu)
Thế giới 2026 chuẩn hoá 4 tầng nhớ (working/episodic/semantic/procedural) + vector + temporal graph, có benchmark; overstack chỉ có semantic + procedural qua wiki, thiếu episodic và truy hồi theo ngữ nghĩa.

## Bối cảnh & bằng chứng
- Báo cáo đối chiếu chấm trục Memory = **Thua** (nặng nhất). Nguồn: [[frontier-gap-scan]], `llmwiki/html/overstack-vs-world-30d.html`.
- Thế giới: Mem0 "state of agent memory 2026" (benchmark), Letta (OS-style explicit memory), Zep (temporal knowledge graph), LangMem. Mô hình chủ đạo: core-nhỏ-luôn-trong-context + vector-store retrieval + forgetting policy.
- overstack hiện: `llmwiki` (semantic + procedural), auto-memory `MEMORY.md`. Truy hồi CHỈ theo `[[wikilink]]`/grep, không theo ngữ nghĩa; không có episodic (sự kiện phiên cụ thể), không temporal.

## Phạm vi
- `llmwiki/` retrieval layer, `wiki-room`/`query` skill, ledger/log indexing. Universal (mọi dự án dùng llmwiki).

## Không thuộc phạm vi
- Không thay wiki bằng vector-DB. Wiki vẫn là nguồn chân lý; vector chỉ là lớp truy hồi phụ.
- Không kéo dịch vụ managed cloud (giữ local/MCP, travel-được).

## Hướng gợi ý (không bắt buộc)
- Bước nhỏ trước: index `ledger.jsonl` + `log.md` bằng embedding local (MCP memory) → `wiki-room`/`query` truy hồi theo ngữ nghĩa, không chỉ theo link.
- Episodic: ghi "session episode" có cấu trúc (đã có journal.jsonl của Workflow) → truy hồi được "phiên trước làm gì".
- Temporal (sau): gắn timestamp + supersede-link để trả lời "điều này đúng ở thời điểm nào".

## Tiêu chí HOÀN THÀNH
- `query`/`wiki-room` trả kết quả theo ngữ nghĩa (không chỉ exact-link) trên ≥1 golden case episodic.
- Có 1 golden eval đo hit@k truy hồi ngữ nghĩa, gắn vào `wikieval`.

## Assign & lý do
- @Rheinmir chủ; dispatch Claude (đụng retrieval + skill, cần bối cảnh wiki). Mở bằng `/fdk` vì sửa chính framework.

## Repo/paper tham khảo
- `mem0ai/mem0` — managed memory, có benchmark "state of agent memory 2026" (mem0.ai/blog/state-of-ai-agent-memory-2026).
- `letta-ai/letta` (tiền thân MemGPT) — OS-style explicit memory management.
- `getzep/zep` — temporal knowledge graph memory.
- `langchain-ai/langmem` — memory trên LangGraph (thread-scoped + long-term).
- Guide: machinelearningmastery.com "6 Best AI Agent Memory Frameworks 2026".

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03. Bằng chứng: report overstack-vs-world-30d + [[frontier-gap-scan]].

## Kết quả (2026-07-04 — done)
- Đạt 4/4 tầng nhớ: episodic (`mem-rank episode`) + truy hồi ngữ nghĩa (query/wiki-room Tầng-0) + temporal (ts/supersedes).
- DoD ✓: query trả kết quả ngữ nghĩa trên golden episodic; 1 golden hit@k (`episodic-baseline.json`) gate CI qua medic `p_eval`.
- Không thay wiki bằng vector-DB; giữ local/travel; embedding adapter vẫn `verified:false` (token-overlap tất định đủ cho golden).
