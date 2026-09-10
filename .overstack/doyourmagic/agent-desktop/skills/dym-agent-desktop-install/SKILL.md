---
name: dym-agent-desktop-install
disable-model-invocation: true
description: "Cài agent-desktop (CLI computer-use macOS) có pin scope, kiểm quyền Accessibility/Screen Recording, xác minh binary chạy. Gọi khi cần điều khiển app desktop macOS mà chưa có binary, hoặc khi lệnh trả PERM_DENIED."
---

# dym-agent-desktop-install

## When to use
- Sắp dùng `agent-desktop` lần đầu trên máy này, hoặc CI macOS runner cần nó.
- Lệnh bất kỳ trả `PERM_DENIED` → quay lại đây kiểm quyền.
- KHÔNG dùng trên Linux/Windows: postinstall khai `SUPPORTED_PLATFORMS = ['darwin']` và
  sẽ bỏ qua; crate `windows`/`linux` là stub 76 dòng trả `PLATFORM_NOT_SUPPORTED`.

## Steps

1. **Cài có pin scope** — không để installer ghi vào `$HOME` thật:

```bash
S=./scratchpad/agent-desktop-probe && mkdir -p $S/{home,prefix}
HOME=$S/home npm install -g --prefix $S/prefix agent-desktop
AD=$S/prefix/bin/agent-desktop
```
Đo 2026-09-09: rc=0, ~4s, `$S/home` chỉ mọc thêm `.npm/` (cache) — không đụng gì khác.
`bin/` chứa `agent-desktop-darwin-arm64` (3.0M) + `agent-desktop-macos-helper` (498K).
Cài thật cho cả máy thì bỏ `--prefix` và `HOME=` — chỉ làm khi user đồng ý.

2. **Tách state ra khỏi `~/.agent-desktop`** — mọi snapshot/session/trace nằm dưới đây:

```bash
export AGENT_DESKTOP_HOME=$PWD/scratchpad/agent-desktop-state   # PHẢI tuyệt đối
```
Giá trị tương đối hoặc rỗng → `INVALID_ARGS` trước khi lệnh chạy. `status` in lại ở
`data.state_root`. Đường dẫn output tường minh (`screenshot --out`, `--trace <path>`)
KHÔNG bị dời gốc.

3. **Xác minh** — ba lệnh, đều phải rc=0:

```bash
$AD version       # {"version":"2.3","ok":true,...,"data":{"os":"macos","target":"aarch64","version":"0.8.5"}}
$AD permissions   # accessibility.state + screen_recording.state phải là "granted"
$AD status        # thêm state_root, session_id, supported_surfaces
```

4. **Nếu quyền chưa cấp**:

```bash
$AD permissions --request     # bật dialog hệ thống trong helper cô lập
```
Cấp cho **ứng dụng terminal đang chạy lệnh** (iTerm2/Terminal/VS Code), không phải cho
binary. Sau khi cấp phải **thoát hẳn và mở lại terminal** — TCC chỉ đọc lúc tiến trình
khởi động. Screenshot cần thêm Screen Recording.

5. **Gỡ**: xoá `$S` là xong (binary + state đều nằm trong đó). Bản cài toàn máy:
`npm uninstall -g agent-desktop` rồi `rm -rf ~/.agent-desktop`.

## Rules
- **Không chạy `npm install -g agent-desktop` trần** trong phiên agent — nó ghi vào prefix
  npm toàn cục của user. Luôn `--prefix` vào scratchpad trừ khi user bảo cài thật.
- Binary tải từ GitHub Releases lúc postinstall (`lahfir/agent-desktop`), có kiểm hash;
  máy không ra được mạng lúc install → cài hỏng, không có fallback build-from-source
  trong gói npm.
- `permissions` trả `automation.state: "unknown"` là bình thường — chỉ Accessibility và
  Screen Recording mới chặn thật.
- Bản đo: npm `agent-desktop@0.8.5`, 36 version từ 2026-02-23 → 2026-09-06 (đang phát
  triển nhanh). Pin version trong CI: `npm i -g agent-desktop@0.8.5`.
