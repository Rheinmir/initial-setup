# 02 — Quét anti-pattern bằng CLI

**Vì sao dùng:** chấm chất lượng design của code frontend một cách **tất định** — 61 luật, không LLM, không API key, chạy được trong pre-commit hoặc CI.
**Sinh ra cái gì:** danh sách finding ra **stderr** (hoặc JSON ra **stdout** với `--json`), cộng một **mã thoát** để tự động hoá rẽ nhánh.

---

## Chạy nhanh

```bash
npx impeccable detect src/                    # quét thư mục
npx impeccable detect index.html              # quét một file HTML
npx impeccable detect https://example.com     # quét URL (render bằng Puppeteer)
npx impeccable detect --json .                # JSON cho máy đọc
npx impeccable detect --no-config src/        # quét thô, bỏ mọi config/waiver của dự án
```

Dạng rút gọn cũng chạy: `npx impeccable src/`. `cli/bin/cli.js:23-30` coi một tham số là target khi nó bắt đầu bằng `-`, là URL, chứa `/`/`\`/`.`, hoặc là đường dẫn có thật; ngược lại nó bị coi là lệnh gõ sai:

```bash
npx impeccable frobnicate
# Unknown command: "frobnicate"
# rc = 1
```

Output thật trên một file bẩn:

```
probe/index.html
  [gray-on-color] text #808080 on bg gradient(#667eea, #764ba2)
    → Gray text looks washed out on colored backgrounds. ...
  [low-contrast] 1.1:1 (need 4.5:1) — text #808080 on #667eea
    → Text does not meet WCAG AA contrast requirements ...
  [overused-font] Primary font: inter
    → Inter, Roboto, Fraunces, Geist, Plus Jakarta Sans, and Space Grotesk are used on so many sites ...
  [skipped-heading] <h1> "Hi" followed by <h4> "Skipped heading" (missing h2)
  [ai-color-palette] Purple/violet accent colors detected

7 anti-patterns found.
```

## Mã thoát — đọc kỹ, đừng giả định 0/1

Từ `cli/engine/cli/main.mjs:492-495`:

```js
const exitCode = hadOperationalFailure ? 1 : (primary.length > 0 ? 2 : 0);
```

| rc | Nghĩa |
|---|---|
| **0** | Quét xong, **không** có finding chính (advisory vẫn có thể được liệt kê) |
| **1** | **Ít nhất một target không quét được** — lỗi vận hành, ưu tiên hơn rc 2 |
| **2** | Quét xong và **có** finding chính |

`rc == 2` là "có phát hiện", không phải "hỏng". Script nào coi `!= 0` là crash sẽ hiểu sai hoàn toàn. Đã kiểm chứng: file sạch → 0, file bẩn → 2, `--scope bogus` → 1.

### ⚠️ Bẫy: đường dẫn không tồn tại vẫn thoát 0

```bash
npx impeccable detect probe/nope.html
# Warning: cannot access probe/nope.html
# rc = 0
```

`cli/engine/cli/main.mjs:326` chỉ in cảnh báo rồi `continue`, **không** set `hadOperationalFailure`. Nghĩa là gõ sai đường dẫn trong CI = build xanh, quét đúng 0 file. Cách chặn: xác nhận target tồn tại trước khi gọi (xem `04-ci-integration.md`).

## Luồng output — và cái bẫy `npx`

Findings dạng người đọc là **diagnostics, ghi ra stderr**; `--json` ghi ra **stdout**. Đã đo trên cùng một lần quét:

| Cách gọi | stdout | stderr |
|---|---|---|
| `node node_modules/impeccable/cli/bin/cli.js detect ...` | 0 byte | 1733 byte |
| `npx impeccable detect ...` | 1731 byte | **0 byte** |

`npx` (npm 10.9.2) gộp stderr của tiến trình con vào stdout. Nên `npx impeccable detect src/ 2> findings.txt` sẽ tạo ra file **rỗng** — trái với gợi ý trong README. Muốn giữ tách luồng thì gọi thẳng binary local:

```bash
npm install --save-dev impeccable
./node_modules/.bin/impeccable detect src/ 2> findings.txt   # tách luồng đúng
```

## Cờ

Lấy từ `printUsage()` trong `cli/engine/cli/main.mjs:160-221`:

| Cờ | Tác dụng |
|---|---|
| `--json` | Kết quả JSON ra stdout (giữ cả finding advisory, mỗi cái có `"advisory": true`) |
| `--quiet` | Chỉ in dòng đếm cuối cùng |
| `--scope <name>` | Chỉ báo luật thuộc miền design đó. Hợp lệ: **`type`, `layout`** (phân cách bằng dấu phẩy) |
| `--viewport <WxH>` | Viewport cho quét URL, mặc định `1280x800`, ví dụ `--viewport 390x844` |
| `--no-config` | Bỏ config dự án, ignore, inline comment, `DESIGN.md` |
| `--no-inline-ignores` | Bỏ riêng phần comment `impeccable-disable*` trong file |
| `--no-design-system` | Không nạp `DESIGN.md` / `.impeccable/design.json` |
| `--no-advisory` | Bỏ hẳn finding advisory |
| `--help` | In usage, rc 0 |

Cờ đã khai tử, còn nhận nhưng **bị bỏ qua** kèm cảnh báo: `--fast`, `--gpt`, `--gemini`.

### ⚠️ Bẫy: `--scope` dạng tách rời nuốt mất target

```bash
npx impeccable detect --scope src/index.html
# Error: unknown --scope value(s): src/index.html. Valid scopes: type, layout
# rc = 1
```

Bộ parse lấy tham số kế tiếp làm giá trị (`main.mjs:253-266`). **Luôn viết dính:** `--scope=type`.

## Advisory: được báo, không bao giờ làm rớt

Một số luật là advisory: hiện ở khu riêng bị làm mờ, **không** tính vào số finding chính, **không** đổi mã thoát. Vậy nên một lần quét chỉ có advisory vẫn thoát 0 và không bao giờ chặn CI.

Chỉ có đúng **một** luật advisory: `em-dash-overuse` (đọc từ `ADVISORY_RULE_IDS`). Chạy thật trên một file bão hoà em-dash:

```
0 anti-patterns found.

── Advisory (not counted as failures) ──

/…/adv2.html
  [em-dash-overuse] 36 em-dashes in body text
    → Em-dash saturation in body copy is an AI cadence tell. Advisory only: ...

1 advisory note. Suppress with --no-advisory.
```

rc = **0** — đúng như thiết kế: chỉ advisory thì vẫn là một lần quét sạch.

Trong JSON, mỗi mục advisory mang cờ `"advisory": true` — lọc phía consumer nếu cần.

## Ba engine, chọn tự động theo target

| Target | Engine | Ghi chú |
|---|---|---|
| File `.html`/`.htm` | Phân tích tĩnh HTML/CSS | Theo được cả CSS link ngoài |
| File khác (CSS, JSX, TSX, ...) | Khớp regex | Không tính được cascade |
| `http(s)://`, `file://` | Puppeteer render thật | DOM đã render, computed style, layout thật |

`file:///đường/dẫn.html` đi qua **engine trình duyệt**, còn đường dẫn trần `./đường/dẫn.html` ở lại engine tĩnh — cùng một file, hai mức sâu khác nhau. Đã chạy thật cả hai đường trên cùng file.

Quét URL cần `puppeteer` (là `optionalDependencies`) và một bản Chrome. Bảo mật trình duyệt vẫn chặn đọc CSS cross-origin khi không có CORS.

### ⚠️ Bẫy: chạy từ bản clone chưa cài dependency

```
impeccable detect: DEGRADED - HTML parser modules unavailable (htmlparser2, css-select, css-tree, domutils).
Falling back to regex matching. Custom properties, selector matching and computed contrast are NOT evaluated;
findings are an undercount, not a clean bill of health.
```

Cùng một file: bản degraded báo **2** finding, bản đủ dependency báo **7**. Nếu bạn chạy CLI từ một checkout thay vì từ npm, phải `bun install`/`npm install` trước.

## Đọc theo pipe / hook

Khi stdin không phải TTY và không có target nào, CLI đọc stdin. Nó thử parse JSON và lấy `tool_input.file_path` (định dạng hook của agent); không phải JSON thì coi toàn bộ input là văn bản với tên `<stdin>`.

```bash
cat src/app.css | npx impeccable detect
```

## Giới hạn cần nói thẳng

Quét sạch là **bằng chứng, không phải chứng minh**. 61 luật là tất định và hẹp; chúng không thay thế việc mở trang ra nhìn ở các viewport thật. Xem `05-chat-commands.md` cho phần review có LLM (`/impeccable critique`, `/impeccable audit`).
