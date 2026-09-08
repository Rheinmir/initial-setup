---
name: dym-diagram-design-selfcheck-and-your-ci
description: "Tự kiểm output và khoá nó bằng CI của BẠN. sơ đồ do agent sinh ra là HTML tự do — không có compiler nào bắt lỗi. self_check.py là cổng tất định, 0-token, không phụ thuộc ngoài được ship bên trong skill để chính agent tự kiểm sản phẩm của mình. Đây là thứ biến "tr"
disable-model-invocation: true
---

# Skill: dym-diagram-design-selfcheck-and-your-ci — Tự kiểm output và khoá nó bằng CI của BẠN

**Vì sao dùng:** sơ đồ do agent sinh ra là HTML tự do — không có compiler nào bắt lỗi. `self_check.py` là cổng **tất định, 0-token, không phụ thuộc ngoài** được ship **bên trong** skill để chính agent tự kiểm sản phẩm của mình. Đây là thứ biến "trông có vẻ ổn" thành "đã kiểm".

**File này sinh ra gì:** một lệnh gate chạy được ở local, cộng một GitHub Actions workflow tối thiểu cho **repo của bạn**.

> **Toàn bộ file này là lệnh shell.**

---

## 1. `self_check.py` — chữ ký và mã thoát

```text
python3 <skill-dir>/scripts/self_check.py <file.html> [<file.html> ...]
```

Nhận **nhiều file** (`nargs="+"`). Không có cờ nào khác.

| Tình huống | rc | stdout |
|---|---|---|
| Mọi file sạch | `0` | `OK <path>` mỗi file |
| Có ít nhất một file lỗi | `1` | `FAIL <path>` + danh sách gạch đầu dòng |

Đã đo bằng chạy thật: `OK` → rc=0, `FAIL` → rc=1. Đây là quy ước 0/1 quen thuộc — **khác** hai extractor ở `04` (0/2).

Script **không có thư viện ngoài** — chỉ stdlib (`argparse`, `re`, `html.parser`, `pathlib`). Chạy được ngay cả trên Python 3.9.6 (đã đo), dù `references/doctor.md` khai 3.10+.

---

## 2. Nó kiểm gì

Docstring khai ba nhóm; danh sách dưới đây lấy từ chính các thông điệp lỗi trong mã.

### 2.1 Hợp đồng SVG accessible

- File sơ đồ phải có ít nhất một SVG accessible (không `aria-hidden`).
- Mỗi SVG cần `role="img"`.
- `<title>` phải là **con đầu tiên** của SVG.
- `<title>` và `<desc>` phải **không rỗng**.
- ID của title/desc phải có **tiền tố theo sơ đồ**, không bao giờ trần — đây là thứ cho phép nhiều SVG inline chung một trang mà figure này không "mượn" tên của figure kia.
- `aria-labelledby` phải trỏ **title trước, desc sau**, đúng thứ tự.

### 2.2 An toàn một-file

- Không tham chiếu từ xa, **trừ** đúng một stylesheet Google Fonts `/css2` đã duyệt.
- Không URL thực thi được (`javascript:` …).
- Không data-URL phi ảnh.
- **Nhiều nhất một `<script>`**, và script đó phải mang đúng thuộc tính `data-diagram-co…` chính tắc và **khớp verbatim** controller trong `template-motion.html`.

### 2.3 Hợp đồng motion (chỉ khi file có markup motion)

- Đúng **một** `data-motion-root`.
- `data-motion-mode` phải nằm trong tập mode hợp lệ.
- `data-step-count` phải là số nguyên thập phân ASCII; số bước ngữ nghĩa nằm trong khoảng `<min>..8`.
- **Ngân sách 12 item** cho motion.
- Item ngữ nghĩa cần `aria-label` không-phải-tên-màu; item trang trí cần `aria-hidden="true"` và không focus được.
- Không item nào bị ẩn trong source — **fallback phải là khung tĩnh đầy đủ**.
- Các bước ngữ nghĩa phải **liên tục** `1..N`.

Docstring nói rõ đây là **tập con chưng cất** của các cổng repo (`lint-skin.py`, `verify-motion.py`); repo mới là nơi có thẩm quyền cho đóng góp vào chính repo (xem `07`).

---

## 3. Chạy thật — cả đường xanh lẫn đường đỏ

### Xanh

```bash
$ python3 "$SKILL_DIR/scripts/self_check.py" skills/diagram-design/assets/example-architecture.html
OK skills/diagram-design/assets/example-architecture.html
$ echo $?
0
```

### Đỏ — chĩa vào một file không phải sơ đồ để xem nó bắt gì

```bash
$ python3 "$SKILL_DIR/scripts/self_check.py" README.md
FAIL README.md
  - remote reference on <a>: https://trendshift.io/repositories/26141?utm_source=repository-badge&utm_medium=
  - remote reference on <img>: https://trendshift.io/api/badge/repositories/26141
  - svg 1 needs role=img
  - svg 1 title must be its first child
  - svg 1 needs non-empty title and desc
$ echo $?
1
```

Đọc được ngay: mỗi dòng là một lỗi cụ thể, có định danh (`svg 1`), có phạm trù. Không có "something went wrong".

---

## 4. Gate ở local — một dòng

Đặt vào script quen tay của bạn:

```bash
#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/diagram-design}"

# mọi sơ đồ trong repo, một lượt
find docs -name '*.html' -print0 | xargs -0 python3 "$SKILL_DIR/scripts/self_check.py"
```

`xargs` giữ nguyên rc — một file đỏ là cả lệnh đỏ. Không cần vòng lặp.

Muốn báo cáo đầy đủ thay vì dừng ở file đầu tiên thì cứ truyền hết vào một lần gọi như trên: script duyệt **toàn bộ** danh sách rồi mới trả rc, chứ không thoát sớm.

---

## 5. CI cho repo của BẠN — bản viết mới, tối thiểu

Đây **không** phải CI của Diagram Design. CI của họ (`.github/workflows/ci.yml`) có gần 50 gate, ma trận 3 OS × 2 phiên bản Python, Playwright ghim phiên bản, và oracle so pixel — nó build và test *chính Diagram Design*, không phải cách bạn tích hợp Diagram Design. Sao chép nó vào repo bạn là vô nghĩa.

Cái bạn cần chỉ là: *"mọi sơ đồ commit vào repo này phải qua self-check"*.

```yaml
# .github/workflows/diagrams.yml
name: Diagrams

on:
  pull_request:
    paths:
      - 'docs/**/*.html'
      - '.github/workflows/diagrams.yml'

permissions:
  contents: read

jobs:
  self-check:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Chỉ lấy skill — không cần nguyên repo, không cần lịch sử.
      - name: Fetch the diagram-design skill
        run: |
          git clone --depth 1 --filter=blob:none --sparse \
            https://github.com/cathrynlavery/diagram-design.git /tmp/dd
          git -C /tmp/dd sparse-checkout set skills/diagram-design/scripts

      - name: Self-check every diagram
        run: |
          shopt -s globstar nullglob
          files=(docs/**/*.html)
          if [ ${#files[@]} -eq 0 ]; then
            echo "no diagrams to check"; exit 0
          fi
          python3 /tmp/dd/skills/diagram-design/scripts/self_check.py "${files[@]}"
```

Ba lựa chọn có chủ đích trong file trên:

- **Không cài Playwright.** `self_check.py` là stdlib thuần. Playwright chỉ cần khi xuất PNG, và xuất PNG không thuộc về CI.
- **Sparse checkout chỉ thư mục `scripts`.** Repo có ~90MB screenshot và asset; bạn cần đúng 3 file `.py`.
- **`exit 0` khi không có file.** Một PR không đụng sơ đồ không nên đỏ.

**Ghim phiên bản khi cần tái lập:** đổi `--depth 1` thành một tag/commit cụ thể, ví dụ

```bash
git -C /tmp/dd fetch --depth 1 origin <commit-sha> && git -C /tmp/dd checkout FETCH_HEAD
```

Hợp đồng self-check có thể siết thêm giữa các bản; ghim là cách để CI của bạn không đỏ vì upstream đổi luật.

---

## 6. Đưa self-check vào vòng lặp của agent

Bảo agent tự gác mình:

```text
After you write any diagram HTML, run
  python3 <skill-dir>/scripts/self_check.py <file>
and fix every reported error before telling me it's done.
```

Đây là vòng khép kín rẻ nhất trong cả bộ tool: không LLM, không mạng, không phụ thuộc — chỉ 0 hoặc 1.

---

## 7. Xong bước này khi

- [ ] `self_check.py` chạy `OK` trên mọi sơ đồ trong repo bạn.
- [ ] Có workflow CI chặn PR khi sơ đồ hỏng.
- [ ] Agent của bạn được dặn tự chạy self-check trước khi báo xong.

**Tiếp theo:** chỉ khi bạn định **sửa chính Diagram Design** — `07-contributor-gates.md`.
