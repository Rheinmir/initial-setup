---
name: dym-lieflat-charts-contributor-checks
description: "Hai gate khi bạn sửa chính repo. chỉ dành cho người sửa template/token/catalog trong repo. Người dùng cuối không bao giờ cần file này."
disable-model-invocation: true
---

# Skill: dym-lieflat-charts-contributor-checks — Hai gate khi bạn sửa chính repo

**Vì sao dùng:** chỉ dành cho người sửa template/token/catalog trong repo. **Người dùng cuối không bao giờ cần file này.**
**Sinh ra cái gì:** không sinh file. Chỉ trả exit code + danh sách lỗi ra stderr.

Repo **không có `.github/workflows/`** (đã kiểm: `ls .github` → không tồn tại). Hai script này là gate chạy tay.

## Gate 1 — `validate.mjs` (bắt buộc, không phụ thuộc gì)

```bash
cd <repo>
node scripts/validate.mjs; echo "EXIT=$?"
```

Chạy thật ở commit `475c9b6`:

```
检查通过：52 个 HTML 文件，56 个文本文件。
EXIT=0
```

Khi fail:

```
检查失败（N 项）：
- <mô tả lỗi>
...
EXIT=1
```

**Exit code: 0 = pass, 1 = fail. Không có mã nào khác** — kiểm tận nơi ở `scripts/validate.mjs`, chỉ có đúng một lời gọi `process.exit(1)`, còn đường pass rơi xuống `console.log` rồi kết thúc bình thường. Vế pass in ra **stdout**, vế fail in ra **stderr**.

Nó gác 7 nhóm, và điểm đáng chú ý là nó gác cả *nội dung tài liệu*, không chỉ sự tồn tại của file:

1. **File phát hành tồn tại** — `SKILL.md`, `catalog.md`, `report-catalog.md`, `mono-tokens.js`, `color-presets.js`, `agents/openai.yaml`, 19 file `templates/color/*`, và cho mỗi `NN` từ 01→12: cả `report-NN.zh.html`, `report-NN.en.html`, `docs/assets/reports/report-NN.png`.
2. **Gallery đủ hình** — mỗi nhóm (basics/lupi/glance/maps) × mỗi bản màu (gallery/porcelain/palm/wire) phải chứa đủ các `id="..."` bắt buộc (vd basics phải có `treemap`, `histo`, `boxplot`, `stream`, `candle`), và chuỗi đánh số phải khớp regex (`L1–L19` hoặc `19 张`…).
3. **Luật trong `SKILL.md` không được xoá lén** — bắt buộc còn chuỗi `L1–L15 与 F1–F13`, còn 5 ngoại lệ hình dự bị (`F17 Candlestick`, `F15 Tick Box`, `L20 Parallel Coordinates`, `L17 Calendar Heat`, `F16 Stream Ribbon`), và 5 role màu custom `` `BG` `TXT` `MUT` `GRID` `DATA` ``.
4. **`catalog.md` còn đủ dòng** — danh sách cứng F13–F17, L16/L17/L19/L20, G19–G22, M1/M2, và cụm chữ `主力与后备`.
5. **Cú pháp JS** — trích từng khối `<script>` trong **mọi** file HTML rồi `new vm.Script(...)`. Đây là bản `node --check` cho HTML.
6. **Không trùng `id`** trong cùng một file HTML (báo kèm số dòng cả hai lần xuất hiện).
7. **Kỷ luật màu và tính tất định:**
   - `Math.random(` xuất hiện ở bất kỳ file `.html/.js/.mjs` nào (trừ chính `validate.mjs`) → fail, phải dùng `rnd()` tất định.
   - File `templates/color/*-{porcelain,palm,wire}.html` chỉ được dùng đúng các kênh màu có trong preset tương ứng của `color-presets.js` — lệch một hex là fail.
   - File còn lại (trừ `color-presets.js` và `templates/reports/`) không được có hex "có màu": nếu `max(R,G,B) - min(R,G,B) > 18` → "检测到明显彩色值".

Hệ quả thực dụng: **đổi màu trong file mono thì gate cắn.** Muốn thêm màu, phải thêm vào `color-presets.js` và đặt file dưới `templates/color/`.

## Gate 2 — `smoke-new-charts.mjs` (cần Playwright cài GLOBAL)

```bash
npm install -g playwright        # bắt buộc global, xem lý do bên dưới
npx playwright install chromium  # tải browser binary
node scripts/smoke-new-charts.mjs; echo "EXIT=$?"
```

Pass:

```
烟测通过：12 个 gallery 的新增图型均已绘制，无控制台错误。
EXIT=0
```

Fail: liệt kê từng mục ra stderr rồi `EXIT=1`.

**Vì sao phải global:** script tự giải đường dẫn bằng `execFileSync('npm', ['root','-g'])` rồi `import()` từ đó. Comment trong file ghi rõ: `playwright 只装在全局，ESM 不认 NODE_PATH`. Cài local vào `node_modules/` sẽ **không** được nhận. Máy khảo sát chưa có Playwright global (`ls "$(npm root -g)/playwright"` → không có) nên gate này **chưa chạy thật ở đây** — trạng thái pass/fail của nó chưa được xác nhận.

Nó làm gì: mở 12 file gallery bằng `file://` (basics/lupi/glance × gallery/porcelain/palm/wire), chờ 2.5s, cuộn từng `id` vào giữa màn hình (vì render lười bằng IntersectionObserver), chờ thêm 1.2s, rồi khẳng định:

- container tồn tại,
- kích thước ≥ 50×30 px,
- có ≥ 3 node con thuộc `path,rect,circle,line,polygon,canvas,svg,text`,
- không có console error hay pageerror nào.

**Nhóm maps cố tình bị bỏ ngoài** — bản đồ cần GeoJSON online, offline báo lỗi là đúng dự kiến.

## Thứ tự làm khi sửa template

```bash
# 1. sửa file
# 2. gate rẻ trước
node scripts/validate.mjs || echo "FAIL — sửa trước khi đi tiếp"
# 3. gate đắt sau (cần browser)
node scripts/smoke-new-charts.mjs
# 4. mắt người: mở gallery, cuộn hết, so với ảnh trong docs/assets/
open templates/basics-gallery.html
```

Thêm hình mới thì phải sửa đồng bộ **bốn** chỗ, nếu không gate cắn: `templates/<nhóm>-gallery.html`, ba bản `templates/color/<nhóm>-{porcelain,palm,wire}.html`, một dòng trong `catalog.md`, và (nếu nó là hình dự bị được miễn trừ) mục tương ứng trong `SKILL.md` §0 3.2.
