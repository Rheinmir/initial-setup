# 01 — Cài đặt và chứng minh nó chạy

**Vì sao dùng:** Diagram Design là một *plugin/agent-skill*, không phải package npm hay pypi — không có `npm install`, không có `pip install`, không có binary. Cài sai đường là skill không bao giờ được nạp và bạn sẽ ngồi chờ một cái gì đó không tồn tại.

**File này sinh ra gì:** một bản cài Diagram Design mà agent của bạn nạp được, cộng với ba bằng chứng chạy thật (gallery mở được, script trong skill chạy được, doctor báo cáo được).

---

## 0. Cần gì trước

| Thứ | Bắt buộc? | Ghi chú đã kiểm chứng |
|---|---|---|
| Python **3.10+** | Bắt buộc cho `/doctor` | `references/doctor.md` §"Required checks" mục 1 — dưới 3.10 là `fail`. Nhưng xem cảnh báo ở §4 bên dưới: các script trong skill **vẫn chạy được trên 3.9.6**. |
| Playwright + Chromium | Chỉ cần khi xuất PNG | `pip install playwright && playwright install chromium` — chuỗi lệnh này lấy nguyên văn từ `references/doctor.md` và `references/export.md:65-66`. |
| Node/npm | Không cần | Chỉ dùng bởi CI của chính repo (`npx @anthropic-ai/claude-code plugin validate`), không phải bởi người dùng. |

Không có bước build. Không có `node_modules`. Toàn bộ "sản phẩm" là file Markdown + HTML tĩnh + 3 script Python thuần (không thư viện ngoài).

---

## 1. Cài theo host (chọn đúng một)

Các lệnh `/plugin ...` gõ **trong khung chat**, các lệnh `codex`/`droid`/`pi` gõ **trong terminal**.

### Claude Code — chat

```text
/plugin marketplace add cathrynlavery/diagram-design
/plugin install diagram-design@diagram-design
```

Sau đó bật cập nhật **một lần**: gõ `/plugin` → **Marketplaces** → chọn **diagram-design** → **Enable auto-update**. Claude Code mặc định tắt auto-update cho marketplace bên thứ ba, nên bỏ bước này là bạn đứng yên ở phiên bản đã cài. Gõ `/reload-plugins` khi được nhắc.

### Codex — shell

```bash
codex plugin marketplace add cathrynlavery/diagram-design
codex plugin add diagram-design@diagram-design
# lấy bản mới ngay, không chờ khởi động phiên sau:
codex plugin marketplace upgrade diagram-design
```

### Factory Droid — shell

```bash
droid plugin marketplace add https://github.com/cathrynlavery/diagram-design
droid plugin install diagram-design@diagram-design --scope user
# cập nhật (Droid bám commit, không bám version trong manifest):
droid plugin marketplace update diagram-design
droid plugin update diagram-design@diagram-design --scope user
```

### Pi — shell

```bash
pi install https://github.com/cathrynlavery/diagram-design
pi update --extensions   # Pi không tự refresh; phải gọi tay
```

Trong phiên Pi đang mở thì gõ `/reload`. Pi nạp thêm 4 prompt template `/export-diagram`, `/import-mermaid`, `/profile`, `/doctor` từ thư mục `prompts/`.

### Kiro — nhập URL thư mục con

```text
https://github.com/cathrynlavery/diagram-design/tree/main/skills/diagram-design
```

Kiro **copy** vào `.kiro/skills/` (workspace) hoặc `~/.kiro/skills/` (global) — muốn cập nhật thì nhập lại URL.

### OpenCode và mọi host Agent-Skills khác — symlink

```bash
git clone git@github.com:cathrynlavery/diagram-design.git ~/code/diagram-design
ln -s ~/code/diagram-design/skills/diagram-design ~/.config/opencode/skills/diagram-design
```

---

## 2. Cài kiểu "sửa được" (editable) — chọn khi bạn muốn tự sửa `style-guide.md`

Bản cài qua marketplace bị **ghi đè khi cập nhật**. Nếu bạn định sửa trực tiếp `references/style-guide.md` trong bản cài, hãy clone rồi symlink:

```bash
git clone git@github.com:cathrynlavery/diagram-design.git ~/code/diagram-design

# Claude Code
ln -s ~/code/diagram-design/skills/diagram-design ~/.claude/skills/diagram-design

# Pi
pi install ~/code/diagram-design

# các host Agent-Skills khác — chỉ tạo root nào bạn thực sự dùng
mkdir -p ~/.agents/skills ~/.cursor/skills ~/.cline/skills ~/.kiro/skills ~/.config/opencode/skills
ln -s ~/code/diagram-design/skills/diagram-design ~/.agents/skills/diagram-design
ln -s ~/code/diagram-design/skills/diagram-design ~/.cursor/skills/diagram-design
```

**Lưu ý quan trọng:** ngay cả bản cài marketplace cũng không mất brand của bạn nếu bạn dùng **profile** (`~/.diagram-design/profiles/`) hoặc **marker dự án** (`.diagram-design`) — xem `02-brand-onboarding-and-profiles.md`. Editable install chỉ cần khi bạn cố tình sửa working copy.

---

## 3. Chứng minh nó chạy — 3 bằng chứng, không đoán

### 3.1 Gallery mở được (không cần cài gì)

```bash
open  ~/code/diagram-design/skills/diagram-design/assets/index.html   # macOS
xdg-open ~/code/diagram-design/skills/diagram-design/assets/index.html # Linux
```

Kỳ vọng: một trang HTML tự chứa hiển thị đủ **39 loại sơ đồ**. Không cần server, không cần mạng (trừ font Google).

### 3.2 Script trong skill chạy được — chạy thật trên fixture

```bash
cd ~/code/diagram-design
python3 skills/diagram-design/scripts/drawio_extract.py scripts/fixtures/sample-architecture.drawio | head -12
python3 skills/diagram-design/scripts/self_check.py skills/diagram-design/assets/example-architecture.html
```

Kỳ vọng (đã chạy thật, output nguyên văn):

```text
# draw.io IR — sample\-architecture\.drawio
1 page(s): [0] Platform (12n/8e)
...
- budget: nodes OVER (max 9), edges ok (max 12)
```

```text
OK skills/diagram-design/assets/example-architecture.html
```

### 3.3 Doctor báo cáo được — chat

```text
/diagram-design:doctor
/diagram-design:doctor --strict --json
```

Ở Pi / Factory Droid thì gõ `/doctor`. Đây là lệnh **chat**, không phải shell — không có `bin/doctor` để gọi.

Doctor chạy **read-only**: không cài gói, không sửa file, không chạy lệnh git phá hoại (`references/doctor.md` §"Safety and behavior rules"). Nó chạy ở một trong hai chế độ:

- **Installed-skill mode** (mặc định) — chỉ kiểm runtime + bản cài. Thiếu script maintainer **không** phải lỗi.
- **Maintainer-checkout mode** — chỉ bật khi thư mục gốc có đủ `CONTRIBUTING.md` + `.github/workflows/ci.yml` + `scripts/verify-plugin-package.py`. Lúc đó mới kiểm 5 script và 9 file routing.

Định dạng output cố định:

```text
Doctor summary: <PASS|WARN|FAIL> (<n> pass, <n> warn, <n> fail)
[PASS] Python 3.11.9 found at /usr/bin/python3
[WARN] Playwright not installed ...
```

`--json` phụ thêm object có `status`, `counts`, `checks[]`, `timestamp`.

---

## 4. Hai cái bẫy đã tự vấp phải (đo trên máy thật, không suy đoán)

### Bẫy 1 — macOS mặc định là Python 3.9, doctor sẽ báo FAIL

Trên máy test: `/usr/bin/python3` là **3.9.6**. Doctor trả về đúng như thiết kế:

```text
Doctor summary: FAIL (3 pass, 1 warn, 1 fail)
[FAIL] Python runtime: Python 3.9.6 found via python3 at /usr/bin/python3; Diagram Design requires Python >= 3.10.
```

Nhưng — và đây mới là điều README không nói — **cả ba script trong skill vẫn chạy xanh trên 3.9.6**: `drawio_extract.py`, `mermaid_extract.py`, `self_check.py` đều rc=0. Ngưỡng 3.10 là ngưỡng *khai báo* trong `references/doctor.md`, không phải ngưỡng *kỹ thuật* của đường import/export. Cách sửa sạch nhất là trỏ `python3` sang Homebrew (`/opt/homebrew/bin/python3`) chứ đừng bỏ qua doctor.

### Bẫy 2 — doctor báo "Playwright không có" DÙ Playwright đã cài

Đo được trên máy test:

```bash
$ python3 -c "import importlib.metadata as m; print(m.version('playwright'))"
1.58.0
$ python3 -c "from playwright.sync_api import sync_playwright; print('sync_api import ok')"
sync_api import ok
```

Playwright **có thật**, `sync_api` import được. Vậy mà doctor vẫn in:

```text
[WARN] Playwright PNG export readiness: Playwright package is not available in the active Python interpreter.
```

Nguyên nhân, đọc thẳng trong mã: `scripts/verify-doctor.py:158` dò bằng

```python
[python_cmd, "-c", "import playwright; print(playwright.__version__)"]
```

nhưng package `playwright` **không có thuộc tính `__version__`** — lệnh này raise `AttributeError` và bị hiểu nhầm là "chưa cài".

```bash
$ python3 -c "import playwright; print(playwright.__version__)"
AttributeError: module 'playwright' has no attribute '__version__'
```

Hệ quả thực tế: **đừng tin cảnh báo Playwright của doctor**. Kiểm bằng tay bằng `importlib.metadata` như trên. Xuất PNG vẫn chạy bình thường.

---

## 5. Xong bước này khi

- [ ] Gallery `assets/index.html` mở ra thấy đủ 39 sơ đồ.
- [ ] `self_check.py` trên một example bất kỳ in `OK` và rc=0.
- [ ] `/diagram-design:doctor` in được summary (kể cả FAIL — quan trọng là nó *chạy*).
- [ ] Bạn biết `python3` của mình là bản nào, và đã quyết định sửa hay chấp nhận.

**Tiếp theo:** `02-brand-onboarding-and-profiles.md` — vì sơ đồ đầu tiên sẽ bị chặn bởi cổng style-guide nếu bạn chưa onboard brand.
