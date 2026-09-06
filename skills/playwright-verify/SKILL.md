---
name: playwright-verify
description: "Cài + dùng Playwright bằng standalone .mjs script (không qua npx playwright test / *.spec.ts) để verify code nhanh, một lần: chụp ảnh localhost/file://, đọc console/pageerror, đo getBoundingClientRect khi phần tử không thấy/không bấm được, auth bypass qua addCookies+addInitScript. Dùng khi user nói 'verify bằng playwright', 'chụp ảnh trang', 'test nhanh UI bằng script', 'claude-in-chrome bị chặn localhost', 'không click được / không thấy phần tử', hoặc invoke /playwright-verify. KHÁC uat-nonit-testcase (bộ test case UAT cho non-IT) và claude-in-chrome (extension, bị chặn localhost/file://) — đây là hướng dẫn CHUNG áp dụng mọi task."
---

# Skill: playwright-verify

Đúc kết từ GH#96 — công cụ verify RẺ (< 5s/lần, không LLM) và là cách DUY NHẤT tương tác
được với `localhost`/`file://` khi `claude-in-chrome` bị chặn 2 scheme này trên máy.

## When to use
- `claude-in-chrome` báo `Frame with ID 0 is showing error page` hoặc `Can't interact with
  browser-internal or unparseable URLs` trên `localhost:*` / `file://`.
- Cần chẩn đoán phần tử UI "không thấy" / "không bấm được" — ảnh chụp không đủ, cần số đo
  thật (`getBoundingClientRect`, `getComputedStyle`).
- Cần verify 1 giả thuyết code rồi vứt (không xứng tạo `*.spec.ts` + test runner).
- Cần test qua dev-login/session giả thay vì đăng nhập SSO thật mỗi lần.

## Steps
1. **Kiểm tra đã cài chưa** trước khi cài lại: `ls ~/Library/Caches/ms-playwright` (macOS) —
   binary cache dùng chung mọi project, không cần cài lại per-repo.
   - Chưa có: `pnpm add -D @playwright/test` (bỏ qua nếu project đã có sẵn trong
     `devDependencies`) rồi `npx playwright install chromium`.
   - `npx playwright install` tải binary từ CDN ngoài (`cdn.playwright.dev`) — sandbox/CI có
     allowlist mạng sẽ treo hoặc fail. Set timeout khi gọi tự động; nếu bị chặn, báo lỗi rõ
     thay vì để lệnh treo vô thời hạn.
2. **Viết 1 file `.mjs` chạy thẳng bằng `node`** (không qua `npx playwright test`) — nặng hơn
   cho việc verify-rồi-vứt:
   ```js
   import { chromium } from "@playwright/test"; // export chromium dùng được như package "playwright"

   const browser = await chromium.launch();
   const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
   page.on("console", m => console.log("[console]", m.type(), m.text()));
   page.on("pageerror", e => console.log("[pageerror]", e.message));

   await page.goto("http://localhost:3000/some-page", { waitUntil: "load" }); // KHÔNG "networkidle" — xem Rules #2
   await page.waitForTimeout(1500);
   await page.screenshot({ path: "/tmp/check.png", fullPage: true });

   await browser.close();
   ```
3. **Chạy từ đúng thư mục** (xem Rules #1), `node check.mjs`, đọc console/pageerror log +
   ảnh chụp. Dọn file `.mjs` sau khi xong nếu chạy trong 1 project cụ thể (không cần xoá gì
   khỏi git — script không nằm trong repo nếu chạy từ scratch dir).

## Rules
- **`import { chromium } from "@playwright/test"` phải chạy TỪ TRONG thư mục project** có
  `@playwright/test` trong `node_modules` — ESM resolve theo `cwd`, không theo vị trí file
  script. Script ở thư mục khác (vd `/tmp`) → `cp` vào project trước khi chạy, hoặc trỏ
  `NODE_PATH`.
- **`waitUntil: "networkidle"` TREO VÔ THỜI HẠN trên Next.js dev server** — HMR/webpack dev
  giữ 1 kết nối long-poll/websocket sống liên tục nên network không bao giờ "idle". Dùng
  `waitUntil: "load"` + `page.waitForTimeout(N)` cố định.
- **Auth bypass cho dev-login**: `context.addCookies([{url, name, value}])` (ưu tiên `url`
  thay vì `domain`+`path` riêng lẻ — tránh cookie không match) + `context.addInitScript(...)`
  set `localStorage` — set state TRƯỚC khi gọi `newPage()`, không phải sau.
- **1 `context` cho mỗi route độc lập** nếu app có logic "gặp 401 ở API phụ → tự xoá session
  toàn cục" — dùng lại 1 context cho nhiều navigation khiến lỗi route N hỏng lây route N+1.
- **Chẩn đoán "không thấy/không bấm được"**: đừng chỉ nhìn ảnh chụp — gọi
  `page.evaluate(() => el.getBoundingClientRect())` + `getComputedStyle(el)` lấy số đo thật;
  `locator.click()` tự báo lỗi rõ ("element is not visible") kèm log các bước thử lại, đọc
  log đó trước khi đoán nguyên nhân.
- File script standalone không vào git — chạy từ scratchpad, không commit vào repo đích.
- Touch only what the task requires — no opportunistic changes.
