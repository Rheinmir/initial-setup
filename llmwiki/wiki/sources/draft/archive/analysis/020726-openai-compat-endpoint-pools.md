---
title: OpenAI-compat endpoint pools & agent CLI
type: draft
status: proposed
tags: [docs-site-macos, output-report]
created: 2026-07-02
id: 020726-openai-compat-endpoint-pools
---

# 020726-openai-compat-endpoint-pools
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-07-02

## What
Trang docs-site (HTML macOS glass) phân loại các endpoint tương thích OpenAI thành 4 pool cung cấp + 1 pool tiêu thụ (agent CLI), nối tiếp câu hỏi "api kiểu OpenAI thì có các vendor agent CLI nào".

## Output
- 4 pool cung cấp: A) Cloud gốc (OpenAI/Azure), B) Gateway (OpenRouter, Vercel AI Gateway, Groq, LiteLLM), C) Compat-shim (Gemini, Grok, DeepSeek, Mistral), D) Local (Ollama, LM Studio, vLLM, LocalAI).
- 1 consumer pool: agent CLI (OpenCode, Crush, Aider, Goose, Cline, Codex CLI) — đều cắm qua base_url + api_key.
- Mind map collapsible, SVG diagram kéo-thả, bảng so sánh CLI, code copy, sidebar glass + ripple, scrollbar overlay, a11y đầy đủ.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/020726-openai-compat-endpoint-pools.html` | created |

## Notes
- Invoked via: `/docs-site-macos` skill
- Preview: http://localhost:8765/llmwiki/html/020726-openai-compat-endpoint-pools.html
- Dữ liệu tổng hợp từ WebSearch (do engine /last30days thiếu scripts, xem phiên trước).

## Origin
- **Draft:** `wiki/sources/draft/020726-openai-compat-endpoint-pools.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
