---
type: issue
kind: foundation
title: "Harness/wiki-graph: khai báo scope index tường minh qua .overstack.yaml (relocate được)"
status: in-progress
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, foundation, scope, wiki-graph, config]
timestamp: 2026-07-05
id: 050726-explicit-index-scope-yaml
source_session: "Phiên hỏi: nếu đặt nhiều dự án dưới folder mẹ thì harness scope thế nào"
---

# Issue: khai báo scope index tường minh qua .overstack.yaml

## Vấn đề (một câu)
Scope index NGẦM ĐỊNH — code-root = repo root cứng, wiki_dir = candidate cố định, không cấu hình/relocate được → mơ hồ khi lồng folder + không thu hẹp được vùng index.

## Bối cảnh & bằng chứng
- `stop.py`: `root=project_dir(payload)`, engine gọi `--code-root root` (cứng).
- `hooklib.find_wiki_dir`: chỉ nhìn `root/{fdk,'',llmwiki}/wiki`, KHÔNG walk-up.
- 3 nỗi lo cùng gốc: scope khi lồng folder · relocate vùng · nhiều harness. Xem GH#49.

## Phạm vi
- `llmwiki/.claude/hooks/stop.py` (`regen_docs` group B).

## Hướng đã làm (bản này)
- `.overstack.yaml` tại root: `wiki_dir` + `code_root` (scalar). `_scope_config()` parse tối giản, fallback = hành vi cũ.

## Tiêu chí HOÀN THÀNH
- [x] `code_root: src` → chỉ index src, bỏ tests. [x] Thiếu config → không hồi quy.
- [ ] (follow-up) `index_roots` NHIỀU path (engine cần nhận nhiều --code-root).

## Assign & lý do
`@Rheinmir` / Claude / `/fdk` — thay đổi hook core.

## Origin
- Raise + implement phiên 2026-07-05. Mirror: GH#49.
