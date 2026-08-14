---
type: entity
title: "repowise (repowise-dev/repowise)"
tags: [competitor, code-intelligence, mcp, code-health, benchmark]
timestamp: 2026-08-11
---

# repowise (repowise-dev/repowise)

Open-source (AGPL-3.0) "codebase intelligence" CLI + MCP server, Python, 5088★ tại thời điểm quét (repo tạo 2026-03-23, push gần nhất 2026-08-10). Index một repo một lần (`pip install repowise && repowise init`), phục vụ 10 MCP tool task-shaped (batchable, không entity-shaped) cho Claude Code/Codex/Cursor/VS Code, cộng dashboard web + PR bot + VS Code extension. Đối thủ trực tiếp của [[code-graph]] (MCP tool nội bộ) và một phần vùng phủ của `/ingest`-`/query` (wiki tự sinh) trong overstack, dù overstack rộng hơn (toàn bộ dev-workflow harness, repowise chỉ là một lớp codebase-intelligence).

## Details
- **Nguồn:** https://github.com/repowise-dev/repowise (README + `gh api repos/.../readme`, fetch 2026-08-11)
- **5 lớp index (1 pass, đồng bộ mỗi commit):** Graph (dependency graph 18 ngôn ngữ, 3-tier call resolution, Leiden communities, PageRank) · Git (hotspot, ownership, co-change, bus factor) · Docs (wiki sinh tự động, no-LLM mặc định, nâng cấp prose theo yêu cầu) · Decisions (ADR khai thác từ 5 nguồn, evidence-backed exact/fuzzy/unverified) · Code health (49 detector tất định, 1-10/file, defect-validated ROC AUC 0.737/21 repo)
- **10 MCP tool:** `get_overview` `get_answer` `get_context` `get_symbol` `search_codebase` `get_risk` `get_change_risk` `get_why` `get_dead_code` `get_health` — mỗi response có `_meta.stale_warning` khi index lệch HEAD thật
- **Zero-LLM path:** `repowise init --no-prose -y` không cần API key; code-health/change-risk/dead-code/PR-bot đều 0 LLM call
- **PR bot** (free GitHub App): 1 comment/PR sửa tại chỗ, im lặng nếu sạch, blast-radius cấp symbol, Check Run có thể gate merge, trang public per-PR (treemap)
- **`repowise distill <cmd>`**: nén output lệnh shell trước khi agent đọc (61-89% token, lossless qua marker `[repowise#<ref>]`) — trùng ý tưởng với `rtk` (RTK — Rust Token Killer, công cụ global của user, xem `~/.claude/RTK.md`), khác implementation
- **Tự-benchmark công khai, kể cả hàng thua:** thắng file-coverage (0.876 vs CodeGraph 0.610, n=42 sealed) và output-token (-31.6% vs bare agent), NHƯNG thua index-speed nặng (366.8s vs CodeGraph 16.4s, 22x-135x)

## So với overstack (điểm chạm thật)
- [[code-graph]] (MCP nội bộ, 12 tool: get_callees/get_callers/get_file_imports/get_file_symbols/get_symbol_context/get_usage_stats/list_files/list_projects/reindex_file/reindex_repo/search_symbols/get_stats) — entity-shaped (1 file/1 symbol mỗi lệnh), KHÔNG có staleness meta, KHÔNG batch nhiều target 1 call như `get_context(targets)` của repowise.
- `harness/validators/code_health.py` — chỉ là cổng `py_compile` (lỗi cú pháp = đỏ), KHÔNG có scoring 1-10, KHÔNG detector nào, KHÔNG refactoring plan, KHÔNG defect-validation. Repowise's "code health" (49 detector, calibrated trên corpus lỗi thật) là một hạng mục khác hẳn về độ sâu.
- `/ingest`+`/query` sinh wiki bằng LLM đọc source thật (chất lượng cao hơn nhưng tốn token/thời gian người); repowise sinh wiki 0-LLM từ structure trước, nâng cấp sau — mô hình chi phí ngược lại.
- Không có tương đương PR-bot (blast-radius + change-risk + Check-Run) hay dead-code detector trong overstack hiện tại.

## Notes
- [[code-graph]] — MCP tool nội bộ tương đương gần nhất, xem so sánh trên
- [[frontier-gap-scan]] — runbook quét đối thủ hàng tuần mà entry này thuộc về
- [[innovation-110826]] — note so sánh chi tiết + quyết định có raise issue không

## Origin
- **Source:** https://github.com/repowise-dev/repowise (README, `gh api`, fetch 2026-08-11)
- **Date:** 2026-08-11
