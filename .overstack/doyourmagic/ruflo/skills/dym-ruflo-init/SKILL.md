---
name: dym-ruflo-init
disable-model-invocation: true
description: "Đo chính xác `ruflo init` ghi gì vào một dự án: 241 file trong .claude/, 13 hook trên 10 loại, chiếm statusLine/model/permissions trong settings.json. Gọi TRƯỚC khi chạy init lên dự án thật."
---

# dym-ruflo-init

## When to use
- Trước khi gõ `ruflo init` vào **bất kỳ** dự án đang có `.claude/` — nhất là dự án dùng
  overstack.
- Cần biết chính xác cái gì bị ghi đè để quyết định có cách ly được không.

## Steps

1. **Luôn init vào dự án RỖNG trong hộp cát trước**, không init thẳng dự án thật:

```bash
mkdir -p ./scratchpad/ruflo-proj && cd ./scratchpad/ruflo-proj && git init -q .
HOME=<sandbox-home> <prefix>/bin/ruflo init --no-signup
```

2. **Đo dấu chân** — số đo thật 2026-09-10, `ruflo@3.40.0`, dự án git rỗng:

| ghi vào | số lượng |
|---|---|
| `.claude/` tổng | **241 file · 6.0 MB** |
| `.claude/commands/` | 148 file (slash command) |
| `.claude/helpers/` | 44 file |
| `.claude/skills/` | 30 skill |
| `.claude/agents/` | 18 agent |
| `.claude-flow/` | 8 file (config.yaml, CAPABILITIES.md, data/logs/sessions) |
| `.gitignore` | thêm khối "Ruflo local secrets and runtime data" |

3. **Đo phần CHIẾM `settings.json`** — đây mới là chỗ đau:

```bash
python3 -c "import json;d=json.load(open('.claude/settings.json'));print({k:len(v) for k,v in d['hooks'].items()});print([k for k in d if k!='hooks'])"
```
Kết quả đo: hook **13 đăng ký trên 10 loại** — `PreToolUse` 2 · `PostToolUse` 2 ·
`UserPromptSubmit` 1 · `SessionStart` 1 · `SessionEnd` 1 · `Stop` 1 · `PreCompact` 2 ·
`SubagentStart` 1 · `SubagentStop` 1 · `Notification` 1. Ngoài `hooks` còn ghi
`statusLine`, `permissions`, `model` (ghim `claude-sonnet-5`), `env`, `claudeFlow`.

4. **Muốn chỉ lấy runtime, không đụng `.claude/`**: `--skip-claude`.

```bash
ruflo init --minimal --skip-claude --no-signup
```
Đo: `.claude/` chỉ còn **4 thư mục RỖNG (0 file)**, không có `settings.json`, tổng 108 KB.

## Rules
- **`--skip-claude` nói dối ở phần thông báo**: init vẫn in `[INFO] Hooks: 4 hook types
  enabled in settings.json` trong khi **không có `settings.json` nào được tạo**. Đừng tin
  dòng đó, đi `find`/`git status` mà kiểm.
- Init **không hỏi trước khi ghi đè** `statusLine`/`model`/`permissions`. Dự án nào đã có
  statusline hoặc đã ghim model khác thì mất, không có prompt.
- 30 skill của ruflo **không trùng tên** với 86 skill overstack và 8 skill Orca.app quản
  (đã đối chiếu bằng `comm`) — rủi ro không nằm ở tên skill mà ở `settings.json`.
- Luôn `git status` ngay sau init: `.gitignore` bị sửa và 241 file mới là thứ phải quyết
  commit hay không, đừng để lẫn vào commit khác.
