# 05 — Bằng chứng trình duyệt thật và vòng preview trực tiếp

**Vì sao dùng:** `deliver` chứng minh artifact qua được các kiểm tra tất định trên SVG/HTML. Nó **không** chứng minh trang đó hành xử đúng trong một trình duyệt thật. Đó là việc của `visual-check`. Còn `preview` là vòng lặp bàn phím khi bạn đang chỉnh JSON liên tục.

**Kết quả nhận được:** một biên lai JSON, một contact sheet HTML, và bốn ảnh PNG thật ở hai kích thước × hai chế độ màu — hoặc một server loopback tự nạp lại chỉ khi bản mới đã qua mọi cổng.

```bash
export A=~/.claude/skills/archify
```

## Bằng chứng trình duyệt: `visual-check`

Chạy trên **đúng file HTML đã giao**, không sửa và không render lại:

```bash
node $A/bin/archify.mjs visual-check out/workflow.html --json
```

Dạng người đọc (kết quả thật đã chạy trên macOS với Chrome cài sẵn):

```
automated browser evidence pass: /…/wf.html
visual-check containment pass; captures pass; perceptual visual review pending
receipt /…/wf.visual-check.json
contact sheet /…/wf.visual-check.html
```

### Sidecar sinh ra (quan sát trực tiếp trên đĩa)

Cạnh `wf.html`, sau một lần chạy:

```
wf.visual-check.json                  16.6K   biên lai máy đọc được
wf.visual-check.html                   1.8K   contact sheet mở bằng trình duyệt
wf.visual-check.1440x900.light.png   392.2K
wf.visual-check.1440x900.dark.png    413.7K
wf.visual-check.2048x1320.light.png  547.2K
wf.visual-check.2048x1320.dark.png   580.7K
```

### Mã thoát — đọc kỹ chỗ này

Từ hằng `EXIT` tại `bin/visual-check.mjs:24`:

| rc | Nghĩa |
|---|---|
| `0` | pass |
| `1` | fail — có vấn đề thật trong trình duyệt |
| `2` | **skipped** — không tìm thấy Chrome/Chromium |

`2` **không phải** pass. Từ `CONTRIBUTING.md`: *"A browser test that was skipped because Chrome was unavailable is **skipped**, not passed."* Một cổng CI coi `!= 1` là xanh sẽ âm thầm bỏ qua toàn bộ bằng chứng trình duyệt trên runner không có Chrome.

### Tìm Chrome

Thứ tự dò trong `bin/visual-check.mjs`:

1. Biến môi trường `ARCHIFY_CHROME` (nếu được đặt, dùng đúng nó, không dò tiếp).
2. Đường mặc định theo hệ: `/Applications/Google Chrome.app/…`, `/Applications/Chromium.app/…` trên macOS; `chrome.exe` dưới Program Files trên Windows; `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser` trên Linux.

```bash
export ARCHIFY_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
export ARCHIFY_CHROME_NO_SANDBOX=1   # chỉ trong container chạy bằng root
```

`ARCHIFY_CHROME_NO_SANDBOX=1` tắt sandbox của Chrome. Chỉ đặt trong CI container, đừng bao giờ đặt trên máy cá nhân.

### Ba tuyên bố tách rời

| Tuyên bố | Chứng minh bởi | Không chứng minh |
|---|---|---|
| Artifact qua kiểm tất định | `deliver` | Trang hành xử đúng trong trình duyệt |
| Hành vi có ràng buộc trong trình duyệt thật | `visual-check` | Thẩm mỹ, độ tinh |
| Review thị giác cảm quan | Người thật hoặc reviewer đọc được ảnh | — |

Báo cáo chúng **riêng biệt**. Một cái liếc mắt không có ràng buộc chỉ đủ để đỡ cho tuyên bố thứ ba. Chi tiết hợp đồng ở `references/delivery-contract.md`.

### Đừng chạy visual-check sau một deliver hỏng

`deliver` thất bại **bảo toàn** artifact tốt trước đó. Chạy `visual-check` lúc đó là đi soi bản cũ và tưởng bản mới đã xanh. Sửa chẩn đoán, deliver lại, rồi mới visual-check.

## Vòng lặp preview

```bash
node $A/bin/archify.mjs preview workflow candidate.json /tmp/workflow.html --quality showcase
```

Hành vi, đối chiếu `bin/preview.mjs`:

- Server chỉ bind **loopback**: `const loopbackHost = '127.0.0.1'` (dòng 13), `server.listen(0, loopbackHost, …)` (dòng 320) — cổng ngẫu nhiên, không lộ ra mạng.
- Theo dõi **đúng một** file JSON.
- Chỉ nạp lại sau khi bản ứng viên mới qua **mọi** cổng. Lưu file giữa chừng hoặc JSON hỏng thì sơ đồ tốt cuối cùng vẫn hiển thị.
- Dừng bằng Ctrl-C.
- **Không** thêm runtime nào vào HTML sinh ra.

Cho test hoặc khi bạn muốn tự mở URL:

```bash
node $A/bin/archify.mjs preview workflow candidate.json /tmp/workflow.html --no-open
```

**Đừng khởi động preview theo mặc định.** Nó là chế độ desktop chủ động; trong script tự động thì `validate` + `deliver` mới là đường đúng.

## Ngưỡng khung nhìn desktop

`SKILL.md` yêu cầu mở HTML thật ở **1440×900, 1600×1000, 1920×1080**, và thêm **2048×1320** khi bố cục nhắm màn hình lớn. Ở mỗi kích thước phải thoả:

```js
document.documentElement.scrollWidth  <= window.innerWidth
document.documentElement.scrollHeight <= window.innerHeight
```

Cách sửa khi tràn, **theo đúng thứ tự**: bỏ nội dung thật sự thừa, rồi nén khoảng cách — trước khi thu nhỏ node, nhãn, hay panel chính. Nếu ở khung lớn nhất còn một dải trống rõ rệt phía dưới, hãy phân bố lại toạ độ Y đã khai và tăng chiều cao viewBox tương ứng; **không** độn thêm chữ hay thẻ trang trí.

Bốn cách nguỵ tạo một lần pass, `SKILL.md` cấm thẳng: `overflow: hidden`, cắt nội dung, nhét một scroller riêng trong sơ đồ, kéo giãn chiều cao SVG, hoặc thu nhỏ chữ.
