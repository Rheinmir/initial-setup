# 04 — Cắm detector vào CI của dự án bạn

**Vì sao dùng:** biến 61 luật tất định thành một cổng chặn, để design slop không lọt qua review.
**Sinh ra cái gì:** một bước CI có mã thoát rõ ràng, cộng file `impeccable.json` làm artifact để soi lại.

> Đây là ví dụ **viết mới, tối giản, cho người tiêu thụ**. Đừng copy `.github/workflows/ci.yml` của repo Impeccable: nó build và test *chính Impeccable* (matrix Node 22.18.0/24, Playwright, provider API key, cổng generated-output) — không liên quan gì tới việc bạn quét dự án mình.

---

## Ba điều phải xử lý đúng trong CI

1. **rc 2 nghĩa là "có phát hiện", không phải crash.** Coi mọi `rc != 0` là lỗi hạ tầng là hiểu sai. Rẽ nhánh tường minh: `0` xanh, `2` đỏ vì design, `1` đỏ vì quét không xong.
2. **Đường dẫn sai không làm CI đỏ.** Target không tồn tại chỉ in `Warning: cannot access ...` rồi thoát **0** (`cli/engine/cli/main.mjs:326`). Đổi tên thư mục là cổng lặng lẽ quét 0 file mà vẫn xanh. Phải tự kiểm tra target tồn tại.
3. **Đừng gọi qua `npx` nếu cần tách stdout/stderr.** `npx` gộp stderr vào stdout (đo trên npm 10.9.2). Cài dependency và gọi `./node_modules/.bin/impeccable`.

Thêm: `package.json` khai `engines.node >= 22.18.0`. Node thấp hơn vẫn chạy nhưng npm cảnh báo `EBADENGINE` — pin runner ở 22.18 trở lên cho gọn log.

## Script cổng (dùng chung cho mọi CI)

`scripts/design-gate.sh`:

```bash
#!/usr/bin/env bash
# Cổng design tất định. rc: 0 sạch · 1 quét không xong · 2 có finding.
set -uo pipefail

TARGET="${1:-src}"
REPORT="${2:-impeccable.json}"
BIN=./node_modules/.bin/impeccable

[ -x "$BIN" ] || { echo "::error::impeccable chưa được cài. Chạy: npm ci"; exit 1; }
[ -e "$TARGET" ] || { echo "::error::target quét không tồn tại: $TARGET"; exit 1; }

"$BIN" detect --json "$TARGET" > "$REPORT"
rc=$?

case "$rc" in
  0) echo "Design gate: sạch (0 finding chính)."; ;;
  2) echo "::error::Design gate: có finding. Xem $REPORT."
     node -e '
       const f = require("./'"$REPORT"'").filter(x => !x.advisory);
       for (const x of f) console.log(`${x.file}${x.line ? ":" + x.line : ""}  [${x.antipattern}] ${x.snippet}`);
       console.log(`\n${f.length} finding chính.`);
     '
     ;;
  1) echo "::error::Design gate: ít nhất một target không quét được (lỗi vận hành)."; ;;
  *) echo "::error::Design gate: mã thoát lạ ($rc)."; ;;
esac

exit "$rc"
```

```bash
chmod +x scripts/design-gate.sh
./scripts/design-gate.sh src
```

Script này **đã được chạy thật** trên cả ba nhánh:

| Tình huống | Output | rc |
|---|---|---|
| `src/` có finding | `::error::Design gate: có finding.` + 7 dòng finding | **2** |
| Target không tồn tại | `::error::target quét không tồn tại: nope` | **1** (chứ không phải 0 như khi gọi `detect` trần) |
| Thư mục sạch | `Design gate: sạch (0 finding chính).` | **0** |

Advisory không cần lọc ở tầng mã thoát — chúng **đã** bị loại khỏi số đếm quyết định mã thoát. Bộ lọc `!x.advisory` ở trên chỉ để in cho gọn.

## GitHub Actions

`.github/workflows/design.yml`:

```yaml
name: Design

on:
  pull_request:
    paths:
      - 'src/**'
      - '.impeccable/**'
      - 'DESIGN.md'

jobs:
  detect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22.18.0'
          cache: npm

      - run: npm ci

      - name: Impeccable design gate
        run: ./scripts/design-gate.sh src impeccable.json

      - name: Upload findings
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: impeccable-findings
          path: impeccable.json
          retention-days: 7
```

Pin phiên bản trong `package.json` để CI không đổi luật giữa chừng:

```json
{ "devDependencies": { "impeccable": "3.6.1" } }
```

## GitLab CI

```yaml
design:
  image: node:22.18
  stage: test
  rules:
    - changes: [ "src/**/*", ".impeccable/**/*", "DESIGN.md" ]
  script:
    - npm ci
    - ./scripts/design-gate.sh src impeccable.json
  artifacts:
    when: always
    paths: [ impeccable.json ]
    expire_in: 1 week
```

## Hạ cổng dần trên codebase đã có sẵn

Bật cổng chặn ngay trên dự án cũ là đỏ hàng trăm finding. Hai cách hạ dần:

**Cách A — chỉ chặn code mới.** Quét đúng phần file đã đổi trong PR:

```bash
CHANGED=$(git diff --name-only --diff-filter=ACMR "origin/$GITHUB_BASE_REF"...HEAD \
          | grep -E '\.(html|css|scss|jsx|tsx|vue|svelte)$' || true)
[ -z "$CHANGED" ] && { echo "Không có file UI nào đổi."; exit 0; }
./node_modules/.bin/impeccable detect --json $CHANGED > impeccable.json
```

**Cách B — thu hẹp bằng scope.** Chỉ bật một miền luật trước, mở rộng sau:

```bash
./node_modules/.bin/impeccable detect --scope=type --json src/ > impeccable.json
```

(Scope hợp lệ: `type`, `layout`. Nhớ viết dính `--scope=`, dạng tách rời sẽ nuốt mất target.)

Nợ cũ thì đóng băng bằng waiver có lý do thay vì tắt luật — xem `03-tune-detector-ignores.md`.

## Pre-commit hook (git thuần)

`.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
STAGED=$(git diff --cached --name-only --diff-filter=ACMR \
         | grep -E '\.(html|css|scss|jsx|tsx|vue|svelte)$' || true)
[ -z "$STAGED" ] && exit 0

./node_modules/.bin/impeccable detect --quiet $STAGED
rc=$?
[ "$rc" -eq 2 ] && echo "Có anti-pattern. Bỏ qua bằng: git commit --no-verify"
exit "$rc"
```

## Quét URL trong CI

`detect https://staging.example.com` render bằng Puppeteer. Trong CI cần cài Chrome tường minh:

```yaml
      - run: npx puppeteer browsers install chrome
      - run: ./node_modules/.bin/impeccable detect --json https://staging.example.com > impeccable-url.json
```

Đường này **chưa được chạy thử** trong lượt khảo sát: chỉ đường `file://` đi qua engine Puppeteer là đã chạy thật. Đo thời gian trên chính CI của bạn trước khi đặt vào đường tới hạn, và nhớ CSS cross-origin không có CORS thì trình duyệt vẫn không đọc được.
