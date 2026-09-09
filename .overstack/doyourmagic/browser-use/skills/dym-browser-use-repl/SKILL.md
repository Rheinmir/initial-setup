---
name: dym-browser-use-repl
disable-model-invocation: true
description: "Lái trình duyệt kiểu REPL có trạng thái qua browser-harness (CDP) — tab giữ nguyên giữa các lượt gọi CLI, mỗi lượt một hành động rồi quan sát. Dùng khi việc verify UI cần NHIỀU bước (đăng nhập → điều hướng → điền form → kiểm), khi script Playwright một-phát-ăn-ngay đã hỏng vài lần, hoặc khi cần chạm file:// và localhost mà claude-in-chrome chặn."
---

# dym-browser-use-repl

## When to use
- Việc cần **nhiều bước có điều kiện** — bước sau phụ thuộc thứ nhìn thấy ở bước trước.
  Script Playwright buộc phải viết mù toàn bộ kịch bản trước khi chạy; sai một chỗ là chạy lại
  từ đầu, mất cả login lẫn state.
- Đã viết `.mjs` verify 2–3 lần mà vẫn trượt phần tử → đổi sang REPL, xem trang thật rồi mới quyết.
- Cần chạm `file://` hoặc `localhost` (claude-in-chrome chặn 2 scheme này).

**KHÔNG dùng khi**: chỉ cần chụp một ảnh, hoặc chỉ đọc console một lần.
Đó là việc của `/playwright-verify` — một file `.mjs`, một lần chạy, xong vứt. Rẻ hơn.

## Số đo (máy user, 09/09/2026, cùng một trang `file://`)
| cách | thời gian một lượt | state giữa các lượt |
|---|---|---|
| Playwright script (`chromium.launch()` → goto → title → close) | **1.1–1.9s** (đo 3 lần; lần đầu cold-cache 3.38s) | mất sạch |
| browser-harness lượt đầu (khởi daemon + `new_tab` + screenshot) | ~2s | — |
| browser-harness lượt sau | **0.138s** | tab + cookie + scroll giữ nguyên |

## Steps
1. **Cài một lần** (yêu cầu Python ≥ 3.11 — `python3` mặc định của macOS là 3.9.6, sẽ trượt):
   ```bash
   python3.13 -m venv ~/.bh-venv && ~/.bh-venv/bin/pip install \
     "git+https://github.com/browser-use/browser-harness"
   ~/.bh-venv/bin/browser-harness --version   # 0.1.13 (đo 09/2026)
   ```
2. **Chuẩn bị một Chrome có CDP** — KHÔNG mượn Chrome của user (macOS sẽ bật hộp thoại xin
   phép remote-debugging và chiếm tab đang làm việc). Dựng riêng một Chrome for Testing:
   ```bash
   CH="$HOME/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
   "$CH" --remote-debugging-port=9333 --user-data-dir=/tmp/bh-prof --headless=new --no-first-run about:blank &
   ```
   Chưa có binary → `npx playwright install chromium` (dùng chung cache `~/Library/Caches/ms-playwright`).
3. **Mỗi hành động = một heredoc.** Helper đã import sẵn, daemon tự bám vào tab cũ:
   ```bash
   export BH="HOME=/tmp/bhh BU_CDP_URL=http://localhost:9333 $HOME/.bh-venv/bin/browser-harness"

   env $BH <<'PY'
   new_tab("http://localhost:3000/checkout")   # lượt ĐẦU dùng new_tab, không phải goto_url
   wait_for_load()
   print(page_info())
   PY

   env $BH <<'PY'
   print(js("[...document.querySelectorAll('button')].map(b=>b.innerText)"))
   PY
   ```
4. **Bấm bằng toạ độ đọc từ DOM, không từ pixel ảnh đã co**:
   ```python
   r = js("document.querySelector('#submit').getBoundingClientRect()")
   click_at_xy(r["x"] + r["width"]/2, r["y"] + r["height"]/2)
   ```
5. **Sau mỗi bước, moi lỗi ảnh chụp không thấy**:
   ```python
   errs = [e for e in drain_events() if e["method"] == "Runtime.exceptionThrown"
           or (e["method"] == "Runtime.consoleAPICalled" and e["params"].get("type") == "error")
           or e["method"] == "Network.loadingFailed"
           or (e["method"] == "Network.responseReceived" and e["params"]["response"]["status"] >= 400)]
   ```
6. **Dọn**: `pkill -f "remote-debugging-port=9333"`.

## API có thật (đọc từ `src/browser_harness/helpers.py`, v0.1.13)
`cdp` · `drain_events` · `goto_url` · `page_info` · `click_at_xy` · `type_text` · `fill_input` ·
`press_key` · `scroll` · `capture_screenshot` · `list_tabs` · `current_tab` · `activate_tab` ·
`switch_tab` · `new_tab` · `close_tab` · `ensure_real_tab` · `iframe_target` · `wait` ·
`wait_for_load` · `wait_for_element` · `wait_for_network_idle` · `js` · `dispatch_key` ·
`upload_file` · `http_get`

## Rules
- **`AF_UNIX path too long` nếu `$HOME` sâu.** Đo thật: đặt `HOME` vào scratchpad
  (`/private/tmp/claude-501/.../scratchpad/fakehome`) → `browser-harness: fatal: AF_UNIX path too long`,
  rc=1. Dùng `HOME=/tmp/bhh` (ngắn) là chạy. Socket daemon nằm dưới `$HOME`, giới hạn 104 ký tự của macOS.
- **`doctor --json` FAIL-OPEN: rc=0 kể cả khi `"healthy": false`.** Đo thật:
  `{"chrome_running": true, "daemon": {"alive": false, ...}, "healthy": false}` → rc=0.
  Đừng rẽ nhánh theo mã thoát — parse `.healthy` trong JSON.
- **Lượt đầu `new_tab(url)`, các lượt sau KHÔNG gọi lại `new_tab`** — daemon giữ tab; gọi lại là
  đẻ tab trùng.
- Bấm bằng toạ độ CDP xuyên được iframe / shadow DOM / cross-origin ở tầng compositor —
  đây là lý do họ chọn toạ độ làm mặc định thay vì selector.
- Không cài gói `browser-use` — chỉ `browser-harness` (4 dep). Xem Rules của hub.
- Chrome riêng, profile riêng. Không bao giờ bám vào Chrome cá nhân của user.
- Touch only what the task requires — no opportunistic changes.
