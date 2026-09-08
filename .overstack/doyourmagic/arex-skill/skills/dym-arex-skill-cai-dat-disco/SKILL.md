---
name: dym-arex-skill-cai-dat-disco
description: "Cài `disco` CLI. Không có disco thì không dùng được gì trong AREX-Skill — cả thư viện 1.000 repo skill lẫn 15 meta skill Creator đều chạy qua CLI này."
disable-model-invocation: true
---

# Skill: dym-arex-skill-cai-dat-disco — Cài `disco` CLI

**Vì sao dùng:** Không có `disco` thì không dùng được gì trong AREX-Skill — cả thư viện 1.000 repo skill lẫn 15 meta skill Creator đều chạy qua CLI này.
**Sinh ra cái gì:** Một lệnh `disco` global, thư mục cấu hình `~/.disco/agent/`, và ít nhất một provider model đã cấu hình.

---

## 0. Điều kiện tiên quyết (kiểm trước, đừng đoán)

```bash
node --version    # PHẢI >= 22.19.0
git --version     # cần cho `disco repo-skills install` (nó clone shallow)
```

`engines.node` trong `cli/package.json` là `">=22.19.0"`. Node 22.17.x **không đạt** — bản cài qua npm sẽ cảnh báo/chặn engine, còn bản cài qua installer curl thì tự chuẩn bị runtime Node riêng ở mức user.

## 1. Cách khuyến nghị — managed installer (macOS / Linux / WSL / Git Bash)

```bash
curl -fsSL https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.sh | sh
```

Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { irm https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.ps1 | iex }"
```

Installer đặt state release dưới `~/.disco/agent/install/`, **không** đè lệnh `disco` lạ đã có, **không** xoá settings/credentials/sessions/skills của bạn. Nếu nó bảo refresh `PATH` thì mở shell mới.

Kiểm chứng:

```bash
disco --version     # in số version rồi thoát 0
disco --help        # in bảng Commands/Options/Examples
```

Gỡ riêng phần installer quản lý:

```bash
~/.disco/agent/install/install-disco.sh --uninstall
```

## 2. Cách thay thế — package manager

```bash
npm  install -g --ignore-scripts @arex-skill/disco
pnpm add     -g --ignore-scripts @arex-skill/disco
bun  add     -g --ignore-scripts @arex-skill/disco
```

Cập nhật / gỡ đúng bằng manager đã cài:

```bash
npm update -g @arex-skill/disco   ;  npm uninstall -g @arex-skill/disco
pnpm update -g @arex-skill/disco  ;  pnpm remove -g @arex-skill/disco
bun update -g @arex-skill/disco   ;  bun uninstall -g @arex-skill/disco
```

`disco update self` cũng cập nhật được bản package-manager **khi** runtime xác định được global package root và ghi được vào đó; báo "not writable" thì quay lại lệnh của manager.

## 3. Cách build từ nguồn (khi cần sửa CLI, hoặc installer không dùng được)

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
bash scripts/build-from-source-link.sh
```

Nếu kẹt proxy HTTP(S): `NODE_USE_ENV_PROXY=1 bash scripts/build-from-source-link.sh`.

Script làm đúng 4 việc: `npm ci --include=dev --ignore-scripts` → `npm run build` → `npm link --ignore-scripts` → tự chạy `disco --version` và `disco --help` để smoke.

Nó **dừng với lỗi** (exit 1) nếu:
- không có `node`/`npm` trên PATH;
- build không tạo được `cli/dist/cli.js` executable;
- `<npm-global-prefix>/bin/disco` đã tồn tại nhưng **không** trỏ về checkout này → tự tay xoá/đổi tên lệnh `disco` cũ rồi chạy lại;
- link xong mà `disco` vẫn không có trên PATH → thêm `$(npm prefix --global)/bin` vào PATH.

Script này là **smoke build/link**, không phải cổng release. Cổng release là `npm run prepublishOnly` (xem `09-contributor-phat-trien-cli.md`).

## 4. Cấu hình provider model

Chọn một trong hai:

```bash
# (a) biến môi trường — đọc lúc chạy
export OPENAI_API_KEY=...        # hoặc ANTHROPIC_API_KEY / GEMINI_API_KEY
export OPENROUTER_API_KEY=...    # hoặc MISTRAL_API_KEY
```

```bash
# (b) đăng nhập tương tác: mở disco rồi gõ lệnh chat /login
disco
```

`/login` là **lệnh chat trong TUI**, không phải lệnh shell — xem `08-lenh-chat-trong-tui.md`. Chọn model ngay từ shell thì dùng cờ:

```bash
disco --provider openai --model gpt-4o-mini "..."
disco --model openai/gpt-4o "..."        # dạng provider/id, không cần --provider
disco --model sonnet:high "..."          # hậu tố :<thinking>
disco --list-models                      # liệt kê model khả dụng (có thể kèm chuỗi tìm kiếm)
```

## 5. Đường dẫn cần biết

| Thứ | Đường dẫn |
|---|---|
| Agent dir toàn cục | `~/.disco/agent/` (đổi bằng `DISCO_CODING_AGENT_DIR`) |
| Settings toàn cục | `~/.disco/agent/settings.json` |
| Auth | `~/.disco/agent/auth.json` |
| Override theo project | `<project>/.disco/settings.json` (các lệnh dùng cờ `-l`) |
| Thư viện repo skill sau khi cài | `~/.disco/agent/skills/repositories/` |

## Bước kế

`02-cai-thu-vien-skill.md` — cài bộ 1.000 repo skill và router.
