---
name: reskin
description: Lột da một app đang chạy theo DNA của một thiết kế tham chiếu, gác bằng luật tất định cho tới khi hết AI-slop, rồi ship. Sáu chặng nối liền: đo DNA từ URL/ảnh thật bằng runtime (WAAPI keyframes, scroll trace, hover diff) chứ không đọc HTML tĩnh; khoá vào design.md của hallmark; đổ thành DESIGN.md contract cho impeccable; tokenize hex cứng thành CSS var để đổi bảng màu là đổi ~20 dòng chứ không sed 18 file; chạy vòng impeccable detect trên BẢN BUILD PRODUCTION tới khi sạch; ship ra git + Vercel kèm biên bản audit. Gọi khi user nói: 'lấy theme trang này', 'áp design này vào app', 'trang trông AI quá dọn đi', 'đổi bộ màu theo brand book', 'quét slop', 'reskin', 'redesign rồi deploy demo', hoặc invoke /reskin.
---

# Skill: reskin

Ghép sáu flow rời — trích design, hallmark, impeccable, tokenize, gate, ship — thành **một
đường ống**. Mỗi chặng đưa ra một artifact mà chặng sau đọc được, nên bỏ chặng giữa là gãy.

Giá trị không nằm ở việc đổi màu. Nằm ở chỗ **có một cổng tất định** đứng giữa "trông đẹp"
và "được ship": `impeccable detect` cho một con số, và con số đó phải giảm.

## When to use

- "Lấy theme/design của trang này áp vào app tôi", "clone cảm giác của site kia".
- "Trang trông AI-generated quá", "dọn slop", "audit design".
- "Đổi bộ màu theo brand book", "làm bản màu thương hiệu để demo".
- Sau redesign muốn có **bằng chứng** chứ không phải cảm tính: 108 → 2 finding.
- KHÔNG dùng cho: sửa một component lẻ (dùng `hallmark` component-scope), hay chỉ đổi
  một hằng số màu (sửa token, xong).

## Steps

### 0 · Khoanh phạm vi + hỏi quyền trích

Hỏi hai câu TRƯỚC khi đo, vì cả hai đổi việc phải làm:

1. **Nguồn là gì với user?** (a) site của họ · (b) tham chiếu công khai cho brand của họ ·
   (c) của người khác. `(c)` → chỉ giao bản chẩn đoán, **không** emit `design.md`
   (luật refusal của `hallmark study`).
2. **Ghi vào project nào, màn hình nào?** Cột path trống là chỗ phải hỏi, không phải chỗ đoán.
   Mặc định an toàn: chỉ surface marketing/landing, không đụng portal nội bộ.

Nếu project đã có `DESIGN.md`/`design.md` cũ → **đổi tên thành `*-<tên-hệ-cũ>.legacy.md`**,
đừng ghi đè. Hệ cũ là tài liệu, không phải rác.

### 1 · MEASURE — đo runtime, đừng đọc HTML

Framer/Next/SPA không lộ motion trong HTML. `WebFetch` chỉ thấy vỏ. Dùng Playwright script
standalone (`playwright-verify`), đo bốn thứ:

```js
// tokens: duyệt `body *`, gom computed style theo tần suất
//   color/bg (có text node) · fontFamily/Size/Weight/letterSpacing/lineHeight
//   borderRadius · boxShadow · gap · padding · backgroundImage(gradient) · backdropFilter
// motion: document.getAnimations() NGAY sau domcontentloaded  → WAAPI keyframes
//   spring của framer-motion bị bake thành ~41-47 mẫu linear; đỉnh >1.0 = overshoot
// scroll: scrollTo theo bước 800px, mỗi bước ghi transform/opacity/position/willChange
//   → bắt sticky, marquee, card-stack, parallax, per-char reveal
// hover: el.hover() rồi diff computed style trước/sau → biết hover đổi ĐÚNG mấy thuộc tính
```

Chụp full-page ở **1440 và 390**. Rhythm/độ đặc phải nhìn bằng mắt, số không nói được.

> Đọc được `dur`, `delay`, `from → to` của từng phần tử thì mới chép được nhịp. Ví dụ đo
> thật: cascade hero `0 · 100 · 200 · 400 · 600 · 800 · 900ms`, container chỉ fade,
> **chỉ nội dung mới travel** — đó là thứ HTML không bao giờ nói cho bạn.

### 2 · LOCK — khoá vào hallmark

Ba file, một nguồn chân lý:

| file | vai trò |
|---|---|
| `design.md` | DNA: System · Provenance · Tokens · CTA voice · Motion stance · **Notes (thứ KHÔNG kế thừa)** |
| `tokens.css` | canonical — mọi giá trị OKLCH/font/space/radius/shadow/motion |
| `motion.md` | spec chuyển động đầy đủ; `design.md` và contract impeccable đều trỏ vào đây |

`## Notes` là mục quan trọng nhất: nguồn tham chiếu **luôn** có khuyết tật đáng chép nhầm.
Bắt buộc soi và ghi rõ 4 thứ này (thực nghiệm: trang nào cũng dính ít nhất 2):
focus ring có không · `prefers-reduced-motion` có không · thẻ heading chọn theo cỡ chữ hay
theo thứ tự tài liệu · số liệu có phải placeholder không.

⚠️ **macOS case-insensitive: `design.md` và `DESIGN.md` LÀ MỘT FILE.** Đừng tạo cả hai ở
root. Gộp làm một, đặt tên `DESIGN.md` (Linux CI phân biệt hoa thường, impeccable tìm tên này).

### 3 · CONTRACT — đổ sang impeccable

```bash
npm install --save-dev impeccable        # KHÔNG dùng npx: npx gộp stderr vào stdout,
./node_modules/.bin/impeccable --version # `2> findings.txt` sẽ ra file RỖNG
```

⚠️ `npx impeccable install --help` **không in help — nó cài thật**, và không có TTY thì
mặc định rơi về **global** ($HOME). Nếu phải cài skill bundle: `install -y --scope=project`.

Viết `DESIGN.md` (root) + copy sang `.impeccable/DESIGN.md`. Ngoài phần DNA, thêm mục
**Enforcement**: bảng luật của riêng dự án, mỗi luật một dòng + severity. Đây là thứ biến
"gu thẩm mỹ" thành thứ review được. Mẫu luật rút từ thực chiến:

| # | luật | sev |
|---|---|---|
| 1 | `border: 1px solid` để chia khối — hệ này dùng tonal shift + shadow | P1 |
| 2 | Thêm accent có sắc độ ngoài bảng | P1 |
| 3 | Chữ trên nền sáng hơn ngưỡng AA của hệ | P0 |
| 4 | Thiếu `:focus-visible` | P0 |
| 5 | Thiếu nhánh `prefers-reduced-motion` | P0 |
| 6 | `hover:scale-*` / transform khi hover — hover đổi ĐÚNG một thuộc tính | P2 |
| 7 | Font thứ ba, heading in nghiêng, heading viết hoa toàn bộ | P1 |
| 8 | Radius ngoài thang | P2 |
| 9 | Shadow đen thay vì shadow ám màu rule | P2 |
| 10 | Số liệu bịa trong copy | P1 |
| 11 | Màu sáng (accent nhạt) dùng làm **chữ** — nó là nền, không phải foreground | P0 |
| 12 | Chữ xám trung tính trên nền có màu — phải ám theo hue của nền | P2 |

### 4 · APPLY — tokenize trước, đổi màu sau

Sai lầm tốn nhất: sed thẳng hex-cũ → hex-mới trong JSX. Lần đổi bảng màu thứ hai phải sed lại
từ đầu. **Tokenize một lần:**

```
bg-[#121218]  →  bg-[var(--ink)]        // Tailwind arbitrary value ăn var, kể cả /20 opacity
'#121218'     →  'var(--ink)'           // inline style / JS literal
```

Rồi mỗi biến thể = một block ~20 token dưới `.app-scope[data-brand="x"]`. Muốn xem thử:
đọc `?brand=x` từ `window.location.search` trong `useEffect` (khỏi cần Suspense boundary)
và set `data-brand` trên wrapper.

Vai trò token tối thiểu — **tách bạch cặp on-light và cặp on-dark**, đây là chỗ hay sập:

```
--paper --paper-2 --paper-3 --paper-4 --rule
--ink --ink-lift --ink-2 --ink-2-deep --ink-3
--accent --accent-ink      // dùng trên nền SÁNG
--cta-bg --cta-ink         // dùng trên nền TỐI
--on-dark-2                // chữ phụ trên nền tối
--nav-bg --scrim
```

**Neo chữ vào surface, đừng neo vào overlay.** Nền tối phải nằm trên chính element ôm layout;
nếu nó chỉ do một `<div class="absolute inset-0">` anh em vẽ ra thì mọi phân tích tĩnh (và
mắt người khi ảnh 404) đều thấy chữ trắng trên nền sáng.

### 5 · GATE — vòng lặp trên BẢN BUILD

```bash
npm run build                                   # ulimit -n 16384 nếu sập ENFILE
lsof -ti:3001 | xargs -r kill -9                # ⚠️ BẮT BUỘC — xem cảnh báo dưới
PORT=3001 npm start &
./node_modules/.bin/impeccable detect http://localhost:3001 --json > f.json
```

Nhóm finding theo `antipattern`, sửa từ nhóm đông nhất, **quét lại sau mỗi nhóm**, ghi lại
con số từng vòng. Quét thêm `--viewport 390x844`.

Mã thoát: `0` sạch · `1` lỗi vận hành (ưu tiên hơn) · `2` có finding. `rc=2` là "có phát
hiện", không phải "hỏng". Target sai đường dẫn **vẫn thoát 0** — CI xanh mà quét 0 file.

⚠️ **Cổng sai nguy hiểm hơn không có cổng.** Ba lần đọc nhầm đã gặp thật:
- **Server cũ còn giữ port** → `next start` mới báo `EADDRINUSE` rồi chết, bản cũ vẫn phục vụ,
  **mọi finding đều là số của bản cũ**. Luôn `lsof -ti:<port>` trước khi tin kết quả.
- **`npm run build` xoá `.next` khi dev server đang chạy** → trang 500, detect ra "0 finding".
  0 không phải lúc nào cũng là sạch — kiểm HTTP code + grep một chuỗi có thật trong trang.
- **Quét dev server** → dev overlay của Next tự đẻ finding (amber/slate không có trong code).

**Đừng waive khi chưa đo.** Detector đọc `canvas`/compositing layer nên sai được: có case nó
báo `1.6:1` trong khi đo tại chỗ nền `rgb(18,18,24)` + chữ `#FFFFFF` = **18.6:1**. Đo bằng
Playwright trước; sai thật thì sửa, false positive thì **ghi bằng chứng vào DESIGN.md và để
luật sống** — đừng tắt luật chỉ vì nó ồn.

Waive có lý do, đúng tầng (`.impeccable/config.json` commit, `config.local.json` gitignore):

```bash
./node_modules/.bin/impeccable ignores add-value overused-font Inter --reason "..."
./node_modules/.bin/impeccable ignores add-rule nested-cards --reason "..."
```

### 6 · SHIP — kèm biên bản

Ghi vào `DESIGN.md` một mục audit: bảng `đầu → sau khi sửa → sau khi waive`, **root cause**
(không phải danh sách triệu chứng), và những gì cố ý để lại kèm lý do. Rồi:

```bash
git checkout -b feat/<...>          # đang ở nhánh mặc định thì TÁCH NHÁNH trước
git add -A && git commit            # commit body kể root cause, không kể diff
git push -u origin <branch>
```

403 = không có quyền push → **fork + MR**, đừng xin quyền rồi ngồi chờ:
`glab repo fork <ns>/<repo> --clone=false` → push lên fork → `glab mr create --head <you>/<repo> --repo <ns>/<repo>`.

Vercel: `vercel deploy --prod --yes --archive=tgz < /dev/null`. Đóng stdin vì nó sẽ hỏi
"connect git remote nào" và treo. Kiểm URL live: HTTP 200 **và** grep một chuỗi có thật
(deployment protection trả 200 kèm trang đăng nhập). Quét `impeccable detect <url-live>` —
số trên live phải khớp số trên local, lệch là build khác.

## Rules

- **Đo trước, kết luận sau.** Mọi con số trong artifact phải đến từ một lần chạy thật.
  Không có "khoảng 400ms" — có `dur=400 delay=900 fill=both` hoặc không có gì.
- **Fix ở gốc, không ở triệu chứng.** Ba root cause đã trả giá, gặp lại thì nhớ ngay:
  - `background:` shorthand **xoá** `background-color` → mọi mặt tối resolve về nền sáng của
    cha. Dùng `background-image` + `background-color` tách bạch.
  - `letter-spacing` theo `px` vỡ theo cỡ chữ: `-1.44px` đúng ở 72px, thành `-0.08em` ở 18px.
    Luôn dùng `em`.
  - framer-motion ghi `transform` inline khi animation đáp → `left:50% + translateX(-50%)`
    bị xoá. Căn giữa bằng `left/right:0 + margin-inline:auto`.
- **Brand book thắng file asset.** SVG logo render một màu, brand book ghi màu khác → theo
  book. Đọc luôn luật ghép màu của book (thường có dạng "một core + một vibrant, đừng ghép
  hai core") và luật typography — nó có thể **phủ định** DNA vừa trích (vd: book bắt một font
  sans cho mọi cấp chữ ⇒ biến thể brand phải bỏ serif display). Nói rõ chỗ mâu thuẫn đó ra.
- **Kiểm subset font trước khi nhận.** Sản phẩm tiếng Việt mà font không có subset
  `vietnamese` thì dấu rơi sang font fallback, chữ lai. Kiểm bằng
  `curl 'https://fonts.googleapis.com/css2?family=X' -H 'User-Agent: Mozilla/5.0…'` rồi tìm
  dải `U+1EA0-1EF9`. Không có thì đổi mặt chữ, đừng đổi ngôn ngữ.
- **Màu nhạt là nền, không phải chữ.** Accent có luminance cao (mint/amber/pastel) không bao
  giờ làm chữ trên nền sáng, cũng không bao giờ để chữ trắng lên nó. Tính contrast rồi mới gán
  vai trò, đừng gán rồi mới tính.
- **Sắc độ mạnh làm quầng radial = slop.** Cùng một màu thương hiệu: làm nền đặc (nút, gạch
  chân) thì sạch; trải thành `radial-gradient` mờ trên nền tối thì detector bắt
  `ai-color-palette` / `radial-spotlight-glow`. Không khí dùng màu core, accent dùng đặc.
- **Taxonomy màu (category/status) giữ màu ở bảng ops, tonal ở trang marketing.** Ở bảng dữ
  liệu hue mang nghĩa; ở landing 15 hue là dấu vết AI. Cùng một catalog, hai cách render.
- **Chữ trên ảnh: màu đặc, đừng dùng alpha.** `text-white/60` trộn với ảnh bên dưới. Dùng màu
  đặc + scrim thật, và cân nhắc `filter: grayscale()` cho ảnh nếu hệ là monochrome — nó vừa
  đúng DNA vừa giết luôn phần lớn finding contrast.
- **Đừng bulldoze.** Nêu đúng danh sách file sẽ sửa/tạo/xoá trước khi sửa; xoá phải xin phép.
  Chỉ chạm surface đã khoanh — portal nội bộ giữ nguyên hệ cũ là chuyện bình thường.
- **Tài liệu nội bộ đóng dấu Confidential thì gitignore, không hỏi.** Không đẩy lên repo dù
  repo là private.

## Verify

Xong chặng 6 mới được gọi là xong. Bằng chứng tối thiểu:

1. `impeccable detect <url-prod-local>` và `<url-live>` cho **cùng một con số**.
2. Con số vòng đầu và vòng cuối đều nằm trong `DESIGN.md`, kèm root cause.
3. `tsc --noEmit` sạch, lint sạch, build rc=0.
4. Ảnh full-page 1440 + 390 của **từng biến thể**, không tràn ngang, không link 2 dòng.
5. Mọi finding còn lại: hoặc có waiver kèm lý do trong `.impeccable/config.json`, hoặc có
   phép đo phản chứng ghi trong `DESIGN.md`. Không có finding nào "để đó".
