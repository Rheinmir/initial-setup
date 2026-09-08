---
name: dym-diagram-design-import-extractors-shell
description: "Hai extractor chạy trong terminal (draw.io và Mermaid). hai script này là nửa tất định của luồng import. Chúng không bao giờ ra quyết định thiết kế — chúng giải mã file nguồn và in ra một bản IR (intermediate representation) mà agent đọc để chọn loại sơ đồ và mức chi tiết. Ch"
disable-model-invocation: true
---

# Skill: dym-diagram-design-import-extractors-shell — Hai extractor chạy trong terminal (draw.io và Mermaid)

**Vì sao dùng:** hai script này là **nửa tất định** của luồng import. Chúng không bao giờ ra quyết định thiết kế — chúng giải mã file nguồn và in ra một bản IR (intermediate representation) mà agent đọc để chọn loại sơ đồ và mức chi tiết. Chạy chúng bằng tay khi bạn muốn *nhìn thấy* nguồn có gì trước khi để agent vẽ, hoặc khi cần cắm vào script/CI.

**File này sinh ra gì:** một digest Markdown (mặc định, in ra stdout) hoặc IR JSON đầy đủ (`--json`).

> **Toàn bộ file này là lệnh shell.** Bản slash-command tương ứng nằm ở `05` — đừng trộn hai bên.

---

## 1. Định vị script trước đã

Đây là lỗi số một. `commands/import-drawio.md` yêu cầu rõ: *"Never assume the skill is under the current working directory."*

```bash
# tuỳ host, chọn cái nào tồn tại
SKILL_DIR=~/.claude/skills/diagram-design
SKILL_DIR=~/code/diagram-design/skills/diagram-design
SKILL_DIR=~/.config/opencode/skills/diagram-design

ls "$SKILL_DIR/scripts/"
# kỳ vọng: drawio_extract.py  mermaid_extract.py  self_check.py
```

---

## 2. `drawio_extract.py`

### Chữ ký thật (đọc từ `argparse` cuối file, không phải từ README)

```text
python3 drawio_extract.py <file> [--page N|NAME] [--json] [--max-rows N] [--out PATH]
```

| Tham số | Ý nghĩa |
|---|---|
| `file` (bắt buộc) | `.drawio` / `.xml` / `.drawio.png` / `.drawio.svg` |
| `--page N\|NAME` | chọn trang theo chỉ số hoặc tên |
| `--json` | in **toàn bộ IR** (mọi node, mọi edge, mọi style) thay vì digest |
| `--max-rows N` | giới hạn số dòng bảng; **phải ≥ 1**, ngược lại `parser.error` |
| `--out PATH` | ghi ra file thay vì stdout |

### Nó giải mã được gì

Docstring nói thẳng: script *"decodes whatever draw.io wrote (raw XML, deflate+base64 payloads, PNG/SVG files with an embedded `mxfile`), flattens the mxGraphModel into absolute-positioned nodes and edges."*

Đây là lý do **không được đọc thẳng file `.drawio` bằng `cat`** — phần lớn bị nén, XML thô là nhiễu.

### Chạy thật

```bash
python3 "$SKILL_DIR/scripts/drawio_extract.py" platform.drawio
```

Output thật trên fixture của repo (`scripts/fixtures/sample-architecture.drawio`):

```text
# draw.io IR — sample\-architecture\.drawio

1 page(s): [0] Platform (12n/8e)

## Page 0 — Platform

- source canvas: 800×478 px (aspect 1.67)
- nodes: 12 total / 12 drawable / 2 containers, depth 1
- edges: 8 (7 labeled, 0 dangling), cycle: False
- shapes: {'rect': 5, 'swimlane': 2, 'cylinder': 2, 'rhombus': 1, 'aws': 1, 'note': 1}
- type candidates: flowchart, architecture
- budget: nodes OVER (max 9), edges ok (max 12)
- hubs (focal candidates): API Gateway(4), Auth Service(3), Orders Service(3), Web App · next\.js(1), Mobile App(1)
- entry points: Web App · next\.js, Mobile App
- terminals: Token valid?, Postgres, Redis, Object Store
- unconnected: Legacy path, to be retired
- collapsible groups (simplify here first):
  - Core Services — 3 children: API Gateway, Auth Service, Orders Service
  - Edge — 2 children: Web App · next\.js, Mobile App
```

Đọc digest này thế nào:

- `budget: nodes OVER (max 9)` — nguồn vượt ngân sách. Bạn sẽ phải chọn `--detail=simplified`, hoặc chấp nhận zone hoá.
- `hubs (focal candidates)` — ứng viên làm node tiêu điểm, xếp theo bậc.
- `collapsible groups (simplify here first)` — chính xác chỗ nên gộp đầu tiên nếu cần cắt.
- `unconnected` — thứ trong nguồn không nối vào đâu; thường là note nên bỏ.

---

## 3. `mermaid_extract.py`

### Chữ ký thật

```text
python3 mermaid_extract.py <file> [--diagram N|all] [--json] [--max-rows N] [--out PATH]
```

Nhận `.mmd`, `.mermaid`, và file Markdown chứa block ```` ```mermaid ````.

Ngữ pháp hỗ trợ — **đúng bốn**: `flowchart`/`graph`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram`.

### Ranh giới tin cậy — điều quan trọng nhất về script này

Docstring, nguyên văn:

> *"Trust boundary: this program parses bounded text. It never evaluates, renders, fetches, or executes Mermaid, JavaScript, URLs, directives, or label content. Every label and directive value is untrusted data. Click targets and styling are counted and discarded; retained labels are emitted only as inert text."*

Nghĩa là: bạn có thể chĩa nó vào file Mermaid từ nguồn không tin cậy. Nó không fetch, không eval, không theo click target. Repo còn có fixture đối kháng riêng — `scripts/fixtures/sample-adversarial.mmd` — và nó chạy rc=0 (parse sạch, không nổ).

### Chạy thật

```bash
python3 "$SKILL_DIR/scripts/mermaid_extract.py" architecture.mmd
```

Output thật trên `scripts/fixtures/sample-flowchart.mmd`:

```text
# Mermaid IR — sample-flowchart.mmd

1 diagram(s): [0] flowchart (9n/7e)

## Diagram 0 — flowchart

- source layout: none (Mermaid is layout-free); direction: LR
- nodes: 9 total / 7 drawable / 2 containers, depth 1
- edges: 7 (4 labeled, 0 dangling), cycle: True
- shapes: {'rect': 3, 'container': 2, 'cylinder': 1, 'rhombus': 1, 'round': 1, 'stadium': 1}
- type candidates: flowchart, architecture
- budget: nodes ok (max 9), edges ok (max 12)
- hubs (focal candidates): API Gateway(6), Token valid?(3), Orders Service(2), Web App(1), Postgres(1)
```

Chú ý dòng đầu: `source layout: none (Mermaid is layout-free)`. Khác với draw.io — draw.io có toạ độ, Mermaid thì không. Cả hai đều **không** được mang layout sang output.

### Markdown nhiều block

```bash
python3 "$SKILL_DIR/scripts/mermaid_extract.py" README.md
```

Output thật:

```text
# Mermaid IR — sample-readme-with-mermaid.md

2 diagram(s): [0] flowchart (3n/2e), [1] sequenceDiagram (3n/4e)
```

Chọn một block: `--diagram 1`. Xuất tất cả: `--diagram all`.

---

## 4. Mã thoát — KHÔNG phải quy ước 0/1

Đã đo bằng cách chạy thật, không đọc doc:

| Lệnh | rc | Nghĩa |
|---|---|---|
| `drawio_extract.py fixture.drawio` | `0` | ok |
| `mermaid_extract.py fixture.mmd` | `0` | ok |
| `mermaid_extract.py /nope.mmd` | **`2`** | file không tồn tại |
| `drawio_extract.py --badflag x` | **`2`** | lỗi cách dùng (argparse) |
| `mermaid_extract.py adversarial.mmd` | `0` | parse sạch, không nổ |

Docstring của cả hai script khai đúng vậy: *"Exit codes: 0 ok, 2 unreadable / unsupported input"* và *"0 success, 2 unreadable, unsupported, malformed, or over limits."*

**`2` gộp chung ba thứ**: input hỏng, input không hỗ trợ, và lỗi cách dùng. Nghĩa là trong script gọi, `rc == 2` **không** phân biệt được "file người dùng hỏng" với "tôi gõ sai cờ". Muốn phân biệt thì phải đọc stderr:

```bash
python3 "$SKILL_DIR/scripts/mermaid_extract.py" "$f" > ir.md 2> err.txt
rc=$?
case $rc in
  0) echo "ok" ;;
  2) echo "không đọc được / không hỗ trợ / sai cờ: $(cat err.txt)" ;;
  *) echo "lỗi bất ngờ rc=$rc" ;;
esac
```

Định dạng lỗi thật: `mermaid_extract: /nope.mmd: no such file`.

---

## 5. Đưa IR sang cho agent

Đường dùng thường gặp: dump IR ra file rồi bảo agent đọc.

```bash
python3 "$SKILL_DIR/scripts/drawio_extract.py" platform.drawio --out platform-ir.md
# stdout: wrote platform-ir.md (4123 bytes)
```

Rồi trong chat: *"Read `platform-ir.md` and redraw page 0 as an architecture diagram at slide-16x9, simplified."*

Cần IR máy đọc thì `--json`:

```bash
python3 "$SKILL_DIR/scripts/mermaid_extract.py" arch.mmd --json --out arch-ir.json
```

---

## 6. Ba luật cứng khi vẽ lại (áp cho cả hai nguồn)

Từ `commands/import-drawio.md` §"Required behaviour" và bản Mermaid tương ứng:

1. **Digest báo 0 node** → nguồn là ảnh hoặc bị mã hoá. Nói thẳng, xin file gốc. **Không bịa nội dung.**
2. **Không bao giờ mang toạ độ, màu, font của nguồn sang.** Output là bản **vẽ lại** trong skin `style-guide.md`. Với Mermaid còn thêm: không render Mermaid, không mang theme/class/layout đã tính của nó.
3. **`--detail=faithful` trên 9 node** → phải zone hoá bố cục; **trên 24 node** → tách thành file overview + file detail.

---

## 7. Xong bước này khi

- [ ] Chạy được extractor trên file thật của bạn, rc=0.
- [ ] Đọc được dòng `budget:` và biết mình sẽ cần mức `detail` nào.
- [ ] Biết `rc=2` là gộp chung và script gọi của bạn có đọc stderr.

**Tiếp theo:** `05-import-export-slash-commands.md` — phần chat để agent vẽ lại và xuất file.
