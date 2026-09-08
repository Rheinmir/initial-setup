---
name: dym-archify-ci-diagram-gate
description: "Chốt cổng CI cho sơ đồ trong dự án của bạn. sơ đồ kiến trúc bị thối là vì không ai bắt buộc chúng phải đúng. Nếu nguồn JSON của sơ đồ nằm trong repo, CI có thể từ chối merge khi nguồn không còn validate được."
disable-model-invocation: true
---

# Skill: dym-archify-ci-diagram-gate — Chốt cổng CI cho sơ đồ trong dự án của bạn

**Vì sao dùng:** sơ đồ kiến trúc bị thối là vì không ai bắt buộc chúng phải đúng. Nếu nguồn JSON của sơ đồ nằm trong repo, CI có thể từ chối merge khi nguồn không còn validate được.

**Kết quả nhận được:** một job CI chặn PR, và (tuỳ chọn) các file HTML đã render làm artifact tải về.

> Đây là ví dụ **viết mới, tối thiểu**. Nó **không** phải bản sao của `.github/workflows/ci.yml` trong repo Archify — file đó build và test *chính Archify* (ma trận Node 18/20/22/24, test trình duyệt thật, decode WebM, kiểm định danh release) và không liên quan gì tới việc bạn dùng Archify.

## Bố cục repo giả định

```
docs/diagrams/
  runtime.architecture.json
  release.workflow.json
  checkout.sequence.json
```

Quy ước đặt tên `<tên>.<type>.json` là thứ giữ script bên dưới ngắn — loại sơ đồ suy ra từ chính tên file. Nếu bạn không theo quy ước này, hãy khai một bảng ánh xạ tường minh.

## Script cổng

`scripts/check-diagrams.sh`:

```bash
#!/usr/bin/env bash
set -uo pipefail

A="${ARCHIFY_HOME:?đặt ARCHIFY_HOME trỏ vào thư mục skill archify}"
CLI="node $A/bin/archify.mjs"
failed=0

shopt -s nullglob
for f in docs/diagrams/*.json; do
  base="$(basename "$f" .json)"
  type="${base##*.}"
  case "$type" in
    architecture|workflow|sequence|dataflow|lifecycle) ;;
    *) echo "BỎ QUA  $f (không suy ra được loại từ tên file)"; continue ;;
  esac

  $CLI validate "$type" "$f" --quality showcase --json > "/tmp/${base}.validate.json"
  rc=$?
  case $rc in
    0) echo "OK      $f" ;;
    2) echo "LỖI GỌI $f — dòng lệnh sai, không phải lỗi nội dung sơ đồ"; failed=1 ;;
    *) echo "HỎNG    $f"; failed=1
       python3 -c "import json,sys;[print('  ',d['code'],'—',d['message']) for d in json.load(open(sys.argv[1])).get('diagnostics',[])]" \
         "/tmp/${base}.validate.json" ;;
  esac
done

exit $failed
```

Ba điểm cố ý:

- **Phân biệt rc `2` với rc `1`.** `2` nghĩa là script của *bạn* gọi sai (loại sơ đồ lạ, cờ lạ, `--repo-root` sai chỗ). Gộp chung với `1` sẽ khiến bạn đi sửa sơ đồ trong khi lỗi nằm ở CI.
- **Ép `--quality showcase`.** Nếu không, một biên lai 4-check có thể trôi qua và bạn tưởng đã nghiệm thu showcase.
- **In `diagnostics[].code`**, không in stack. Mã ổn định, thông điệp thì không.

## GitHub Actions

`.github/workflows/diagrams.yml`:

```yaml
name: Diagrams

on:
  pull_request:
    paths:
      - 'docs/diagrams/**'
      - 'scripts/check-diagrams.sh'

jobs:
  validate:
    runs-on: ubuntu-latest
    env:
      ARCHIFY_UPDATE_CHECK_DISABLED: '1'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Lấy Archify về một thư mục cố định
        run: |
          git clone --depth 1 https://github.com/tt-a1i/archify.git /tmp/archify-src
          echo "ARCHIFY_HOME=/tmp/archify-src/archify" >> "$GITHUB_ENV"

      - name: Kiểm tra runtime
        run: node "$ARCHIFY_HOME/bin/archify.mjs" doctor

      - name: Validate mọi nguồn sơ đồ
        run: bash scripts/check-diagrams.sh
```

Không có bước `npm install`. CLI là zero-dependency — đã kiểm chứng bằng cách chạy `validate` xanh trên cây nguồn không hề có `node_modules`.

`ARCHIFY_UPDATE_CHECK_DISABLED: '1'` giữ CI hoàn toàn offline và tất định.

> Ghim một tag hoặc commit thay vì `--depth 1` trên nhánh mặc định, nếu bạn muốn cổng CI không tự đổi hành vi khi upstream đổi.

## Tuỳ chọn: xuất HTML làm artifact

Thêm sau bước validate:

```yaml
      - name: Render sơ đồ
        run: |
          mkdir -p out
          for f in docs/diagrams/*.json; do
            base="$(basename "$f" .json)"
            type="${base##*.}"
            node "$ARCHIFY_HOME/bin/archify.mjs" deliver "$type" "$f" "out/${base}.html" \
              --quality showcase --json > "out/${base}.receipt.json"
          done

      - uses: actions/upload-artifact@v4
        with:
          name: diagrams
          path: out/
```

Mỗi `*.receipt.json` mang SHA-256 và số byte của cả spec lẫn artifact — đủ để chứng minh HTML tải về đúng là bản sinh từ nguồn trong commit đó.

## Tuỳ chọn: bằng chứng trình duyệt trong CI

Chỉ thêm khi runner **thật sự có** Chrome. Đọc kỹ [05](05-visual-check-and-preview.md) trước:

```yaml
      - name: Bằng chứng trình duyệt
        env:
          ARCHIFY_CHROME_NO_SANDBOX: '1'
        run: |
          for html in out/*.html; do
            node "$ARCHIFY_HOME/bin/archify.mjs" visual-check "$html" --json > "${html%.html}.visual.json"
            rc=$?
            if [ "$rc" = "2" ]; then
              echo "::error::visual-check BỊ BỎ QUA cho $html — không có Chrome. Bỏ qua không phải pass."
              exit 1
            fi
            [ "$rc" = "0" ] || exit "$rc"
          done
```

Bẫy chết người: `visual-check` trả `2` khi **không tìm thấy Chrome**. Nếu cổng của bạn chỉ kiểm `rc == 1` là hỏng, thì trên một runner thiếu Chrome mọi thứ sẽ "xanh" trong khi chưa có một dòng bằng chứng trình duyệt nào. Đoạn trên biến "skipped" thành lỗi tường minh.

## Cổng cho architecture có bằng chứng mã nguồn

Nếu nguồn khai `sources[]` (xem [04](04-repository-evidence.md)), thêm `--repo-root` — và nhớ rằng `meta.repository.revision` phải là SHA 40 ký tự **đã tồn tại** trong checkout:

```yaml
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0        # bắt buộc: bằng chứng ghim vào một commit cụ thể
```

```bash
node "$ARCHIFY_HOME/bin/archify.mjs" validate architecture docs/diagrams/runtime.architecture.json \
  --quality showcase --repo-root "$GITHUB_WORKSPACE"
```

Checkout nông mặc định (`fetch-depth: 1`) sẽ làm hỏng cổng này ngay khi revision đã ghim không nằm trong lịch sử được kéo về.

## Đã chạy thử

Script `check-diagrams.sh` ở trên được chạy thật với ba file: một workflow hợp lệ, một architecture hợp lệ, và một JSON cố tình hỏng. Kết quả:

```
HONG    docs/diagrams/broken.workflow.json
   schema/required — / must have required property 'schema_version' …
   schema/required — / must have required property 'diagram_type' …
   schema/required — / must have required property 'lanes' …
   schema/required — / must have required property 'edges' …
   schema/minItems — /nodes must NOT have fewer than 1 items {"limit":1}
OK      docs/diagrams/release.workflow.json
OK      docs/diagrams/runtime.architecture.json
```

rc `1` — cổng chặn đúng như mong đợi, và chỉ ra chính xác file nào cùng mã chẩn đoán nào.
