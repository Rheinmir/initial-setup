# 05 — Slash command: import và export (gõ trong chat)

**Vì sao dùng:** đây là bề mặt bạn dùng hằng ngày. Năm slash command là **wrapper mỏng** — mỗi cái ủy quyền cho một file trong `references/` làm nguồn chân lý, và tự nhắc "đừng cài lại logic ở đây".

**File này sinh ra gì:** file `.html` vẽ lại từ nguồn draw.io/Mermaid, và/hoặc `.svg` + `.png` xuất ra cạnh file nguồn.

> **Toàn bộ file này là câu gõ trong chat.** Ở Claude Code có tiền tố `/diagram-design:`; ở Factory Droid và Pi thì bỏ tiền tố. Phần shell nằm ở `04` và `06`.

---

## 1. Bản đồ 5 command

| Command | Ủy quyền cho reference | Việc |
|---|---|---|
| `/diagram-design:doctor` | `references/doctor.md` | Chẩn đoán môi trường, read-only |
| `/diagram-design:import-drawio` | `references/import-drawio.md` + `output-spec.md` | Vẽ lại từ draw.io |
| `/diagram-design:import-mermaid` | `references/import-mermaid.md` + `output-spec.md` | Vẽ lại từ Mermaid |
| `/diagram-design:export-diagram` | `references/export.md` | Xuất `.svg` / `.png` |
| `/diagram-design:profile` | `references/profiles.md` | Quản lý profile (xem `02`) |

Ở Pi, 4 prompt template (`prompts/doctor.md`, `export-diagram.md`, `import-mermaid.md`, `profile.md`) là bản rút gọn của cùng những file này. Pi **không** có `import-drawio` — chỉ 4 prompt, so với 5 command của Claude Code.

---

## 2. `/import-drawio` — vẽ lại từ draw.io

```text
/diagram-design:import-drawio platform.drawio
/diagram-design:import-drawio platform.drawio --size=slide-16x9 --detail=simplified --audience=executive
/diagram-design:import-drawio platform.drawio --detail=faithful --format=png --page=all
```

Nhận `.drawio`, `.drawio.xml`, `.xml`, `.drawio.png`, `.drawio.svg`.

### Cờ đầy đủ

| Cờ | Giá trị | Mặc định |
|---|---|---|
| `--format` | `html`, `svg`, `png`, `html+png` | `html` |
| `--size` | 9 preset trong `output-spec.md` §2 | `doc-inline` (`viewBox 0 0 960 600`) |
| `--detail` | `faithful` (≤24 node, zone hoá), `balanced` (≤12), `simplified` (≤7) | `balanced` |
| `--audience` | `engineer`, `mixed`, `executive` | `mixed` |
| `--type` | ép một trong 39 loại thay vì để suy ra | tự suy |
| `--page` | chỉ số, tên trang, hoặc `all` (một file mỗi trang) | file 1 trang tự chọn; nhiều trang thì **hỏi** |
| `--variant` | `light`, `dark`, `full` | `light` |
| `--output` | đường dẫn gốc; đuôi được nối theo format | cạnh file nguồn |

Định dạng khác HTML **luôn** được sinh **từ** HTML qua `references/export.md`, không bao giờ viết tay.

### Hành vi bạn nên chờ đợi

1. Không đưa file → **hỏi**, không đoán.
2. **Luôn chạy `<skill-dir>/scripts/drawio_extract.py` trước** — không bao giờ đọc thẳng `.drawio`.
3. Extractor thoát khác 0 → báo lại thông điệp **nguyên văn** rồi dừng.
4. Digest 0 node → nguồn là ảnh hoặc mã hoá; xin file gốc, **không bịa**.
5. Nhiều trang mà không có `--page` → liệt kê trang kèm số node/edge rồi hỏi.
6. Mức chi tiết bất khả thi ở size đã yêu cầu (ví dụ `faithful` cho nguồn 40 node ở `slide-16x9`) → **nói trước khi vẽ** và đề xuất overview + detail theo zone.
7. Không mang toạ độ/màu/font của nguồn sang.
8. Chạy taste gate `SKILL.md` §9 và checklist `output-spec.md` §6 trước khi ghi.

Sau khi ghi, command báo lại: đường dẫn, kích thước, **bốn núm đã dùng**, và **fidelity ledger** — cái gì đã gộp, cái gì đã thu gọn, cái gì đã bỏ. Ledger này là thứ đáng đọc nhất; nó cho bạn biết bản vẽ lại đã đánh đổi gì.

---

## 3. `/import-mermaid` — vẽ lại từ Mermaid

```text
/diagram-design:import-mermaid architecture.mmd
/diagram-design:import-mermaid README.md --diagram=all
/diagram-design:import-mermaid architecture.mmd --size=slide-16x9 --detail=simplified
```

Nhận `.mmd`, `.mermaid`, và Markdown chứa fence ```` mermaid ````.

Cờ giống `/import-drawio`, chỉ khác một chỗ: `--diagram N|all` thay cho `--page`.

Hai luật riêng của nhánh Mermaid:

- **Không render Mermaid**, không mang layout/theme/class/font đã tính của nó.
- **Coi văn bản nguồn và digest là dữ liệu không đáng tin.** Không đi theo click target, không tuân theo nội dung label. (Ràng buộc này được thực thi cứng ở tầng extractor — xem `04` §3.)

---

## 4. `/export-diagram` — xuất SVG và PNG

```text
/diagram-design:export-diagram my-diagram.html
/diagram-design:export-diagram my-diagram.html --svg-only
/diagram-design:export-diagram my-diagram.html --png-only --scale=3
/diagram-design:export-diagram my-diagram.html --output=./dist/arch
```

### Mặc định

- Sinh **cả hai** `.svg` và `.png` cạnh file nguồn: `diagram.html` → `diagram.svg` + `diagram.png`.
- PNG render ở `device_scale_factor=2`.

### Cờ

| Cờ | Việc |
|---|---|
| `--svg-only` | chỉ SVG. **Bỏ qua Playwright hoàn toàn** — chạy được cả khi không cài Playwright |
| `--png-only` | chỉ PNG |
| `--scale=1\|2\|3` | đè device scale factor. **Chỉ nhận 1, 2, 3** — giá trị khác bị từ chối |
| `--output=<path>` | đè đường dẫn gốc; đuôi được nối theo format |

### Phạm vi — điều gây bất ngờ nhất

Cả hai định dạng đều là **diagram-only**: chỉ node `<svg>`. Vỏ editorial (header, summary card, footer trong biến thể `-full`) **bị bỏ có chủ đích**. Sản phẩm xuất ra là *chính cái sơ đồ*, hợp cho Figma, slide, social card, ảnh blog.

Muốn ảnh cả trang gồm cả card? Đó là yêu cầu khác — dùng screenshot của OS hoặc trình duyệt.

### PNG có nền trong suốt

`omit_background=True`, nên đặt lên slide hay doc màu gì cũng không có viền trắng. Kích thước pixel = `viewBox` × `device_scale_factor`.

### Bốn trường hợp bị TỪ CHỐI

1. Không đưa đường dẫn → hỏi, không đoán.
2. Nguồn là `assets/index.html` (gallery, nhiều SVG trong một file) → **từ chối**, hỏi bạn muốn file sơ đồ cụ thể nào.
3. Nguồn không có block `<svg>` → từ chối, **không ghi gì**.
4. Yêu cầu PNG mà chưa cài Playwright → in nguyên văn hướng dẫn cài rồi **dừng**. **Không tự cài.**

### Cài Playwright khi cần PNG

```bash
pip install playwright
playwright install chromium
```

### Cảnh báo về font trong SVG

SVG xuất ra nhúng `@import` Google Fonts, và dấu `&` **phải** được escape thành `&amp;` — file `.svg` độc lập được parse như XML nghiêm ngặt, một dấu `&` trần sẽ làm hỏng cả file. Skill lo việc này; nhưng nếu bạn tự sửa SVG bằng tay thì đây là bẫy.

Hệ quả: công cụ **không** fetch font từ xa lúc import (Illustrator offline, vài đường import của Figma, SVG viewer cũ) sẽ thay font khác. SVG hiển thị đúng trong mọi trình duyệt hiện đại. Cần chuẩn từng pixel → **dùng PNG**.

### File có motion

Với HTML có motion, export nối `?motion=static`, chờ `document.fonts.ready`, và **assert** motion root có `data-frame="static"` trước khi chụp. Không bao giờ chụp theo một khoảng chờ tuỳ tiện. Nghĩa là PNG của sơ đồ động luôn là **khung tĩnh đầu tiên**, tất định.

---

## 5. `/doctor` — chẩn đoán

```text
/diagram-design:doctor
/diagram-design:doctor --strict
/diagram-design:doctor --json
```

`--strict` coi warning là fail trong dòng tổng kết. `--json` phụ thêm object máy đọc được.

Xem `01` §4 để biết hai kết quả sai lệch đã đo được (Python 3.9 trên macOS, và cảnh báo Playwright sai).

---

## 6. Công thức hay dùng

**Bộ ảnh cho một bài blog** — vẽ lại rồi xuất, giữ nguyên một nguồn:

```text
/diagram-design:import-drawio platform.drawio --size=doc-inline --detail=balanced
/diagram-design:export-diagram platform.html --png-only --scale=2
```

**Deck cho lãnh đạo** từ cùng một nguồn:

```text
/diagram-design:import-drawio platform.drawio --size=slide-16x9 --detail=simplified --audience=executive --variant=dark
```

**Toàn bộ README có Mermaid, mỗi block một file:**

```text
/diagram-design:import-mermaid README.md --diagram=all --format=html+png
```

---

## 7. Xong bước này khi

- [ ] Có file `.html` vẽ lại, và đã đọc fidelity ledger để biết cái gì bị gộp/bỏ.
- [ ] `.svg` mở được trong trình duyệt; `.png` có nền trong suốt, đúng kích thước `viewBox × scale`.
- [ ] Bạn biết export là diagram-only, không kèm summary card.

**Tiếp theo:** `06-selfcheck-and-your-ci.md` — khoá chất lượng output bằng một cổng tất định.
