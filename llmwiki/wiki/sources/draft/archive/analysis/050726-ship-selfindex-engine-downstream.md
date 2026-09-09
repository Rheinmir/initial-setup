---
type: issue
kind: foundation
title: "Ship self-index engine (wiki-graph + retrieval) xuống downstream — hết credibility gap 'query được'"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, foundation, downstream, self-index, wiki-graph, retrieval, credibility]
timestamp: 2026-07-05
id: 050726-ship-selfindex-engine-downstream
source_session: "Phiên test bootstrap downstream (newproj-notes) — phát hiện mindmap + engine query không ship xuống"
---

# Issue: Ship self-index engine (wiki-graph + retrieval) xuống downstream

## Vấn đề (một câu)
Downstream projects nhận `query.md` (prompt) + `overstack.html` tĩnh nhưng KHÔNG nhận engine nào (`build-wiki-graph.py`, `code_imports.py`, retrieval issue-9), nên không vẽ được mindmap wiki+code của họ và "query" chỉ là agent grep theo prompt — mâu thuẫn với tuyên bố "query được / có tri thức đồ thị".

## Bối cảnh & bằng chứng
- Test bootstrap thật trên `newproj-notes` (worktree riêng): curl kéo 61/62 file từ `raw.githubusercontent/Rheinmir/setup@orca`. Mở `.template-manifest.json` → includes chỉ có: `llmwiki/skills/wiki-loop/query.md`, `llmwiki/html/overstack.html`, và các hook `.py`. KHÔNG có `fdk/tools/build-wiki-graph.py`, `code_imports.py`, `harness/scripts/retrieval-eval.py`, engine episodic.
- `stop.py` downstream: `regen_docs()` `return` ngay vì thiếu `fdk/tools/build-overstack-docs.py` ("không phải repo framework → bỏ") → dù có engine cũng không được gọi.
- Hệ quả: mindmap `wiki-graph.html` gitignore + framework-only → không bao giờ vào template; retrieval token-overlap (hit@k) của [[030726-memory-episodic-vector]] cũng framework-only.
- Council quyết định: `llmwiki/html/council/council-report-028-seed42.html` (5 ghế Munger/Taleb/Socrates/Kahneman/Aurelius, blind peer-rank, seed 42). Consensus winner Munger, á quân Taleb → **phương án B**.

## Phạm vi
- `.template-manifest.json` (thêm engine vào includes).
- `llmwiki/.claude/hooks/stop.py` (nới guard: regen khi CÓ engine, không cần repo framework; opt-in + fail-open).
- Engine cần ship: `fdk/tools/build-wiki-graph.py` + `fdk/tools/code_imports.py`; cân nhắc retrieval issue-9 (`harness/scripts/retrieval-eval.py` + phụ thuộc).
- Universal: ảnh hưởng MỌI downstream project bootstrap từ template.

## Không thuộc phạm vi
- KHÔNG chuyển sang RAG/vector-DB — giữ token-overlap tất định (no-RAG school).
- KHÔNG đẻ hook downstream riêng (phương án A) — chống 2-codepath drift (Munger).
- KHÔNG auto-on downstream — phải opt-in (Taleb: bán kính vụ nổ = mọi máy downstream).

## Hướng gợi ý (phương án B từ council)
1. Thêm `build-wiki-graph.py` + `code_imports.py` (+ engine retrieval nếu khả thi) vào `.template-manifest.json`.
2. Nới guard `stop.py`: regen wiki-graph khi phát hiện engine tại chỗ (không đòi `fdk/tools/build-overstack-docs.py`), gói try/except fail-open, opt-in qua cờ (env/config).
3. MỘT codepath — cùng engine, khác môi trường; không nhánh hook riêng.

## Tiêu chí HOÀN THÀNH (kiểm chứng được)
- `newproj-notes` (golden case) bootstrap xong: chạy được `build-wiki-graph.py` sinh `wiki-graph.html` của CHÍNH nó (node = wiki + code của notes.py), và query trả kết quả trên wiki của nó.
- `stop.py` downstream: wiki/code đổi + cờ opt-in bật → tự regen; engine lỗi → phiên vẫn sống (fail-open chứng minh bằng test hỏng engine).
- Không có 2-codepath: engine downstream == engine framework (cùng file).
- Tài liệu: nếu hoãn phần nào, sửa lời văn để không tuyên bố quá năng lực.

## Assign & lý do
`@Rheinmir` / dispatch Claude / entry `/fdk` — đây là thay đổi framework core (manifest + hook), cần chạy trên nhánh riêng + PR + golden case, hợp vòng `/fdk`.

## Origin
- Raise bởi `/raise-issue`, phiên 2026-07-05, sau khi test bootstrap `newproj-notes` lộ gap.
- Bằng chứng: `.template-manifest.json` (đã mở kiểm), `llmwiki/html/council/council-report-028-seed42.html`, [[030726-memory-episodic-vector]].
