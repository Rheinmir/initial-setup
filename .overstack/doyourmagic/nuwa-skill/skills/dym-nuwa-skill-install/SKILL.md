---
name: dym-nuwa-skill-install
description: "Cài nüwa (女娲) vào runtime của bạn. Vì sao dùng: đây là bước bắt buộc đầu tiên — nüwa không phải CLI, nó là một Agent Skill (một file SKILL.md + references/ + scripts/), phải nằm đúng thư mục skills thì agent mới nạp được."
disable-model-invocation: true
---

# Skill: dym-nuwa-skill-install — Cài nüwa (女娲) vào runtime của bạn

**Vì sao dùng**: đây là bước bắt buộc đầu tiên — nüwa không phải CLI, nó là một *Agent Skill* (một file `SKILL.md` + `references/` + `scripts/`), phải nằm đúng thư mục skills thì agent mới nạp được.
**Sinh ra cái gì**: một thư mục skill trong runtime của bạn, và một agent biết phản ứng với các trigger như «蒸馏XX» / "distill [person]".

---

## Repo này thực chất là gì

Không có `package.json`, `pyproject.toml`, `Cargo.toml` hay `go.mod` — **không có gì để `npm install` hay `pip install`**. Entry point duy nhất là `SKILL.md` ở gốc repo, mở đầu bằng YAML frontmatter:

```yaml
---
name: huashu-nuwa
description: |
  女娲造人：输入人名/主题/甚至只是模糊需求，自动深度调研→思维框架提炼→生成可运行的人物Skill。
  ...
---
```

Kèm theo là ba thư mục có ý nghĩa vận hành:

| Thư mục | Nội dung | Ai đọc |
|---|---|---|
| `references/` | `extraction-framework.md` (phương pháp chắt lọc), `fidelity-scorecard.md` (thang chấm), `skill-template.md` (khung SKILL.md đích) | agent đọc trong lúc chạy Phase 2–4 |
| `scripts/` | 4 script CLI thật (xem [05-helper-scripts-cli.md](05-helper-scripts-cli.md)) | bạn hoặc agent gọi qua shell |
| `examples/` | 15 skill đã chắt lọc hoàn chỉnh (Jobs, Munger, Feynman, Naval, Taleb, MrBeast…) | dùng làm mẫu đối chiếu, hoặc copy thẳng ra dùng |

## Cách 1 — installer đa runtime (khuyến nghị)

```bash
npx skills add alchaincyf/nuwa-skill
```

Installer là [`vercel-labs/skills`](https://github.com/vercel-labs/skills); nó tự nhận runtime đang dùng. Ép chỉ định runtime khi máy có nhiều agent:

```bash
npx skills add alchaincyf/nuwa-skill -a claude-code
npx skills add alchaincyf/nuwa-skill -a codex
npx skills add alchaincyf/nuwa-skill -a cursor
```

## Cách 2 — clone tay vào đúng thư mục skills

```bash
# Claude Code
git clone https://github.com/alchaincyf/nuwa-skill ~/.claude/skills/nuwa-skill

# Codex CLI
git clone https://github.com/alchaincyf/nuwa-skill ~/.codex/skills/nuwa-skill

# Cursor
git clone https://github.com/alchaincyf/nuwa-skill ~/.cursor/skills/nuwa-skill

# OpenClaw
git clone https://github.com/alchaincyf/nuwa-skill ~/.openclaw/workspace/skills/nuwa-skill
```

Repo nặng ~17 MB vì chứa ảnh promo (`advisory-board.png` 5.4 MB, `cover-distill-minds.png` 6.4 MB, `promo/`). Nếu chỉ cần phần chạy được, `--depth 1` và bỏ qua promo là đủ:

```bash
git clone --depth 1 https://github.com/alchaincyf/nuwa-skill ~/.claude/skills/nuwa-skill
```

## Cách 3 — không cần runtime hỗ trợ skill

Dán thẳng nội dung `SKILL.md` vào hội thoại. Nó chỉ là markdown + YAML frontmatter, không có binary hay hook nào cả.

## Kiểm chứng cài xong

```bash
ls ~/.claude/skills/nuwa-skill/SKILL.md          # phải tồn tại
head -3 ~/.claude/skills/nuwa-skill/SKILL.md     # phải thấy "---" và "name: huashu-nuwa"
ls ~/.claude/skills/nuwa-skill/scripts/          # 4 file: download_subtitles.sh, merge_research.py,
                                                 # quality_check.py, srt_to_transcript.py
```

Rồi thử kích hoạt bằng câu tiếng tự nhiên trong chat agent:

```
蒸馏一个费曼
```

hoặc tiếng Anh: `distill Paul Graham`.

## Cạm bẫy đã kiểm chứng

- **Tên frontmatter ≠ tên thư mục**: frontmatter khai `name: huashu-nuwa` nhưng thư mục cài là `nuwa-skill/`. Repo **không định nghĩa slash command** nào — kích hoạt là bằng trigger phrase tự nhiên, không phải `/nuwa`. Nếu runtime của bạn hiển thị skill theo frontmatter, nó sẽ hiện là `huashu-nuwa`.
- **Trigger đa phần là tiếng Trung**: 「造skill」「蒸馏XX」「女娲」「造人」「XX的思维方式」. Trigger tiếng Anh có nhưng ít hơn: `distill [person]`, `nuwa`, `create a [person] perspective skill`, `how does [person] think`, `I need a thinking advisor`. Nói tiếng Việt thuần ("chắt lọc tư duy của X") **không nằm trong danh sách trigger** — gõ thẳng `蒸馏X` hoặc `distill X` cho chắc.
- **Không cần yt-dlp/Python để cài**, chỉ cần khi dùng script phụ trợ (xem 05).
