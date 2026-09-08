---
name: dym-scientific-agent-skills-gate-trong-ci-cua-ban
description: "Đưa skill vào CI của DỰ ÁN BẠN. skill là chỉ dẫn agent tuân theo. Cắm chúng vào CI để (a) skill được commit đúng như lúc bạn thẩm định, (b) upstream thay đổi thì CI báo thay vì agent lặng lẽ đổi hành vi."
disable-model-invocation: true
---

# Skill: dym-scientific-agent-skills-gate-trong-ci-cua-ban — Đưa skill vào CI của DỰ ÁN BẠN

> **Đây là ví dụ viết mới, tối thiểu, cho *người dùng*.** Nó **không** phải bản sao `.github/workflows/*.yml` của repo skill — bốn workflow trong đó (`skill-tests`, `skill-spec-validation`, `pr-skill-scan`, `security-scan`) tồn tại để kiểm *chính repo skill*, cần secret riêng của họ, và không có ý nghĩa gì trong dự án của bạn. Nếu bạn đóng góp cho repo gốc thì xem [08](08-dong-gop-validate-test-scan.md).

**Vì sao dùng:** skill là chỉ dẫn agent tuân theo. Cắm chúng vào CI để (a) skill được commit đúng như lúc bạn thẩm định, (b) upstream thay đổi thì CI báo thay vì agent lặng lẽ đổi hành vi.
**Sinh ra cái gì:** một job CI đỏ khi skill đã cài trôi khỏi bản đã duyệt, hoặc khi một skill không còn hợp lệ theo spec.

---

## Quyết định trước: commit skill hay cài lúc chạy CI

| | Commit vào repo | Cài trong CI |
|---|---|---|
| Tái lập | tuyệt đối — đúng byte bạn đã đọc | phụ thuộc tag/SHA remote |
| Review | diff hiện trong PR, người soát thấy | thay đổi vô hình |
| Kích thước repo | tăng (một skill ~4 KB–1.2 MB) | không |
| Khuyến nghị | ✅ **mặc định nên chọn cái này** | chỉ khi repo bạn cấm vendor |

Commit skill vào repo là mặc định đúng: bạn đã bỏ công thẩm định ở [02](02-tham-dinh-truoc-khi-cai.md), commit là cách duy nhất giữ được kết quả thẩm định đó.

## Gate 1 — Phát hiện drift so với upstream (đã chạy thật)

`gh skill install` ghi `github-tree-sha` vào frontmatter lúc cài. So nó với tree SHA remote hiện tại là phát hiện được upstream đã sửa skill.

Lưu thành `ci/check-skill-drift.sh`:

```bash
#!/usr/bin/env bash
# Đỏ nếu một skill đã cài trôi khỏi tree SHA ghi lúc cài.
set -euo pipefail
status=0
for skill in "$@"; do
  f=".claude/skills/$skill/SKILL.md"
  [ -f "$f" ] || { echo "MISSING $skill"; status=1; continue; }
  repo=$(awk '/github-repo:/{print $2; exit}' "$f" | sed 's#https://github.com/##')
  ref=$(awk '/github-ref:/{print $2; exit}' "$f")
  path=$(awk '/github-path:/{print $2; exit}' "$f")
  pinned=$(awk '/github-tree-sha:/{print $2; exit}' "$f")
  parent=$(dirname "$path"); name=$(basename "$path")
  remote=$(gh api "repos/$repo/git/trees/${ref#refs/tags/}:$parent" \
             --jq ".tree[] | select(.path==\"$name\") | .sha")
  if [ "$pinned" = "$remote" ]; then
    echo "OK      $skill  $pinned"
  else
    echo "DRIFTED $skill  local=$pinned remote=$remote"; status=1
  fi
done
exit $status
```

Đã chạy thật trên máy này với `depmap` cài từ `v2.66.0`:

```
$ ci/check-skill-drift.sh depmap
OK      depmap  9c13e51a32b3a91510f2d7f6e1e5bf9c6e6f373a
→ exit 0

# sau khi sửa tay tree-sha trong frontmatter:
DRIFTED depmap  local=0000...0000 remote=9c13e51a32b3a91510f2d7f6e1e5bf9c6e6f373a
→ exit 1
```

Chi tiết cần biết: khi cài theo tag, `github-ref` là `refs/tags/v2.66.0`, nên script cắt tiền tố `refs/tags/` trước khi truyền cho `gh api`. Cài theo branch thì giá trị khác — chỉnh cho hợp.

## Gate 2 — Skill còn hợp lệ theo spec

Đây là cùng một validator mà repo gốc dùng, nhưng chạy trên *bản bạn đã commit*, nên nó bắt được cả trường hợp bạn tự sửa skill làm hỏng frontmatter:

```bash
uv tool install "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
for d in .claude/skills/*/; do skills-ref validate "$d"; done
```

Không có `uv` thì venv thuần cũng chạy (đã kiểm chứng theo đúng cách này, Python 3.13):

```bash
python3.13 -m venv .venv-skills
./.venv-skills/bin/pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
for d in .claude/skills/*/; do ./.venv-skills/bin/skills-ref validate "$d" || exit 1; done
```

Output khi hợp lệ: `Valid skill: .claude/skills/depmap` và exit 0. Đã chạy trên toàn bộ 163 skill của repo gốc: **0 lỗi**.

## Workflow tối thiểu

`.github/workflows/skills.yml` trong **dự án của bạn**:

```yaml
name: Skills

on:
  pull_request:
    paths: [".claude/skills/**", "ci/check-skill-drift.sh"]
  schedule:
    - cron: "0 6 * * 1"   # Thứ Hai — bắt drift upstream ngay cả khi bạn không đụng gì

permissions:
  contents: read

jobs:
  skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Spec validation
        run: |
          pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
          for d in .claude/skills/*/; do skills-ref validate "$d"; done

      - name: Upstream drift
        env:
          GH_TOKEN: ${{ github.token }}
        run: ./ci/check-skill-drift.sh depmap paper-lookup database-lookup
```

Có ba lựa chọn thiết kế cố ý ở đây:

- **`schedule` bên cạnh `pull_request`.** Drift là chuyện xảy ra ở *upstream*, không phải trong PR của bạn. Chỉ chạy theo PR thì bạn chỉ biết khi tình cờ có người sửa file khác.
- **Liệt kê tên skill tường minh** trong bước drift, không quét `*`. Danh sách hiện trong file CI chính là bản kê những gì bạn đã thẩm định.
- **`permissions: contents: read`.** Job này không cần ghi gì.

## Gate 3 (tuỳ chọn) — quét bảo mật trong CI của bạn

Chỉ thêm khi bạn tự nhận trách nhiệm soát skill, vì nó cần một LLM API key:

```yaml
      - name: Skill security scan
        env:
          SKILL_SCANNER_LLM_API_KEY: ${{ secrets.SKILL_SCANNER_LLM_API_KEY }}
        run: |
          pip install cisco-ai-skill-scanner
          for d in .claude/skills/*/; do skill-scanner scan "$d" --use-behavioral; done
```

Đọc kỹ phần exit code và bẫy "fail open khi thiếu key" ở [02](02-tham-dinh-truoc-khi-cai.md) **trước khi** tin exit 0 của bước này.

## Cạm bẫy

- **Đừng chép `.github/workflows/skill-tests.yml` của repo gốc.** Nó chạy `pytest tests/_meta` trên cây `tests/` của *repo đó* — dự án bạn không có cây ấy, và cũng không nên có.
- **Skill vendored dễ bị sửa lén.** Gate 2 bắt được frontmatter hỏng nhưng không bắt được ai đó sửa nội dung chỉ dẫn. Muốn chặt hơn thì băm cả thư mục lúc merge và so lại trong CI.
- **`gh api` cần token trong CI.** Đặt `GH_TOKEN: ${{ github.token }}`; thiếu nó thì bước drift đỏ vì lý do sai.
