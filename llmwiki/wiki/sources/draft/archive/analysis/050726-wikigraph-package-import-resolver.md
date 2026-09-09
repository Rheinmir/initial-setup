---
type: issue
kind: tech-debt
title: "Engine wiki-graph: resolver Python chỉ khớp basename 1-segment → import qualified theo package không nối cạnh"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, wiki-graph, code-imports, python, resolver]
timestamp: 2026-07-05
id: 050726-wikigraph-package-import-resolver
source_session: "Dựng golden case newproj-notes (GH#41) — app kiểu package/ ra 0 cạnh code"
---

# Issue: resolver Python của wiki-graph chỉ khớp basename 1-segment

## Vấn đề (một câu)
`code_imports.py` resolve import Python bằng `module.split(".")[0]` nên `from app.core import X` thu về module `app` (không map tới `app/core.py`) → import qualified theo package không nối được cạnh `imports` trên graph.

## Bối cảnh & bằng chứng
- `fdk/tools/code_imports.py` `_py()` (dòng ~327-329): `mods.add(n.module.split(".")[0])`.
- `fdk/tools/build-wiki-graph.py` `enrich_code` (~340-346): `modindex.setdefault(p.stem, rel)` — chỉ index theo file-stem một-segment.
- Kiểm chứng khi dựng golden case [[050726-ship-selfindex-engine-downstream]] (GH#41): app kiểu `app/cli.py` (`from app.core import`) → **0 cạnh**; phải làm phẳng `src/cli.py` (`from core import`) mới ra `cli→core→store`.
- Hệ quả: dự án Python thật (dùng package) mất phần lớn quan hệ code trong graph → graph nhìn "thuần docs".

## Phạm vi
- `fdk/tools/code_imports.py` (`_py`), `fdk/tools/build-wiki-graph.py` (`enrich_code` modindex).
- Universal: ảnh hưởng mọi graph có code Python theo package.

## Không thuộc phạm vi
- Không đụng TS/JS/Go/Rust resolver (đã theo path/tsconfig).
- Không chuyển sang code-graph MCP — giữ engine tĩnh self-contained.

## Hướng gợi ý (không bắt buộc)
- Giữ nguyên module đầy đủ `app.core` (không split), map qua `pkg/mod.py` (join "/" + ".py") lẫn `pkg/mod/__init__.py`; fallback về basename cũ. Fail-open.
- Cân nhắc import tương đối (`from .core import`) theo thư mục file đang xét.

## Tiêu chí HOÀN THÀNH (kiểm chứng được)
- Golden case dạng package (`app/cli.py` → `from app.core import`) sinh cạnh `app/cli.py → app/core.py`.
- Không hồi quy import phẳng (hooks `from hooklib import` vẫn nối).
- `medic --ci` xanh + eval self-index không tụt.

## Assign & lý do
`@Rheinmir` / Claude / `/fdk` — thay đổi engine core, cần test hồi quy + golden case.

## Origin
- Raise bởi `/raise-issue`, phiên 2026-07-05, khi dựng golden case GH#41.
- Mirror: GH#43.
