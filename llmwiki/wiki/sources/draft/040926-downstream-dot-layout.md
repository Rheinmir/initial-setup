# 040926-downstream-dot-layout
**Type:** draft
**Status:** proposed
**Tags:** install, downstream, layout, migration, hallmark, gate-scope
**Proposed:** 2026-09-04

## Vấn đề

`harness/poc-vendor-neutral/install.sh` đặt hai thư mục **không có dấu chấm** ngay gốc dự án đích:

```
<dự-án>/llmwiki/     raw · wiki/{concepts,entities,sources/{adr,draft}} · html/ · .harness-stamp
<dự-án>/harness/     (mkdir -p, dùng cho state cục bộ)
```

Trong khi mọi thứ khác installer đặt đều đã ẩn: `.claude/`, `.cursor/rules/`, `.kiro/steering/`.

Hệ quả đo được:

1. **Cổng thiết kế chấm nhầm artifact framework thành UI sản phẩm.** Bất kỳ skill/tool nào quét `**/*.html` trong dự án đích sẽ vớ phải `llmwiki/html/overstack.html` (530KB tài liệu framework) và các trang report khác. Cụ thể: `hallmark` khi được bảo "audit giao diện app", `impeccable detect .`, hay bất kỳ linter design nào của bên thứ ba. Chúng không có cách nào biết đây không phải UI sản phẩm.
2. **Làm bẩn cây thư mục dự án của người ta.** `ls`, file tree trong IDE, `find`, kết quả search — framework chiếm chỗ ngang hàng với `src/`.
3. **Không nhất quán với chính installer** — nó đã ẩn 3 thư mục provider khác.

Đây là vấn đề CẤU TRÚC, không phải vấn đề của cổng: sửa từng cổng để né `llmwiki/` là vá triệu chứng, và không chặn được tool của bên thứ ba.

## Số đo blast radius

| Nhóm | File | Lần nhắc |
|---|---:|---:|
| Code ĐI XUỐNG dự án đích nhắc `llmwiki/` hoặc `harness/` | 200 | 1.287 |
| Trong đó **thật sự dựng đường dẫn lúc chạy** | **79** | **261** |
| Chỉ ở repo framework (không ảnh hưởng downstream) | 483 | 9.980 |

Nặng nhất: `test-broad.sh` 41 · `install-harness.sh` 25 · `install.sh` 15 · `harness-doctor.py` 13 · `artifacts.py` 9.

## Ba phương án

### A — Đổi tên cứng, sửa hết 261 chỗ
`llmwiki/` → `.llmwiki/`, `harness/` → `.harness/`, sửa mọi chỗ dựng path.
Rủi ro cao: sót một chỗ là bản cài cũ gãy câm. Big-bang, không lùi được từng phần.

### B — Một resolver, chấp CẢ HAI layout (KHUYẾN NGHỊ)
Theo thang Meadows đây là **đổi luồng thông tin**, bậc cao hơn hẳn việc sửa 261 tham số:

1. Thêm **một** hàm phân giải dùng chung — `overstack_root()` / `wiki_dir()` — thử theo thứ tự `.llmwiki/wiki` → `llmwiki/wiki` → `wiki`. Khuôn này đã tồn tại sẵn ở `wiki-sync.py::detect_wiki_dir` (nó vốn đã thử 2 layout), chỉ cần nâng thành nguồn chung và thêm nhánh dấu chấm.
2. Mọi consumer gọi resolver thay vì nối chuỗi. Sửa dần, không big-bang: file chưa sửa vẫn chạy vì layout cũ vẫn được chấp.
3. Installer **mới** tạo `.llmwiki/`; installer chạy trên bản cũ thì migrate.

Vì resolver chấp cả hai, bản chưa migrate không bao giờ gãy → migration không phải sự kiện một-lần-ăn-cả.

### C — Không đổi thư mục, chỉ khai thể loại
Nhúng marker `<!-- genre: framework-artifact -->` vào HTML sinh, cổng đọc marker để chọn bộ luật.
Rẻ nhất và **nên làm dù chọn gì** — nhưng một mình nó không giải quyết được: tool bên thứ ba không đọc marker của ta, và cây thư mục vẫn bẩn.

**Đề xuất: B, kèm C như bổ sung rẻ.**

## Migration trong installer (phần "sửa script kéo về")

Chạy trước mọi bước seed, idempotent, có `--dry-run`:

1. **Nhận diện**: `$ROOT/llmwiki` tồn tại VÀ `$ROOT/.llmwiki` chưa → cần migrate.
2. **Chặn tự hại**: repo framework có `fdk/wiki` → **KHÔNG migrate**. Installer đã dùng đúng dấu hiệu này ở bước U10.
3. **Dời**: `git mv` nếu file đang được track, `mv` nếu không. Giữ nguyên nội dung, không đụng gì bên trong.
4. **Viết lại con trỏ** — đây là phần dễ sót nhất, phải liệt kê đủ:
   - `.claude/settings.json` + `settings.local.json`: `$CLAUDE_PROJECT_DIR/llmwiki/.claude/hooks/*` → `.llmwiki/...`
   - `.pre-commit-config.yaml`: entry `harness/poc-vendor-neutral/bin/llmwiki-validate.py`
   - `.cursor/hooks.json`, `.codex/hooks.json`, `.grok/hooks/*.json` nếu có
   - `.gitignore`: các dòng `llmwiki/...`
   - `llmwiki/.harness-stamp` → `.llmwiki/.harness-stamp`
5. **Verify**: chạy lại `session_start.py` một lượt khô + `medic --ci` nếu có; đỏ thì rollback bằng cách dời ngược.

## Cần chốt trước khi code

1. Đổi cả `harness/` hay chỉ `llmwiki/`? (`harness/` ở downstream chỉ giữ state cục bộ, ít tham chiếu hơn nhiều — có thể làm cùng lượt hoặc để sau.)
2. Có giữ tương thích ngược **vĩnh viễn** trong resolver, hay đặt hạn (vd 2 minor version rồi bỏ nhánh `llmwiki/`)?
3. Migration chạy **tự động** trong `install`/`update`, hay là một lệnh riêng người dùng gọi tay?

## Files (dự kiến — CHƯA code)
| File | Action |
|------|--------|
| `harness/scripts/overstack_paths.py` | created — resolver dùng chung |
| `harness/poc-vendor-neutral/install.sh` | modified — seed `.llmwiki/` + bước migrate |
| `harness/scripts/wiki-sync.py` | modified — dùng resolver chung |
| 79 file dựng path lúc chạy | modified dần, không big-bang |

## Notes
- Invoked via: `/fdk`
- Đang ở cổng DUYỆT — chưa sửa dòng code nào (fdk pre-flight #4).

## Origin
- **Draft:** `wiki/sources/draft/040926-downstream-dot-layout.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
