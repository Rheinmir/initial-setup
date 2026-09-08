# Impeccable — bộ workflow chạy được

Sinh từ một lượt khảo sát **read-only** repo `pbakaus/impeccable` tại commit `fcc271c` (2026-09-03), đối chiếu với bản npm `impeccable@3.6.1` cài thật vào sandbox. Impeccable gồm hai thứ ghép lại:

- **CLI dò anti-pattern** (`npx impeccable detect`) — 61 luật tất định, không cần LLM, không cần API key.
- **Bộ skill/lệnh chat** (`/impeccable ...`) — 23 lệnh design chạy bên trong AI coding agent, cộng chế độ `live` lặp trực tiếp trên trình duyệt.

Bundle chia theo **đối tượng người dùng**, không theo tính năng:

- **Nhánh tiêu thụ (`01`–`05`)** — bạn muốn *dùng* Impeccable trong dự án của mình.
- **Nhánh đóng góp (`06`–`07`)** — bạn clone chính Impeccable để *sửa* nó.

| # | File | Mục đích | Nhánh |
|---|------|----------|-------|
| 1 | [01-install-into-your-project.md](01-install-into-your-project.md) | Cài skill + hook vào harness, tránh bẫy cài nhầm global; `update` / `check` / `link` / gỡ sạch | Tiêu thụ — setup |
| 2 | [02-detect-cli-scan.md](02-detect-cli-scan.md) | Quét anti-pattern từ shell: target, cờ, luồng stdout/stderr, mã thoát 0/1/2 | Tiêu thụ — dùng hằng ngày |
| 3 | [03-tune-detector-ignores.md](03-tune-detector-ignores.md) | Dập false positive bền vững: `impeccable ignores`, inline comment, cái gì commit cái gì gitignore | Tiêu thụ — tinh chỉnh |
| 4 | [04-ci-integration.md](04-ci-integration.md) | Cắm detector vào CI **dự án của bạn** như một cổng chặn, rẽ nhánh đúng theo mã thoát | Tiêu thụ — CI |
| 5 | [05-chat-commands.md](05-chat-commands.md) | 23 lệnh `/impeccable` + `init` + `pin` + `live` — **chỉ gõ trong chat**, không phải terminal | Tiêu thụ — dùng hằng ngày |
| 6 | [06-contributor-build-and-test.md](06-contributor-build-and-test.md) | `bun install` → `bun run build` → cổng generated-output → các suite test | Đóng góp |
| 7 | [07-browser-extension-build.md](07-browser-extension-build.md) | Build detector bản browser + đóng gói extension Chrome/Firefox, load unpacked | Đóng góp |

## Thứ tự chạy đề xuất

**Người mới dùng:** `01` → rồi `02` và `05` song song (đường CLI thuần và đường agent độc lập nhau) → `03` khi đã có finding thật cần phân loại → `04` khi waiver local đã ổn.

**Người đóng góp:** vào thẳng `06`; nó không phụ thuộc `01`–`05`. `07` chỉ cần khi bạn động vào engine detector.

## Ba cái bẫy đắt nhất — đọc trước khi gõ lệnh

1. **`npx impeccable install --help` KHÔNG in help — nó cài thật.** Bản npm 3.6.1 không có nhánh help cho subcommand; không có TTY thì prompt tự nhận mặc định và cài **global** vào `$HOME`. Chi tiết + cách gỡ: `01`.
2. **Target sai đường dẫn không làm CI đỏ.** File không tồn tại chỉ in `Warning: cannot access ...` rồi thoát **0**. Chi tiết: `02`, `04`.
3. **`npx` gộp stderr vào stdout.** Findings được ghi ra stderr, nhưng qua `npx` thì `2> findings.txt` bắt được rỗng. Chi tiết: `02`.

## Bundle này được KIỂM CHỨNG thế nào, không chỉ diễn giải README

Mọi lệnh trong `01`–`07` đều đối chiếu mã nguồn, và phần lớn được **chạy thật** trong sandbox (`node v22.17.0`, `npm 10.9.2`, `bun 1.3.5`, macOS 24.6.0):

| Khẳng định | Nguồn kiểm chứng |
|---|---|
| Danh sách subcommand, heuristic "bareword = detect target", lỗi `init` | `cli/bin/cli.js:20-92` — đọc mã + chạy `impeccable frobnicate` (rc 1), `impeccable init` (rc 1) |
| Cờ của `detect`, scope hợp lệ (`type`, `layout`), cờ deprecated | `cli/engine/cli/main.mjs:160-300` + `printUsage()` chạy thật |
| Mã thoát 0 / 1 / 2 | Lời gọi `process.exit(...)` tại `cli/engine/cli/main.mjs:492-495`; chạy thật trên file sạch (0), file bẩn (2), `--scope bogus` (1) |
| Bẫy target thiếu → exit 0 | `cli/engine/cli/main.mjs:326` (`Warning: cannot access`, `continue`, không set `hadOperationalFailure`) + chạy thật |
| Findings ra stderr, JSON ra stdout | Chạy binary đã cài: `stdout=0 stderr=1733`; qua `npx`: `stdout=1731 stderr=0` |
| `install --help` chạy install thật | `grep -c SUBCOMMAND_HELP` = **0** trong tarball npm 3.6.1, nhưng **có** trong git `main` — bản phát hành đi sau repo |
| Mặc định scope khi không có TTY | `cli/bin/commands/skills.mjs:1169-1186` (`if (yes) return 'project'`, ngược lại rơi về `defaultInstallScope`) + quan sát cài nhầm global thật |
| Lệnh `ignores` và định dạng `.impeccable/config.json` | `cli/bin/commands/ignores.mjs:33-62` + chạy thật: 7 → 6 finding sau khi ignore `overused-font` |
| Inline ignore comment | Chạy thật: 6 → 5 finding; `--no-inline-ignores` trả về 6 |
| 61 luật, scope `type`/`layout` | Import trực tiếp `cli/engine/registry/antipatterns.mjs` → `ANTIPATTERNS.length === 61`, `RULE_SCOPES = ['type','layout']` |
| 23 lệnh chat | `plugin/skills/impeccable/scripts/command-metadata.json` — đếm bằng script, không đếm bảng trong README |
| Bundle skill v4.1.3 ≠ CLI v3.6.1 | `impeccable check` chạy thật → `Skills are up to date (v4.1.3)` |
| Cổng generated-output của contributor | `.github/workflows/ci.yml:113-114` + chạy `bun run build` rồi `git diff --exit-code` → sạch |
| Suite test và alias | `scripts/test-suites.mjs` (import trực tiếp) + `node scripts/run-tests.mjs --help` |
| `test:core` xanh 874/874 sau khi bỏ biến môi trường rò | Chạy thật: có `OPENCODE_CONFIG_DIR` → 8 fail; `env -u OPENCODE_CONFIG_DIR` → 0 fail, ~72s |
| Extension MV3 v1.3.3, quyền, output zip | `extension/manifest.json` + `scripts/build-extension.js:86-141` |
| CI của Impeccable **không** được bê nguyên vào `04` | `.github/workflows/ci.yml` build/test *chính Impeccable* (matrix Node 22.18.0/24, Playwright, provider key) — `04` viết mới, tối giản, cho người tiêu thụ |


**Chưa kiểm chứng, đã ghi rõ tại chỗ:** quét URL `http(s)://` một trang thật (chỉ chạy `file://` qua đúng engine Puppeteer), các suite opt-in cần API key (`skill-behavior`, `live-e2e-*`), và luồng `live` đầu-cuối cần dev server + harness thật.
