<!--
════════════════════════════════════════════════════════════════════════════
 design-template.md — TEMPLATE THIẾT KẾ TÁI DÙNG cho dây chuyền br
 Khung: Google-style Design Doc (Context/Scope · Goals · Design · Alternatives
 · Cross-cutting). Phần §3 "Hệ thống thiết kế thị giác" nạp từ skill
 /high-end-visual-design — DÙNG CHUNG mọi project, KHÔNG sửa khi copy.
 Cách dùng: copy file này → <project>/br/DESIGN.md, điền các ô {{...}} và §1/§2/
 §4/§6/§7 cho riêng sản phẩm; giữ nguyên §3 + §5 làm chuẩn kế thừa.
 BR.md trỏ tới file này bằng một clause NFR (vd N01 giao-diện), không chép lại.
════════════════════════════════════════════════════════════════════════════
-->
# DESIGN — {{Tên sản phẩm}}

| | |
|---|---|
| **Tác giả** | {{tên}} |
| **Trạng thái** | draft · in-review · approved |
| **Ngày** | {{YYYY-MM-DD}} |
| **BR nguồn** | `br/BR.md` (clause NFR: {{N01…}}) |
| **Design system** | §3 dưới đây (kế thừa `/high-end-visual-design`) |

---

## 1. Bối cảnh & Phạm vi (Context & Scope)
{{2–4 câu: sản phẩm là gì, ai dùng, thiết kế này phủ màn hình/luồng nào. Nêu
ràng buộc nền tảng: web/mobile, framework (React/Tailwind hay stdlib HTML…),
có phải single-file không.}}

## 2. Mục tiêu / Không phải mục tiêu (Goals / Non-goals)
**Mục tiêu**
- {{vd: mọi màn hình đạt cảm giác "agency-tier", không template-generic}}
- {{vd: dark/light toggle nhớ lựa chọn, chống FOUC}}

**Không phải mục tiêu**
- {{vd: chưa làm i18n}} · {{vd: không hỗ trợ IE11}}

---

## 3. Hệ thống thiết kế thị giác (kế thừa — KHÔNG sửa khi copy)
> Distill từ skill `/high-end-visual-design` (Vanguard_UI_Architect). Đây là
> chuẩn dùng chung; mỗi sản phẩm chỉ CHỌN archetype ở §3.2, không viết lại luật.

### 3.1 "Absolute Zero" — chống mẫu (bất kỳ cái nào lọt = fail)
- **Font cấm:** Inter, Roboto, Arial, Open Sans, Helvetica. Dùng: `Geist`, `Clash Display`, `PP Editorial New`, `Plus Jakarta Sans`.
- **Icon cấm:** Lucide/FontAwesome/Material nét dày. Dùng nét siêu mảnh: Phosphor Light, Remix Line.
- **Viền/bóng cấm:** viền `1px solid gray`; bóng tối gắt (`shadow-md`, `rgba(0,0,0,.3)`).
- **Layout cấm:** navbar sticky dán sát mép trên; grid 3 cột Bootstrap đối xứng thiếu whitespace.
- **Motion cấm:** transition `linear`/`ease-in-out`; đổi trạng thái tức thì không nội suy.

### 3.2 Creative Variance Engine — chọn 1 Vibe + 1 Layout mỗi sản phẩm
> **MẶC ĐỊNH DÂY CHUYỀN = Neumorphism (Vibe 0).** Mọi app /br sinh ra dùng
> Neumorphism trừ khi BR/DESIGN của sản phẩm nêu lý do đổi (vd cần OLED-dark cho AI
> tool → chọn Ethereal Glass). Đổi Vibe phải ghi lý do ở §6. Chi tiết công thức
> Neumorphism ở §3.6.

**Vibe (texture)**
0. **Neumorphism (MẶC ĐỊNH)** (app nghiệp vụ/dashboard/form nội bộ như Payroll): một mặt phẳng đơn sắc nhạt, component "đùn" ra hoặc "lõm" vào CÙNG màu nền bằng CẶP bóng mềm (sáng trên-trái + tối dưới-phải) — KHÔNG viền, KHÔNG đổi màu nền card. Tương phản bề mặt thấp, sang & tĩnh. Xem §3.6.
1. **Ethereal Glass** (SaaS/AI): OLED đen `#050505`, mesh gradient phát sáng nhẹ, card vantablack `backdrop-blur-2xl`, hairline `white/10`, chữ Grotesk hình học rộng.
2. **Editorial Luxury** (lifestyle/agency): kem ấm `#FDFBF7`, sage/espresso, serif biến thiên tương phản cao, phủ noise film-grain `opacity-[.03]`.
3. **Soft Structuralism** (consumer/health/portfolio): nền trắng/xám bạc, Grotesk đậm cỡ lớn, component nổi với bóng khuếch tán rất mềm.

**Layout**
1. **Asymmetrical Bento** — grid card kích cỡ lệch (`col-span-8 row-span-2` cạnh cột `col-span-4`). Mobile: về `grid-cols-1`, `gap-6`.
2. **Z-Axis Cascade** — card xếp chồng, lệch nhẹ `-2deg`/`3deg`. Mobile <768px: bỏ xoay + overlap, xếp dọc.
3. **Editorial Split** — chữ khổng lồ nửa trái `w-1/2`, nội dung cuộn/pill nửa phải. Mobile: `w-full` stack dọc.

**Mobile override (chung):** <768px ép `w-full`, `px-4`, `py-8`. Full-height dùng `min-h-[100dvh]` (không `h-screen` — tránh nhảy viewport iOS Safari).

### 3.3 Haptic micro-aesthetics
- **Double-Bezel (Doppelrand):** không đặt card phẳng lên nền. **Vỏ ngoài** `div` `bg-*/5` + hairline `ring-1 ring-*/5` + `p-1.5` + `rounded-[2rem]`; **Lõi trong** nền riêng + `shadow-[inset_0_1px_1px_rgba(255,255,255,.15)]` + bán kính đồng tâm `rounded-[calc(2rem-.375rem)]`.
- **Button-in-Button:** CTA là pill `rounded-full px-6 py-3`; icon `↗` nằm trong vòng tròn riêng `w-8 h-8 rounded-full bg-*/10`, sát mép phải.
- **Spatial rhythm:** section `py-24`→`py-40`. Eyebrow tag trước H1/H2: pill `text-[10px] uppercase tracking-[0.2em]`.

### 3.4 Motion choreography
- Cubic-bezier riêng: `transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]`.
- **Fluid Island nav:** pill kính nổi `mt-6 mx-auto w-max rounded-full`; hamburger morph thành 'X' (`rotate-45`/`-rotate-45`); menu mở overlay `backdrop-blur-3xl`; link reveal so le `translate-y-12 opacity-0` → `0/100` với `delay-100/150/200`.
- **Magnetic hover:** `group`; nhấn `active:scale-[0.98]`; icon lõi `group-hover:translate-x-1 -translate-y-[1px] scale-105`.
- **Scroll entry:** `translate-y-16 blur-md opacity-0` → `0 blur-0 100` >800ms, dùng `IntersectionObserver`/`whileInView` (KHÔNG `addEventListener('scroll')`).

### 3.5 Performance guardrails
- Chỉ animate `transform` + `opacity` (không `top/left/width/height`). `will-change` dùng dè sẻn.
- `backdrop-blur` chỉ trên fixed/sticky; không trên container cuộn.
- Noise overlay: pseudo-element `position:fixed; inset:0; pointer-events-none; z-index:50`.
- Z-index kỷ luật theo tầng hệ thống (nav/modal/overlay/tooltip), không `z-[9999]` tuỳ tiện.

### 3.6 Neumorphism recipe (Vibe mặc định — công thức bắt buộc)
Neumorphism = "đùn từ chất liệu": card/nút KHÔNG nổi TRÊN nền mà mọc RA TỪ nền, cùng
một màu, phân biệt chỉ bằng ánh sáng. Bốn luật cứng:

- **Một mặt đơn sắc:** nền và mọi surface CÙNG màu gốc (light `#e0e5ec`, dark `#2a2d32`). KHÔNG viền, KHÔNG màu card khác nền. Chiều sâu do bóng, không do màu.
- **Cặp bóng đối xứng (extrude/outset):** mỗi khối nổi có ĐÚNG 2 bóng — sáng góc trên-trái + tối góc dưới-phải, cùng offset/blur:
  ```css
  /* light: nguồn sáng trên-trái */
  box-shadow: -6px -6px 12px rgba(255,255,255,.75), 6px 6px 12px rgba(163,177,198,.55);
  /* dark */
  box-shadow: -6px -6px 12px rgba(255,255,255,.04), 6px 6px 12px rgba(0,0,0,.55);
  border-radius: 16px;  /* neumorphism cần bo tròn để bóng đọc được */
  ```
- **Trạng thái lõm (inset/pressed):** input, toggle bật, nút đang nhấn → ĐẢO bóng vào trong (`inset`), giữ nguyên cặp sáng/tối. Đây là cách DUY NHẤT thể hiện active/pressed:
  ```css
  box-shadow: inset -4px -4px 8px rgba(255,255,255,.7), inset 4px 4px 8px rgba(163,177,198,.6);
  ```
- **Không xung đột §3.1:** cặp bóng mềm này KHÁC bóng cấm — cấm là bóng tối gắt đơn (`rgba(0,0,0,.3)` một hướng) + viền `1px solid gray`. Neumorphism không viền, bóng khuếch tán, hợp lệ.

**Accent = NEAR-BLACK, không phải màu-rực** (bài học 13/07/26, sai 2 lần mới ra):
- ❌ Accent **cùng họ màu với nền** (vd xanh `#4d6bfe` trên nền xanh-xám) → **hoà vào nền ⇒ "chìm"**, dù pass AA.
- ❌ "Đối nghịch" **KHÔNG** có nghĩa là complementary hue. Chọn màu ấm (nâu/cam) để chọi nền lạnh → **lạc quẻ**, cãi nhau với bảng màu trung tính của neumorphism.
- ✅ Đối nghịch đúng là đối nghịch **ĐỘ SÁNG**: accent = **họ trung tính quanh đen** (`#1c1f26`), CTA phẳng đen chữ trắng. Tương phản tối đa mà **không thêm hue mới** ⇒ AAA + cohesive + premium.
- Màu rực chỉ dùng cho **semantic** (đỏ = destructive), KHÔNG làm accent chính.
- ✅ **Accent LẬT theo theme.** Đối nghịch là đối nghịch với **MẶT ĐANG DÙNG**: mặt sáng → accent tối (`#1c1f26`, chữ trắng); mặt tối → accent **sáng** (`#eef1f5`, chữ đen). Một hằng số accent cho cả 2 theme là **sai từ định nghĩa** — bản dark hay bị bỏ quên vì gate không chụp dark (xem `/visual-qa` § theme là một trạng thái).
- ❌ **Cấm hardcode màu chữ trên accent** (`color:#fff !important`): accent lật thì chữ phải lật ngược lại. Hardcode ⇒ theme kia thành **trắng-trên-trắng 1.13:1** (chữ tàng hình). Dùng token (`--primary-foreground`).

**Cảnh báo A11y — BAR LÀ AAA (7:1), KHÔNG PHẢI AA:** tương phản BỀ MẶT thấp là bản chất neumorphism, nhưng CHỮ và ICON phải đạt **WCAG AAA ≥7:1** (chữ lớn ≥4.5:1). **Pass ở SÀN AA (4.5:1) vẫn ra giao diện "chìm"/nhợt — người dùng nhìn phát biết ngay.** Sàn a11y ≠ đủ tương phản để đọc thoải mái. Ink light `#14171c`, muted `#3a4049` (bản `#454b56` chỉ 6.93:1 → trượt AAA). Không hạ contrast chữ để "cho mềm". Focus ring phải thấy rõ (ring accent, không dựa vào bóng).

**Tương phản là CON SỐ — bắt máy tính, cấm ước lượng bằng mắt.** Rubric ghi "chữ đạt AA" mà không cài assert ⇒ evaluator MÙ. Dùng `/visual-qa` (bất biến `contrast-aa`, FAIL cứng).

---

## 4. Theme & Design tokens (điền cho sản phẩm)
> Ràng buộc bắt buộc của repo: **có toggle dark/light, nhớ localStorage, chống FOUC**
> (đặt script set `data-theme` trong `<head>` TRƯỚC khi body render).

> Mặc định dưới đây là **palette Neumorphism** (Vibe 0). Đổi Vibe thì thay cả bảng.

| Token | Light | Dark |
|---|---|---|
| `--bg` (= `--card`, cùng màu) | `#e0e5ec` | `#2a2d32` |
| `--ink` (chữ, đạt AA) | `#3a4252` | `#c8ccd4` |
| `--accent` (CTA/trạng thái) | `#4a6cf7` | `#5d7bf9` |
| `--sh-light` (bóng sáng) | `rgba(255,255,255,.75)` | `rgba(255,255,255,.04)` |
| `--sh-dark` (bóng tối) | `rgba(163,177,198,.55)` | `rgba(0,0,0,.55)` |

- **Không có `--card` riêng:** neumorphism dùng chung màu nền cho card (§3.6). Chiều sâu = cặp bóng `--sh-light`/`--sh-dark`, không phải màu.
- **Cơ chế:** `:root[data-theme=dark]{…}` + `@media(prefers-color-scheme:dark){:root:not([data-theme=light]){…}}`.
- **Toggle:** nút `role="switch"`, ghi `localStorage`, đọc lại lúc load.
- **Chống FOUC:** inline `<script>` đọc localStorage → set `data-theme` ngay đầu `<head>`.

### 4.1 TOKEN KHOÁ — stream nhất quán xuyên frame (distill hallmark)
> File này là **HỆ THIẾT KẾ KHOÁ của sản phẩm** — đọc TRƯỚC, nó **đè** mọi lựa chọn khác. Mọi frame UI defer về đây.

- **Locked tokens, không ứng biến giữa lúc render:** mọi màu + `font-family` + bước spacing trong MỌI frame PHẢI trỏ token có tên ở §4 (`var(--accent)`, `var(--ink)`, `var(--font-display)`, thang 4/8px). **CẤM** inline hex/OKLCH/`rgb()`/`font-family:"…"` vượt token. Cần giá trị chưa có → **thêm token vào bảng §4 rồi trỏ tên**, KHÔNG tự chế tại frame.
- **Luật ĐẢO NGƯỢC của design-system (hallmark):** dự án có DESIGN.md = các trang/frame phải **CHIA SẺ hệ, GIỐNG nhau** — không mỗi frame một kiểu. Đa dạng hoá là SAI ở đây. Mục tiêu: mockup của frame-01 và frame-09 trông như **MỘT sản phẩm**, không phải hai người làm.
- **Gác drift (tất định):** `/qc-uiux` mục *consistency* + engine visual-qa bắt token lệch (màu/spacing/shadow ngoài hệ). Frame nào inline off-token = drift = CẦN SỬA. Đây là cách "stream UI/UX thống nhất" chạy được, không dựa lời dặn.

## 5. Pre-output checklist (cổng chốt — copy nguyên)
- [ ] Không dính font/icon/viền/bóng/layout/motion cấm ở §3.1
- [ ] Đã chọn 1 Vibe + 1 Layout archetype (§3.2) và áp nhất quán — **mặc định Neumorphism (Vibe 0), đổi thì ghi lý do §6**
- [ ] **(Neumorphism §3.6)** Surface đơn sắc cùng màu nền, KHÔNG viền/không màu card khác
- [ ] **(Neumorphism §3.6)** Mọi khối nổi dùng CẶP bóng sáng+tối đối xứng; active/input dùng `inset`
- [ ] **(Neumorphism §3.6)** Chữ/icon đạt WCAG AA dù bề mặt low-contrast; focus ring bằng accent, không dựa bóng
- [ ] Mọi card lớn dùng Double-Bezel (vỏ ngoài + lõi trong)
- [ ] CTA dùng Button-in-Button khi có icon
- [ ] Section tối thiểu `py-24` — bố cục "thở"
- [ ] Mọi transition dùng cubic-bezier riêng
- [ ] Có scroll entry animation — không phần tử nào hiện tĩnh
- [ ] <768px về 1 cột, `w-full`, `px-4`
- [ ] Animation chỉ `transform`/`opacity`
- [ ] `backdrop-blur` chỉ trên fixed/sticky
- [ ] Dark/light toggle + localStorage + chống FOUC hoạt động
- [ ] Ấn tượng tổng: "$150k agency build", không phải "template gắn font đẹp"

## 6. Phương án đã cân nhắc (Alternatives considered)
{{Nêu 1–2 hướng thiết kế khác đã loại + lý do — vd "material default: loại vì generic".}}

## 7. Vấn đề xuyên suốt (Cross-cutting)
- **A11y:** tương phản ≥ WCAG AA; focus ring rõ; `role`/`aria-*` cho toggle & nav.
- **Responsive:** breakpoint chuẩn theo §3.2 mobile override.
- **Hiệu năng:** theo §3.5; đo lại trên mobile thật nếu có blur/noise.
- **Nguồn design system:** `/high-end-visual-design` — cập nhật skill thì re-distill §3.
