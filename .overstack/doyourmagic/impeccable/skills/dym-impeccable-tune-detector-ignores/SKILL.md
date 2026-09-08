---
name: dym-impeccable-tune-detector-ignores
description: "Dập false positive: ignore của detector. giữ detect sạch mà không phải tắt hẳn luật — font thương hiệu, thư mục legacy, một file demo cố tình phá luật."
disable-model-invocation: true
---

# Skill: dym-impeccable-tune-detector-ignores — Dập false positive: ignore của detector

**Vì sao dùng:** giữ `detect` sạch mà không phải tắt hẳn luật — font thương hiệu, thư mục legacy, một file demo cố tình phá luật.
**Sinh ra cái gì:** mục `detector` trong `.impeccable/config.json` (chung, commit) hoặc `.impeccable/config.local.json` (per-dev, gitignore), hoặc comment inline đi theo file.

---

## Ba tầng waiver, chọn đúng tầng

| Tầng | Phạm vi | Ghi ở đâu | Dùng khi |
|---|---|---|---|
| Inline comment | Một file hoặc một dòng | Ngay trong file nguồn | Trường hợp cá biệt cần lý do đứng cạnh code |
| `config.json` (shared) | Cả repo, cả team | `.impeccable/config.json`, **commit** | Quyết định của dự án: font brand, thư mục legacy |
| `config.local.json` (local) | Chỉ máy bạn | `.impeccable/config.local.json`, **gitignore** | Thử nghiệm cá nhân, không ép lên team |

`detect` mặc định tôn trọng cả ba. `--no-config` tắt hết; `--no-inline-ignores` chỉ tắt tầng inline.

## Lệnh `impeccable ignores`

```bash
npx impeccable ignores list                    # xem merged / shared / local
npx impeccable ignores add-rule bounce-easing  # tắt hẳn một luật
npx impeccable ignores add-file "src/legacy/**"
npx impeccable ignores add-value overused-font Inter --reason "Brand font"
npx impeccable ignores add-value design-system-color "*" --file "src/demo.css"
npx impeccable ignores remove-value overused-font Inter
npx impeccable ignores clear                   # xoá ignore trong scope đang chọn
```

Đủ action (từ `cli/bin/commands/ignores.mjs:33-62`): `list`, `add-rule`, `add-file`, `add-value`, `remove-rule`, `remove-file`, `remove-value`, `clear`.

Cờ scope: `--shared` (mặc định) · `--local` · `--all` (chỉ cho `remove-*` và `clear`). Cờ giá trị: `--file <glob>` để giới hạn một `add-value`/`remove-value` vào một glob, `--reason <text>` để ghi kèm lý do.

`ignores` cũng nhận tên số ít `ignore` (`cli/bin/cli.js:70`).

### Vòng lặp thật, đã chạy

```bash
$ npx impeccable detect --quiet index.html
7 anti-patterns found.        # rc 2

$ npx impeccable ignores add-value overused-font Inter --reason "Brand font"
Added overused-font=inter to shared detector ignoreValues (.impeccable/config.json).

$ npx impeccable detect --quiet index.html
6 anti-patterns found.        # rc 2 — đúng 1 finding bị dập
```

Chú ý: giá trị được **chuẩn hoá về chữ thường** (`Inter` → `inter`) khi ghi vào config.

File sinh ra:

```json
{
  "detector": {
    "ignoreRules": [],
    "ignoreFiles": ["legacy/**"],
    "ignoreValues": [
      {
        "rule": "overused-font",
        "value": "inter",
        "createdAt": "2026-09-03T16:22:01.694Z",
        "reason": "Brand font"
      }
    ]
  }
}
```

`ignores list` in ba khối — Merged, Shared, Local — cộng trạng thái `designSystem`:

```
Impeccable detector ignores
  shared file: .impeccable/config.json
  local file:  .impeccable/config.local.json

Merged:
  ignoreRules:  (none)
  ignoreFiles:  (none)
  ignoreValues: (none)
  designSystem: enabled
...
```

## Inline ignore: waiver đi theo file

```html
<!-- impeccable-disable overused-font -- exported brand doc -->
```
```css
.brand { font-family: Inter } /* impeccable-disable-line overused-font */
```
```js
// impeccable-disable-next-line bounce-easing: intentional bounce
```

- `impeccable-disable` áp cho **cả file**; `-line` / `-next-line` chỉ một dòng.
- Liệt kê một hoặc nhiều rule id, phân cách bằng dấu phẩy; bỏ trống hoặc `*` là tất cả.
- Marker chạy trong mọi cú pháp comment.

Đã chạy thật, thêm một dòng vào `<style>`:

```
/* impeccable-disable ai-color-palette,bounce-easing -- brand */

6 anti-patterns found          → 5 anti-patterns found
--no-inline-ignores            → 5 quay lại 6
```

## Cấu hình đầy đủ trong `.impeccable/config.json`

Đây là file config **thật** mà chính repo Impeccable commit — mẫu tốt hơn tài liệu:

```json
{
  "detector": {
    "ignoreRules": [],
    "ignoreFiles": [
      "tests/fixtures/**",
      "tests/framework-fixtures/**",
      "tests/detect-antipatterns.test.js"
    ],
    "ignoreValues": [
      {
        "rule": "design-system-font-size",
        "value": "*",
        "files": ["skill/scripts/live-browser.js"],
        "createdAt": "2026-07-17T00:00:00.000Z",
        "reason": "Live overlay chrome is injected over arbitrary host pages and builds a self-contained UI with its own small type scale; DESIGN.md's ramp describes the impeccable website, not this widget"
      }
    ]
  },
  "hook": {
    "enabled": true,
    "limits": { "maxFindings": 5, "maxChars": 8000 }
  }
}
```

Ba điều rút ra:

1. `ignoreValues[].files` cho phép tắt một luật **chỉ trong vài file**, thay vì tắt toàn repo — dạng waiver hẹp nhất mà vẫn commit được.
2. `reason` được dùng nghiêm túc, không phải trang trí: nó nói *vì sao* luật không áp, để lần review sau không phải đoán.
3. Khoá `detector` dùng chung cho cả `npx impeccable detect` **và** hook design. Khoá `hook` chỉ ảnh hưởng hook tự động.

## Có nên `add-rule` không?

`add-rule <id>` tắt luật trên toàn repo. Trước khi làm, thử hai bậc hẹp hơn:

1. `add-value <rule> <value>` — chỉ dập đúng giá trị đang gây ồn (ví dụ đúng font brand), luật vẫn bắt các vi phạm khác.
2. `add-value <rule> "*" --file "<glob>"` — tắt luật trong một vùng, giữ nguyên nơi khác.

`add-value <rule> "*"` không kèm `--file` bị **từ chối** (`hook-admin.mjs:17`): hoặc giới hạn phạm vi, hoặc dùng `ignore-rule` cho tường minh.

## Bên cạnh CLI: hook-admin

Bản cài skill có script tương đương, thao tác cùng file config, dùng được từ trong chat của agent:

```bash
node .claude/skills/impeccable/scripts/hook-admin.mjs status
node .claude/skills/impeccable/scripts/hook-admin.mjs ignore-rule overused-font --all-values
node .claude/skills/impeccable/scripts/hook-admin.mjs ignore-file "src/legacy/**" --local
node .claude/skills/impeccable/scripts/hook-admin.mjs ignore-value overused-font Inter
node .claude/skills/impeccable/scripts/hook-admin.mjs reset
```
