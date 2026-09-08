---
name: dym-scientific-agent-skills-cai-dat-skills
description: "Cài Scientific Agent Skills vào agent của bạn. đưa một subset trong 163 skill khoa học vào agent (Claude Code / Cursor / Codex / Gemini CLI / Antigravity…) để nó có quy trình sẵn cho bioinformatics, cheminformatics, tra cứu database, viết báo khoa học…"
disable-model-invocation: true
---

# Skill: dym-scientific-agent-skills-cai-dat-skills — Cài Scientific Agent Skills vào agent của bạn

**Vì sao dùng:** đưa một *subset* trong 163 skill khoa học vào agent (Claude Code / Cursor / Codex / Gemini CLI / Antigravity…) để nó có quy trình sẵn cho bioinformatics, cheminformatics, tra cứu database, viết báo khoa học…
**Sinh ra cái gì:** các thư mục `<skill-name>/SKILL.md` (kèm `references/`, `scripts/`, `assets/` nếu có) nằm trong thư mục skill của host, cộng metadata truy vết được chèn vào frontmatter.

> ⚠️ **Chạy [02-tham-dinh-truoc-khi-cai.md](02-tham-dinh-truoc-khi-cai.md) trước.** Chính repo khuyến cáo **không cài cả bộ**, và 16/163 skill hiện mang finding CRITICAL/HIGH trong báo cáo quét của họ.

---

## Đường A — `npx skills` (khuyến nghị, hỗ trợ chọn subset)

Xem repo có gì mà **không cài** gì:

```bash
npx -y skills add K-Dense-AI/scientific-agent-skills --list
```

Đã chạy thật: in `Found 163 skills` rồi liệt kê từng skill kèm `description`. Lệnh này clone repo vào cache tạm, không ghi vào thư mục skill.

Cài đúng vài skill bạn cần (đây là cách nên dùng):

```bash
# project scope (mặc định) — cài vào dự án hiện tại
npx -y skills add K-Dense-AI/scientific-agent-skills -s "depmap,paper-lookup,database-lookup" -y

# user scope — dùng được ở mọi dự án
npx -y skills add K-Dense-AI/scientific-agent-skills -g -s "depmap,paper-lookup" -y

# chỉ định host cụ thể
npx -y skills add K-Dense-AI/scientific-agent-skills -a claude-code -s "depmap" -y
```

Cờ đã kiểm chứng qua `npx skills@1.5.23 --help`:

| Cờ | Ý nghĩa |
|---|---|
| `-s, --skill <skills>` | chọn skill (dùng `'*'` cho tất cả) |
| `-a, --agent <agents>` | chọn host (dùng `'*'` cho tất cả) |
| `-g, --global` | user scope thay vì project scope |
| `-l, --list` | chỉ liệt kê, không cài |
| `--copy` | copy file thay vì symlink vào thư mục agent |
| `-y, --yes` | bỏ qua prompt |
| `--all` | viết tắt của `--skill '*' --agent '*' -y` — **đừng dùng với repo này** |

Muốn thử một skill mà không cài gì cả:

```bash
npx -y skills use K-Dense-AI/scientific-agent-skills@depmap
```

## Đường B — `gh skill` (GitHub CLI ≥ 2.90, có provenance)

```bash
# xem nội dung SKILL.md trước, không cài
gh skill preview K-Dense-AI/scientific-agent-skills depmap

# cài một skill cho Claude Code, phạm vi project
gh skill install K-Dense-AI/scientific-agent-skills depmap --agent claude-code --scope project

# phạm vi user
gh skill install K-Dense-AI/scientific-agent-skills depmap --agent claude-code --scope user

# đích tuỳ ý (bỏ qua --agent/--scope)
gh skill install K-Dense-AI/scientific-agent-skills depmap --dir ./vendor/skills
```

**Vị trí file thật — đã chạy và quan sát,** trong một git repo rỗng:

```
--agent claude-code --scope project  →  .claude/skills/depmap/{SKILL.md,references/}
--agent cursor       --scope project  →  .agents/skills/depmap/{SKILL.md,references/}
```

`.agents/skills` là thư mục *dùng chung* của nhiều host (GitHub Copilot, Cursor, Codex, Gemini CLI, Antigravity, Amp, Cline, OpenCode, Warp). Chọn nhiều host cùng trỏ về đó thì skill chỉ nằm một bản.

Output thật của lệnh cài (exit 0):

```
Using ref v2.66.0 (1e5eeffb)
✓ Installed depmap (from K-Dense-AI/scientific-agent-skills@v2.66.0) in ...
  depmap/
  ├── SKILL.md
  └── references/
      └── dependency_analysis.md
```

Khi không truyền version, `gh` giải version theo thứ tự: **(1)** release tag mới nhất, **(2)** HEAD của default branch. Ghim version xem [05-pin-va-cap-nhat.md](05-pin-va-cap-nhat.md).

### Ba cạm bẫy của đường B

- **`--agent gemini` trong README repo là sai.** Giá trị đúng là `gemini-cli`. Danh sách hợp lệ nằm trong `gh skill install --help`.
- **Non-interactive bắt buộc có tên skill.** README ghi `gh skill install K-Dense-AI/scientific-agent-skills` là "browse interactively" — chỉ đúng trong terminal tương tác. Trong CI hoặc khi agent gọi, thiếu tên skill là lỗi.
- **Repo 163 skill nên tra cây rất chậm nếu chỉ đưa tên.** Truyền đường dẫn chính xác để bỏ qua bước duyệt toàn cây:

```bash
gh skill install K-Dense-AI/scientific-agent-skills skills/depmap
```

## Đường C — Agent Plugins / clone tay (lấy trọn bộ)

Repo root là một Agent Plugins 1.0.0 package hợp lệ (`plugin.json` + `skills/`). Client hỗ trợ chuẩn này sẽ phát hiện mọi thư mục con trực tiếp của `skills/` có `SKILL.md`.

```bash
# Cursor
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/K-Dense-AI/scientific-agent-skills.git \
  ~/.cursor/plugins/local/scientific-agent-skills
# rồi Developer: Reload Window

# Host quét ~/.agents/skills (user-level)
git clone https://github.com/K-Dense-AI/scientific-agent-skills.git \
  ~/.agents/skills/scientific-agent-skills

# project-level
git clone https://github.com/K-Dense-AI/scientific-agent-skills.git \
  .agents/skills/scientific-agent-skills
```

**Đường này nạp cả 163 skill.** Toàn bộ cây `skills/` nặng 28 MB và mọi `SKILL.md` đều thường trú trong context của agent — repo tự khuyến cáo "cân nhắc cài một subset theo chủ đề thay vì cả bộ". Chỉ nên dùng đường C khi bạn chủ động muốn tất cả.

## Kiểm tra sau khi cài

```bash
# skill nào đang cài (nếu dùng npx skills)
npx -y skills list

# đọc lại đúng file agent sẽ nạp
ls .claude/skills/ .agents/skills/ 2>/dev/null
head -20 .claude/skills/depmap/SKILL.md
```

Trong agent: hỏi thẳng "bạn có skill depmap không, mô tả nó" — nếu host đã nạp, nó phải đọc được `description` trong frontmatter.

## Điều kiện môi trường

- **Python 3.13+** cho tooling repo; từng skill có thể chấp nhận dải Python rộng hơn.
- **`uv`** — nhiều skill hướng dẫn cài dependency bằng `uv`. Kiểm bằng `uv --version`; nếu chưa có, cài theo hướng dẫn chính thức của Astral. (Máy đang chạy bundle này **chưa có** `uv`; mọi bước verify vì thế đã dùng venv Python 3.13 thuần — xem [08](08-dong-gop-validate-test-scan.md).)
- **Host**: bất kỳ agent nào theo chuẩn Agent Skills.
- **OS**: macOS, Linux, hoặc Windows + WSL2.
