---
name: orca-workflow
description: Daily propose → gate → dispatch workflow with Orca
---

# Skill: orca-workflow

> 🧭 Dispatch backend — chọn agent/model rẻ, chạy nhiều worker song song, cú pháp opencode/orchestration → xem **orca-dispatch-reference** (nguồn chân lý duy nhất, đừng nhân bản syntax ở đây).

## Purpose

Propose → gate → dispatch → verify qua Orca. Agent pool 1:1 per engine (claude, agy, opencode, kiro, copilot).

Claude: analyze. Others: execute. Kill opencode nếu chờ quá lâu.

**Caveman Mode**: Chọn độ chi tiết theo người đọc file. File markdown mà MÁY hoặc AGENT đọc và thực thi (SKILL.md, policy.yaml, AGENT.md, bảng tham chiếu thuần) thì viết ngắn gọn được — caveman ở đây tiết kiệm token mà không hại gì. Nhưng **tài liệu CON NGƯỜI đọc hoặc review thì BẮT BUỘC tắt caveman và viết đầy đủ** — proposal, output-report, wiki content (concept/ADR/registry), README, CONTRIBUTING và runbook, cùng mọi trang HTML. Những file này phải là văn xuôi với câu hoàn chỉnh, dễ đọc; không bỏ liên từ, không viết tắt cụt, không nhồi bảng thay cho câu giải thích. Bài học 2026-06-27: user phản hồi "caveman đã nén quá mức khi viết tài liệu", rồi làm rõ — file máy đọc thì gọn được, file người đọc thì cần đầy đủ.


## Triggers

- "propose <feature>", "feature request", "implement <name>"
- "chạy lint", "verify wiki"
- "sync template", "upstream"

## Rẽ nhánh: SỰ CỐ ≠ tính năng
Đầu vào là **sự cố** (bug, lỗi runtime, regression, "hôm qua còn chạy") → **GỌI skill `orca-issue`** thay vì propose: vòng riêng triage → repro-first gate (chưa tái hiện chưa được sửa) → fix red→green → distill kép. Sự cố nặng cần fan-out thì orca-issue escalate ngược về đây để dispatch, nhưng 2 chốt cứng của nó vẫn giữ.

## Sổ vấn đề quy trình (problem-tree) — convention mọi dự án
Dự án có `llmwiki/` thì sổ cây vấn đề nằm ở `llmwiki/html/problem-tree.html` (repo framework: `fdk-problem-tree.html`). Phiên nào **phát hiện hoặc giải một vấn đề quy trình/framework** → cập nhật node vào block JSON `#tree-data` (append-only; solved phải ghi `solvedBy`; scope theo 3 trụ harness/skills/llmwiki — xanh lá chỉ khi 3/3). Quên cũng không mất: hook SessionEnd (R17) tự ghi thẻ pending bằng code, lần sau distill.

## Workflow: propose

0. **R12 (B) — pre-work sweep cả workspace (MỘT LẦN, trước khi làm / fan-out đa-agent)**: orchestrator chạy `harness/poc-vendor-neutral/bin/pull-gate-sweep.sh` — quét MỌI subrepo (từ `.harness-workspace.yaml`, thiếu → auto-discover harnessed), fetch song song; subrepo **TARGET** sau remote → DỪNG, `git pull --rebase` trong repo đó rồi mới dispatch (cả đàn agent chung base tươi); subrepo `watch` chỉ cảnh báo. 1 repo → sweep tự rút về `pull-gate.sh`. Offline → fail-open. **KHÔNG chặn từng-edit** (cố tình bỏ per-edit PreToolUse). **R12 (C)** gate2 per-repo: cài mọi subrepo bằng `install-harness.sh --all-subrepos`; check tay `pull-gate.sh gate2`.
1. **query**: GỌI skill `query` (Skill tool → `query`, hoặc `/query`) để synthesis context từ `wiki/` về tính năng — KHÔNG đọc tay rời rạc, dùng đúng wiki-loop `query` (tổng hợp `[[wikilinks]]`, trả về điều đã biết + lỗ hổng). Project chưa có `wiki/` (hoặc query trả rỗng) → ghi nhận "chưa có tiền lệ" rồi sang bước 2.
2. **propose** — KHÔNG mô tả lại; **GỌI skill `propose`** (Skill tool → `/propose`, đúng pattern bước 1 gọi `query`). Mọi yêu cầu R7 (cặp `.md`+`.html`, `## Plan`, `## Agent Task Assignment`, glass-style `docs-site-macos`, prose chi tiết) sống trong skill con — sửa hành vi propose chỉ sửa `llmwiki/skills/dev-loop/propose.md`, KHÔNG sửa ở đây (single source of truth, xem `ADR-003-skill-as-single-source-of-truth`).
   - **Tách Claude-nghĩ / CLI-rẻ-render:** Claude (qua `/propose`) chỉ sản xuất SUBSTANCE = `.md` render-complete (Plan + prose + `## Render brief` = bước diagram dạng data + đoạn prose mỗi task). Phần `.html` là RENDER **cơ học** của `## Render brief` → **dispatch sang một CLI rẻ** theo bảng chi phí (OpenCode `big-pickle` → `agy` → `kiro`, $0). Render free nên dùng **Full** `docs-site-macos` richness, KHÔNG cắt bớt — token Claude chỉ tốn cho substance, không phình theo độ giàu HTML.
   - **Watchdog + R7 gate (bài học 250626 — headless giao ~1/5):** chờ ~60–90s; im lặng / không tạo file / thiếu `diagram-box` → **kill, Claude render fallback**. Thử CLI rẻ theo thứ tự sẵn-có (probe `--version`); cạn → Claude. R7 vẫn chặn lúc write+commit nên chất lượng được gác bất kể ai render.
3. **gate**: `orca orchestration gate-create --question "Duyệt proposal này?"` → chờ user (gửi kèm preview URL của html)
   - **Trụ 3 lifecycle (best-effort, fail-open):** user DUYỆT → `python3 harness/scripts/code-logger.py --task set <T-id> state=approved note="gate"` (`<T-id>` = field `task:` trong frontmatter draft do `/propose` mint; trống thì bỏ qua). User TỪ CHỐI → `--task set <T-id> state=rejected`. Lệnh fail-open, không chặn flow.
4. **Sau duyệt**: Phân rã tasks từ proposal → `orca orchestration task-create` mỗi task
5. **dispatch**: `orca orchestration dispatch --task <id> --to <agent> --inject`
   - **Trụ 3 lifecycle (best-effort):** khi giao việc → `python3 harness/scripts/code-logger.py --task set <T-id> state=dispatched note="<agent>"`. Đây là `T-id` bền (audit trail bất biến), độc lập với `task_xxxx` ephemeral của orca orchestration. Fail-open.
   - **Persona theo archetype (Boris Cherny — 5 vai vòng đời):** muốn dispatch theo một *posture* cụ
     thể thì gọi bằng **từ khoá** — `/proto` `/build` `/sweep` `/grow` `/maintain`. Cơ chế:
     `python3 harness/scripts/archetype.py --get /<kw>` → in (a) **CLI gợi ý** cho archetype đó
     (Prototyper→opencode rẻ · Builder/Grower/Maintainer→Claude · Sweeper→opencode), và (b)
     **PREAMBLE persona** (`llmwiki/personas/<archetype>.md`) — **inject preamble đó vào `<task>`**
     trước khi dispatch để agy/opencode/kiro vào đúng vai (vd Sweeper bị cấm thêm feature). CLI nào
     hợp archetype nào là adapter `verified:false` (`harness/archetypes.config.yaml`). Xem ADR-015.
6. **Chờ**: `orca orchestration check --wait --types worker_done --timeout-ms 300000`
7. **Kiểm tra**: `verify-before-commit` tự động chạy trước mỗi commit

## Gotchas orchestration CLI (bài học 230626)

- **2 id từ `task-create --json`**: response có envelope `id` (uuid) VÀ `result.task.id` (`task_xxxx`). Mọi lệnh sau (`gate-create --task`, `dispatch --task`, `task-update --id`) PHẢI dùng `result.task.id`, KHÔNG dùng envelope id. Dùng nhầm: gate vẫn tạo/resolve được nhưng trỏ task ma → task thật kẹt ở `ready`.
- **Status hợp lệ của `task-update --status`**: `ready` | `in_progress` | `completed` | `failed`. KHÔNG có `done` — truyền `done` trả `ok:false` lặng lẽ (không báo lỗi rõ).
- Lấy id thật chắc ăn: `orca orchestration task-list --json` rồi match theo `spec`.

## An toàn container / DB (BẮT BUỘC trước khi đụng docker)

### Trước khi đụng container (docker compose / docker run)

```bash
# BẮT BUỘC chạy trước bất kỳ --force-recreate, down, recreate nào:
docker inspect <container_name> --format '{{json .Mounts}}' | python3 -m json.tool
```

So sánh `Source` path với volume trong compose file sắp dùng. Nếu khác → DỪNG, hỏi user.

**Production DB của Cozyroom:** `/mnt/c/Users/olive/orca/workspaces/home-spotify/m/data/metadata.db`
Không bao giờ đổi volume mount mà không backup + xác nhận user.

> Bài học 2026-05-29: recreate container với compose sai path → mất toàn bộ DB người dùng.

## Dispatch nhanh

> ⚠️ **CLI agent headless KHÔNG đáng tin (bài học 250626 — orca-eval):** `opencode run` / `agy -p` / `kiro run` chạy nền từ Claude Code thường **không giao hàng** (process thoát/treo, không tạo file — thực đo 1/5 task thành công). Quy tắc: đặt **watchdog** (~60–90s), nếu im lặng/không có file → **kill + Claude tự tiếp quản theo spec** (đừng chờ vô ích). Dùng OpenCode cho task boilerplate ĐỘC LẬP, đã verify được; task có dependency/nuance → Claude làm. Muốn dispatch THẬT cho agent → ưu tiên `orca terminal` interactive thay vì `-p`/`run`.

```bash
# OpenCode non-interactive (DEFAULT — dùng big-pickle miễn phí):
# ⚠ KHÔNG dùng --dangerously-skip-permissions khi dispatch từ Claude Code — auto-mode classifier sẽ DENY (bài học 120626)
opencode run -m opencode/big-pickle --dir "<project>" "<task>"

# Antigravity non-interactive:
agy -p "<task>"

# Kiro non-interactive:
kiro run --dir "<project>" "<task>"

# GitHub Copilot Coding Agent (async — via GitHub issue):
gh issue create --title "<task>" --body "<task details>" --assignee "@me"
# Then: gh copilot suggest "<task>" or trigger via VS Code Copilot Chat

# Nếu dùng Orca terminal (interactive):
orca terminal list
orca terminal create --worktree active --title "OpenCode" --command "opencode"
orca terminal send --title "OpenCode" --text "<task>"
orca terminal wait --for tui-idle && orca terminal read --title "OpenCode"
```

## Phân công task theo chi phí

| Task | Agent | Model |
|------|-------|-------|
| Search, grep, list, read | OpenCode | `opencode/big-pickle` ($0) |
| Viết boilerplate, CRUD | OpenCode | `opencode/big-pickle` ($0) |
| Wiki ingest/lint | OpenCode | `opencode/big-pickle` ($0) |
| Review diff, explain | agy | default |
| Architectural decisions | Claude Code | sonnet-4-6 |
| Debug lỗi khó | Claude Code | sonnet-4-6 |
| Frontend UI boilerplate | Kiro | default |
| Cross-file refactor | Kiro | default |
| PR review + suggest fixes | Copilot | gpt-4o (GitHub) |

## Agent binaries

| Agent | Binary | CHECK |
|-------|--------|-------|
| Antigravity | `agy` | `agy --version` |
| OpenCode | `opencode run -m opencode/big-pickle` | `opencode --version` |
| Kiro | `kiro run` | `kiro --version` |
| GitHub Copilot | `gh copilot suggest` | `gh copilot --version` |
| Orca | GUI only — dùng qua `orca terminal *` commands | `orca terminal list` |

## Antigravity Dispatch Reality (tested 2026-05-21, updated 2026-05-23)

**Binary**: `agy` — `%LOCALAPPDATA%\agy\bin\agy.exe`. NOT `antigravity`, NOT `~/.local/bin/agy` (Linux).

**Tạo terminal**:
```bash
orca terminal create --worktree active --title "Antigravity" --command "agy"
```

**Hook**: Orca v1.4.21 fix Windows hook quoting — `antigravity-hook.cmd` no manual edit needed.

**OpenCode**: `opencode` — npm global at `%APPDATA%\npm\opencode.cmd`.

Dispatch status:

| Bước | Trạng thái |
|------|-----------|
| `dispatch --inject` | Thử sau v1.4.21 — nếu fail, dùng `terminal send` |
| `terminal send` thủ công | **OK** |
| Antigravity đọc file/chạy lệnh | **OK** |
| `worker_done` về inbox | Cần retest |

## Slash Skill Installation per Agent CLI

Agent nhận dispatch: **tự cài skill** từ `llmwiki/skills/` trước khi bắt đầu.

### Claude Code CLI
```bash
mkdir -p .claude/commands/
cp llmwiki/skills/<loop>/<name>.md .claude/commands/<name>.md
# User-level:
mkdir -p ~/.claude/commands/
cp llmwiki/skills/<loop>/<name>.md ~/.claude/commands/<name>.md
```

### OpenCode CLI
```bash
mkdir -p ~/.agents/skills/<name>/
cp llmwiki/skills/<loop>/<name>.md ~/.agents/skills/<name>/SKILL.md
# Restart OpenCode để discover skill mới.
```

### Antigravity CLI
```bash
mkdir -p ~/.agents/skills/<name>/
cp llmwiki/skills/<loop>/<name>.md ~/.agents/skills/<name>/SKILL.md
```

### Kiro CLI
```bash
mkdir -p ~/.kiro/skills/<name>/
cp llmwiki/skills/<loop>/<name>.md ~/.kiro/skills/<name>/SKILL.md
```

### GitHub Copilot
```bash
# Workspace-level steering via .github/copilot-instructions.md
# Skills injected as context file:
mkdir -p .github/
cat llmwiki/skills/<loop>/<name>.md >> .github/copilot-instructions.md
# Or per-skill steering file (Copilot Workspace):
mkdir -p .github/skills/
cp llmwiki/skills/<loop>/<name>.md .github/skills/<name>.md
```

### Rules cho tất cả agent
- Copy skill files only — skip `README.md`, `index.md`, `log.md`.
- File by file — no `cp -R`.
- Scope: `.claude/commands/` (Claude Code); `~/.agents/skills/` (OpenCode/agy); `~/.kiro/skills/` (Kiro); `.github/` (Copilot).
- Sau khi cài, report:
  ```
  | Agent       | Skill   | Installed at                            |
  |-------------|---------|------------------------------------------|
  | claude-cli  | propose | .claude/commands/propose.md              |
  | opencode    | propose | ~/.agents/skills/propose/SKILL.md        |
  | antigravity | propose | ~/.agents/skills/propose/SKILL.md        |
  | kiro        | propose | ~/.kiro/skills/propose/SKILL.md          |
  | copilot     | propose | .github/skills/propose.md                |
  ```

## AgentMemory — Persistent Cross-Session Memory

Service tại `https://agentmemory.giatbh.io.vn/` — lưu context giữa các session.

```bash
BASE="https://agentmemory.giatbh.io.vn"
TOKEN="${AGENTMEMORY_TOKEN}"

# Health check
curl -sk -H "Authorization: Bearer $TOKEN" "$BASE/agentmemory/health"

# Ghi memory (cuối session hoặc sau quyết định quan trọng)
curl -sk -X POST "$BASE/agentmemory/remember" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"<nội dung>","category":"fact|preference|decision|context"}'

# Tìm kiếm (đầu session hoặc trước khi propose)
curl -sk -H "Authorization: Bearer $TOKEN" \
  "$BASE/agentmemory/search?query=<từ+khóa>"
```

**Khi dùng:**
- **Đầu session**: search context trước khi bắt đầu
- **Sau decision**: lưu approach + lý do
- **Cuối session**: lưu tasks xong, commits, trạng thái

## Commands chính

```bash
orca orchestration run --spec "Propose: <tính năng>. Query wiki, tạo draft, gate chờ duyệt."
```

> Dispatch chi tiết: `llmwiki/skills/orchestrate/orca-dispatch-reference.md`

---

## Output Report (sau khi implement xong)

> Đây là **báo cáo kết quả** sau khi implement, KHÔNG phải propose plan.
> Propose plan phải được tạo ở Bước 2 TRƯỚC khi làm bất kỳ thứ gì.

After all implementation tasks complete, write an output report to the wiki.

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
