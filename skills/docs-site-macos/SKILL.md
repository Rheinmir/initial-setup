---
name: docs-site-macos
description: >
  Build a beautiful macOS-inspired documentation site (single HTML file) with a liquid-glass
  surface system (tiered glassmorphism: opacity ladder, blur scale, edge highlights), animated
  SVG diagrams, traffic-light window chrome, and a light-blue + white liquid-glass palette
  (white glass surfaces over a soft blue gradient field, per-section blue-tone theming).
  Also trigger on "liquid glass", "frosted glass", or "translucent UI" requests for docs/showcase pages.
  Trigger when the user wants to create a docs site, landing page, showcase, portfolio, guide,
  tutorial site, feature overview, or product documentation — especially when they mention
  wanting it to look "clean", "modern", "Apple-like", "macOS style", "glass", "frosted",
  "animated diagrams", or "single HTML file". Also use when the user has multiple markdown
  files and wants them rendered into a cohesive visual HTML page with sections.
  If the user says "6 file" or wants separate pages per topic, generate one HTML file per
  wiki file (index.html as overview + N topic files), NOT a single combined page.
---

# macOS Docs Site Builder

Build a **single-file HTML documentation site** with macOS-inspired design system.
Output is a self-contained `.html` file (no JS libraries, no build step).

## Design System

### Color Palette

Base: white glass surfaces over a soft light-blue gradient field (see Background Plane below)
Text: `#0f0f12` / `#4a4a55`
Border: `rgba(30,90,170,.14)` (cool blue-gray — never white-on-white)

Palette is LIQUID-GLASS LIGHT-BLUE + WHITE for the PATTERN (surfaces, background field, nav, hero, links). CONTENT section accents cycle Apple's secondary palette (see Palette Philosophy below) — confined to tags/h4/bullets so nhiều màu vẫn không rối. No flat-black accents, no saturated-color headings.

### Background Plane (glass needs something to sample)

Honest naming: this design system is **pragmatic CSS glass** (transparency + backdrop blur), not true refraction. For the blur to read as material at all, the body background must NOT be a flat fill — give it a restrained monochrome gradient field:

```css
body{
  background:
    radial-gradient(900px 500px at 12% -10%, rgba(10,132,255,.10), transparent 60%),
    radial-gradient(700px 420px at 95% 15%, rgba(90,162,232,.08), transparent 55%),
    linear-gradient(180deg, #f7fbff 0%, #eaf2fd 100%);
}
```

Keep it this quiet — blue-family tints only, no loud glow layers ("light pollution"). The per-section `.s-bgN::before` overlays add the rest of the local variation.

**Base refraction plane (BẮT BUỘC — gương phải thấy gì bên dưới):** gradient phẳng không đủ cho blur "nghiền" — thêm 2 lớp fixed `z-index:-1` dưới mọi content: (1) ORBS — 5-6 radial blobs lớn (blue chủ đạo + 1-2 tint Apple secondary, alpha .06-.22) trôi rất chậm (~46s ease alternate, translate ≤2.5% + scale ≤1.05); (2) DOT-GRID mảnh 1px/22px alpha ~.11 có mask fade dọc — chi tiết tần số cao để backdrop-filter biến thành texture kính thật. **Đặt ít nhất 1-2 orb dọc mép TRÁI viewport (sau lưng sidebar)** — sidebar là pane kính lớn nhất trang, không có màu sau lưng thì blur cỡ nào cũng ra tấm trắng. Kèm `@media (prefers-reduced-motion:reduce){animation:none}`:

```css
body::before{content:'';position:fixed;inset:-10%;z-index:-1;pointer-events:none;
  background:
    radial-gradient(640px 440px at 10% 14%,rgba(10,132,255,.22),transparent 65%),
    radial-gradient(380px 460px at 4% 52%,rgba(48,176,199,.18),transparent 65%),
    radial-gradient(540px 400px at 88% 10%,rgba(88,86,214,.13),transparent 60%),
    radial-gradient(720px 500px at 74% 76%,rgba(48,176,199,.13),transparent 65%),
    radial-gradient(480px 380px at 16% 86%,rgba(255,149,0,.12),transparent 60%);
  animation:orbDrift 46s ease-in-out infinite alternate}
@keyframes orbDrift{100%{transform:translate(2.2%,1.6%) scale(1.045)}}
body::after{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;
  background-image:radial-gradient(rgba(30,90,170,.11) 1px,transparent 1.3px);
  background-size:22px 22px;
  mask-image:linear-gradient(180deg,rgba(0,0,0,.55),rgba(0,0,0,.22))}
```

### Liquid-Glass Surface System (opacity ladder + blur scale)

Glass is a **depth system, not a single class**. Three surface tiers, each with its own alpha + blur — never repeat one alpha everywhere:

```css
:root{
  --glass-1: rgba(255,255,255,.55);  /* tier 1 — chrome: nav, floating panels */
  --glass-2: rgba(255,255,255,.7);   /* tier 2 — cards, diagram-box, repo-card */
  --glass-3: rgba(255,255,255,.88);  /* tier 3 — data: tables, long text (calmer, near-solid) */
  --blur-1: 24px; --blur-2: 8px; --blur-3: 4px;
  --edge-hi: inset 0 1px 0 rgba(255,255,255,.85);  /* top inner highlight — REQUIRED on every glass surface */
  --border: rgba(30,90,170,.14);
}
```

Tier assignment: `nav` = tier 1 · `.card` / `.diagram-box` / `.repo-card` = tier 2 · `table` / dense data zones = tier 3. Reserve the strongest glass for chrome; content density rises as material strength drops.

### Palette Philosophy: blue = PATTERN, Apple secondary = CONTENT

**Blue is the chrome/pattern color ONLY** — sidebar nav, hero gradient, links, structural accents. Modern iOS tone `#0a84ff`, never dark/navy starts. **Content sections cycle through Apple's secondary palette** (teal/indigo/green/orange/pink) — nhiều màu được, miễn không rối: accents stay confined to `.tag`, `.card h4`, and `li::before` bullets.

**Headings are DARK, never saturated color**: `.section-header h2 { color: #1d1d1f }` for every section. A saturated blue heading reads dated ("nhà quê") — Apple uses near-black headlines with a colored eyebrow tag above.

### Section Color Cycle (Apple secondary)

```css
#sec-0 .tag { background: rgba(10,132,255,.10); color: #0a84ff; }   /* blue */
#sec-0 .card h4 { color: #0a84ff; } #sec-0 .card li::before { color: #0a84ff; }
#sec-0 .section-header h2 { color: #1d1d1f; }  /* h2 luôn tối, mọi section */
.s-bg0::before { background: linear-gradient(180deg, rgba(10,132,255,.05) 0%, transparent 60%); }
/* then sec-1..5 per the table; repeat #sec-6 = #sec-0, ... */
```

**Full accent table:**

| Index | Accent | h4 tone | Gradient overlay |
|-------|--------|---------|------------------|
| 0     | `#0a84ff` blue   | `#0a84ff` | `rgba(10,132,255,.05)` |
| 1     | `#30b0c7` teal   | `#30b0c7` | `rgba(48,176,199,.05)` |
| 2     | `#5856d6` indigo | `#5856d6` | `rgba(88,86,214,.05)` |
| 3     | `#34c759` green  | `#28a745` | `rgba(52,199,89,.05)` |
| 4     | `#ff9500` orange | `#f08c00` | `rgba(255,149,0,.06)` |
| 5     | `#ff2d55` pink   | `#e0264b` | `rgba(255,45,85,.05)` |

For each section, use the accent for:
- `.tag` background (at 10-12% opacity) + text
- `.card h4` color (use the darker h4 tone for orange/green/pink so text stays readable)
- `.card li::before` color (the `›` bullet)
- ⛔ NOT for `.section-header h2` — h2 is always `#1d1d1f`

### Glassmorphism Cards

```css
.card {
  background: var(--glass-2);
  backdrop-filter: blur(var(--blur-2)) saturate(1.1);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--edge-hi), 0 4px 20px rgba(20,40,90,.08);  /* top highlight + lower BLUE-TINTED shadow = directional light; never pure black on a blue field */
  padding: 20px;
}
```

`.diagram-box` and `.repo-card` share this tier-2 recipe. `table` (and any dense data region) drops to tier 3: `background: var(--glass-3); backdrop-filter: blur(var(--blur-3))` — same border + edge highlight, calmer material so rows stay legible.

**Liquid-glass rules (distilled from the liquid-glass-design skill):**
- Edge highlight is mandatory — glass without `--edge-hi` reads as a washed card.
- Directional light: faint top inner highlight + soft lower outer shadow on every pane.
- Text never sits on heavy blur alone; tier 3 (near-solid) backs all long-form reading and tables.
- Stacked glass must differ by at least one tier (alpha AND blur step) or the layers collapse into mud.
- Glow stays faint and blue-family only — depth comes from the ladder, edges, and shadow, not atmosphere.
- **Large chrome panes (sidebar, full-height panels) NEVER use one flat alpha** — flat white fill reads as a milky wall ("màu trơn trông chắn"). They need gradient-alpha glass + a specular sheen `::before` + a color orb directly behind them. See the Navigation section for the canonical recipe.

### macOS Chrome Elements

The **repo card** and **converter mockup** use a macOS window header:
```html
<div class="chrome">
  <span style="width:12px;height:12px;border-radius:50%;background:#ff5f57"></span>
  <span style="width:12px;height:12px;border-radius:50%;background:#ffbd2e"></span>
  <span style="width:12px;height:12px;border-radius:50%;background:#28c840"></span>
  <div class="url-bar">...</div>
</div>
```

⚠️ **Boxed full-width elements (repo-card, converter mockup, bất kỳ panel có viền) PHẢI có gutter ngang giống hero/section** (bài học 13/06/2026 — user chê repo-card "chạm sát mép màn hình, nên có padding trái phải"): hero/section ăn gutter qua `padding:…24px` BÊN TRONG container `max-width:1100px`, nhưng một boxed element chỉ đặt `max-width:1100px;margin:auto` sẽ **chạm sát 2 mép viewport** khi màn hẹp hơn 1100px (vì nó không có padding trong, mà chính cái box là content). Fix: cho box cùng lề NỘI DUNG với hero bằng `max-width:1052px` (= 1100 − 48 gutter) **và** `width:calc(100% - 48px)`:

```css
.repo-card{ max-width:1052px; width:calc(100% - 48px); margin:8px auto 0; /* …glass tier-2… */ }
```

Rộng → cap 1052 căn giữa, thẳng hàng với chữ trong hero (1100−24−24); hẹp → luôn chừa 24px mỗi bên. Áp dụng cho MỌI boxed element đặt trực tiếp dưới `<body>` (ngoài luồng `section`): repo-card, converter mockup, banner/callout full-width.

⚠️ **Body cuối của boxed element cần padding-bottom rộng hơn padding-top** (bài học 13/06/2026 — user chê "chỗ chuyển tiếp bị cắt đứt không mượt"): khối nội dung cuối (vd `.rc-body`) nối thẳng xuống section kế tiếp; nếu padding dưới = padding trên (16px) thì chữ áp sát mép box, đọc như bị cụt. Cho đáy thở thêm: `padding:16px 18px 22px` (đáy ≥ trên + 6px). Quy tắc: pane kết thúc bằng text → bottom-pad ≥ top-pad.

### Navigation — SIDEBAR ONLY (không bao giờ dùng top bar)

Mọi cỡ màn hình đều dùng LEFT SIDEBAR + nút collapse. ⛔ KHÔNG có chế độ top bar — top bar nhồi link wrap chữ rất xấu trên màn hẹp. Màn hẹp (<640px): sidebar OVERLAY đè content (body giữ padding-left:0), mặc định THU GỌN, user mở bằng nút toggle:

⚠️ **Sidebar PHẢI là kính thật, không phải tấm trắng sữa** (bài học 12/06/2026 — user chê "màu trơn trông hơi chắn"): fill phẳng `--glass-1` alpha .55 trên nền sáng ra "sữa" đục, không ra gương. Pane chrome LỚN (sidebar, panel cao full màn) bắt buộc 3 thứ: (1) **gradient-alpha glass** — alpha biến thiên dọc mặt kính thay vì một hằng số; (2) **specular sheen** `::before` — vùng sáng radial góc trên + dải sheen chéo; (3) **orb màu ngay sau lưng pane** (xem Background Plane) — blur 24px phải có màu thật để nghiền. `--glass-1` chỉ còn dùng cho floating panel nhỏ:

```css
nav{position:fixed;top:0;left:0;bottom:0;width:200px;z-index:100;
  display:flex;flex-direction:column;align-items:stretch;gap:2px;padding:18px 12px;
  background:linear-gradient(165deg,rgba(255,255,255,.46) 0%,rgba(255,255,255,.22) 48%,rgba(240,248,255,.34) 100%);
  backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
  -webkit-backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
  border-right:1px solid rgba(255,255,255,.55);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9),inset 1px 0 0 rgba(255,255,255,.5),
    inset -1px 0 0 rgba(30,90,170,.10),4px 0 24px rgba(30,90,170,.08)}
/* specular sheen — vệt sáng chéo trên mặt kính; con của nav cần position:relative để nổi trên sheen */
nav::before{content:'';position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(220px 160px at 18% 4%,rgba(255,255,255,.55),transparent 70%),
    linear-gradient(115deg,rgba(255,255,255,.28) 0%,transparent 28%,transparent 72%,rgba(255,255,255,.14) 100%)}
nav>*{position:relative}
nav .logo{margin:0 0 12px;padding:6px 10px;
  background:linear-gradient(135deg,#0a84ff,#64b5f7);-webkit-background-clip:text;background-clip:text;color:transparent}
nav a{padding:8px 12px;border-radius:10px;font-size:13px;position:relative;overflow:hidden}
nav a.active{color:#0a84ff;background:rgba(10,132,255,.08);font-weight:600}
body{padding-left:200px}
@media(max-width:640px){
  body{padding-left:0}                       /* sidebar overlay, không chiếm column */
  nav{box-shadow:0 8px 30px rgba(0,0,0,.14)} /* nổi trên content khi mở */
}
```

**Ripple effect (BẮT BUỘC trên nút sidebar + toggle):** click vào đâu, một hình tròn lan ra TỪ ĐÚNG TOẠ ĐỘ đó và phủ từ từ kín nút (bán kính = khoảng cách xa nhất tới 4 góc), rồi fade. Phần tử cha cần CÓ position (relative/fixed/absolute đều chứa được ink) + `overflow:hidden`. ⚠️ KHÔNG viết rule chung ép `position:relative` lên `.nav-toggle` — nó sẽ đè `position:fixed` (cùng specificity, rule sau thắng) làm nút rơi xuống cuối trang:

Ripple ink là LIQUID GLASS, không phải vệt màu phẳng: specular highlight lệch góc (circle at 35% 30%), thân trắng mờ, viền xanh nhạt, `backdrop-filter:blur(2px)` để giọt nước tự khúc xạ content bên dưới, edge highlight inset:

```css
.ripple-ink{position:absolute;border-radius:50%;pointer-events:none;
  background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.70) 0%,rgba(255,255,255,.28) 38%,rgba(10,132,255,.20) 72%,transparent 100%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.9),inset 0 -10px 20px rgba(10,132,255,.12),0 0 14px rgba(10,132,255,.10);
  backdrop-filter:blur(2px) saturate(1.25);-webkit-backdrop-filter:blur(2px) saturate(1.25);
  transform:scale(0);opacity:1;animation:rippleGrow .6s cubic-bezier(.25,.46,.45,.94) forwards}
@keyframes rippleGrow{55%{transform:scale(1);opacity:.75}100%{transform:scale(1.04);opacity:0}}
```

```js
(function(){
  function attach(el){
    el.addEventListener('pointerdown', function(e){
      const r = el.getBoundingClientRect();
      const x = e.clientX - r.left, y = e.clientY - r.top;
      const rad = Math.hypot(Math.max(x, r.width - x), Math.max(y, r.height - y));
      const ink = document.createElement('span'); ink.className = 'ripple-ink';
      ink.style.width = ink.style.height = rad * 2 + 'px';
      ink.style.left = (x - rad) + 'px'; ink.style.top = (y - rad) + 'px';
      el.appendChild(ink);
      ink.addEventListener('animationend', () => ink.remove());
    });
  }
  document.querySelectorAll('nav a, .nav-toggle, .nav-close').forEach(attach);
})();
```
Chạy SAU script tạo .nav-toggle để nút toggle cũng có ripple.

- Tier-1 glass cho cả hai dạng
- Scroll spy via IntersectionObserver watching `section[id]` (selector `nav a` không đổi)

**Collapse (BẮT BUỘC với sidebar) — 2 nút riêng biệt:** nút ĐÓNG `✕` nằm TRONG sidebar (góc trên phải, 26×26, bg mờ nhẹ) — bấm → sidebar `translateX(-100%)`, `body{padding-left:0}` (trả lại nguyên column). Nút MỞ `☰` glass 32×32 lơ lửng góc trên trái, CHỈ hiện khi sidebar đang đóng (`body:not(.nav-collapsed) .nav-toggle{opacity:0;pointer-events:none}`). Cả 2 nút đều có ripple liquid-glass. Trạng thái nhớ `localStorage('navCollapsed')`; màn hẹp mặc định collapsed (matchMedia 640px). JS tự tạo cả 2 button — không cần sửa markup:

```js
(function(){
  const nav = document.querySelector('nav'); if (!nav) return;
  const btn = document.createElement('button'); btn.className = 'nav-toggle'; btn.textContent = '☰';
  document.body.appendChild(btn);
  const close = document.createElement('button'); close.className = 'nav-close'; close.textContent = '✕';
  nav.appendChild(close);
  const apply = c => { document.body.classList.toggle('nav-collapsed', c);
    try { localStorage.setItem('navCollapsed', c ? '1' : '0'); } catch(e){} };
  btn.addEventListener('click', () => apply(false));
  close.addEventListener('click', () => apply(true));
  try { const s = localStorage.getItem('navCollapsed');
    if (s === '1' || (s !== '0' && matchMedia('(max-width:640px)').matches)) apply(true);
  } catch(e){}
})();
```

```css
nav{transition:transform .28s cubic-bezier(.4,0,.2,1)}
body{transition:padding-left .28s cubic-bezier(.4,0,.2,1)}
body.nav-collapsed nav{transform:translateX(-100%)}
body.nav-collapsed{padding-left:0}
.nav-toggle{position:fixed;top:12px;left:12px;z-index:120;width:32px;height:32px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-size:14px;color:#4a4a55;cursor:pointer;
  background:linear-gradient(165deg,rgba(255,255,255,.5),rgba(255,255,255,.24));
  backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
  -webkit-backdrop-filter:blur(var(--blur-1)) saturate(1.7) brightness(1.04);
  border:1px solid transparent;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.75),0 0 0 1px rgba(30,90,170,.08),0 2px 10px rgba(30,90,170,.12);
  transition:opacity .2s,transform .28s cubic-bezier(.4,0,.2,1)}
.nav-toggle:hover{color:#0a84ff}
body:not(.nav-collapsed) .nav-toggle{opacity:0;pointer-events:none;transform:translateX(-6px)}
.nav-close{position:absolute;top:10px;right:10px;width:26px;height:26px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:12px;color:#4a4a55;cursor:pointer;
  background:rgba(0,0,0,.04);border:none;overflow:hidden}
.nav-close:hover{color:#0a84ff;background:rgba(10,132,255,.10)}
/* .nav-toggle hiện ở mọi cỡ màn */
```

⚠️ **Chip kính NỔI trên nền sáng KHÔNG được dùng viền trắng đặc** (bài học 13/06/2026 — user chê viền `.nav-toggle` "trông kỳ"): nút toggle (và mọi floating glass chip góc trên-trái) nằm trên vùng nền trang gần trắng-xanh phẳng → `backdrop-filter:blur` không có gì tối phía sau để nghiền thành kính, nên thứ rõ nhất lại là cái viền `rgba(255,255,255,.55)` — một vòng 1px nét căng, đọc thành "viền sticker dán lên", không ra mép kính. Fix: `border:1px solid transparent`, để mép sinh ra từ inset top-highlight + ring lạnh cực mảnh + drop-shadow lạnh:
```css
border:1px solid transparent;
box-shadow:inset 0 1px 0 rgba(255,255,255,.75),0 0 0 1px rgba(30,90,170,.08),0 2px 10px rgba(30,90,170,.12);
```
Quy tắc: viền trắng đặc CHỈ hợp khi pane có content tối/đa sắc phía sau để blur sample (vd sidebar đè lên section). Chip nổi trên nền sáng → mép bằng shadow lạnh, không bằng stroke trắng.

## Scrollbar — overlay tự ẩn (theme thay scrollbar mặc định)

Thay scrollbar mặc định của trình duyệt bằng overlay **ẩn HOÀN TOÀN — track/nền/corner/button đều trong suốt, KHÔNG còn dải gutter**. Chỉ **viên pill (thumb)** fade-in (alpha 0 → tint xanh) và trượt theo nội dung khi **đang cuộn** hoặc khi **rê chuột vào dải scrollbar** (hover thumb). Áp dụng cho cả viewport lẫn sidebar (`nav` có `overflow-y:auto`). Thumb dùng `background-clip:content-box` + `border:3px solid transparent` để pill mảnh, bo tròn, nổi giữa gutter. JS thêm class `.scrolling` khi cuộn rồi gỡ sau ~900ms idle:

⚠️ **Bài học 13/06/2026 (user: "ẩn đi hoàn toàn luôn kể cả thanh nền"):** chỉ set `track{background:transparent}` là CHƯA đủ — `track-piece`, `corner`, `button` vẫn có thể vẽ nền/viền mặc định thành một dải xám mờ. Phải ép TẤT CẢ phần không phải thumb về `background:transparent;border:0;box-shadow:none`. Default thumb cũng alpha 0 (vô hình); chỉ fade qua `background-color` (transition mượt như opacity) khi `.scrolling` / `:hover`. KHÔNG `opacity` trực tiếp lên pseudo scrollbar (webkit không hỗ trợ ổn định) — dùng alpha của `background-color`.

⚠️ **Khi scrollbar trong suốt → dải gutter lộ CANVAS, phải set nền cho `html`:** gutter `width:11px` vẫn chiếm chỗ; track + thumb transparent nên nó lộ canvas phía sau. Nền gradient thường đặt trên `body` (đã trừ scrollbar) → KHÔNG phủ dải gutter → canvas `html` mặc định **trắng** → thành **vệt trắng dọc mép phải full-height**. Fix: cho `html` một nền tông xanh khớp field (`html{background:#e9f0fb}`).

```css
/* Chromium / Safari */
::-webkit-scrollbar{width:11px;height:11px;background:transparent}
::-webkit-scrollbar-track,
::-webkit-scrollbar-track-piece,
::-webkit-scrollbar-corner,
::-webkit-scrollbar-button{background:transparent;border:0;box-shadow:none}
::-webkit-scrollbar-thumb{background:transparent;border-radius:8px;
  border:3px solid transparent;background-clip:content-box;transition:background-color .25s ease}
/* hiện pill khi đang cuộn (JS toggle .scrolling) HOẶC khi trỏ vào dải scrollbar (hover thumb) */
html.scrolling::-webkit-scrollbar-thumb,
nav.scrolling::-webkit-scrollbar-thumb,
::-webkit-scrollbar-thumb:hover{background-color:rgba(10,132,255,.32)}
::-webkit-scrollbar-thumb:active{background-color:rgba(10,132,255,.6)}
/* set nền html để gutter trong suốt không lộ canvas trắng */
html{background:#e9f0fb;scrollbar-width:thin;scrollbar-color:transparent transparent}
html.scrolling{scrollbar-color:rgba(10,132,255,.32) transparent}
```

```js
/* hiện khi cuộn, ẩn sau ~900ms idle — gắn cho cả trang lẫn sidebar */
(function(){
  const flash = (el) => { let t; return () => { el.classList.add('scrolling'); clearTimeout(t);
    t = setTimeout(() => el.classList.remove('scrolling'), 900); }; };
  const root = document.documentElement;
  window.addEventListener('scroll', flash(root), { passive:true });
  const nav = document.querySelector('nav');
  if (nav) nav.addEventListener('scroll', flash(nav), { passive:true });
})();
```

Lưu ý: tint xanh `#0a84ff` để khớp pattern; thumb đậm dần theo hover→active. Firefox không ẩn hẳn được (reserve width), nên fallback là thanh `thin` đổi màu — chấp nhận được.

## Page Architecture

```
<a class="skip-link"> — first focusable, jumps to #main (see Accessibility section)
<nav>          — fixed LEFT sidebar with section links (never a top bar)
<main id="main">  — wraps everything below for the landmark + skip-link target
<hero>         — gradient title + subtitle
<div class="mm">  — MẶC ĐỊNH: một mind map collapsible (xem § Mind Map) — luôn vẽ
<repo-card>    — optional: link to source repo with chrome + collapse
<section id="sec-{i}">  — repeat for each topic (i = 0..N-1):
  class="section-bg s-bg{i}"
  .section-header  — .tag badge ("0{i+1} · Title") + h2 + p
  .diagram-box     — animated SVG (see below)
  .content-grid    — 2-column cards (Workflow + Use cases)
  .table-wrap      — optional comparison table
  footer link      — "Chi tiết: file.md"
<footer>
```

## Mind Map (MẶC ĐỊNH — luôn vẽ một bản)

Mọi docs site PHẢI kèm **một mind map collapsible kiểu NotebookLM** tóm tắt cấu trúc trang (các section / thực thể / mục chính) — đặt ngay sau hero hoặc trong section "Tổng quan". Đặc trưng: **đường nối CONG (bezier) màu theo nhánh** + node chip glass + chevron; **mặc định ĐÓNG, click mở/đóng**. Self-contained (CSS + JS thuần vẽ SVG, KHÔNG thư viện). Nội dung **sinh từ chính tài liệu** (mỗi section = một nhánh, mục con = lá), cắt mô tả lá ≤~54 ký tự cho gọn. **Nhánh quá dài (>~8 lá đã là vấn đề) → KHÔNG để phẳng, chia tiếp thành nhánh con theo CHỨC NĂNG** (root → nhánh → nhóm → lá): mỗi nhóm là node `.cat has-children` lồng trong, mang class màu `.g0..g5` riêng (JS `colorOf` trả đúng màu cho đường cong); cố giữ mỗi nhóm ≤~8 lá. Ví dụ overstack chia CẢ `dev-loop` (12 → sửa-code / dựng-onboard / eval), `orchestrate` (10 → điều-phối / đánh-giá / vận-hành), `utils` (37 → 6 nhóm) — xem `fdk/tools/build-overstack-docs.py` (`LOOP_GROUPS`).

**Cấu trúc** (tree ngang: root → nhánh `.cat` → lá `.leaf`; có `.mm-canvas` + `<svg class="mm-links">` để vẽ đường cong):
```html
<div class="mm"><div class="mm-canvas"><svg class="mm-links"></svg><div class="tree"><div class="row">
  <div class="node root has-children"><span class="nm">Chủ đề</span><span class="ds">phụ đề</span><span class="ct">N</span></div>
  <div class="children">
    <div class="row">
      <div class="node b-0 cat has-children"><span class="nm">Nhánh</span><span class="ds">mô tả</span><span class="ct">3</span></div>
      <div class="children">
        <div class="row"><div class="node b-0 leaf"><span class="nm">mục</span><span class="ds">mô tả ngắn</span></div></div>
      </div>
    </div>
  </div>
</div></div></div></div>
```

**CSS** (trong `<style>`; `--ink2`/`--border` từ design system; `.b-0..b-4` cycle Apple secondary cho `.nm`+`.ct`+border — JS dùng CÙNG màu cho đường cong):
```css
.mm{overflow-x:auto;padding:14px 4px 6px}
.mm-canvas{position:relative;width:max-content}
.mm-links{position:absolute;top:0;left:0;pointer-events:none;overflow:visible;z-index:0}
.mm-links path{fill:none;stroke-width:2.2;opacity:.55;stroke-linecap:round}
.mm .tree{position:relative;z-index:1}
.mm .tree,.mm .children{display:flex;flex-direction:column;gap:9px;justify-content:center}
.mm .row{display:flex;align-items:center;gap:48px;position:relative}
.mm .children{position:relative}.mm .children.collapsed{display:none}
.mm .node{position:relative;display:inline-flex;flex-direction:column;gap:1px;padding:7px 13px;border-radius:13px;cursor:default;white-space:nowrap;background:rgba(255,255,255,.72);backdrop-filter:blur(7px) saturate(1.1);border:1px solid var(--border);box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 3px 14px rgba(20,40,90,.07);transition:transform .12s}
.mm .node.has-children{cursor:pointer}.mm .node:hover{transform:translateY(-1px)}
.mm .node .nm{font-size:13px;font-weight:700;letter-spacing:-.01em}.mm .node .ds{font-size:10.5px;color:var(--ink2)}
.mm .node .ct{font-size:10px;color:#fff;font-weight:700;padding:1px 7px;border-radius:999px;position:absolute;top:-8px;right:-8px;background:#0a84ff}
.mm .node.has-children::after{content:'';position:absolute;right:-7px;top:50%;width:6px;height:6px;border-right:2px solid var(--ink2);border-bottom:2px solid var(--ink2);transform:translateY(-50%) rotate(-45deg);opacity:.5}
.mm .node.collapsed-parent::after{transform:translateY(-50%) rotate(45deg)}
.mm .node.root{background:linear-gradient(135deg,rgba(10,132,255,.16),rgba(88,86,214,.14));border-color:rgba(10,132,255,.4)}
```
(KHÔNG còn connector thẳng `.row::before`/`.children::before` — đường nối do JS vẽ bezier vào `<svg class="mm-links">`.)

**JS** (vẽ bezier màu theo nhánh + mặc định ĐÓNG nhánh `.cat` + click toggle + redraw — trong `<script>`):
```js
(function(){var mm=document.querySelector('.mm');if(!mm)return;var NS='http://www.w3.org/2000/svg';
function colorOf(n){return n.classList.contains('b-0')?'#30b0c7':n.classList.contains('b-1')?'#5856d6':n.classList.contains('b-2')?'#ff9500':n.classList.contains('b-3')?'#34c759':n.classList.contains('b-4')?'#ff2d55':'#9aa4b2';}
function draw(){var canvas=mm.querySelector('.mm-canvas'),svg=mm.querySelector('.mm-links');if(!canvas||!svg)return;var w=canvas.offsetWidth,h=canvas.offsetHeight;svg.setAttribute('width',w);svg.setAttribute('height',h);svg.setAttribute('viewBox','0 0 '+w+' '+h);while(svg.firstChild)svg.removeChild(svg.firstChild);var cR=canvas.getBoundingClientRect();[].slice.call(canvas.querySelectorAll('.node.has-children')).forEach(function(p){var row=p.parentElement,kids=null,ch=row.children;for(var i=0;i<ch.length;i++){if(ch[i].classList.contains('children'))kids=ch[i];}if(!kids||kids.classList.contains('collapsed'))return;var pr=p.getBoundingClientRect(),px=pr.right-cR.left,py=pr.top+pr.height/2-cR.top;[].slice.call(kids.children).forEach(function(crow){var cn=crow.querySelector(':scope > .node');if(!cn)return;var rr=cn.getBoundingClientRect(),cx=rr.left-cR.left,cy=rr.top+rr.height/2-cR.top,dx=Math.max(22,(cx-px)*0.55);var pa=document.createElementNS(NS,'path');pa.setAttribute('d','M'+px+' '+py+' C'+(px+dx)+' '+py+' '+(cx-dx)+' '+cy+' '+cx+' '+cy);pa.setAttribute('stroke',colorOf(cn));svg.appendChild(pa);});});}
[].slice.call(mm.querySelectorAll('.node.has-children')).forEach(function(n){var row=n.parentElement,kids=null,c=row.children;for(var i=0;i<c.length;i++){if(c[i].classList.contains('children'))kids=c[i];}if(!kids)return;if(n.classList.contains('cat')){kids.classList.add('collapsed');n.classList.add('collapsed-parent');}n.addEventListener('click',function(e){e.stopPropagation();var open=kids.classList.toggle('collapsed');n.classList.toggle('collapsed-parent',open);draw();});});
draw();addEventListener('load',function(){setTimeout(draw,60);});addEventListener('resize',function(){clearTimeout(window.__mmt);window.__mmt=setTimeout(draw,120);},{passive:true});})();
```
Root (`.has-children` không `.cat`) mở sẵn → nhánh hiện; nhánh `.cat` đóng → click xổ lá; đường cong tự vẽ lại mỗi lần toggle/resize. `colorOf` trả CÙNG màu với class `.b-N`. Bản chạy thật: `llmwiki/html/overstack.html` tab "Tham chiếu".

## Section-Bg Pattern

Each `<section>` gets two classes: `section-bg s-bgN` (N = section index mod 6).
The gradient overlay is a `::before` pseudo-element:

```css
.section-bg { position: relative; overflow: visible; }
/* FULL-BLEED: dải màu tràn hết viewport (100vw), content vẫn max-width — KHÔNG đóng khung
   dải tint trong box section, nhìn như panel rời, mất liền mạch */
.section-bg::before { content: ''; position: absolute; top: 0; bottom: 0; left: 50%;
  width: 100vw; transform: translateX(-50%); pointer-events: none; }
/* Generate one .s-bgN::before per section index, cycling through 6 colors */
```

Section padding: `padding: 64px 24px 72px; max-width: 1100px; margin: 0 auto;`

### CSS Generator Pattern

Generate the per-section CSS dynamically. For N sections, generate N rule sets using `#sec-{i}` IDs:

```
For i in 0..N-1:
  accent = palette[i % 6]
  dark   = dark[i % 6]
  gradient = overlay[i % 6]

  #sec-{i} .tag { background: accent at 12%; color: accent; }
  #sec-{i} .card h4 { color: accent; }
  #sec-{i} .card li::before { color: accent; }
  #sec-{i} .section-header h2 { color: dark; }
  .s-bg{i}::before { background: linear-gradient(180deg, gradient 0%, transparent 60%); }


## Animated SVG Diagrams

Each diagram is an inline SVG (not external file) with `viewBox` for responsiveness.

### Key Animations (reusable CSS in `<defs><style>`)

```css
@keyframes flowArrow { 0% { stroke-dashoffset: 20; } 100% { stroke-dashoffset: 0; } }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
@keyframes glow { 0%,100% { filter: drop-shadow(0 0 4px rgba(...)); } 50% { filter: drop-shadow(0 0 12px rgba(...)); } }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
@keyframes orbit { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes scanLine { 0% { transform: translateX(-40px); } 100% { transform: translateX(320px); } }
@keyframes stack { 0%,100% { opacity:.15; } 50% { opacity:.7; } }
```

Apply to SVG elements: `.flow` (dashed arrows), `.pulse` (nodes), `.float` (output badges), `.glow` (phone icon), `.drone` (bouncing), `.blink` (drone light), `.orbit-ring` (spinning product), `.cameraFlash` (strobe), `.scan` (scan line), `.stackAnim` (DICOM slices), `.center-pulse` (orbit core).

### SVG Box Styling

- **Nodes**: `rx="6"` or `rx="8"` rounded rects with `fill="rgba(255,255,255,.7)"` and colored stroke
- **Arrows**: `<line>` with `marker-end="url(#arrowN)"` using `<marker>` def, `stroke-width="2"`, and `.flow` class
- **Text**: `text-anchor="middle"`, `font-size="9-11"`, `font-weight="600"` for labels
- Use `font-family` from the page (`var(--font-text)` — macOS-first stack, see Font section)
- Always include `xmlns="http://www.w3.org/2000/svg"` on `<svg>`

### Node-Draggable Diagrams (REQUIRED for every `.diagram-box`)

Every `.diagram-box` MUST be an interactive node graph, NOT a static or merely-pannable picture:

- **Drag each box (node) individually** — moving one table/step does NOT move the others. Connector lines re-route to follow the node automatically.
- **Drag empty background** = pan the whole canvas.
- **Wheel** = zoom toward the cursor. **Double-click / ⟲ reset** = restore node positions + canvas.
- **`.diagram-box` is vertically resizable** (CSS `resize`) so the container expands smoothly.

This is auto-detected from the authored SVG — **no SVG markup changes needed**. The JS treats every `<rect>` ≥ 70×30 as a node, adopts the `<text>`/small-`<rect>` children whose coords fall inside that rect, wraps them in a `<g class="dnode">`, and binds each `<line>` endpoint to the nearest node so connectors track movement. Coordinate conversion uses `getScreenCTM().inverse()` so dragging stays accurate under zoom/pan.

CSS — replace the old static `.diagram-box` rule with:

```css
.diagram-box{background:var(--glass-2);backdrop-filter:blur(var(--blur-2)) saturate(1.1);
  border:1px solid var(--border);border-radius:16px;box-shadow:var(--edge-hi),0 4px 20px rgba(20,40,90,.08);
  padding:24px;margin:24px 0;
  position:relative;overflow:hidden;display:flex;flex-direction:column;
  resize:vertical;min-height:160px;transition:box-shadow .2s ease}
.diagram-box:hover{box-shadow:var(--edge-hi),0 6px 28px rgba(20,40,90,.14)}
.diagram-viewport{position:relative;flex:1 1 auto;width:100%;overflow:hidden;cursor:grab;touch-action:none}
.diagram-viewport.grabbing{cursor:grabbing}
.diagram-viewport svg{width:100%;height:auto;display:block;overflow:visible;transform-origin:0 0;
  will-change:transform;user-select:none;-webkit-user-select:none}
.dnode{cursor:move}
.dnode>rect{transition:filter .15s ease}
.dnode:hover>rect:first-of-type{filter:drop-shadow(0 3px 8px rgba(0,0,0,.18))}
.diagram-hint{position:absolute;top:8px;right:12px;z-index:5;font-size:10px;color:#4a4a55;
  background:rgba(255,255,255,.75);border:1px solid rgba(0,0,0,.05);border-radius:20px;
  padding:3px 10px;white-space:nowrap;opacity:0;transition:opacity .2s;pointer-events:none}
.diagram-box:hover .diagram-hint{opacity:.9}
.diagram-reset{position:absolute;bottom:8px;right:10px;z-index:5;font-size:11px;
  background:rgba(255,255,255,.85);border:1px solid rgba(0,0,0,.08);border-radius:8px;
  padding:3px 9px;cursor:pointer;color:#4a4a55;opacity:0;transition:opacity .2s}
.diagram-box:hover .diagram-reset{opacity:1}
.diagram-reset:hover{background:#fff;color:#0f0f12}
/* resize grip kiểu macOS: 3 vạch chéo trong tam giác góc — ẨN mặc định, hover mới hiện.
   ⛔ KHÔNG dùng góc L 2 cạnh đậm luôn-hiện (bài học 12/06/2026 — user chê "luôn hiện mà còn xấu").
   Kèm ::-webkit-resizer{display:none} để giấu grip mặc định của browser. */
.diagram-box::after{content:'';position:absolute;right:5px;bottom:5px;width:16px;height:16px;
  pointer-events:none;opacity:0;transition:opacity .25s ease;
  clip-path:polygon(100% 0,100% 100%,0 100%);
  background:repeating-linear-gradient(135deg,transparent 0 3.5px,rgba(10,132,255,.45) 3.5px 5px)}
.diagram-box:hover::after{opacity:.85}
.diagram-box::-webkit-resizer{display:none}
```

JS — add once, call after DOM is parsed (script at end of `<body>`):

```js
function initDraggableDiagrams() {
  const NS = 'http://www.w3.org/2000/svg';
  const nearest = (nodes, x, y) => {
    let best = null, bd = 1e9;
    nodes.forEach(n => {
      const cx = Math.max(n.x, Math.min(x, n.x + n.w)), cy = Math.max(n.y, Math.min(y, n.y + n.h));
      const d = Math.hypot(x - cx, y - cy);
      if (d < bd) { bd = d; best = n; }
    });
    return bd <= 42 ? best : null;
  };
  document.querySelectorAll('.diagram-box').forEach(box => {
    const svg = box.querySelector('svg');
    if (!svg || box.dataset.draggable) return;
    box.dataset.draggable = '1';
    const vp = document.createElement('div'); vp.className = 'diagram-viewport';
    box.insertBefore(vp, svg); vp.appendChild(svg);
    const hint = document.createElement('div'); hint.className = 'diagram-hint';
    hint.textContent = '✥ kéo từng ô · kéo nền để pan · cuộn để zoom · kéo mép dưới để mở rộng';
    box.appendChild(hint);
    const reset = document.createElement('button'); reset.className = 'diagram-reset'; reset.textContent = '⟲ reset';
    box.appendChild(reset);

    // detect node rects + adopt children
    const allRects = [...svg.querySelectorAll('rect')];
    const nodes = allRects.filter(r => (+r.getAttribute('width')) >= 70 && (+r.getAttribute('height')) >= 30)
      .map(r => ({ rect: r, x: +r.getAttribute('x'), y: +r.getAttribute('y'),
        w: +r.getAttribute('width'), h: +r.getAttribute('height'), els: [r], tx: 0, ty: 0 }));
    const inNode = (px, py) => nodes.find(n => px >= n.x-1 && px <= n.x+n.w+1 && py >= n.y-1 && py <= n.y+n.h+1);
    [...svg.querySelectorAll('text')].forEach(t => {
      const x = parseFloat(t.getAttribute('x')), y = parseFloat(t.getAttribute('y'));
      if (isNaN(x) || isNaN(y)) return; const n = inNode(x, y); if (n) n.els.push(t);
    });
    allRects.forEach(r => { if (nodes.some(n => n.rect === r)) return;
      const x = +r.getAttribute('x'), y = +r.getAttribute('y'), w = +r.getAttribute('width')||0, h = +r.getAttribute('height')||0;
      const n = inNode(x+w/2, y+h/2); if (n) n.els.push(r); });
    nodes.forEach(n => { const g = document.createElementNS(NS, 'g'); g.setAttribute('class', 'dnode');
      n.rect.parentNode.insertBefore(g, n.rect); n.els.forEach(el => g.appendChild(el)); n.g = g; });

    // bind connector lines
    const links = [...svg.querySelectorAll('line')].filter(l => l.hasAttribute('x1') && l.hasAttribute('x2'));
    links.forEach(l => { l._x1=+l.getAttribute('x1'); l._y1=+l.getAttribute('y1'); l._x2=+l.getAttribute('x2'); l._y2=+l.getAttribute('y2');
      l._n1 = nearest(nodes, l._x1, l._y1); l._n2 = nearest(nodes, l._x2, l._y2); });
    const reroute = () => links.forEach(l => {
      if (l._n1) { l.setAttribute('x1', l._x1+l._n1.tx); l.setAttribute('y1', l._y1+l._n1.ty); }
      if (l._n2) { l.setAttribute('x2', l._x2+l._n2.tx); l.setAttribute('y2', l._y2+l._n2.ty); } });

    // auto-fit: viewBox (→ svg height → box) grows to contain dragged nodes ("sizing cùng")
    const vbBase = (svg.getAttribute('viewBox') || '0 0 900 200').split(/\s+/).map(Number);
    const fitViewBox = () => {
      const pad = 16;
      let minX = vbBase[0], minY = vbBase[1], maxX = vbBase[0]+vbBase[2], maxY = vbBase[1]+vbBase[3];
      nodes.forEach(n => { minX = Math.min(minX, n.x+n.tx-pad); minY = Math.min(minY, n.y+n.ty-pad);
        maxX = Math.max(maxX, n.x+n.w+n.tx+pad); maxY = Math.max(maxY, n.y+n.h+n.ty+pad); });
      svg.setAttribute('viewBox', `${minX} ${minY} ${maxX-minX} ${maxY-minY}`);
    };

    // pan + zoom + per-node drag
    let ptx=0, pty=0, scale=1;
    const applyCanvas = () => { svg.style.transform = `translate(${ptx}px,${pty}px) scale(${scale})`; };
    const toSvg = (cx, cy) => { const p = svg.createSVGPoint(); p.x=cx; p.y=cy; return p.matrixTransform(svg.getScreenCTM().inverse()); };
    let mode=null, node=null, start=null, t0=null, p0=null;
    vp.addEventListener('pointerdown', e => { vp.setPointerCapture(e.pointerId);
      const g = e.target.closest && e.target.closest('g.dnode');
      if (g) { mode='node'; node = nodes.find(n => n.g === g); start = toSvg(e.clientX, e.clientY); t0 = { x: node.tx, y: node.ty }; }
      else { mode='pan'; p0 = { x: e.clientX-ptx, y: e.clientY-pty }; vp.classList.add('grabbing'); } });
    vp.addEventListener('pointermove', e => {
      if (mode==='node') { const c = toSvg(e.clientX, e.clientY); node.tx = t0.x+(c.x-start.x); node.ty = t0.y+(c.y-start.y);
        node.g.setAttribute('transform', `translate(${node.tx},${node.ty})`); reroute(); }
      else if (mode==='pan') { ptx = e.clientX-p0.x; pty = e.clientY-p0.y; applyCanvas(); } });
    const end = () => { if (mode==='node') fitViewBox(); mode=null; node=null; vp.classList.remove('grabbing'); };
    vp.addEventListener('pointerup', end); vp.addEventListener('pointercancel', end);
    vp.addEventListener('wheel', e => { e.preventDefault();
      const r = vp.getBoundingClientRect(), mx = e.clientX-r.left, my = e.clientY-r.top;
      const ns = Math.min(4, Math.max(0.5, scale*(e.deltaY<0?1.1:0.9)));
      ptx = mx-(mx-ptx)*(ns/scale); pty = my-(my-pty)*(ns/scale); scale = ns; applyCanvas(); }, { passive:false });
    const doReset = () => { ptx=0; pty=0; scale=1; svg.style.transition='transform .3s cubic-bezier(.4,0,.2,1)'; applyCanvas();
      setTimeout(() => { svg.style.transition=''; }, 320);
      nodes.forEach(n => { n.tx=0; n.ty=0; n.g.setAttribute('transform', 'translate(0,0)'); }); reroute(); fitViewBox(); };
    reset.addEventListener('click', doReset); vp.addEventListener('dblclick', doReset);
  });
}
initDraggableDiagrams();
```

Notes:
- Author SVGs exactly as before (fixed `viewBox`, flat `<rect>`/`<text>`/`<line>`). Node grouping + line binding are inferred at runtime — keep node labels' `x`/`y` INSIDE their rect bounds so they get adopted correctly.
- Connectors must be `<line>` (with `x1/y1/x2/y2`) to auto-track. `<path>` connectors stay static — use `<line>` for anything that should follow a node.
- **Auto-fit**: on drag release the SVG `viewBox` grows to contain dragged nodes, so the svg height (and the box) sizes WITH the content — nodes never get clipped after release. `svg{overflow:visible}` keeps a node visible mid-drag too. `fitViewBox()` runs on pointerup + reset.
- Idempotent (`dataset.draggable` guard); `resize:vertical` lets the user grow the container; flex viewport fills new height.

### Copy Button on Code Panels (REQUIRED for every `pre.code-block`)

Every code panel MUST have a hover-revealed Copy button. Capture `textContent` BEFORE injecting the button (so the button label isn't copied), wrap the `<pre>` in a relative `.code-wrap`, and copy via the Clipboard API with an `execCommand` fallback.

```css
.code-wrap{position:relative}
.code-copy{position:absolute;top:7px;right:7px;z-index:2;width:28px;height:26px;display:inline-flex;align-items:center;justify-content:center;
  background:rgba(255,255,255,.1);color:#cbd5e1;border:1px solid rgba(255,255,255,.15);
  border-radius:7px;cursor:pointer;opacity:0;transition:opacity .15s,background .15s,color .15s}
.code-copy svg{width:14px;height:14px;display:block}
.code-wrap:hover .code-copy{opacity:1}
.code-copy:hover{background:rgba(255,255,255,.2);color:#fff}
.code-copy.copied{background:rgba(16,185,129,.25);color:#6ee7b7;border-color:rgba(16,185,129,.45);opacity:1}
@media(max-width:640px){.code-copy{opacity:1}}
```

```js
function initCodeCopy() {
  const COPY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
  document.querySelectorAll('pre.code-block').forEach(pre => {
    if (pre.dataset.copy) return; pre.dataset.copy = '1';
    const code = pre.textContent;
    const wrap = document.createElement('div'); wrap.className = 'code-wrap';
    pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
    const btn = document.createElement('button'); btn.className = 'code-copy';
    btn.setAttribute('aria-label', 'Copy'); btn.title = 'Copy'; btn.innerHTML = COPY;
    wrap.appendChild(btn);
    btn.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code); }
      catch { const ta = document.createElement('textarea'); ta.value = code;
        document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
      btn.innerHTML = CHECK; btn.classList.add('copied');
      setTimeout(() => { btn.innerHTML = COPY; btn.classList.remove('copied'); }, 1500);
    });
  });
}
initCodeCopy();
```

### Water-Ripple Click Effect (REQUIRED on every interactive control)

Every clickable control (any `<button>`, `.nav-link`, `.collapse-toggle`, `.code-copy`, `.diagram-reset`, checklist labels) gets a liquid-glass water ripple on pointer-down: a soft white splash with a faint blue tint that expands from the click point like a water ring and fades. One global listener — no per-button wiring.

```css
.ripple{position:absolute;border-radius:50%;pointer-events:none;transform:scale(0);opacity:.9;
  background:radial-gradient(circle, rgba(255,255,255,.6) 0%, rgba(10,132,255,.22) 35%, transparent 70%);
  box-shadow:0 0 0 1px rgba(255,255,255,.45);
  animation:rippleWave .65s cubic-bezier(.2,.6,.3,1) forwards}
@keyframes rippleWave{to{transform:scale(2.8);opacity:0}}
```

```js
function initRipple() {
  document.addEventListener('pointerdown', e => {
    const el = e.target.closest('button, .nav-link, .collapse-toggle, .checklist label');
    if (!el || el.dataset.noRipple) return;
    const r = el.getBoundingClientRect();
    const d = Math.max(r.width, r.height) * 1.2;
    const s = document.createElement('span');
    s.className = 'ripple';
    s.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d/2}px;top:${e.clientY - r.top - d/2}px`;
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(s);
    s.addEventListener('animationend', () => s.remove());
  });
}
initRipple();
```

Notes:
- The ripple origin is the actual click point (`clientX/Y` relative to the control), not the center — that is what makes it read as water, not a flash.
- `overflow:hidden` is forced on the host so the ring clips to the control's rounded shape.
- Opt out with `data-no-ripple` on controls where clipping would break layout (e.g. the diagram viewport itself — pan/drag should not splash).
- Keep the tint blue-family (`rgba(10,132,255,…)`) per the palette; on dark surfaces (code panels) the white core carries the effect.

## Collapse / Xem thêm

Animated expand/collapse section:

```html
<button class="collapse-toggle" onclick="toggleX()">
  <span class="arrow" id="arrowX">▶</span> Label
</button>
<div class="collapse-body" id="bodyX">
  <div class="collapse-body-inner">...</div>
</div>
```

CSS:
```css
.collapse-body {
  max-height: 0; overflow: hidden;
  transition: max-height .35s cubic-bezier(.4,0,.2,1), opacity .25s ease;
  opacity: 0;
}
.collapse-body.open { opacity: 1; }   /* open max-height is set by JS = scrollHeight, NOT a magic cap */
.collapse-toggle .arrow { transition: transform .25s cubic-bezier(.4,0,.2,1); }
.collapse-toggle .arrow.open { transform: rotate(90deg); }
```

⛔ NEVER hardcode `.collapse-body.open{max-height:800px}` — any content taller than the cap gets silently clipped. Measure `scrollHeight` and set `max-height` inline so the panel always fits its content; clear it back to `0` on close so the transition animates:

JS:
```js
function toggleX() {
  const body = document.getElementById('bodyX');
  const open = body.classList.toggle('open');
  document.getElementById('arrowX').classList.toggle('open');
  body.style.maxHeight = open ? body.scrollHeight + 'px' : '0';
}
/* if a panel contains images/late-laid-out content, re-measure on resize for any .open panel */
addEventListener('resize', () => document.querySelectorAll('.collapse-body.open')
  .forEach(b => { b.style.maxHeight = b.scrollHeight + 'px'; }));
```

## Master-Detail Click-Reveal (list trái → chi tiết phải, trong 1 trang cuộn)

Khi một section có một DANH SÁCH mục mà mỗi mục có nội dung chi tiết dài (tour steps,
endpoints, modules, rule list…), KHÔNG đổ hết chi tiết ra hoặc tách thành trang/tab riêng.
Dùng **master-detail**: cột trái = list mục (chip glass, bấm được); cột phải = 1 panel chi
tiết **đổi tại-chỗ** khi bấm — KHÔNG điều hướng, KHÔNG ẩn section khác (vẫn trong trang cuộn
liền mạch). Đây là cách cho "đọc tuần tự + bấm để đào sâu" mà không vỡ scroll-spy.

```html
<div class="md-wrap"><ul class="md-list" role="listbox"></ul><div class="card md-detail"></div></div>
```
```css
.md-wrap{display:grid;grid-template-columns:268px 1fr;gap:18px}
.md-list li{padding:11px 13px;border-radius:13px;cursor:pointer;margin-bottom:8px;background:var(--glass-2);
  backdrop-filter:blur(var(--blur-2));border:1px solid var(--border);box-shadow:var(--edge-hi);transition:.16s}
.md-list li:hover{transform:translateX(3px)}
.md-list li[aria-selected=true]{background:linear-gradient(120deg,rgba(255,255,255,.92),rgba(244,242,255,.85));border-color:#cdc4ff}
@media(max-width:760px){.md-wrap{grid-template-columns:1fr}}
```
- A11y: `role="listbox"`/`role="option"` + `aria-selected` trên mục đang chọn; mục chọn đầu = index 0.
- Ripple: chỉ gắn ở list-control nếu muốn — KHÔNG để splash lan sang panel chi tiết.
- Bản chạy thật: skill `orca-onboard` tab "Guided Tour" (skeleton v2).

## Sidebar Icon Tiles (macOS SF-Symbols-style)

Mỗi mục `nav a` = **tile bo góc đổ màu** (kiểu macOS System Settings) chứa **icon line vẽ
bằng inline SVG** (stroke trắng, ~14px, round caps). ⛔ KHÔNG dùng glyph unicode (◫ ▸ ▤ —
lệch baseline, xấu). Logo app = icon "display/monitor" SVG trong tile gradient. SF Symbols là
font độc quyền Apple → **vẽ lại path SVG mô phỏng**, KHÔNG nhúng font (self-contained).

```css
nav a .ic{width:24px;height:24px;border-radius:7px;display:grid;place-items:center}
nav a .ic svg{width:14px;height:14px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
/* mỗi tab 1 màu tile (theo section accent) */
```
Map gợi ý: overview→`info.circle` · architecture→`square.stack.3d` · guided-tour→`mappin.and.ellipse`
· modules→`cube.box` · run/docker→`terminal`. Bản chạy thật: `orca-onboard` skeleton v2.

## Responsive

```css
@media (max-width: 700px) {
  .content-grid { grid-template-columns: 1fr; }
}
```

## Scroll Spy

```js
const observer = new IntersectionObserver(entries => {
  let active = '';
  for (const entry of entries) {
    if (entry.isIntersecting) active = entry.target.id;
  }
  if (active) links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + active));
}, { rootMargin: '-40% 0px -55% 0px' });
sections.forEach(s => observer.observe(s));
```

## Font

System fonts ONLY — NO Google Fonts `<link>`, no `@import`, no webfont download. Ưu tiên bộ font macOS (San Francisco); máy không có SF thì rơi xuống Roboto / Segoe UI — các fallback đều phải thanh lịch, không để rơi về Arial/Times:

```css
:root{
  --font-text: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', 'Roboto', 'Segoe UI', sans-serif;
  --font-display: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', 'Roboto', 'Segoe UI', sans-serif;
  --font-mono: 'SF Mono', ui-monospace, 'SFMono-Regular', Menlo, 'Roboto Mono', Consolas, monospace;
}
body{font-family:var(--font-text)}
h1,h2,h3,.logo{font-family:var(--font-display);letter-spacing:-.02em}  /* SF Pro Display cho cỡ ≥20px */
pre.code-block,.foot-tree{font-family:var(--font-mono)}
```

- `-apple-system`/`BlinkMacSystemFont` đã resolve ra San Francisco trên macOS — 'SF Pro Text/Display' chỉ là tên tường minh cho máy cài rời.
- Roboto/Segoe UI là fallback hệ (Android/Linux/Windows có sẵn) — KHÔNG tải webfont để giữ self-contained.
- Mono luôn đi qua `ui-monospace` trước Menlo để bắt SF Mono trên macOS mới.

## Theme Toggle sáng/tối (REQUIRED — feedback user 2026-07-06, KHÔNG được ép một mode)

Mọi trang sinh ra phải cho user TỰ CHỌN sáng/tối bằng một nút toggle — `prefers-color-scheme` chỉ là **mặc định ban đầu**, không phải quyết định cuối. Ép cứng dark (hoặc light) là vi phạm. Ba mảnh bắt buộc, không mảnh nào được thiếu:

**1. CSS — dark là override theo token, viết MỘT lần dùng cho cả 2 ngả** (theo-hệ *khi user chưa chọn light*, và user-chọn-dark tường minh; light = base CSS nên không cần khối riêng):
```css
/* mặc định theo hệ — chỉ khi user CHƯA chọn light */
@media (prefers-color-scheme: dark){
  html:not([data-theme=light]){ --glass2:…; --border:…; --t1:…; --t2:…; background:#0c0f16 }
  html:not([data-theme=light]) body{ … } /* prefix từng selector */
}
/* user bấm toggle chọn dark tường minh */
html[data-theme=dark]{ /* CÙNG token như trên */ }
html[data-theme=dark] body{ … }
```
Sinh trang bằng script? Giữ MỘT danh sách rule rồi emit 2 khối với 2 prefix (xem `_DARK_RULES` trong `fdk/tools/build-overstack-docs.py`) — chép tay 2 bản là mầm drift.

**2. `<head>` — chống FOUC** (áp lựa chọn đã lưu TRƯỚC khi CSS render):
```html
<script>(function(){try{var t=localStorage.getItem("<tên-trang>-theme");
if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}})();</script>
```

**3. NÚT GẠT (switch), KHÔNG phải chip icon rải góc** (feedback lần 3: chip 2 góc "không giống ai") — hàng footer **dính đáy sidebar/nav**: nhãn "Giao diện" bên trái + switch bên phải, vách ngăn mảnh phía trên. Track pill 50×26 có ☀️/🌙 hai đầu, knob trượt; `role="switch"` + `aria-checked` + Enter/Space toggle:
```css
.theme-row{position:sticky;bottom:-<pad-nav>;margin-top:auto;display:flex;align-items:center;justify-content:space-between;
  padding:11px 16px;border-top:1px solid rgba(30,90,170,.14);background:…glass…;backdrop-filter:blur(14px)}
.theme-switch .track{display:inline-block;position:relative;width:50px;height:26px;border-radius:999px;…}
.theme-switch .track::before{content:'☀️';left:6px;…} .theme-switch .track::after{content:'🌙';right:6px;…}
.theme-switch .knob{position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:#fff;transition:left .18s}
.theme-switch.on .knob{left:26px} .theme-switch.on .track{background:…dark…}
```
```js
(function(){var K='<tên-trang>-theme',d=document.documentElement,nav=document.querySelector('nav');if(!nav)return;
function isDark(){var t=d.getAttribute('data-theme');return t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
var sw=document.createElement('div');sw.className='theme-switch';sw.setAttribute('role','switch');sw.setAttribute('tabindex','0');
sw.innerHTML='<span class="track"><span class="knob"></span></span>';
var row=document.createElement('div');row.className='theme-row';
var lb=document.createElement('span');lb.className='lbl';lb.textContent='Giao diện';row.appendChild(lb);row.appendChild(sw);nav.appendChild(row);
function paint(){var dk=isDark();sw.classList.toggle('on',dk);sw.setAttribute('aria-checked',dk?'true':'false');
  sw.setAttribute('aria-label',dk?'Nút gạt giao diện: đang tối — gạt sang sáng':'Nút gạt giao diện: đang sáng — gạt sang tối')}
function flip(){var n=isDark()?'light':'dark';d.setAttribute('data-theme',n);try{localStorage.setItem(K,n)}catch(e){}paint()}
sw.addEventListener('click',flip);sw.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();flip()}});paint()})();
```
Trang không có sidebar (landing một cột)? Đặt cùng hàng footer của trang, vẫn là NÚT GẠT có nhãn — tuyệt đối không quay lại chip icon trôi nổi ở góc.

## Accessibility & Document Head (REQUIRED)

These are easy to forget and break silently — wire all of them on every page.

**`<head>` — meta + favicon (without `viewport` the whole Responsive section is dead on mobile):**
```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Title — concise, sentence case</title>
<meta name="description" content="One specific sentence about the page.">
<meta name="theme-color" content="#eaf2fd">
<!-- inline favicon, keeps the file self-contained (no /favicon.ico request) -->
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
```
Add Open Graph (`og:title`/`og:description`/`og:image`) only when the page is meant to be shared/linked externally — skip for purely local `file://` docs.

**Focus ring (a11y, not optional)** — every custom control (`nav a`, `button`, `.code-copy`, `.diagram-reset`, `.collapse-toggle`, checkboxes) hides the native outline; restore a visible keyboard ring. Use `:focus-visible` so it shows for keyboard, not mouse:
```css
:focus-visible{outline:2px solid #0a84ff;outline-offset:2px;border-radius:8px}
:focus:not(:focus-visible){outline:none}
```

**Skip link + `<main>` landmark** — wrap the content (everything after `<nav>`) in `<main id="main">` and add a hidden skip-link as the first focusable element so keyboard users can jump past the sidebar:
```html
<a class="skip-link" href="#main">Skip to content</a>
```
```css
.skip-link{position:fixed;top:8px;left:8px;z-index:200;padding:8px 14px;border-radius:10px;
  background:var(--glass-1);backdrop-filter:blur(var(--blur-1));border:1px solid var(--border);
  transform:translateY(-150%);transition:transform .2s}
.skip-link:focus-visible{transform:translateY(0)}
```

**Smooth scroll + anchor offset** — anchor clicks must glide, and a section must not hide under the top edge:
```css
html{scroll-behavior:smooth}
section[id]{scroll-margin-top:24px}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
```

**`prefers-reduced-motion` — cover ALL motion, not just the body orbs** — one global guard kills decorative animation (orbs, ripple, float/pulse/glow/flowArrow, mind-map draw) for users who ask for it:
```css
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
    transition-duration:.001ms!important;scroll-behavior:auto!important}
}
```

**Informative SVG diagrams need a text alternative** — a draggable node graph carries meaning, so give each `.diagram-box` SVG `role="img"` + a `<title>` (first child) describing what it shows; mark purely decorative SVG (icons already paired with a text label) `aria-hidden="true"`.

**Data figures use tabular numerals** — tables and diagram number labels must not jiggle column width:
```css
table, .diagram-box text, .mm .node .ct{font-variant-numeric:tabular-nums}
```

**Headline orphans** — add `text-wrap:balance` to hero/`h2` and `text-wrap:pretty` to body paragraphs so a single word never strands on its own line.

## Self-Contained — CRITICAL

The user opens these files directly (`file://`, offline, double-click). The output HTML must make ZERO external requests: no font/CSS/JS CDN links, no remote images, no `@import`, no `<script src>`. Everything (CSS, JS, SVG, icons) lives inline in the one file. `<a href>` hyperlinks to external sites are fine — they are navigation, not resource loads.

## Output Path — CRITICAL

**ALWAYS write HTML files to `llmwiki/html/` inside the current project root.**

**Filename MUST be prefixed with today's date `DDMMYY-`** (same `DDMMYY` as the output-report draft, so HTML and wiki draft stay paired). E.g. on 4 Jun 2026 → `040626-cell-formula-override.html`.

- Single file: `llmwiki/html/DDMMYY-<slug>.html`
- Multi-file: `llmwiki/html/DDMMYY-index.html` + `llmwiki/html/DDMMYY-<slug>.html`
- `<slug>` = 2–4 kebab-case words; `DDMMYY` = today (e.g. `040626`).
- NEVER write to the project root or any other directory.
- If `llmwiki/html/` does not exist, create it first.

## Auto-Host

After creating the HTML file(s), ALWAYS start a local HTTP server for preview:

```bash
cd <project-root>
kill -9 $(lsof -ti :8765) 2>/dev/null
nohup npx serve -p 8765 > /tmp/serve.log 2>&1 &
```

Notify user: open `http://localhost:8765/llmwiki/html/DDMMYY-<file>.html`

If port 8765 is already in use, skip (server already running).

## Multi-File Mode

When generating separate pages per wiki file (all files share the same `DDMMYY-` date prefix):
- Create an `DDMMYY-index.html` overview page (card grid linking to all N pages)
- Create `DDMMYY-{slug}.html` for each wiki file (slug derived from filename)
- Each page shares the same CSS design system but uses its section accent color
- Each page has a nav bar linking to all other pages (highlight current page)
- Each page has its own animated SVG diagram based on the topic content

## Interactive Prototype / Editable Data-Grid (optional)

When the user asks to "see how the UI will look", "tạo bảng tương tác thử", or wants a clickable demo of an editable grid/spreadsheet feature, build a **standalone interactive prototype** (same `DDMMYY-<slug>.html`, vanilla JS, no build). ⚠️ **Self-Contained still applies — do NOT pull Tailwind CDN, Google Fonts, or any remote script.** Use plain inline CSS (or an inlined utility layer copied into `<style>`) and the system-font stack from the Font section; the file must open from `file://` with ZERO external requests like every other page this skill emits. These reusable patterns make override/cascade UIs consistent and self-explanatory:

- **Locale-aware number input** — `parseUserNumber(raw, locale)`: strip the locale's thousand sep, swap decimal to `.`, `Number()`. Display via `Intl.NumberFormat(locale)`. Offer a VN ↔ US/Đài toggle.
- **Override vs Affected, persistent coloring** — compute each row TWICE: with overrides (`v`) and without (`base`). A cell is: **override** (in the override map) → amber `bg-amber-50 ring-amber-300` + `✦`; **affected/cascade** (`base[code] !== v[code]`) → emerald `bg-emerald-50 ring-emerald-200` + `↻`. Both persist (not just a flash) until the override is removed. Add a transient `flash` (~1.4s) on the cells that changed this commit.
- **Attribution (which override caused which cell)** — perturbation: for each override in the row, recompute with that one removed; cells whose value differs are caused by it. Build `causes: affected→[ov]` and `affects: ov→[affected]`. Surface via: (a) hover a cell → add a highlight class to linked cells IN THE SAME ROW (`data-affects` / `data-srcs`), (b) `title` tooltip listing names, (c) a toast after save listing recomputed cells.
- **Frictionless editing** — double-click ANY editable column → inline input immediately. Do NOT gate edits behind a blocking `confirm()`. Surface "sensitive" columns passively (kind-tag in header, tooltip, a flag), never a modal that blocks every edit.
- **Proper modal, not `confirm()`** — reserve a styled modal ONLY for destructive actions (e.g. "clear all overrides"); parametrize title/okText/danger.
- **Focus after async UI** — when an edit starts right after closing a modal/dialog, focus the input on a tick (`setTimeout(...,0)`), or it won't take focus.

Keep the chrome (traffic-light header), the system-font stack (`var(--font-text)`), and the liquid-glass blue/white palette consistent with the doc sites (amber/emerald override-state colors in the data-grid pattern above are the one allowed exception — they encode editing state, not theme).

## Best Practices

- **THANG CỠ CHỮ COMPACT — tối ưu màn laptop 13″ (feedback user 2026-07-06, đã đảo chiều một lần — KHÔNG tăng size):** GIẢM chứ đừng tăng: body `p` 13–13.5px, `.lead` 14px, nav link 12px (padding dọc ~5px), list/bảng 12.5px, nhãn/caption 10–10.5px, `h2` ~21px, hero `clamp(26px,4vw,40px)`. Tăng cỡ chữ để "dễ đọc" là SAI trên 13″ — ít nội dung lọt màn hình, wrap chật, nhìn tệ hơn; muốn dễ đọc thì chỉnh line-height/contrast, không chỉnh size. Badge đếm số được phép <10px.
- **SIDEBAR: CUỘN chứ không NÉN (feedback user 2026-07-07):** nav flex-column sẽ flex-shrink co dẹp từng item khi thiếu chỗ — phải chặn: `nav>*{flex-shrink:0}` + `overflow-y:auto`, và ẨN HOÀN TOÀN scrollbar: `nav{scrollbar-width:none;-ms-overflow-style:none} nav::-webkit-scrollbar{width:0;height:0;display:none}`. Stack item luôn giữ chiều cao tự nhiên, thiếu chỗ thì cuộn ngầm.
- ALWAYS inline SVG directly in the HTML (not external files)
- ALWAYS use `clamp()` for hero heading size: `font-size: clamp(32px,5vw,56px)`
- NEVER use `☐` Unicode for checklists — ALWAYS use real `<input type="checkbox">` with `<label for="...">` so items are clickable. Add this CSS for every checklist:

```css
.checklist { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.checklist li { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: var(--text-2); cursor: pointer; }
.checklist li::before { display: none; }
.checklist input[type="checkbox"] {
  width: 16px; height: 16px; border-radius: 4px; border: 1.5px solid #cbd5e1;
  appearance: none; -webkit-appearance: none; cursor: pointer; flex-shrink: 0;
  background: rgba(255,255,255,.8); margin-top: 2px; transition: all .15s;
}
.checklist input[type="checkbox"]:checked {
  background: #0a84ff; border-color: #0a84ff;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M13 4L6.5 11 3 7.5' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E");
  background-size: contain;
}
.checklist label { cursor: pointer; line-height: 1.5; }
.checklist input[type="checkbox"]:checked + label { text-decoration: line-through; color: #94a3b8; }
```

```html
<!-- Correct checklist markup -->
<ul class="checklist">
  <li><input type="checkbox" id="c1"><label for="c1">Item text</label></li>
  <li><input type="checkbox" id="c2"><label for="c2">Item text</label></li>
</ul>
```
- ALWAYS make each `<section>` self-contained with accent colors from the cycle by its index (use `#sec-{i}` CSS rules)
- Keep SVG viewBox widths consistent (900) across diagrams for visual harmony
- Use relative `../file.md` links for "Chi tiết" footers pointing to companion markdown files
- The hero heading gradient should use 3 stops, blue → light blue (KHÔNG bắt đầu bằng navy đậm): `linear-gradient(135deg, #0a84ff, #5aa2e8, #cfe3fb)`
- Nav logo gradient: `linear-gradient(135deg, #0a84ff, #64b5f7)`
- Number of sections is variable — cycle through the 6-blue palette with modulo (`i % 6`)
- ALWAYS start an auto-host server after writing the HTML file (see Auto-Host section above)


---

## Output Report

After all main skill tasks complete, write a propose draft to the wiki.

### Steps

**1. Build the filename:**
- Format: `DDMMYY-<ten>.md`
- `DDMMYY` = today (e.g., `020626` for 2 June 2026)
- `<ten>` = 2–4 kebab-case words summarising what was done (e.g., `landing-page-coteccons`, `brand-kit-fintech`, `ingest-auth-spec`)

**2. Write** `llmwiki/wiki/sources/draft/DDMMYY-<ten>.md`:

```
# DDMMYY-<ten>
**Type:** draft
**Status:** proposed
**Tags:** <skill-name>, output-report
**Proposed:** YYYY-MM-DD

## What
<One sentence — what this skill invocation produced or decided>

## Output
<Key artefacts, files created/modified, or decisions made>

## Files
| File | Action |
|------|--------|
| `path/to/file` | created / modified |

## Notes
- Invoked via: `/<skill-name>` skill

## Origin
- **Draft:** `wiki/sources/draft/DDMMYY-<ten>.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
```

**3. Update wiki index & log:**
- `llmwiki/wiki/index.md` — append one row: `| [DDMMYY-<ten>](sources/draft/DDMMYY-<ten>.md) | draft | YYYY-MM-DD |`
- `llmwiki/wiki/log.md` — append: `## YYYY-MM-DD — <skill-name> — <ten>`

> Skip only when the skill produces zero artefacts and zero decisions (e.g., a pure display mode like `/caveman-stats`).
