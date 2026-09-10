---
name: dym-ruflo
disable-model-invocation: true
domains: [orchestration, agent, swarm]
source: https://github.com/ruvnet/ruflo
description: "ruflo (claude-flow 3.40) — điều phối swarm agent BÊN TRONG Claude Code qua MCP + hook + Task tool. Gõ /dym-ruflo <slug> — slugs: install · init · route."
---

# dym-ruflo

Bundle sinh từ `/doyourmagic git@github.com:ruvnet/ruflo.git` (chạy thật 2026-09-10,
npm `ruflo@3.40.0`, macOS 24.6 arm64).

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng.
2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `.claude/skills/dym-ruflo-<slug>/SKILL.md`
   (2) `.overstack/doyourmagic/ruflo/skills/dym-ruflo-<slug>/SKILL.md`
   (3) `doyourmagic-bundles/ruflo/skills/dym-ruflo-<slug>/SKILL.md`
   Làm theo Steps/Rules của file đó; không đọc file con khác.

| slug | mục đích |
|---|---|
| `install` | cài có pin scope + đo dấu chân thật (1.5 GB, ghi vào `$HOME`) |
| `init` | `ruflo init` ghi gì vào dự án — 241 file + 13 hook + chiếm settings.json |
| `route` | dùng ruflo hay không: nó CHIẾM `.claude/`, đụng thẳng overstack |

## Rules
- **ruflo KHÔNG chạy agent.** Nó điều phối; việc thật do **Task tool của Claude Code**
  làm. CLAUDE.md của nó nói thẳng: *"Never use MCP tools alone for execution — Task tool
  agents do the actual work"*. Không có Claude Code thì không có gì chạy.
- Tên npm là `ruflo`, nhưng `package.json` vẫn khai `"name": "claude-flow"` và thông báo
  lỗi vẫn in `claude-flow` — cùng một sản phẩm, hai tên.
