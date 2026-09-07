---
name: dym-setup-ci
description: "Cắm luật overstack vào CI dự án TIÊU THỤ: workflow GitHub Actions tối giản viết mới, 3 bẫy CI xanh giả, pre-commit, adapter non-Claude. Gọi khi: 'thêm overstack vào CI', 'github actions cho wiki rules', 'pre-commit overstack'."
disable-model-invocation: true
---

# Skill: dym-setup-ci — Cắm luật overstack vào CI của **dự án bạn**

## When to use
- **Tại sao chạy:** hook phiên chỉ gác agent Claude, và agent non-Claude lờ mọi rule advisory. CI là chỗ duy nhất nói "không" mà không bypass được khi merge.
- **Sinh ra gì:** một job GitHub Actions chặn PR khi file `.md` wiki vi phạm luật tầng `repo`.
- Gọi qua hub: `/dym-setup ci` — hoặc trực tiếp `/dym-setup-ci` nếu đã symlink riêng.

## Steps
### 1. Đừng dùng workflow mà installer sinh ra

Installer đặt sẵn `.github/workflows/harness.yml`. File đó **không phải** workflow tối giản cho người tiêu thụ: nó `git clone` cả framework về runner, chạy `install-harness.sh --global`, rồi chạy `harness-doctor --ci` fire-drill và `harness-local run.py firedrill`. Đó là **CI của chính overstack** — nó chứng minh framework còn cắn, không chứng minh wiki dự án bạn sạch. Nó cũng pin `HARNESS_REF: orca` nên mỗi lần upstream đổi là CI của bạn đổi theo mà bạn không biết.

Nếu bạn không phát triển framework: **xoá nó và dùng bản dưới**.

```bash
rm .github/workflows/harness.yml
```

### 2. Workflow tối giản, tự đủ

`.github/workflows/wiki-rules.yml`:

```yaml
name: wiki rules

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.x' }

      # BẮT BUỘC: thiếu pyyaml thì validator fail-OPEN (exit 0) và CI xanh giả.
      - run: pip install pyyaml

      - name: validator có mặt?
        run: test -f .harness/poc-vendor-neutral/bin/llmwiki-validate.py

      - name: kiểm file .md thay đổi
        run: |
          set -euo pipefail
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          if [ -z "$base" ] || ! git cat-file -e "$base^{commit}" 2>/dev/null; then
            base="$(git rev-parse HEAD~1 2>/dev/null || git rev-parse HEAD)"
          fi

          # CHỈ giữ file .md CÒN TỒN TẠI: validator trả 0 cho file đã xoá → xanh giả.
          files=$(git diff --name-only --diff-filter=d "$base" HEAD | grep -E '\.md$' || true)
          [ -z "$files" ] && { echo "không có .md đổi — bỏ qua"; exit 0; }

          echo "kiểm tra:"; echo "$files" | sed 's/^/  /'
          # mode `files` → exit 1 khi có vi phạm (KHÔNG phải 2)
          # shellcheck disable=SC2086
          python3 .harness/poc-vendor-neutral/bin/llmwiki-validate.py files $files
```

### 3. Ba chỗ dễ tạo CI xanh giả

| Bẫy | Vì sao | Đã xử ở workflow trên |
|---|---|---|
| Thiếu `pyyaml` | validator không đọc được policy → in `fail-open` ra stderr rồi **exit 0**. Mọi luật tắt, CI vẫn xanh | `pip install pyyaml` + `test -f` validator |
| File đã xoá vẫn nằm trong danh sách | validator trả **0** im lặng cho file không tồn tại | `--diff-filter=d` |
| Rẽ nhánh theo `rc == 2` | mode `files` thoát **1**, không phải 2 | dùng exit code trực tiếp, không tự so sánh |

Muốn tự rẽ nhánh (ví dụ báo cáo thay vì chặn), nhớ đúng bảng ở [02](../dym-setup-guardrail-cli/SKILL.md):

```bash
python3 .harness/poc-vendor-neutral/bin/llmwiki-validate.py files $files
rc=$?
case $rc in
  0) echo "sạch" ;;
  1) echo "có vi phạm luật tầng repo"; exit 1 ;;
  *) echo "lỗi hạ tầng validator (rc=$rc)"; exit 1 ;;
esac
```

### 4. Pre-commit (tuỳ chọn, tầng nhanh hơn CI)

```bash
pipx install pre-commit    # hoặc: pip install pre-commit
pre-commit install
pre-commit run --all-files
```

⚠️ Bản cài **trước** PR #114 sẽ đỏ ở bước này với `can't open file … harness/poc-vendor-neutral/…` trên **mọi** commit chạm `.md`. Đó là triệu chứng của bẫy dot-layout, không phải wiki của bạn bẩn — chạy lại installer bản mới, hoặc áp bản vá ở [01](../dym-setup-install/SKILL.md).

### 5. Cắm luật cho agent non-Claude

`gen-converters.py` sinh sẵn adapter cho từng vendor dưới `.harness/poc-vendor-neutral/out/`:

| Vendor | File sinh ra | Mức |
|---|---|---|
| Claude / OpenClaude | `out/claude/settings.snippet.json` | **chặn** (hook) |
| opencode | `out/opencode/opencode.json` | **chặn** (`permission.edit` native) |
| Cursor | `out/cursor/.cursor/rules/harness.mdc` | advisory |
| Kiro | `out/kiro/.kiro/steering/harness.md` | advisory |
| Codex | `out/codex/AGENTS.snippet.md` | advisory (dán tay vào `AGENTS.md`) |

Sửa luật thì sửa `policy.yaml` rồi sinh lại — **đừng sửa adapter bằng tay**:

```bash
python3 .harness/poc-vendor-neutral/gen-converters.py
```

Từ PR #114, generator lấy tên thư mục harness từ env `OVERSTACK_HARNESS_DIR` (mặc định `harness`). Ở dự án layout dot phải truyền vào, nếu không snippet sinh ra lại trỏ sai:

```bash
OVERSTACK_HARNESS_DIR=.harness python3 .harness/poc-vendor-neutral/gen-converters.py
```

(Chạy lại `install.sh` thì nó tự truyền — đây chỉ là đường gọi generator trực tiếp.)

Advisory chỉ là *nhắc*, agent lờ được. Vì thế với đội dùng nhiều vendor, CI ở mục 2 là tầng gác duy nhất đáng tin.

## Rules
- ⚠️ Bản cài **trước** PR #114 sẽ đỏ ở bước này với `can't open file … harness/poc-vendor-neutral/…` trên **mọi** commit chạm `.md`. Đó là triệu chứng của bẫy dot-layout, không phải wiki của bạn bẩn — chạy lại installer bản mới, hoặc áp bản vá ở [01](../dym-setup-install/SKILL.md).
