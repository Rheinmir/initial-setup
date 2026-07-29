---
name: orca-dispatch-reference
description: Reference for Antigravity/OpenCode dispatch, skill installation, AgentMemory, RTK token proxy — NOT a loop skill
---

# Orca Dispatch Reference

> Reference doc, not a skill. Do not invoke in loop.

> **Nguồn chân lý DUY NHẤT cho dispatch.** Mọi skill orca-* / orchestration (orca-workflow, orca-onboard, orca-cli, orchestration, council…) chỉ TRỎ về đây — đừng nhân bản roster/syntax ở nơi khác (chống drift).

## Agent backends — roster & chọn theo cost (verified 2026-07-01)

Orca drive model bằng cách chạy một **agent CLI** trong terminal/worktree. Picker UI: **OpenCode · Claude · GitHub Copilot · Antigravity · Kiro**. Ba hệ tên hay lệch (picker ≠ `@`-handle ≠ `--agent` id) → bảng này hoà giải:

| Picker (UI) | `--agent <id>` | provider/model | Cost | Dùng cho |
|---|---|---|---|---|
| OpenCode | `opencode` | `opencode/big-pickle` (+free khác) | **$0** | task rẻ, render, **seat answer-only** |
| Claude | `claude` | (phiên hiện tại) | **đắt nhất** | reasoning khó, chairman — **để dành** |
| Antigravity | `agy` | — | rẻ | render dự phòng |
| GitHub Copilot | `copilot` | — | rẻ | dự phòng |
| Kiro | `kiro` | — | rẻ | dự phòng |

- `--agent <id>` bịa → `"Unknown TUI agent"` (validate TRƯỚC khi tạo worktree). Tập recognized cho `--inject` (live error): `claude · codex · gemini · droid`. Không có lệnh liệt kê — **picker UI là ground truth**.
- **Cost-tier (luật):** rẻ / cơ học / **answer-only → opencode free**; reasoning đắt / tổng hợp / chairman → **Claude** (đắt nhất, để dành). Khớp split "Claude-nghĩ / CLI-rẻ-render" của `orca-workflow`.

## OpenCode — cheap dispatch (verified)

**Free models ($0, opencode zen):** `opencode/big-pickle` · `deepseek-v4-flash-free` · `mimo-v2.5-free` · `nemotron-3-ultra-free` · `north-mini-code-free`.

```bash
opencode run -m opencode/big-pickle --dir "<worktree-path>" "<task>"   # headless, $0
opencode run -m opencode/big-pickle --format json "<task>"            # JSON events (parse máy)
opencode run -m <model> -s <session_id> "<task>"                      # nối session (--continue / --fork)
# ⚠ KHÔNG --dangerously-skip-permissions khi dispatch TỪ Claude Code (classifier DENY — bài học 120626).
#   Task answer-only (không đụng file) thì KHÔNG cần quyền → chạy thẳng được.
```

**⚠ Reliability (verified 2026-07-01):** `big-pickle` ngon với câu **ngắn/answer-only** (toán → vài giây); **STALL/timeout trên task NẶNG** (đọc nhiều file / sinh dài — đo >560s vẫn chưa xong). Đặt **watchdog 60–90s** → im lặng thì kill + **fallback Claude**. Task có file-edit/dependency → đừng giao opencode.

## Concurrency — KHÔNG mở nhiều opencode trong CÙNG 1 folder (researched + verified)

Nhiều opencode cùng 1 folder **dùng chung SQLite/session** (resolve `project_id` theo working dir) → **đè nhau, hỏng git snapshot** (opencode issues #31307 / #4251 / #28249). Test "3 song song 1 folder OK" là MISLEADING — chỉ đúng với câu tí hon answer-only.

**Pattern ĐÚNG (đã validate):** mỗi worker = **1 worktree riêng**, 1 opencode/worktree:
```bash
orca worktree create --name <w> --setup skip --no-parent --json       # tách dir+branch
opencode run --dir "<worktree-path>" -m opencode/big-pickle "<task>" &  # N cái song song được
orca worktree rm --worktree name:<w> --force --json                   # dọn
```
Hoặc multiplexer: `opencode serve --port <P>` + `opencode run --attach http://localhost:<P> -s <id>`.

## Orchestration dispatch (qua orca runtime — plumbing đã verify live)

```bash
orca orchestration task-create --spec "<task>" --task-title "<t>" --json     # → task_id
orca orchestration dispatch --task <id> --to <handle> --inject --json        # --inject CẦN agent CLI đang chạy trong terminal đích
orca orchestration check --terminal <handle> --types worker_done --wait --timeout-ms 300000 --json
```
- Spawn agent vào terminal trước khi `--inject`: `orca worktree create --agent <id> --prompt "<task>"` hoặc `orca terminal create --command "<cli>"`.
- Group address: `@all @idle @claude @codex @opencode @gemini @droid @worktree:<id>`.

---

## Antigravity (agy)

**Binary**: `agy` — `%LOCALAPPDATA%\agy\bin\agy.exe`. NOT `antigravity`, NOT `~/.local/bin/agy`.

```bash
# CHECK trước khi dùng:
agy --version
```

**Hook**: Orca v1.4.21 fix Windows hook quoting — no manual `antigravity-hook.cmd` edit.

**Dispatch status** (post v1.4.21):

| Method | Status |
|--------|--------|
| `dispatch --inject` | retest |
| `terminal send` | OK |
| Tool calls | OK |
| `worker_done` callback | retest |

**Fallback if `--inject` fails:**
```bash
orca terminal send --title "Antigravity" --text "<task>"
orca terminal wait --for tui-idle
orca terminal read --title "Antigravity"
```

## Skill Installation per Agent CLI

Skills: `llmwiki/skills/<category>/<name>.md`.

### Claude Code
```bash
# CHECK:
ls .claude/commands/

# Install:
cp llmwiki/skills/dev-loop/propose.md .claude/commands/propose.md
```

### OpenCode / Antigravity
```bash
# CHECK:
ls ~/.agents/skills/

# Install (skill = folder with SKILL.md):
mkdir -p ~/.agents/skills/propose/
cp llmwiki/skills/dev-loop/propose.md ~/.agents/skills/propose/SKILL.md
# Restart OpenCode after install.
```

## AgentMemory

```bash
BASE="https://agentmemory.giatbh.io.vn"
TOKEN="${AGENTMEMORY_TOKEN}"

# CHECK health:
curl -sk -H "Authorization: Bearer $TOKEN" "$BASE/agentmemory/health"

# Ghi:
curl -sk -X POST "$BASE/agentmemory/remember" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"<text>","category":"fact|preference|decision|context"}'

# Tìm:
curl -sk -H "Authorization: Bearer $TOKEN" "$BASE/agentmemory/search?query=<keyword>"
```

## RTK — Token Proxy

RTK (Rust Token Killer): auto-filter CLI output before context — 60-90% token reduction.

```bash
# CHECK:
rtk --version

# Install hook (once):
rtk hooks install --agent claude
rtk hooks install --agent opencode
# All agent commands auto-route through RTK.

# Savings:
rtk stats --today
```

> Xem concepts/RTK để biết chi tiết.

---

## Output Report

After all main skill tasks complete, write a propose draft to the wiki.

### Steps

**1. Build the filename:**
- Format: `DDMMYY-<ten>.md`
- `DDMMYY` = today (e.g., `020626` for 2 June 2026)
- `<ten>` = 2–4 kebab-case words summarising what was done (e.g., `landing-page-coteccons`, `brand-kit-fintech`, `ingest-auth-spec`)

**2. Write** `llmwiki/wiki/draft/orca/DDMMYY-<ten>.md`:

```
# DDMMYY-<ten>
**Type:** draft
**Status:** proposed
**Tags:** <skill-name>, output-report
**Proposed:** YYYY-MM-DD

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| <mô tả task 1> | <tên agent> | pending / in-progress / done |
| <mô tả task 2> | <tên agent> | pending / in-progress / done |

## What
<One sentence — what this skill invocation produced or decided>

## Output
<Key artefacts, files created/modified, or decisions made>

## Files
| File | Action |
|------|--------|
| `path/to/file` | created / modified |

## Notes
- Invoked via: `/<skill-name>` skill

## Origin
- **Draft:** `wiki/draft/orca/DDMMYY-<ten>.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
```

**3. Update wiki index & log:**
- `llmwiki/wiki/index.md` — append one row: `| [DDMMYY-<ten>](draft/orca/DDMMYY-<ten>.md) | draft | YYYY-MM-DD |`
- `llmwiki/wiki/log.md` — append: `## YYYY-MM-DD — <skill-name> — <ten>`

**4. Update agent statuses & sync push — BẮT BUỘC, không bỏ qua:**
- Mở lại file `llmwiki/wiki/draft/orca/DDMMYY-<ten>.md`
- Cập nhật cột **Status** trong bảng `## Agent Task Assignment` theo trạng thái thực tế của từng agent (pending → in-progress → done)
- Clone `rheinmir/setup` nhánh `orca`, copy các skill file đã sửa, rồi push ngược lên:
  ```bash
  git clone git@github.com:rheinmir/setup.git /tmp/rheinmir-setup-sync -b orca --depth 1
  cp /path/to/skill.md /tmp/rheinmir-setup-sync/skills/<skill-name>/SKILL.md
  cd /tmp/rheinmir-setup-sync
  git add .
  git commit -m "skill: sync update — DDMMYY-<ten>"
  git push origin orca
  rm -rf /tmp/rheinmir-setup-sync
  ```

> Skip chỉ khi skill không tạo ra artifact hoặc quyết định nào.
