---
name: dym-lieflat-charts-install
description: "Cài lieflat-charts vào agent. đây là bước duy nhất có lệnh shell trong track người dùng. Skill nằm dưới thư mục skills của agent thì agent mới đọc được SKILL.md và mở được templates/."
disable-model-invocation: true
---

# Skill: dym-lieflat-charts-install — Cài lieflat-charts vào agent

**Vì sao dùng:** đây là bước duy nhất có lệnh shell trong track người dùng. Skill nằm dưới thư mục skills của agent thì agent mới đọc được `SKILL.md` và mở được `templates/`.
**Sinh ra cái gì:** một thư mục skill ~52 file HTML + `SKILL.md` + hai catalog, dưới `~/.claude/skills/lieflat-charts` (hoặc `~/.codex/skills/...`).

## Cách A — clone thẳng (khuyến nghị, không phụ thuộc bên thứ ba)

```bash
git clone https://github.com/larashero3-dotcom/lieflat-charts.git \
  ~/.claude/skills/lieflat-charts
```

Codex thì đổi đích thành `~/.codex/skills/lieflat-charts`.

## Cách B — qua `npx skills`

README của repo đề nghị:

```bash
npx skills add https://github.com/larashero3-dotcom/lieflat-charts --skill lieflat-charts
```

`skills` là package npm bên thứ ba (đã kiểm: tồn tại, v1.5.23, bin `skills`), **không thuộc repo này**. Nó tiện nhưng thêm một mắt xích tin cậy; nếu bạn không muốn thế, dùng cách A.

## Verify sau khi cài (bắt buộc — đừng bỏ)

```bash
cd ~/.claude/skills/lieflat-charts
ls SKILL.md catalog.md report-catalog.md mono-tokens.js color-presets.js
ls templates/*.html | wc -l          # mong đợi 7 (4 gallery + 3 big-*)
ls templates/reports/*.html | wc -l  # mong đợi 25 (12×2 + index.html)
head -3 SKILL.md                     # phải thấy front-matter: name: lieflat-charts
```

Thiếu bất kỳ file nào ở dòng đầu → agent sẽ im lặng bỏ qua luật và tự chế biểu đồ. Cài lại.

## Cập nhật

```bash
cd ~/.claude/skills/lieflat-charts && git pull && git log -1 --format='%h %ad %s' --date=short
```

## Gỡ

```bash
rm -rf ~/.claude/skills/lieflat-charts
```

## Đánh thức skill trong hội thoại

Sau khi cài, không có lệnh nào phải gõ. Cứ nhắc tên trong câu:

```text
Dùng lieflat-charts vẽ giúp tôi số liệu này.
```

Agent nào có `/skills` list thì kiểm nó xuất hiện với tên `lieflat-charts`.
