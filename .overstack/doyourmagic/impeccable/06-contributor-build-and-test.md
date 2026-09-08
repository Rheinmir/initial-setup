# 06 — Đóng góp: build và test chính Impeccable

**Vì sao dùng:** bạn clone `pbakaus/impeccable` để sửa luật detector, sửa skill, hoặc thêm provider — và cần vòng lặp build/test đúng ngay từ lần đầu.
**Sinh ra cái gì:** `dist/` (bundle theo từng provider), các thư mục provider đã regenerate trong repo (**phải commit**), và kết quả test.

---

## Yêu cầu

| Thứ | Phiên bản | Ghi chú |
|---|---|---|
| Bun | 1.3.x (đã chạy trên 1.3.5) | Package manager + test runner chính |
| Node | ≥ 22.18.0 | CI chạy matrix `22.18.0` và `24` |
| Chrome | — | Chỉ cần cho suite `detector`: `bunx puppeteer browsers install chrome` |
| Playwright chromium | — | Chỉ cần cho các suite `live-e2e*` opt-in: `npx playwright install chromium` |

## Vòng lặp cơ bản

```bash
git clone https://github.com/pbakaus/impeccable
cd impeccable

bun install                    # ~24s, 227 package
bun run build                  # ~7s
env -u OPENCODE_CONFIG_DIR bun run test:core   # ~72s — xem cảnh báo bên dưới
```

`bun run build` kết thúc bằng một loạt self-check, dùng đúng chỗ này để biết build có lành không:

```
✓ Generated counts: 23 commands, 61 detection rules
✓ Plugin/skill versions agree: 4.1.3
✓ Plugin manifest shape matches the verified loader contract
✓ Prose validator: no AI tells in user-facing copy
✓ Skill prose validator: skill/ is clean
✓ ask_instruction call sites: 8 sentence-initial

✨ Build complete!
```

Các script build khác trong `package.json`:

| Lệnh | Làm gì |
|---|---|
| `bun run build:skills` | Chỉ build skill, bỏ qua sync vào root |
| `bun run build` | `build:skills` + copy `dist` sang `build/_data/dist` |
| `bun run build:release` | Như trên nhưng **có** sync vào root (dùng khi release) |
| `bun run build:browser` | Sinh lại `cli/engine/detect-antipatterns-browser.js` |
| `bun run build:extension` | Đóng gói extension — xem `07` |
| `bun run clean` / `rebuild` | `rm -rf dist build` / clean rồi build |

## ⚠️ Cổng dễ trượt nhất: generated output phải được commit

CI kiểm tra rằng các thư mục provider được sinh ra **đã có trong commit** (`.github/workflows/ci.yml:113-114`):

```yaml
- name: Verify generated tracked outputs
  run: git diff --exit-code -- .agents .claude .cursor .gemini .github/skills plugin cli/engine/detect-antipatterns-browser.js extension/detector
```

Nghĩa là sửa `skill/SKILL.src.md` mà chỉ commit file nguồn là CI đỏ. Quy trình đúng:

```bash
# sửa skill/SKILL.src.md hoặc cli/engine/...
bun run build
git add -A .agents .claude .cursor .gemini .github/skills plugin \
          cli/engine/detect-antipatterns-browser.js extension/detector
git commit -m "..."
```

Tự kiểm tra trước khi push, đúng lệnh CI dùng:

```bash
bun run build && \
git diff --exit-code -- .agents .claude .cursor .gemini .github/skills plugin \
  cli/engine/detect-antipatterns-browser.js extension/detector \
  && echo "GATE CLEAN" || echo "GATE DIRTY — commit generated output"
```

Đã chạy thật trên checkout sạch tại `fcc271c`: `bun run build` xong thì cổng **sạch** — build tất định, không tự sinh nhiễu.

Commit mới nhất của repo tên đúng là `Sync generated provider output` — đây là nhịp làm việc bình thường, không phải sự cố.

## ⚠️ Bẫy môi trường: `OPENCODE_CONFIG_DIR` làm rớt 8 test

Chạy trần trên máy có biến này (Orca có set):

```
518 pass · 8 skip · 8 fail
```

Cả 8 fail nằm trong `tests/skills-cli.test.js`, và assertion nói rõ lý do:

```
Expected to contain: "Install target: [1] Detected only (claude, codex, cursor, gemini)  [2] Customize [1]:"
Received:            "... [1] Detected only (claude, codex, cursor, gemini, opencode)  [2] Customize [1]: ..."
```

Nguyên nhân, từ `cli/bin/commands/skills.mjs:80-84`:

```js
function opencodeGlobalConfigDir(home) {
  if (process.env.OPENCODE_CONFIG_DIR) return process.env.OPENCODE_CONFIG_DIR;
  if (process.env.XDG_CONFIG_HOME) return join(process.env.XDG_CONFIG_HOME, 'opencode');
  return join(home, '.config', 'opencode');
}
```

Bộ dò harness đọc biến môi trường **thật** của máy bạn, nên OpenCode bị nhận diện và rò vào assertion. Suite này không hermetic. Ghi đè `HOME` **không** cứu được (đã thử — vẫn 8 fail) vì đường dẫn đến từ biến môi trường, không từ home.

Cách chạy đúng:

```bash
env -u OPENCODE_CONFIG_DIR bun run test:core
# 874 pass · 0 fail · ~72s
```

Nếu máy bạn có set `XDG_CONFIG_HOME` hoặc `HERMES_HOME`, bỏ luôn chúng khi chạy test.

## Các suite test

Chạy qua `node scripts/run-tests.mjs <suite...>`; `package.json` bọc lại thành script npm.

| Suite | Lệnh | Số file | Nội dung |
|---|---|---|---|
| `core` | `bun run test:core` | 45 | Build, provider transform, CLI helper, context, storage |
| `detector` | `bun run test:detector` | 11 | Detector qua đường text, fixture, và Puppeteer |
| `live` | `bun run test:live` | 44 | Unit + local-server của live mode |
| `framework` | `bun run test:framework` | 1 | Fixture framework: inject, CSP, generated-file, wrap |
| `plugin-e2e` | `bun run test:plugin-e2e` | 1 | Cài subtree `./plugin` vào một Claude Code sandbox thật |
| `cli-e2e` | `bun run test:cli-e2e` | 1 | Install/update tất định với bundle universal local |

Alias:

```
default / all-local  = core, detector, live, framework, plugin-e2e
all                  = default + cli-remote-e2e, live-e2e, live-e2e-accept-cleanup,
                       new-work-e2e, skill-behavior, live-svelte-adapter-deepseek
```

```bash
node scripts/run-tests.mjs --list     # xem từng suite gồm file nào
node scripts/run-tests.mjs --help
bun run test                          # = suite default
```

**Suite opt-in** (không chạy mặc định, tốn tiền hoặc tốn thời gian):

| Suite | Cần gì |
|---|---|
| `live-e2e` | `npx playwright install chromium`, ~2 phút |
| `live-e2e-accept-cleanup` | Provider API key |
| `new-work-e2e` | Playwright |
| `skill-behavior` | API key của 3 provider trong `.env` ở root (gitignored); ~5 phút, tốn vài cent. Baseline hiện tại 21-22/24 |
| `cli-remote-e2e` | Mạng ra impeccable.style |
| `live-svelte-adapter-deepseek` | DeepSeek key |

Thiếu key thì suite **skip sạch**, không fail.

Suite `skill-behavior` chạy 3 model rẻ nhất của 3 hãng, nội tuyến `skill/SKILL.src.md` làm system prompt, rồi assert trên **vết gọi tool** chứ không phải văn bản tự do. Chạy nó bất cứ khi nào bạn sửa phần Setup của `skill/SKILL.src.md`, `skill/scripts/context.mjs`, hoặc các reference chạm Setup.

## CI kiểm gì

| Job | Nội dung |
|---|---|
| `changes` | `node scripts/ci-test-plan.mjs` quyết định phần nào cần chạy |
| `test-matrix` | Node 22.18.0 + 24: `bun install` → core → cài Chrome → detector → live → framework → `build:browser` → `build` → `build:extension` → lint Firefox extension bằng `web-ext@10` → **cổng generated output** → upload `dist/` |
| `test` | Cổng tổng hợp, chỉ kiểm kết quả của `test-matrix` |
| `cli-remote-e2e`, `live-e2e-smoke`, `live-e2e-full`, `live-e2e-accept-cleanup`, `live-svelte-adapter-deepseek`, `skill-behavior` | Các đường opt-in, gate theo thay đổi và theo secret |

## Kiến trúc: sửa ở đâu

| Muốn đổi | Sửa file |
|---|---|
| Nội dung skill và lệnh chat | `skill/SKILL.src.md` (nguồn duy nhất) → `bun run build` |
| Metadata lệnh (mô tả, argument hint) | `plugin/skills/impeccable/scripts/command-metadata.json` (generated — sửa nguồn rồi build) |
| Luật detector | `cli/engine/registry/antipatterns.mjs`, `cli/engine/rules/checks.mjs` |
| Engine tĩnh HTML/CSS | `cli/engine/engines/static-html/` |
| Engine regex | `cli/engine/engines/regex/detect-text.mjs` |
| Engine trình duyệt | `cli/engine/engines/browser/detect-url.mjs` |
| Parse tham số CLI, mã thoát | `cli/engine/cli/main.mjs` |
| Install/update/link | `cli/bin/commands/skills.mjs` |
| Thêm provider mới | Xem `docs/DEVELOP.md` mục "Adding a New Provider" |

Tài liệu contributor đầy đủ: `docs/DEVELOP.md`, `docs/STYLE.md`, `docs/HARNESSES.md`.

## Release

```bash
node scripts/release.mjs skill        # bun run release:skill
node scripts/release.mjs cli          # bun run release:cli
node scripts/release.mjs extension    # bun run release:ext
```

Ba dòng phiên bản tách rời nhau: CLI (npm, hiện 3.6.1), bundle skill (hiện 4.1.3), extension (hiện 1.3.3).

> Ghi chú đã kiểm chứng: bản npm 3.6.1 **đi sau** git `main` cùng số hiệu — `SUBCOMMAND_HELP` (help cho từng subcommand) có trong `main` nhưng không có trong tarball đã publish. Khi debug báo cáo của người dùng, hỏi họ dùng `npx` (bản npm) hay chạy từ checkout, đừng giả định hai bên giống nhau.

## Kiểm tra khác

```bash
bun run audit                       # bun audit --audit-level=moderate
bun run smoke:hooks                 # smoke provider hook
bun run bench:detector              # benchmark detector
bun run bench:detector:browser
```
