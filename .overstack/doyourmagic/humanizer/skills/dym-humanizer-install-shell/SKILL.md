---
name: dym-humanizer-install-shell
description: "Cài Humanizer bằng shell (Skills CLI / copy tay). Humanizer chỉ là một file prompt Markdown (SKILL.md). Nó không làm gì cho tới khi nằm trong thư mục skill của agent. Đây là đường cài bằng terminal, dùng được cho mọi agent hỗ trợ skill, không riêng Claude Code."
disable-model-invocation: true
---

# Skill: dym-humanizer-install-shell — Cài Humanizer bằng shell (Skills CLI / copy tay)

**Vì sao dùng:** Humanizer chỉ là một file prompt Markdown (`SKILL.md`). Nó không làm gì cho tới khi nằm trong thư mục skill của agent. Đây là đường cài bằng **terminal**, dùng được cho mọi agent hỗ trợ skill, không riêng Claude Code.

**Sinh ra cái gì:** một thư mục skill trong dự án hoặc ở cấp user (ví dụ `.claude/skills/humanizer/`), cộng `skills-lock.json` ở gốc dự án khi cài theo scope project.

## Yêu cầu trước

- Node.js (để chạy `npx`). Repo **không có** build step, không có `package.json`, không có dependency cần cài.
- Không cần Python trừ khi bạn là người sửa chính skill này — xem `06-contributor-validate-and-release.md`.

## Cài cho một dự án

Chạy tại **gốc dự án đích** (không phải trong repo humanizer):

```bash
npx skills add blader/humanizer
```

Kết quả đã kiểm chứng khi cài cho Claude Code:

```
./.claude/skills/humanizer/
./skills-lock.json
```

`skills-lock.json` ghi lại `source`, `sourceType` và `computedHash` của bản đã cài.

## Cài cho toàn máy (mọi dự án)

```bash
npx skills add blader/humanizer --global
```

`-g` là dạng viết tắt của `--global`. Bỏ cờ này thì cài ở mức project.

## Chọn agent nhận skill

```bash
# một agent cụ thể
npx skills add blader/humanizer --agent claude-code

# nhiều agent
npx skills add blader/humanizer --agent claude-code cursor

# tất cả agent CLI biết
npx skills add blader/humanizer --agent '*' --skill '*' -y
```

Với `--agent '*'`, CLI dựng một bản chuẩn ở `.agents/skills/humanizer/` rồi **symlink** các thư mục agent về đó. Đã quan sát thật:

```
.agents/skills/humanizer/          # bản thật
.claude/skills/humanizer -> ../../.agents/skills/humanizer
agent/skills/humanizer/
```

Sau khi cài xong phải **reload agent** thì skill mới xuất hiện.

## Xem và gỡ

```bash
npx skills ls                 # skill trong project
npx skills ls -g              # skill toàn máy
npx skills ls --json          # dạng máy đọc, không màu
npx skills update humanizer   # cập nhật lên bản mới nhất
```

Gỡ:

```bash
npx skills remove humanizer --agent claude-code -y
```

**Bẫy đã kiểm chứng:** `skills remove humanizer --agent '*' -y` **không gỡ được**, dù `--help` ghi là `use '*' for all agents`. Nó in `■ Invalid agents: *` kèm danh sách agent hợp lệ, thoát code `0`, và file vẫn nguyên. Phải nêu đích danh từng agent khi gỡ. `--agent '*'` chỉ hoạt động đúng ở phía `add`.

## Bẫy thứ hai: CLI copy nguyên repo

Bản cài không chỉ có `SKILL.md`. Đã quan sát thật trong `.claude/skills/humanizer/`:

```
SKILL.md  README.md  AGENTS.md  LICENSE
agents/openai.yaml
scripts/validate-package.py
.claude-plugin/plugin.json  .claude-plugin/marketplace.json
.github/workflows/validate.yml
```

Nếu bạn commit thư mục skill vào dự án, bạn kéo theo cả CI config và script của tool. Muốn gọn thì cài tay chỉ một file:

```bash
mkdir -p .claude/skills/humanizer
curl -fsSL https://raw.githubusercontent.com/blader/humanizer/main/SKILL.md \
  -o .claude/skills/humanizer/SKILL.md
```

Cách này đúng với ghi chú "For a manual install, copy `SKILL.md` into the agent's skill folder" trong README, và hợp lệ vì `.claude-plugin/plugin.json` khai `"skills": ["./"]` — skill nằm ở gốc, một file duy nhất là đủ.

## Claude Desktop

Tải repo dưới dạng ZIP từ GitHub rồi upload làm skill. Từ bản `2.11.2` trở đi việc này chạy được vì repo đã **bỏ symlink plugin** — trước đó ZIP nguồn của GitHub chứa symlink nên Claude Desktop nạp hỏng (xem release note `2.11.1` và `2.11.2`).

## Cách nào cho ai

| Tình huống | Lệnh |
|---|---|
| Dùng riêng, mọi dự án | `npx skills add blader/humanizer --global` |
| Cả team, commit vào repo | `curl` một file `SKILL.md` (tránh rác) |
| Nhiều agent trên cùng máy | `npx skills add blader/humanizer --agent '*' --skill '*' -y` |
| Chỉ dùng Claude Code | xem `02-install-claude-plugin.md` |
