# lieflat-charts — workflows

Repo: `git@github.com:larashero3-dotcom/lieflat-charts.git`
Commit khảo sát: `475c9b6` (2026-09-03)
License: PolyForm Noncommercial 1.0.0 — **học/sửa/chia sẻ/dùng phi thương mại được; dùng thương mại phải xin phép riêng.**

## Đây là cái gì

**Không phải CLI, không phải npm package.** Không có `package.json`. Đây là một **Agent Skill pack**: một `SKILL.md` 355 dòng (bộ luật chọn biểu đồ + luật màu + checklist tự soát) đứng cạnh ~52 file HTML template. Agent đọc `SKILL.md`, tra `catalog.md`/`report-catalog.md` để khoá kiểu biểu đồ, mở gallery tương ứng lấy khung code thật, rồi đẻ ra **một file HTML đơn** cho người dùng.

Hai script `.mjs` trong `scripts/` **không phải** đường dùng của người dùng cuối — chúng là gate phát hành của người bảo trì repo.

Vì vậy bundle này chia hai track rạch ròi:

- **Track A — người dùng (consumer)**: cài skill vào agent, rồi *nói chuyện* với agent. Chỉ có đúng một lệnh shell (bước cài); phần còn lại là prompt.
- **Track B — người sửa repo (contributor)**: chạy validate/smoke, hiểu chúng gác cái gì.

## Bảng chỉ mục

| File | Mục đích một dòng | Track | Loại lệnh |
|---|---|---|---|
| `01-install.md` | Cài skill vào Claude Code / Codex / agent khác, và verify cài đúng | A | shell |
| `02-chart-request.md` | Yêu cầu agent ra biểu đồ (chế độ mặc định) và lái nó chọn đúng template | A | chat |
| `03-report-request.md` | Yêu cầu agent ra báo cáo nguyên trang R01–R12 (chế độ phải gọi tên mới bật) | A | chat |
| `04-browse-templates.md` | Mở gallery/report index tại chỗ để tự xem có gì trước khi hỏi agent | A | shell |
| `05-contributor-checks.md` | `validate.mjs` + `smoke-new-charts.mjs`: hai gate khi sửa template | B | shell |
| `06-ci-example.md` | Ví dụ CI tối thiểu tự viết cho fork của bạn | B | shell/yaml |

## Thứ tự chạy đề xuất

**Track A (người dùng):** `01` → (tuỳ chọn `04` để xem hàng) → `02` cho biểu đồ, hoặc `03` khi thật sự cần báo cáo.

**Track B (người sửa):** `01` (hoặc clone thẳng) → `04` để xem template đang trông thế nào → sửa → `05` bắt buộc → `06` nếu muốn tự động hoá.

Track A và Track B không giao nhau: **người dùng cuối không bao giờ cần chạy `validate.mjs`.**

## Ba điều dễ vấp nhất

1. **Mặc định là BIỂU ĐỒ, không phải báo cáo.** `SKILL.md` §0.1 nói rõ: chỉ đưa dữ liệu, hay nói "phân tích giúp tôi", đều phải ra biểu đồ. Chỉ khi bạn gọi đúng chữ "báo cáo / annual report / white paper / poster / brief / dashboard report" thì R01–R12 mới được bật. Nói "phân tích" mà mong ra báo cáo là hụt.
2. **Bản đồ phải gọi đích danh.** Dữ liệu có cột quốc gia/tỉnh **không** tự kích hoạt M1/M2. Phải nói "vẽ bản đồ" / "phân bố theo địa lý".
3. **Nhiều template cần mạng.** Lupi/Basics là SVG viết tay chạy offline; nhưng Glance, Circular, Force, F13 Treemap, R11, R12 nạp Chart.js/ECharts qua CDN, và hầu hết template nạp font online. Bản đồ còn cần GeoJSON online. Cần offline thật thì yêu cầu agent inline dependency.

## Kiểm chứng thế nào, không phải chép lại README

Mỗi khẳng định trong bundle này đều truy được về file nguồn dưới đây, không lấy từ văn xuôi README:

| Khẳng định | Chứng cứ |
|---|---|
| Không phải npm CLI, không có entry point thực thi | `find . -name package.json` → rỗng; chỉ có `scripts/*.mjs` chạy trực tiếp bằng `node` |
| `validate.mjs` exit 1 khi fail, 0 khi pass | `scripts/validate.mjs` dòng cuối: `if (failures.length) { … process.exit(1) }` rồi `console.log(...)`; **đã chạy thật** → `检查通过：52 个 HTML 文件，56 个文本文件。` `EXIT=0` |
| `smoke-new-charts.mjs` exit 1 khi fail | `scripts/smoke-new-charts.mjs` dòng cuối, cùng dạng `process.exit(1)` |
| Smoke cần Playwright cài **global**, không phải local | `smoke-new-charts.mjs` dòng 7–9: `execFileSync('npm', ['root','-g'])` rồi `import(path.join(globalRoot,'playwright','index.js'))` — comment trong file ghi thẳng "playwright 只装在全局" |
| Validate gác cả nội dung `SKILL.md`/`catalog.md`, không chỉ file tồn tại | `validate.mjs` kiểm `skillSource.includes('L1–L15 与 F1–F13')`, danh sách `catalogRows`, và 5 role màu `` `BG` `TXT` `MUT` `GRID` `DATA` `` |
| Validate cấm `Math.random()` và cấm hex "có màu" trong file mono | `validate.mjs`: regex `Math\.random\s*\(` → fail; và `Math.max(...channels) - Math.min(...channels) > 18` → "检测到明显彩色值" |
| Mặc định biểu đồ, báo cáo phải gọi tên | `SKILL.md` §0.1 (dòng 20–26) |
| Bản đồ chỉ bật khi gọi đích danh | `SKILL.md` §4 "地图显式触发规则" (dòng 177) + `catalog.md` mục "地图 · 2 张" + `SKILL.md` §7 |
| Thứ tự chọn Lupi → Basics → Glance | `SKILL.md` §0 luật 3/3.1/3.2/4 + §1 bước 2–3 |
| Số biểu đồ theo số kết luận, tối đa 6/trang | `SKILL.md` §1.2 bảng |
| Một giao phẩm chỉ một hệ màu | `SKILL.md` §6.5 "彩色硬规则" + `templates/color/README.md` |
| `PRESETS.get('porcelain'\|'palm'\|'wire')` là API màu | `color-presets.js` dòng 176–178 (`global.PRESETS = {…, get: n => …}`) |
| Token API: `MONO.CARD_CSS`, `MONO.obsReveal`, `MONO.rnd` | `mono-tokens.js` dòng 174–176 (`global.MONO = {...}`) |
| Bộ khung file HTML đơn | `SKILL.md` §9 (dòng 304+) |
| 12 report × 2 ngôn ngữ, index cục bộ | `report-catalog.md` bảng + `validate.mjs` vòng lặp `for (let i=1; i<=12; i++)` require cả `.zh.html`, `.en.html`, `docs/assets/reports/report-NN.png` |
| Repo **không** có CI riêng | `ls .github` → No such file or directory. Nên `06-ci-example.md` là ví dụ tự viết, không chép của ai. |
| `npx skills add` là package thật | `npm view skills` → version 1.5.23, bin `skills`. Package bên thứ ba, không thuộc repo này — vẫn nên verify sau khi cài (xem `01`). |

### Sai lệch docs↔code phát hiện được

Không chặn việc dùng, nhưng đừng tin con số trong README:

1. **Đếm biểu đồ lệch ba nơi.** `catalog.md` tiêu đề ghi "63 张"; đếm thật các dòng bảng: G=20, L=19, F=17, M=2, B=3 → **61**. Còn `README.md` mục Structure ghi "49 个图型", và bảng Templates ghi 15/13/18/3 (=49) — số cũ chưa cập nhật sau khi thêm L16–L20, F14–F17, G19–G22.
2. **Thiếu L18.** `catalog.md` nhảy từ L17 sang L19. `validate.mjs` cũng chỉ require `| L19 | Ridgeline |`, không require L18 — nên đây là khoảng trống có chủ ý (hoặc đã bị xoá) chứ không phải lỗi gate.
3. Suy ra: khi cần biết thật sự có bao nhiêu/những gì, **đọc `catalog.md` và `report-catalog.md`, không đọc README.**
