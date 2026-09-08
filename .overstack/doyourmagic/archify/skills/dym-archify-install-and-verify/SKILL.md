---
name: dym-archify-install-and-verify
description: "Cài Archify vào agent harness và chứng minh nó chạy. Archify không phải thư viện bạn import. Nó là một skill package (một thư mục có SKILL.md ở gốc) kèm một CLI Node. Nó không làm gì cho tới khi nằm đúng chỗ agent của bạn quét skill, và cho tới khi bạn chứng minh runtime đ"
disable-model-invocation: true
---

# Skill: dym-archify-install-and-verify — Cài Archify vào agent harness và chứng minh nó chạy

**Vì sao dùng:** Archify không phải thư viện bạn `import`. Nó là một **skill package** (một thư mục có `SKILL.md` ở gốc) kèm một CLI Node. Nó không làm gì cho tới khi nằm đúng chỗ agent của bạn quét skill, và cho tới khi bạn chứng minh runtime đủ điều kiện.

**Kết quả nhận được:** thư mục `archify/` nằm trong đường skill của harness, một lần `doctor` xanh, và một file HTML demo mở được trong trình duyệt.

## Điều kiện tiên quyết

- **Node.js >= 18** — lấy từ `archify/package.json` → `engines.node`. CI của dự án phủ 18, 20, 22, 24.
- Không cần `npm install`. Đã kiểm chứng: xoá sạch `node_modules` rồi chạy `validate` vẫn xanh. `devDependencies` (`ajv`, `parse5`, `saxes`, `simple-icons`) chỉ dùng cho test/build của chính Archify.

> Cảnh báo đã kiểm chứng: `archify/package.json` có `"private": true` và package **không** nằm trên npm. `npx archify …` sẽ không chạy. Mọi lệnh trong bộ này đều gọi trực tiếp `node <skill>/bin/archify.mjs`.

## Cách A — cài qua CLI `skills` (đường README khuyến nghị)

```bash
npx skills add tt-a1i/archify -g
```

Không tương tác, chỉ định rõ harness:

```bash
npx -y skills add tt-a1i/archify --skill archify --agent cursor --global --copy --yes
```

Dùng thử không cài:

```bash
npx skills use tt-a1i/archify@archify --agent codex
```

`--agent` nhận `cursor`, `codex`, `claude-code`, `opencode`.

> Chưa kiểm chứng trong lượt khám phá này: `skills` là CLI bên thứ ba và cần mạng. Nếu nó thất bại hoặc bạn không muốn phụ thuộc, dùng Cách B.

## Cách B — cài thủ công (đã kiểm chứng bằng cấu trúc thư mục)

Đơn vị cài đặt là thư mục `archify/` bên trong repo — nơi có `SKILL.md`, `bin/`, `renderers/`, `schemas/`, `examples/`, `references/`.

```bash
git clone https://github.com/tt-a1i/archify.git /tmp/archify-src
cp -R /tmp/archify-src/archify ~/.claude/skills/archify
```

Đường cài theo harness, lấy từ bảng "Installation options" của README:

| Harness | Đích |
|---|---|
| Claude Code | `~/.claude/skills/archify` hoặc `.claude/skills/archify` |
| Codex CLI | `~/.agents/skills/archify` hoặc `.agents/skills/archify` |
| opencode | `~/.config/opencode/skills/archify`, `.opencode/skills/archify`, hoặc `.agents/skills/archify` |
| Raven | giải nén `archify.zip` vào `~/.raven/workspace/skills` → `~/.raven/workspace/skills/archify` |
| Claude.ai | tải `archify.zip` lên Settings → Capabilities → Skills |

Kiểm tra nhanh là đã đặt đúng tầng thư mục:

```bash
test -f ~/.claude/skills/archify/SKILL.md && echo "layout ok" || echo "sai tầng — bạn đang copy nhầm repo root"
```

Lỗi hay gặp: copy cả repo root (`archify-src/`) thay vì thư mục con `archify/`. Khi đó `SKILL.md` nằm sâu một tầng và harness không thấy skill.

## Chứng minh nó chạy

```bash
cd ~/.claude/skills/archify
node bin/archify.mjs doctor
```

Kết quả thật đã chạy (macOS, Node v22.17.0):

```
Archify doctor

[ok] Node.js v22.17.0 (requires >=18)
[ok] Core template
[ok] Example renderer
[ok] Live preview runtime
[ok] Visual-check runtime
[ok] Output path safety runtime
[ok] Scenario recipe guide
[ok] Progressive authoring references
[ok] Architecture compare runtime and proof fixtures
[ok] Standalone schema validators
[ok] architecture renderer, schema, and example
[ok] workflow renderer, schema, and example
[ok] sequence renderer, schema, and example
[ok] dataflow renderer, schema, and example
[ok] lifecycle renderer, schema, and example

Archify is ready.
```

Mã thoát: `0` khi in `Archify is ready.`; `1` khi in `Archify is not ready: …` (Node quá cũ, thiếu file, hoặc runtime check hỏng). Nguồn: `commandDoctor()` trong `bin/archify.mjs`, dòng ~1348.

Sinh một artifact thật để mở bằng mắt:

```bash
node bin/archify.mjs demo /tmp/archify-demo
open /tmp/archify-demo/archify-demo.html   # Linux: xdg-open
```

Đã chạy: sinh `/tmp/archify-demo/archify-demo.html` (~698 KB, một file HTML tự chứa), rc `0`, và in gợi ý bước kế tiếp.

## Tắt kiểm tra cập nhật qua mạng

Archify có thể GET một manifest cố định chỉ để hiện lời nhắc; nó không bao giờ tải hay tự cài bản mới. Tắt hoàn toàn phần mạng và phần ghi trạng thái nhắc:

```bash
export ARCHIFY_UPDATE_CHECK_DISABLED=1
```

Kiểm chứng: `scripts/check-update.mjs:1637` thoát sớm ngay khi biến này bằng `1`.

## Hai lệnh dò nhanh khác

```bash
node bin/archify.mjs --help          # in usage, rc 0
node bin/archify.mjs bogus           # in "Unknown command" + usage, rc 2
```

`2` là mã thoát dùng-sai của Archify, không phải `1`. Ghi nhớ điều này trước khi viết wrapper script.
