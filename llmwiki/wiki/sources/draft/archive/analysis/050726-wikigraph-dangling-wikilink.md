---
type: issue
kind: tech-debt
title: "wiki-graph: broken wikilink [[X]] đẻ cạnh dangling trỏ node không tồn tại (rác graph data)"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P3
tags: [issue, tech-debt, wiki-graph, wikilink, data-cleanliness]
timestamp: 2026-07-05
id: 050726-wikigraph-dangling-wikilink
source_session: "Senior-tester audit trong bộ test 5-project GH#41/#43"
---

# Issue: broken wikilink đẻ cạnh dangling trong graph data

## Vấn đề (một câu)
`build-wiki-graph.py` phát cạnh `wikilink` cho `[[X]]` kể cả khi trang X không tồn tại → cạnh trỏ tới node không có trong danh sách node (rác dữ liệu JSON graph).

## Bối cảnh & bằng chứng
- Negative test (senior-tester): body chứa `[[khong_ton_tai]]` → JSON có `{"from":"n1","rel":"wikilink","to":"khong_ton_tai"}` nhưng KHÔNG có node id `khong_ton_tai`.
- Không crash, render bỏ qua cạnh (thiếu node đích), nhưng dữ liệu graph không nhất quán.
- `harness/scripts/wiki-graph.py broken` đã phát hiện được wikilink gãy → engine visual nên nhất quán.

## Phạm vi
- `fdk/tools/build-wiki-graph.py` (chỗ sinh cạnh wikilink từ `[[...]]`).

## Không thuộc phạm vi
- Không đụng cạnh code `imports` (đã resolve về file thật).

## Hướng gợi ý
- Hoặc **prune** cạnh wikilink khi đích không có node.
- Hoặc **materialize node 'missing'** (badge nét-đứt) để trực quan hoá dead-link — đúng ý "wikilink thất bại = dây mềm nét đứt" trong log framework.

## Tiêu chí HOÀN THÀNH
- Negative test: `[[khong_ton_tai]]` → hoặc 0 cạnh, hoặc cạnh + node 'missing' rõ ràng; không còn cạnh trỏ node rỗng.
- Không hồi quy wikilink hợp lệ.

## Assign & lý do
`@Rheinmir` / Claude / `/fdk` — sửa engine nhỏ, cần regression wikilink.

## Origin
- Raise bởi `/raise-issue`, phiên 2026-07-05, từ senior-tester audit bộ test 5-project.
- Mirror: GH#47.
