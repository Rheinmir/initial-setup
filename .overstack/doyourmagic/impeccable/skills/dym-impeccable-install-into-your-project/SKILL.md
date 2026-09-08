---
name: dym-impeccable-install-into-your-project
description: "Cài Impeccable vào dự án của bạn. đưa skill /impeccable + hook design vào harness AI của dự án, đúng phạm vi bạn muốn (project chứ không phải máy)."
disable-model-invocation: true
---

# Skill: dym-impeccable-install-into-your-project — Cài Impeccable vào dự án của bạn

**Vì sao dùng:** đưa skill `/impeccable` + hook design vào harness AI của dự án, đúng phạm vi bạn muốn (project chứ không phải máy).
**Sinh ra cái gì:** thư mục skill trong các provider dir (`.claude/skills/impeccable/`, `.cursor/skills/impeccable/`, ...), file agent `impeccable-*.md`, và tuỳ chọn hook manifest.

---

## ⚠️ Đọc trước: hai cái bẫy của `install`

### Bẫy 1 — `install --help` không in help, nó cài thật

Bản đang phát hành trên npm (`impeccable@3.6.1`) **không có** nhánh xử lý `--help` cho subcommand. Router chỉ nhận diện `install` rồi chạy luôn:

```js
// cli/bin/commands/skills.mjs (bản npm 3.6.1) — không hề có SUBCOMMAND_HELP
} else if (sub === 'install') {
  await install(args.slice(1));
```

Nhánh `SUBCOMMAND_HELP` (in help thật) **có** trong git `main` nhưng **chưa** được publish — hai bên cùng mang số 3.6.1 mà nội dung khác nhau.

```bash
# ĐỪNG gõ cái này: nó cài thật, không in help
npx impeccable install --help
```

### Bẫy 2 — không có TTY thì mặc định là **global**, không phải project

```js
// cli/bin/commands/skills.mjs:1169-1180
if (yes) return 'project';
...
const answer = await ask(`Install location: project (...) or global (...)? [${fallback === 'user' ? 'global' : fallback}] `);
if (!answer) return fallback;      // stdin EOF ⇒ nhận fallback
```

Trong script / CI / agent (stdin không phải TTY), `ask()` nhận chuỗi rỗng và rơi về `defaultInstallScope()`. Trên máy đã có sẵn `~/.claude`, `~/.cursor`... fallback là **global**, và Impeccable ghi vào 13 thư mục trong `$HOME`.

**Luật an toàn:** trong mọi ngữ cảnh không tương tác, luôn khai báo tường minh cả ba thứ:

```bash
npx impeccable install -y --scope=project --providers=claude
```

---

## Đường 1 — CLI installer (khuyến nghị)

```bash
cd /đường/dẫn/dự-án
npx impeccable install -y --scope=project --providers=claude,cursor
```

Output thật (chạy với `--providers=claude --no-hooks`):

```
Downloading impeccable skills...
Installed impeccable into: .claude (project)
Installed Claude Code agents into: <project>/.claude/agents

Done! Now type /impeccable init in your AI coding agent's chat (not in this terminal) to set up design context.
```

Kết quả: **168 file** dưới `.claude/` — `SKILL.md`, `scripts/` (~50 script `.mjs`), `reference/` (tài liệu từng lệnh), và 4 file agent.

Cờ đáng nhớ (đọc từ `SUBCOMMAND_HELP` trong git `main`, tất cả đều được `install()` bản npm chấp nhận):

| Cờ | Tác dụng |
|---|---|
| `-y`, `--yes` | Nhận mặc định, **ép scope về `project`** |
| `--scope=project\|global` | Chọn phạm vi tường minh |
| `--project` / `--user` / `--global` | Dạng viết tắt của `--scope` |
| `--providers=<tên,tên>` | `claude`, `cursor`, `codex`, `gemini`, `grok`, `hermes`, `github`, `opencode`, `pi`, `kiro`, `qoder`, `trae`, `trae-cn`, `rovo-dev`, `vibe`, `veto`, `antigravity` |
| `--no-hooks` | Không cài hook manifest của provider |
| `--force` | Ghi đè bản cài sẵn có |

> Cần mạng: bundle skill được tải từ `https://impeccable.style`, không nằm trong tarball npm.

## Đường 2 — Git submodule (vendor, cập nhật qua git)

```bash
git submodule add https://github.com/pbakaus/impeccable .impeccable
npx impeccable link --source=.impeccable --providers=claude,cursor
git add .gitmodules .impeccable .claude .cursor
```

`link` tạo symlink từ `.impeccable/dist/universal/` sang thư mục skill của provider; thư mục skill thật đã tồn tại thì được giữ nguyên trừ khi có `--force`.

Cập nhật:

```bash
git submodule update --remote .impeccable
npx impeccable link --source=.impeccable --providers=claude,cursor
```

## Đường 3 — Plugin (chỉ Claude Code / Grok Build)

```bash
# Claude Code — sau đó mở /plugin và chọn Impeccable trong danh sách
/plugin marketplace add pbakaus/impeccable

# Grok Build
grok plugin install pbakaus/impeccable#plugin --trust
```

---

## Kiểm tra và cập nhật

```bash
npx impeccable check     # rc 0
npx impeccable update -y --scope=project
```

`check` in ra phiên bản **bundle skill**, khác phiên bản CLI:

```
Checking for updates...

Skills are up to date (v4.1.3).
```

Hai dòng phiên bản độc lập nhau:

| Thứ | Phiên bản | Nguồn |
|---|---|---|
| CLI (`npx impeccable`) | 3.6.1 | npm |
| Bundle skill (`SKILL.md`, scripts) | 4.1.3 | tải từ impeccable.style |

> `update --help` dính đúng bẫy 1 như `install --help`. Đừng gõ; dùng `update -y --scope=project`.

## Hook: cái gì được ghi ở đâu

`install`/`update` (khi không có `--no-hooks`) ghi hook manifest theo từng provider:

| Harness | File | Script chạy |
|---|---|---|
| Claude Code | `.claude/settings.local.json` (gitignored) | `.claude/skills/impeccable/scripts/hook.mjs` |
| Cursor | `.cursor/hooks.json` | `.cursor/skills/impeccable/scripts/hook-before-edit.mjs` |
| Codex | `.codex/hooks.json` | `.agents/skills/impeccable/scripts/hook.mjs` |
| GitHub Copilot | `.github/hooks/impeccable.json` | `.github/skills/impeccable/scripts/hook.mjs` |
| Grok Build | `.grok/hooks/impeccable.json` | `.grok/skills/impeccable/scripts/hook.mjs` |

Bước thủ công bắt buộc theo harness:
- **Codex:** mở `/hooks` sau khi cài/cập nhật rồi duyệt hook của project. Codex theo dõi trust theo nội dung hook, nên mỗi lần `.codex/hooks.json` đổi là phải duyệt lại.
- **Grok Build:** cần trust thư mục (`/hooks-trust` hoặc chạy với `--trust`).

Bật/tắt hook sau khi cài (không cần cài lại):

```bash
node .claude/skills/impeccable/scripts/hook-admin.mjs status
node .claude/skills/impeccable/scripts/hook-admin.mjs off
node .claude/skills/impeccable/scripts/hook-admin.mjs on
node .claude/skills/impeccable/scripts/hook-admin.mjs reset   # xoá toàn bộ config + cache
```

## `.gitignore`: cái gì commit, cái gì bỏ

Impeccable ghi file làm việc dưới `.impeccable/`. **Commit** những file là artifact chung của dự án:

- `.impeccable/config.json` — config chung (detector ignores, hook)
- `.impeccable/live/config.json` — dây nối live mode với framework
- `.impeccable/design.json` — design spec chung
- `.impeccable/surfaces/*.md`, `.impeccable/critique/*.md`

**Bỏ qua** phần tạm và per-dev — dán khối này vào `.gitignore` của dự án (pattern cố ý *không* neo đầu dòng, vì trong monorepo `.impeccable/` hay nằm dưới `apps/web/`):

```gitignore
# impeccable-ignore-start
.impeccable/config.local.json
.impeccable/hook.cache.json
.impeccable/hook.pending.json
.impeccable/*.png
.impeccable/review/
.impeccable/questions/
.impeccable/live/server.json
.impeccable/live/sessions/
.impeccable/live/previews/
.impeccable/live/annotations/
.impeccable/live/cache/
.impeccable/live/manual-edit-apply-transaction.json
.impeccable/live/manual-edit-events.jsonl
.impeccable/live/manual-edit-evidence/
.impeccable/live/pending-manual-edits.json
.impeccable/live/deferred-svelte-component-accepts.json
.impeccable/live/*.png
# impeccable-ignore-end
```

## Gỡ sạch (kể cả khi lỡ cài nhầm global)

Không có lệnh `uninstall`. Gỡ bằng tay — đây là toàn bộ đích mà `install --scope=global` có thể chạm tới:

```bash
# skill (13 provider)
rm -rf ~/.claude/skills/impeccable ~/.cursor/skills/impeccable ~/.agents/skills/impeccable \
       ~/.gemini/skills/impeccable ~/.gemini/config/skills/impeccable ~/.grok/skills/impeccable \
       ~/.hermes/skills/impeccable ~/.kiro/skills/impeccable ~/.qoder/skills/impeccable \
       ~/.rovodev/skills/impeccable ~/.vibe/skills/impeccable ~/.pi/agent/skills/impeccable \
       ~/.config/opencode/skills/impeccable

# agent
rm -f ~/.claude/agents/impeccable-*.md ~/.cursor/agents/impeccable-*.md
```

Kiểm lại trước khi xoá (liệt kê mọi thứ mang tên impeccable trong home, kèm mtime để biết cái nào mới sinh):

```bash
python3 - <<'PY'
import os, glob, time
home = os.path.expanduser('~')
for d in sorted(os.listdir(home)):
    base = os.path.join(home, d)
    if not (d.startswith('.') and os.path.isdir(base)): continue
    for pat in ('skills/impeccable*', 'config/skills/impeccable*', 'agent/skills/impeccable*', 'agents/impeccable-*'):
        for p in glob.glob(os.path.join(base, pat)):
            print(time.strftime('%Y-%m-%d %H:%M', time.localtime(os.stat(p).st_mtime)), p)
PY
```

Bản cài project-scope thì chỉ cần xoá `.claude/skills/impeccable`, `.claude/agents/impeccable-*.md` và hook manifest tương ứng.

**Lưu ý về scope global:** nếu `$OPENCODE_CONFIG_DIR` được set (Orca có set biến này), OpenCode được nhận diện qua đường dẫn đó chứ không phải `~/.opencode` — xem `cli/bin/commands/skills.mjs:80-84`. Cùng cơ chế này làm hỏng suite test của contributor, xem `06`.

## Bước tiếp theo

Cài xong thì **mở AI agent lên và gõ `/impeccable init` trong chat** — không phải trong terminal. Gõ `npx impeccable init` sẽ bị chặn cố ý:

```
"init" is not a CLI command. Type /impeccable init in your AI coding agent's chat (Claude Code, Cursor, Codex, ...), not in this terminal.
```

(rc = 1). Chi tiết `init` và 23 lệnh chat: xem `05-chat-commands.md`.
