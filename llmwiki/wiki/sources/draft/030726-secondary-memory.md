---
type: draft
title: "030726-secondary-memory — bộ nhớ thứ cấp 3-tầng (auto scratch-log + view session/feature + journal-distill), file-first không RAG"
status: proposed
tags: [secondary-memory, provenance, traceability, file-first, no-rag, output-report]
timestamp: 2026-07-03
relations:
  - {rel: derives-from, to: 030726-session-provenance}
  - {rel: touches, path: harness/scripts/code-logger.py}
  - {rel: touches, path: fdk/tools/build-wiki-graph.py}
  - {rel: touches, path: llmwiki/.claude/hooks/wiki_ledger.py}
---

# 030726-secondary-memory — bộ nhớ thứ cấp 3-tầng

**Type:** draft · **Status:** proposed · **Proposed:** 2026-07-03 · **Task:** T-260703-03

## What
Một **bộ nhớ thứ cấp** bắt **sửa vụn + context vụn** (không chỉ proposal chính thức) để **không mất gì vĩnh viễn** và **tra được ở phiên sau** — **file-first, visualizable bằng mắt, KHÔNG RAG**. Hiện thực kiến trúc 3 tầng do council chốt (`council-report-024-seed42.html`).

## Context (force-query)
- **Issue #5** (github): wiki chỉ lưu proposal chính thức; sửa+context vụn mất khi sang phiên; user muốn file-first + visualizable + không RAG + không mất gì.
- **[[030726-session-provenance]]** (ghi tay lần này) — neo feature→session→context, nhưng THIẾU phần tự-động (đó là **T7 v1.0.6**, được HẤP THỤ vào đề này).
- **Cộng đồng /last30days 2026:** markdown-first chuẩn (AGENTS.md 60k project, Linux Foundation); event-sourced episodic journal (PROJECTMEM arxiv 2606.12329); ADR/MADR immutable-dated; bỏ RAG vì "mất rừng vì cây". Khẳng định triết lý user.
- **Council `council-report-024-seed42.html`** (winner Munger): 3 tầng THÔ(auto)→DISTILL(người)→WIKI(curated); mâu thuẫn rotate-vs-không-mất giải bằng **git** (rotate view, history bất biến); judgment-at-READ; reuse problem-tree/wiki-graph, KHÔNG SQLite/PROJECTMEM.
- Framework ĐÃ có: `ledger.jsonl` (event/session-per-wiki), `events.jsonl` (code-logger, thiếu session), `problem-tree`/`wiki-graph` (visual tự-vẽ), `log.md`.

## Impact
| Vùng | Ảnh hưởng |
|------|-----------|
| `harness/scripts/code-logger.py` / hook | thêm capture scratch-log + field `session` (rủi ro chạm audit-chain — fail-open) |
| `harness/metrics/scratch-log.jsonl` | **file mới** (phụ, tách ledger chính) |
| `fdk/tools/` | script VIEW mới (reuse build-wiki-graph engine) |
| Không đẻ tool RAG/DB | reuse thuần |

## Plan
- [ ] **T1 — Tầng THÔ: hook auto scratch-log.** Hook (post-edit/commit) append `{ts, session, action, file, why?}` vào `harness/metrics/scratch-log.jsonl` — TÁCH ledger chính (chống phình). Ngưỡng = commit/save (không keystroke). `why` **optional, không ép**. Append-only; rotate-theo-tuổi (30 ngày) ở view, git giữ history vĩnh viễn.
- [ ] **T2 — events.jsonl + field `session`.** Nối events code-logger ↔ ledger (chỉ thêm field, không schema mới) → join được code+wiki theo phiên.
- [ ] **T3 — VIEW gom session/feature (2-zoom, reuse engine).** Script tái dùng `build-wiki-graph` render: **zoom-1** timeline session (mỗi phiên 1 điểm + nhãn 1-dòng), **click → zoom-2** graph chi tiết (cạnh `elaborates` nối scratch→wiki). KHÔNG renderer mới, KHÔNG RAG. Xuất `llmwiki/html/memory-map.html`.
- [ ] **T4 — Tầng DISTILL + auto session-provenance (hấp thụ T7).** Stop-hook distill cuối phiên: gom scratch-log+ledger+events → `sources/DDMMYY-session-provenance.md` (session-id → feature → context → commit); `why` 1-dòng từ scratch-log. Distill **KHÔNG xoá thô** — chỉ trỏ về. Judgment "đáng promote" ở lúc ĐỌC.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do | Status |
|------|-------------|-------|--------|
| T1 hook scratch-log | Claude | chạm audit-chain, cần fail-open cẩn trọng | pending |
| T2 events +session | Claude | 1 field, low-risk | pending |
| T3 VIEW 2-zoom | Claude | reuse build-wiki-graph engine | pending |
| T4 distill + provenance | Claude | gom nhiều nguồn + judgment | pending |

**Sequence diagram:** [030726-secondary-memory-seq.html](../../../html/030726-secondary-memory-seq.html)

## Success
1. Sửa vụn + `why` optional tự vào `scratch-log.jsonl` (không ép agent); phiên sau tra được.
2. `events.jsonl` có `session` → join code+wiki theo phiên.
3. `memory-map.html` hiện timeline session → click ra graph chi tiết (nhìn bằng mắt, reuse engine, 0 RAG).
4. Cuối phiên tự sinh session-provenance (không ghi tay như 030726).
5. Distill KHÔNG xoá thô; git giữ history bất biến → **không mất gì vĩnh viễn**.

## Origin
- **Draft:** `wiki/sources/draft/030726-secondary-memory.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
