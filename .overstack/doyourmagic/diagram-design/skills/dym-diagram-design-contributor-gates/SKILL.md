---
name: dym-diagram-design-contributor-gates
description: "Nhánh người đóng góp: cổng kiểm và luật release. chỉ đọc file này khi bạn sửa chính Diagram Design — thêm loại sơ đồ, sửa extractor, đổi bộ icon. Người dùng bình thường không bao giờ cần tới đây; 01–06 là đủ."
disable-model-invocation: true
---

# Skill: dym-diagram-design-contributor-gates — Nhánh người đóng góp: cổng kiểm và luật release

**Vì sao dùng:** chỉ đọc file này khi bạn **sửa chính Diagram Design** — thêm loại sơ đồ, sửa extractor, đổi bộ icon. Người dùng bình thường không bao giờ cần tới đây; `01`–`06` là đủ.

**File này sinh ra gì:** một nhánh vượt được toàn bộ cổng CI ở local trước khi push.

> **Toàn bộ file này là lệnh shell.** Không phụ thuộc `01`–`06`, nhưng nên đọc `04` trước, vì hợp đồng mã thoát của extractor là thứ bạn **không được phép phá**.

---

## 1. Chuẩn bị

```bash
git clone git@github.com:cathrynlavery/diagram-design.git
cd diagram-design
python3 --version   # phải >= 3.10; CI chạy 3.11 và 3.12 trên Linux/Windows/macOS
```

Không có `npm install`, không có venv bắt buộc. Chỉ hai thứ tuỳ chọn:

```bash
python3 -m pip install playwright && python3 -m playwright install chromium  # cho lint-render + render screenshot
python3 -m pip install "Pillow==12.1.1"                                      # cho verify thumbnail README
```

Cả hai phiên bản đều **ghim cứng** trong CI (`PLAYWRIGHT_VERSION: "1.62.0"`, `PILLOW_VERSION: "12.1.1"`). Lý do ghi thẳng trong `ci.yml`: oracle của `lint-render.py` là **pixel**, nên trình duyệt là một phần của hợp đồng — nâng Playwright và Chromium phải làm **cùng nhau, có chủ đích**.

Luật quy trình từ `CONTRIBUTING.md` §"Before you start":

- **Tạo issue trước** cho mọi thứ không tầm thường (loại mới, đổi hành vi, đụng ngữ pháp import). Sửa nhỏ và docs thì PR thẳng.
- **Làm trên nhánh** — không bao giờ commit thẳng vào `main`.
- **Một PR = một mối quan tâm.**

---

## 2. LUẬT SỐ MỘT: đừng bump version trong PR

Đây là thứ làm PR đỏ nhiều nhất, và nó phản trực giác.

Ba manifest — `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.factory-plugin/plugin.json` — **được bump tự động trên `main` sau mỗi lần merge** bởi workflow `auto-bump.yml` (ADR 0009). PR **phải để nguyên** cả ba. CI từ chối bất kỳ thay đổi nào tới chúng:

```bash
python3 scripts/verify-plugin-package.py --require-no-bump origin/main
```

Cần release lớn hơn patch? **Ghi vào mô tả PR**, maintainer sẽ gắn nhãn `release:minor` hoặc `release:major` trước khi merge; nhãn quyết định mức bump. `scripts/bump-plugin-version.py` vẫn tồn tại nhưng dành cho workflow và maintainer — **người đóng góp không bao giờ chạy nó**.

Lý do thiết kế: giữ cho các PR đang mở khỏi xung đột với nhau ở mỗi lần merge.

---

## 3. Ngân sách 40.000 byte của `SKILL.md` — chỉ còn 4 byte

Cổng semantic-pattern giới hạn `skills/diagram-design/SKILL.md` ở **40.000 byte** để skill đã cài còn nạp nổi (ADR 0004; hằng số `MAX_SKILL_BYTES = 40_000` tại `scripts/verify-semantic-motion.py:23`).

Kích thước hiện tại, đo tại commit `4451ead`:

```bash
$ wc -c < skills/diagram-design/SKILL.md
39996
```

**Còn đúng 4 byte.** Thêm một từ vào `SKILL.md` là gãy CI. Khi cổng này đỏ: giảm trùng lặp hoặc **chuyển chi tiết sang một file `references/` được định tuyến**. Tuyệt đối **không** gỡ từ vựng định tuyến khỏi frontmatter — đó là thứ khiến skill được kích hoạt đúng lúc.

---

## 4. Chạy toàn bộ cổng trước khi push

`CONTRIBUTING.md` cho sẵn một chuỗi `&&` dài ~48 lệnh. Dán nguyên si:

```bash
python3 scripts/test-plugin-package.py \
  && python3 scripts/test-maintainer-policy.py \
  && python3 scripts/verify-plugin-package.py --require-no-bump origin/main \
  && claude plugin validate . --strict \
  && python3 scripts/test-lint-a11y.py \
  && python3 scripts/verify-semantic-motion.py --markdown-only \
  && python3 scripts/verify-semantic-motion.py --example-only \
  && python3 scripts/verify-motion.py --shipped \
  && python3 scripts/lint-skin.py --all --baseline \
  && python3 scripts/lint-render.py --self-test \
  && python3 scripts/lint-render.py --all \
  && python3 scripts/test-verify-polar.py && python3 scripts/verify-polar.py \
  && python3 scripts/verify-sequence-oauth.py \
  && python3 scripts/test-verify-semantic-motion.py \
  && python3 scripts/test-verify-sequence-oauth.py \
  && python3 scripts/verify-drawio-import.py && python3 scripts/test-verify-drawio-import.py \
  && python3 scripts/verify-mermaid-import.py \
  && python3 scripts/test-verify-motion.py \
  && python3 scripts/verify-doctor.py && python3 scripts/test-verify-doctor.py \
  && python3 scripts/verify-docs-sync.py && python3 scripts/test-verify-docs-sync.py \
  && python3 scripts/verify-screenshot-freshness.py \
  && python3 scripts/test-build-readme-thumbs.py && python3 scripts/build-readme-thumbs.py --check \
  && python3 scripts/test-self-check.py \
  && python3 scripts/verify-geometry.py --all && python3 scripts/test-verify-geometry.py \
  && python3 scripts/verify-treemap.py --all && python3 scripts/test-verify-treemap.py \
  && python3 scripts/verify-dumbbell.py && python3 scripts/test-verify-dumbbell.py \
  && python3 scripts/verify-slopegraph.py --all && python3 scripts/test-verify-slopegraph.py \
  && python3 scripts/verify-ridgeline.py --all && python3 scripts/test-verify-ridgeline.py \
  && python3 scripts/verify-sankey.py --all && python3 scripts/test-verify-sankey.py \
  && python3 scripts/verify-bubble.py --all && python3 scripts/test-verify-bubble.py \
  && python3 scripts/verify-bump.py --all && python3 scripts/test-verify-bump.py \
  && python3 scripts/verify-beeswarm.py --all && python3 scripts/test-verify-beeswarm.py \
  && python3 scripts/verify-skin-polarity.py --all && python3 scripts/test-verify-skin-polarity.py
```

Mẫu hình đáng chú ý: **mỗi verifier có một test đi kèm**. `verify-sankey.py` kiểm file thật; `test-verify-sankey.py` kiểm rằng *chính verifier đó* bắt được cả ca đúng lẫn ca đối kháng. Một linter hỏng **không được phép** báo repo sạch. Sửa một verifier thì phải sửa cả test của nó.

### Kết quả đo thật (macOS, Python 3.9.6, clone sạch tại `4451ead`)

| Cổng | rc | Ghi chú |
|---|---|---|
| `lint-skin.py --all --baseline` | `0` | `153 file(s) checked, 20 skipped, 0 finding(s)` |
| `verify-geometry.py --all` | `0` | `155 file(s) checked, 0 finding(s)` |
| `verify-semantic-motion.py --markdown-only` | `0` | mode, primitive, fallback tĩnh, a11y |
| `verify-motion.py --shipped` | `0` | mọi file motion đã ship |
| `verify-drawio-import.py` | `0` | `All draw.io import gates passed.` |
| `verify-mermaid-import.py` | `0` | `All Mermaid import gates passed.` |
| `verify-docs-sync.py` | `0` | description hook, gallery, cây README, link reference, routing |
| `test-self-check.py` | `0` | `All self-check tests passed` |
| `verify-plugin-package.py --current-only` | `0` | Claude/Codex/Factory đều `2.6.12` |
| **`verify-doctor.py`** | **`1`** | **đỏ vì môi trường máy, không phải vì code** |

**Cảnh báo về `verify-doctor.py`:** nó không phải unit test — nó **thật sự chạy doctor** và trả rc theo tình trạng máy bạn. Trên máy Python 3.9.6 nó in:

```text
Doctor summary: FAIL (3 pass, 1 warn, 1 fail)
[FAIL] Python runtime: Python 3.9.6 found via python3 at /usr/bin/python3; Diagram Design requires Python >= 3.10.
[WARN] Playwright PNG export readiness: Playwright package is not available in the active Python interpreter.
```

Cổng này **đỏ vì môi trường**, không phải vì thay đổi của bạn. Nâng `python3` lên 3.10+ rồi chạy lại. Cảnh báo Playwright thì là **false negative có thật** — xem `01` §4 bẫy 2: probe ở `scripts/verify-doctor.py:158` dùng `playwright.__version__`, một thuộc tính package **không có**.

Nhiều cổng chạy được trên 3.9 (CI còn có job `python39-compat` riêng cho `test-lint-a11y.py` và `lint-skin.py --all --baseline`), nhưng đừng dựa vào đó — dev cần 3.10+.

---

## 5. Đọc lỗi cổng thế nào

| Cổng đỏ | Nghĩa và cách sửa |
|---|---|
| `verify-plugin-package.py` | Báo đổi version → **bỏ sửa manifest khỏi nhánh**. Báo packaging → giữ mọi marketplace trỏ về root repo và skill dùng chung ở `skills/diagram-design/SKILL.md`. |
| `lint-skin.py` | Thông điệp nêu **file, dòng, phạm trù**: `color`, `font-family`, `a11y`, `external-asset`, `pure-black`, `script`. Màu phải lấy từ palette trong `style-guide.md`; font từ danh sách cho phép. Linter còn đòi controller ghim-SHA từ `template-motion.html` **verbatim**, và từ chối tài nguyên từ xa, CSS `@import`, CSS `url()` không phải fragment, event handler, `srcdoc`, URL thực thi, và script thừa. |
| `verify-*.py` | Hành vi thật của extractor không còn khớp fixture/tài liệu, hoặc wiring reference/command/prompt bị lệch. **Sửa nguồn chân lý — đừng nới test cho qua.** |
| `verify-geometry.py` | Một label mask chồng lên node khai báo sau nó → node fill sẽ cắt label lúc render. Dời label sang đoạn trống của connector, **giữ khoảng cách 6–10px** với nét vẽ theo `SKILL.md` §6, và **đừng thu nhỏ mask** để lách. |
| `verify-slopegraph.py` | Hai trục bất đồng về thang/gốc, hoặc endpoint vẽ sai chỗ so với giá trị nó khai. **Sửa toạ độ, không sửa nhãn** — và đừng dời điểm để tránh hai nhãn chạm nhau, vì nhãn chen chúc nghĩa là hai giá trị *thật sự* gần nhau. |
| `verify-ridgeline.py` | Một ridge vẽ theo biên độ riêng, baseline lệch pitch, ridge lấy mẫu trên trục x riêng, hoặc range in ra rộng hơn bin nó khai. **Đừng chuẩn hoá lại một ridge** cho dễ đọc. |
| `verify-bubble.py` | Bubble vẽ lệch thang chung, bán kính bất đồng với hằng diện tích `r = K·√size`, bubble thứ hai đeo accent, bubble nhỏ bị vẽ dưới bubble lớn khi chồng nhau. **Sửa hình học, không sửa ràng buộc.** |
| `verify-bump.py` | Đỉnh nằm lệch lưới rank, một mốc có rank không phải hoán vị `1..N`, đoạn nối bị cong. **Rank giữa hai rank không phải là rank.** |
| `verify-beeswarm.py` | Chấm lệch thang giá trị, hai chấm cùng giá trị ở hai vị trí, cặp chấm đè nhau thay vì né, xuất hiện bán kính thứ hai, hoặc **định vị mark bằng CSS** (`transform`, `translate`/`rotate`/`scale`, geometry property, motion path) qua bất kỳ vật mang nào — attribute, `style` inline, hay rule `<style>`. **Chen chúc là dữ liệu; né là cách xử lý trung thực duy nhất.** |
| `verify-skin-polarity.py` | Một legend/caption gọi hướng ramp theo **độ sáng** (`darker is larger`) trong file mà ramp đi ngược. `ink` là **vai trò**, không phải màu — nó ra gần-đen trên paper sáng và gần-trắng trên paper tối. Gọi hướng theo **tương phản với paper** (`stronger contrast is larger`), câu đó sống sót khi đổi skin, và **ship cùng một câu ở mọi biến thể**. |
| `verify-treemap.py` | Ô không khớp giá trị nó mang nhãn, hoặc nhãn không vừa ô. |
| `verify-screenshot-freshness.py` | Một example light tối giản hoặc PNG của nó đổi mà catalog chưa refresh đồng bộ. Cài Playwright, chạy `python3 scripts/render-canonical-screenshots.py`, **xem lại cả 39 bản render**, rồi commit PNG mới + `docs/screenshots/manifest.json`. |
| `build-readme-thumbs.py --check` | Preview README thiếu/cũ/hỏng/sai cỡ/mồ côi/không còn link tới PNG đầy đủ. Cài `Pillow==12.1.1`, chạy `build-readme-thumbs.py`, commit WebP + `docs/screenshots/thumbs/manifest.json`. |
| Icon assets | Bạn đổi `scripts/vendor/icons/` hoặc `scripts/build-icons.py` mà file sinh ra đã cũ. Chạy lại `python3 scripts/build-icons.py` và commit `icons.html` + `references/primitive-icons.md`. |

### Luật cấm quan trọng nhất

> **Đừng thêm file vào `scripts/lint-skin-baseline.txt` để lách.**

Baseline (hiện có **20 dòng**) chỉ dành cho các example legacy tiền-2.0 vốn dĩ ra đời trước skin hiện tại — và chúng **vẫn** bị kiểm a11y. Thêm file mới vào đó là gian lận cổng.

---

## 6. Cổng cho từng loại thay đổi

| Bạn đụng vào | Chạy tối thiểu |
|---|---|
| Một example mới | `python3 scripts/lint-skin.py skills/diagram-design/assets/example-my-type.html` rồi `--all --baseline` |
| Loại sơ đồ mới | thêm `references/type-*.md` + example + mục trong bảng `SKILL.md` §3 → `verify-docs-sync.py` + `lint-skin.py --all` + kiểm ngân sách 40.000 byte |
| Đường import | `verify-drawio-import.py` + `test-verify-drawio-import.py` + `verify-mermaid-import.py` |
| Bộ icon | `build-icons.py` rồi `git diff --exit-code` trên `icons.html` và `primitive-icons.md` |
| Motion | `verify-motion.py --shipped` + `test-verify-motion.py` + `verify-semantic-motion.py` (cả hai mode) |
| Doctor | `verify-doctor.py` + `test-verify-doctor.py` |
| Bất kỳ file docs nào | `verify-docs-sync.py` — nó kiểm cả link reference lẫn bề mặt command/prompt |

---

## 7. ADR — đọc trước khi tranh luận thiết kế

`docs/adr/` có 9 quyết định. Bốn cái hay bị vấp nhất:

- **0001** — static theo mặc định, một controller ghim duy nhất.
- **0003** — `reveal` là autoplay được phép **duy nhất**.
- **0004** — ngưỡng byte của `SKILL.md` + description giàu trigger.
- **0009** — version bump trên `main` **sau** merge, không phải trong PR.

Cùng với `docs/cookbook.md` (công thức vận hành) và `docs/superpowers/` (plan + spec mẫu cho một loại mới, dùng polar chart làm ví dụ).

---

## 8. Xong bước này khi

- [ ] Cả chuỗi `&&` chạy xanh ở local (`verify-doctor.py` cần Python 3.10+ mới xanh).
- [ ] Không có manifest version nào bị đụng trong diff.
- [ ] `wc -c < skills/diagram-design/SKILL.md` vẫn dưới 40.000.
- [ ] Không có dòng mới nào trong `scripts/lint-skin-baseline.txt`.
