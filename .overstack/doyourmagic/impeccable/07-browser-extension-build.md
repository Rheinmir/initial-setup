# 07 — Build extension trình duyệt

**Vì sao dùng:** chạy đúng 61 luật detector trên **bất kỳ trang web nào đang mở**, không cần checkout code — hữu ích để soi trang production, trang staging, hoặc sản phẩm của đối thủ.
**Sinh ra cái gì:** `dist/extension.zip` (Chrome Web Store) và `dist/extension-firefox.zip` (AMO), cộng thư mục `extension/` load-unpacked được.

---

## Build

```bash
cd impeccable
bun install
bun run build:browser      # sinh cli/engine/detect-antipatterns-browser.js
bun run build:extension    # nhúng detector vào extension/ rồi đóng gói
```

Output thật:

```
$ bun run build:browser
Generated cli/engine/detect-antipatterns-browser.js (412.3 KB)

$ bun run build:extension
Generated extension/detector/detect.js (412.2 KB)
Generated extension/detector/antipatterns.json (61 rules)
Packaged dist/extension.zip (183.4 KB)
Staged dist/extension-firefox/ (Firefox manifest)
Packaged dist/extension-firefox.zip (183.5 KB)
```

Chạy `build:extension` mà chưa `build:browser` thì detector nhúng vào extension sẽ là bản **cũ**. Luôn chạy theo thứ tự đó khi vừa sửa luật.

`scripts/build-extension.js` làm ba việc: nhúng detector bản browser vào `extension/detector/detect.js`, đổ registry luật ra `extension/detector/antipatterns.json`, rồi zip hai lần — một cho Chrome (manifest giữ nguyên) và một cho Firefox (dựng lại manifest trong `dist/extension-firefox/` rồi mới zip cho AMO).

Cả `extension/detector/` lẫn `cli/engine/detect-antipatterns-browser.js` đều nằm trong **cổng generated-output** của CI, nên phải commit sau khi build — xem `06`.

## Load unpacked để thử

**Chrome / Edge:**
1. Mở `chrome://extensions`
2. Bật **Developer mode**
3. **Load unpacked** → chọn thư mục `extension/` (không phải file zip)

**Firefox:**
1. Mở `about:debugging#/runtime/this-firefox`
2. **Load Temporary Add-on** → chọn `dist/extension-firefox/manifest.json`

Rồi mở một trang bất kỳ và bấm icon Impeccable. Extension cũng gắn thêm một panel trong DevTools (`devtools_page` trong manifest).

## Extension xin quyền gì

Từ `extension/manifest.json` (MV3, phiên bản 1.3.3):

| Quyền | Vì sao cần |
|---|---|
| `activeTab` | Chạy detector trên tab đang xem |
| `scripting` | Inject `detector/detect.js` vào trang |
| `storage` | Nhớ lựa chọn của người dùng |
| `webNavigation` | Biết khi trang điều hướng để quét lại |
| `host_permissions: ["<all_urls>"]` | Cho phép quét mọi trang |

`<all_urls>` là quyền rộng. Nếu bạn phân phối bản build này trong nội bộ, cân nhắc siết `host_permissions` xuống đúng domain của mình trước khi đóng gói.

## Lint như CI làm

CI chạy web-ext lint trên bản staging Firefox (`.github/workflows/ci.yml:105-111`):

```bash
npx --yes web-ext@10 lint --source-dir dist/extension-firefox
```

Fail khi có lỗi mức AMO. Cảnh báo về style `innerHTML` trong renderer của panel là **không chặn** và cố ý không nâng thành lỗi.

## Extension khác CLI ở đâu

| | CLI (`impeccable detect`) | Extension |
|---|---|---|
| Đầu vào | File, thư mục, URL | Trang đang mở trong tab |
| Engine | Tĩnh HTML/CSS · regex · Puppeteer | DOM sống của tab |
| Mã thoát | Có (0/1/2) — tự động hoá được | Không — chỉ xem bằng mắt |
| Config dự án | Đọc `.impeccable/config.json`, inline ignore, `DESIGN.md` | Không có bối cảnh dự án |
| Hợp cho | CI, pre-commit, quét theo lô | Khảo sát nhanh trang đã deploy |

Cần một cổng chặn tự động hoá được thì dùng CLI (`02` và `04`). Extension để nhìn, không để gác.

## Icon và ảnh quảng bá

```bash
node scripts/generate-extension-icons.js
node scripts/generate-promo-tile.js
```

Nội dung listing store nằm ở `extension/STORE_LISTING.md`.
