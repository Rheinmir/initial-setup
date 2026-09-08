# 07 — Ghim & gác thư viện skill trong CI của **dự án bạn**

**Vì sao dùng:** Kết quả nghiên cứu chỉ tái lập được nếu **cùng một bộ skill**. Thư viện đổi âm thầm là kết quả cũ không giải thích được nữa.
**Sinh ra cái gì:** Một job CI fail khi commit thư viện lệch khỏi giá trị đã ghim, hoặc khi bản cài local bị drift.

> ⚠️ Repo AREX-Skill **không có `.github/workflows/` nào cả** (đã kiểm: không tìm thấy file CI nào). Nên không có pipeline nội bộ nào để copy — file dưới đây là ví dụ **viết mới, tối thiểu**, cho phía người dùng.

---

## 1. Nguyên liệu: hai tín hiệu kiểm được

| Lệnh | Ý nghĩa |
|---|---|
| `disco repo-skills status` | Exit `0` sạch · `1` có drift/issue · `2` sai cú pháp. Chạy **hoàn toàn offline**, không gọi GitHub |
| `disco repo-skills status \| grep '^Commit: '` | In `Commit: <sha đầy đủ> (<12 ký tự>)` — đây là thứ đem đi ghim |

`status` không kiểm HEAD remote. Muốn biết có bản mới thì phải chạy `update` (có mạng) — nên đừng đặt `update` trong job gác.

## 2. Ghim commit thư viện vào repo của bạn

```bash
# chạy một lần trên máy, sau khi `disco repo-skills install`
disco repo-skills status | sed -n 's/^Commit: \([0-9a-f]*\).*/\1/p' > .arex-skill-commit
git add .arex-skill-commit && git commit -m "chore: ghim commit thư viện AREX-Skill"
```

## 3. Script gác (tự chạy được cả ở local lẫn CI)

```bash
#!/usr/bin/env bash
# scripts/check-arex-skill.sh
set -euo pipefail

PINNED_FILE=".arex-skill-commit"

if ! command -v disco >/dev/null 2>&1; then
  echo "::error::disco chưa được cài" >&2
  exit 1
fi

# Cổng 1 — drift/toàn vẹn cục bộ. Exit 1 = có issue, exit 2 = sai cú pháp.
if ! status_out="$(disco repo-skills status)"; then
  rc=$?
  echo "$status_out"
  case "$rc" in
    1) echo "::error::thư viện repo-skills bị drift hoặc thiếu router" >&2 ;;
    2) echo "::error::lệnh repo-skills sai cú pháp" >&2 ;;
    *) echo "::error::repo-skills status thất bại (rc=$rc)" >&2 ;;
  esac
  exit "$rc"
fi
echo "$status_out"

# Cổng 2 — commit đúng bản đã ghim.
actual="$(printf '%s\n' "$status_out" | sed -n 's/^Commit: \([0-9a-f]*\).*/\1/p')"
pinned="$(tr -d '[:space:]' < "$PINNED_FILE")"

if [ -z "$actual" ]; then
  echo "::error::status không in ra commit — thư viện chưa cài?" >&2
  exit 1
fi

if [ "$actual" != "$pinned" ]; then
  echo "::error::commit thư viện lệch: ghim=$pinned thực tế=$actual" >&2
  echo "Cập nhật có chủ đích: disco repo-skills update && cập nhật lại $PINNED_FILE" >&2
  exit 1
fi

echo "OK: thư viện AREX-Skill khớp commit đã ghim ($pinned)"
```

```bash
chmod +x scripts/check-arex-skill.sh
./scripts/check-arex-skill.sh          # thử ở local trước khi đưa vào CI
```

## 4. Job GitHub Actions tối thiểu

```yaml
# .github/workflows/arex-skill-pin.yml — TRONG DỰ ÁN CỦA BẠN
name: AREX-Skill pin

on: [push, pull_request]

jobs:
  pin:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22.19.0'   # engines.node của @arex-skill/disco là >=22.19.0

      - name: Cài disco
        run: npm install -g --ignore-scripts @arex-skill/disco

      - name: Cài thư viện repo-skills
        run: disco repo-skills install     # cần git + mạng; runner ubuntu có sẵn git

      - name: Gác drift + commit ghim
        run: ./scripts/check-arex-skill.sh
```

## 5. Chạy chính DisCo trong CI (nếu thật sự cần)

```bash
export DISCO_OFFLINE=1        # tắt update check, thao tác mạng lúc khởi động
export ANTHROPIC_API_KEY=...  # hoặc OPENAI_API_KEY / GEMINI_API_KEY

disco --researcher --no-session --mode json \
  -p "<task cụ thể, kiểm chứng được>" > events.jsonl
```

Nhớ hai điều:
- **`DISCO_OFFLINE=1` chặn luôn `repo-skills install/update`** — nó fail có chủ đích với thông báo rõ. Cài thư viện **trước** khi bật offline.
- **`exit 0` của print mode không đảm bảo task đúng.** Nó chỉ nói phiên agent kết thúc không lỗi (exit 1 khi message cuối có `stopReason` là `error`/`aborted`). Muốn gác chất lượng thì kiểm sản phẩm agent tạo ra, đừng tin exit code.
- Một job gọi LLM là **có tính phí và không tất định** — đừng đặt nó ở đường gác bắt buộc của mọi PR.

## 6. Biến môi trường hữu ích cho CI

| Biến | Tác dụng |
|---|---|
| `DISCO_OFFLINE` | Tắt thao tác mạng lúc khởi động, update check, thao tác package |
| `DISCO_SKIP_VERSION_CHECK` | Chỉ tắt việc hỏi npm registry xem có bản mới |
| `DISCO_CODING_AGENT_DIR` | Đổi agent dir (mặc định `~/.disco/agent`) — hữu ích để cache theo job |
| `DISCO_NO_SPLASH` | Tắt animation khởi động |
| `DISCO_CODING_AGENT_SESSION_DIR` | Đổi nơi lưu session |

## Bước kế

`08-lenh-chat-trong-tui.md` — các lệnh **chỉ gõ trong TUI**, đừng dán vào shell.
