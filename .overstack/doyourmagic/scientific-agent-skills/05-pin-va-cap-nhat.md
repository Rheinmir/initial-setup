# 05 — Ghim version, cập nhật, gỡ bỏ

**Vì sao dùng:** skill là chỉ dẫn mà agent *tuân theo*. Một bản cập nhật thầm lặng đổi hành vi agent giữa hai lần chạy — đúng thứ bạn không muốn trong một phân tích cần tái lập. File này khoá version và làm cho việc nâng cấp thành một hành động có chủ đích.
**Sinh ra cái gì:** skill đã ghim theo tag hoặc SHA, và một quy trình nâng cấp xem trước được diff trước khi áp.

---

## Metadata truy vết mà installer chèn vào

`gh skill install` chèn nguồn gốc vào frontmatter của bản đã cài. Đây là frontmatter thật của `depmap` sau khi cài (so với bản trong repo, phần `metadata` được thêm 3 khoá `github-*`):

```yaml
---
description: Query the Cancer Dependency Map (DepMap) ...
license: CC-BY-4.0
metadata:
    github-path: skills/depmap
    github-ref: refs/tags/v2.66.0
    github-repo: https://github.com/K-Dense-AI/scientific-agent-skills
    github-tree-sha: 9c13e51a32b3a91510f2d7f6e1e5bf9c6e6f373a
    skill-author: Kuan-lin Huang
    version: "1.0"
name: depmap
---
```

Hai version khác nhau, đừng nhầm:

- `metadata.version` — **version của riêng skill** (ví dụ `"1.0"`), do tác giả bump theo luật của repo.
- `github-ref` / `github-tree-sha` — **version của collection**, cái mà `gh skill update` dùng để phát hiện thay đổi.

Kiểm nhanh xem đang cài bản nào:

```bash
grep -A6 'metadata:' .claude/skills/*/SKILL.md | grep -E 'github-ref|version|^\S+SKILL'
```

## Ghim version

```bash
# ghim theo release tag
gh skill install K-Dense-AI/scientific-agent-skills depmap --pin v2.66.0

# ghim theo commit SHA
gh skill install K-Dense-AI/scientific-agent-skills depmap --pin 1e5eeffbdad3749125afe7ab48a39694e27f181c

# hoặc dạng @VERSION ngay sau tên skill
gh skill install K-Dense-AI/scientific-agent-skills depmap@v2.66.0
```

`VERSION` giải theo git tag hoặc commit SHA. Khi không ghim, thứ tự giải là: **release tag mới nhất**, rồi mới tới HEAD của default branch.

Với `npx skills`, bản khoá nằm trong `skills-lock.json` ở dự án; khôi phục bằng:

```bash
npx -y skills experimental_install
```

Lưu ý `skills-lock.json` **có trong `.gitignore` của repo gốc** — nhưng trong **dự án của bạn** thì nên commit nó, đó chính là điểm khoá tái lập.

## Cập nhật

```bash
# xem có gì mới, KHÔNG sửa file nào
gh skill update --dry-run

# cập nhật một vài skill (hỏi xác nhận)
gh skill update depmap paper-lookup

# cập nhật tất cả, không hỏi
gh skill update --all

# tải lại kể cả khi đã mới nhất (ghi đè sửa đổi cục bộ)
gh skill update --force

# bỏ ghim rồi mới cập nhật
gh skill update --unpin depmap
```

Hành vi đã đọc từ `gh skill update --help`:

- Nó so **tree SHA cục bộ** (lấy từ frontmatter) với remote — không phải so ngày tháng.
- Nó **tự quét mọi thư mục host** (Copilot, Claude, Cursor, Codex, Gemini, Antigravity) ở cả project và user scope.
- **Skill đã ghim bị bỏ qua kèm thông báo.** Đây là điều bạn muốn — nhưng cũng nghĩa là "update --all" không hề nghĩa là "mọi thứ đã mới nhất".
- **`--force` ghi đè file skill bị sửa cục bộ**, nhưng **không xoá** file bạn thêm vào. Kết quả có thể là một trộn lẫn nửa vời nếu bạn từng patch skill.

Với `npx skills`:

```bash
npx -y skills update            # tương tác
npx -y skills update -g -y      # chỉ global, không hỏi
npx -y skills update -p -y      # chỉ project
```

## Quy trình nâng cấp an toàn (khuyến nghị)

```bash
# 1. giữ bản đang chạy để đối chiếu
cp -R .claude/skills .claude/skills.bak

# 2. xem cái gì sẽ đổi
gh skill update --dry-run

# 3. áp
gh skill update --all

# 4. đọc diff của chỉ dẫn — đây mới là phần đổi hành vi agent
diff -ru .claude/skills.bak .claude/skills | head -200
```

Bước 4 là bước hay bị bỏ. Diff một `SKILL.md` **là** diff hành vi; không đọc nó thì nâng cấp skill giống như merge code lạ mà không review.

## Gỡ bỏ

```bash
# npx skills
npx -y skills remove -s "depmap,paper-lookup" -y
npx -y skills remove --all          # gỡ sạch (đã hàm ý -y)

# cài tay / gh skill: xoá thư mục
rm -rf .claude/skills/depmap
rm -rf .agents/skills/depmap
```

`gh skill` không có subcommand `remove`; xoá thư mục là cách đúng.

## Cạm bẫy

- **Cài trùng ở hai scope.** Cài project rồi lại cài user cho cùng một skill sẽ có hai bản; host thường lấy bản project. Kiểm cả `ls .claude/skills` lẫn `ls ~/.claude/skills`.
- **`.agents/skills` dùng chung nhiều host.** Gỡ ở đó là gỡ cho *mọi* host trỏ về nó.
- **`metadata.version` của skill có thể đứng yên trong khi nội dung đã đổi** — nếu tác giả quên bump. Đừng dùng nó làm mốc tái lập; dùng `github-tree-sha`.
- **Bản ghim cũng già đi về mặt an toàn.** Ghim làm đóng băng cả những finding bảo mật chưa được vá. Đọc lại [02](02-tham-dinh-truoc-khi-cai.md) định kỳ chứ đừng ghim rồi quên.
