#!/usr/bin/env node
// route-shots — luồng QA thị giác: login rồi chụp headless từng route có tồn tại.
// Dùng playwright-core + Chrome hệ thống (không tải browser riêng). Ảnh → <out>/<name>.png.
// Người/agent đọc ảnh → viết FINDINGS.md → bật luồng sửa. (frame QA của dây chuyền.)
//
// Usage: node route-shots.mjs --base http://localhost:5230 --out ./qa-shots \
//                             --user demo --pass demo --pw-root <scratchpad/qa>
import { chromium } from "playwright-core";
import { mkdirSync, statSync, writeFileSync, existsSync, readFileSync, copyFileSync } from "node:fs";
// Baseline pixel-diff (quyết định 13/07/26 từ /last30days): thứ DUY NHẤT đã chín trong
// ngành cho "AI-generated UI" là baseline snapshot + diff (argos-ci/argos: "detects
// unintended visual changes"). Bắt được đúng loại lỗi mà bất-biến-CSS và mắt agent MÙ:
// thay đổi NGOÀI Ý MUỐN (vd sửa quá tay làm phẳng cả UI). deps: pixelmatch + pngjs.
let pixelmatch = null, PNG = null;
try {
  pixelmatch = (await import("pixelmatch")).default;
  PNG = (await import("pngjs")).PNG;
} catch { /* không có dep → bỏ qua baseline, vẫn chụp bình thường */ }

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
const BASE = arg("--base", "http://localhost:5230");
const OUT = arg("--out", "./qa-shots");
const USER = arg("--user", "demo");
const PASS = arg("--pass", "demo");

// --route /pc : chụp+kiểm ĐÚNG 1 route (cho vòng tự-kiểm của frame UI).
// --assert   : exit 1 nếu route không 200 hoặc trang rỗng/lỗi (dùng làm acceptance gate).
const ONE = arg("--route", null);
const ASSERT = process.argv.includes("--assert");
const BASELINE = arg("--baseline", null);                       // thư mục ảnh chuẩn
const UPDATE_BASELINE = process.argv.includes("--update-baseline");
// NGƯỠNG MẶC ĐỊNH = 0 (nghiêm ngặt). BÀI HỌC 13/07/26: đặt 0.5% thì một regression THẬT
// (làm phẳng toàn bộ card) chỉ tạo diff 0.113% trên trang rỗng → LỌT GATE. Ngưỡng phần trăm
// là mô hình SAI. Mô hình đúng (Argos/Chromatic): MỌI diff ≠ 0 phải được NGƯỜI/AGENT xem +
// duyệt tay bằng --update-baseline. Chỉ nới ngưỡng khi render thật sự nhiễu (antialias).
const DIFF_MAX = parseFloat(arg("--diff-threshold", "0"));

// so ảnh hiện tại với baseline → % pixel khác + ghi ảnh diff. Trả null nếu không so được.
function diffAgainstBaseline(curFile, baseFile, outFile) {
  if (!pixelmatch || !PNG || !existsSync(baseFile)) return null;
  try {
    const a = PNG.sync.read(readFileSync(baseFile));
    const b = PNG.sync.read(readFileSync(curFile));
    if (a.width !== b.width || a.height !== b.height) {
      return { pct: 100, note: `kích thước đổi ${a.width}x${a.height} → ${b.width}x${b.height}` };
    }
    const d = new PNG({ width: a.width, height: a.height });
    const changed = pixelmatch(a.data, b.data, d.data, a.width, a.height, { threshold: 0.1 });
    writeFileSync(outFile, PNG.sync.write(d));
    return { pct: +((changed / (a.width * a.height)) * 100).toFixed(3), diffFile: outFile };
  } catch (e) {
    return { pct: -1, note: "diff lỗi: " + e.message.split("\n")[0] };
  }
}
const ROUTES = ONE
  ? [[ONE.replace(/\W+/g, "_").replace(/^_|_$/g, "") || "route", ONE]]
  : [
      ["auth", "/auth"], ["home", "/"], ["explore", "/explore"],
      ["archived", "/archived"], ["attachments", "/attachments"],
      ["inbox", "/inbox"], ["setting", "/setting"],
    ];

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome", headless: true });
const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();

// KHỬ NGẪU NHIÊN TRƯỚC KHI CHỤP (bài học 14/07/26): con trỏ nhấp nháy + animation làm MỌI route
// lệch baseline ~0.04% ở mỗi lần chụp ⇒ gate đỏ vĩnh viễn ⇒ **gate nhiễu = gate CHẾT** (bị phớt lờ,
// rồi regression thật lọt qua). Sửa NGUỒN NGẪU NHIÊN, đừng nới ngưỡng — nới ngưỡng là làm mù máy.
await ctx.addInitScript(() => {
  const css = `*,*::before,*::after{animation:none!important;transition:none!important;
    caret-color:transparent!important}
    .cm-cursor,.cm-cursorLayer{opacity:0!important}`;   /* CHỈ con trỏ CodeMirror.
    ⚠ KHÔNG dùng [class*="cursor"] — nó trúng luôn class Tailwind `cursor-pointer`/`cursor-text`
       ⇒ ẩn mất ô nhập ⇒ login chết ⇒ gate tự bắn vào chân mình (đã dính 14/07/26). */
  const put = () => { const st = document.createElement("style"); st.textContent = css;
    document.head?.appendChild(st); };
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", put) : put();
});
const results = [];

// ── LỖ MÙ ĐÃ VÁ (13/07/26): driver login TRƯỚC rồi mới chụp ⇒ /auth luôn redirect về home
//    ⇒ trang SIGN-IN chưa bao giờ được audit (đúng trang user báo lỗi contrast). Nay chụp +
//    audit trang chưa-đăng-nhập TRƯỚC, rồi mới login. Không route nào được phép là vùng mù.
await page.goto(BASE + "/auth", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2200);
try {
  const preFile = `${OUT}/signin.png`;
  mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: preFile });
  const preIssues = await page.evaluate(DESIGN_AUDIT).catch(() => []);
  results.push({ name: "signin", path: "/auth (chưa đăng nhập)", status: 200, file: preFile, issues: preIssues, diff: null });
  console.log(`shot signin (/auth pre-login) → 200` +
    (preIssues.length ? `  ⚑ ${preIssues.map((i) => i.rule + (i.count ? "×" + i.count : "")).join(", ")}` : "  ✓ design-ok"));
} catch (e) { console.log("shot signin FAIL —", e.message.split("\n")[0]); }

// LOGIN HỎNG = GATE PHẢI CHẾT (bài học 13/07/26): login fail ⇒ mọi route redirect về /auth ⇒
// gate audit 8 bản sao trang sign-in rồi hô "design-ok" = XANH GIẢ, tệ hơn đỏ.
let LOGIN_FAILED = null;
let CUR_THEME = "light";   // theme app đang bật (setting tài khoản, dính giữa các route)
const THEME_BG = {};       // theme → màu nền đo được (2 theme trùng nền = 1 cái chưa đổi)
const THEME_BROKEN = [];   // theme khai là đổi nhưng nền không đổi ⇒ ảnh giả ⇒ gate phải chết
try {
  await page.fill('input[type="text"]', USER, { timeout: 5000 });
  await page.fill('input[type="password"]', PASS, { timeout: 5000 });
  await page.getByRole("button", { name: /sign in|đăng nhập/i }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/auth"), { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1500);
  console.log("login: OK");
} catch (e) {
  console.log("login: FAIL —", e.message.split("\n")[0]);
  LOGIN_FAILED = e.message.split("\n")[0];
}

// ── BẤT BIẾN MÁY-KIỂM (design invariants) — máy bắt, không dựa mắt người ──
// Sinh ra vì failure 'ui-pass-without-full-visual-review': --assert cũ chỉ kiểm HTTP200 + có
// file ảnh → trang vỡ vẫn "OK". Hai bất biến này bắt đúng 2 lỗi đã lọt (sidebar lệch màu,
// bóng bị clip). Chạy TRONG trang bằng computed style.
function DESIGN_AUDIT() {   // function-declaration (được hoist) — pre-login capture gọi nó trước khi khai
  const issues = [];
  const bodyBg = getComputedStyle(document.body).backgroundColor;
  // 1. MONOCHROME SURFACE (neumorphism move 1): pane lớn (sidebar/aside/nav) phải CÙNG màu nền.
  document.querySelectorAll('aside, nav, [data-slot="sidebar"], [class*="sidebar"]').forEach((el) => {
    if (el.offsetWidth < 40 || el.offsetHeight < 120) return;         // bỏ chip nhỏ
    const bg = getComputedStyle(el).backgroundColor;
    if (bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent" && bg !== bodyBg) {
      issues.push({ rule: "monochrome-surface", el: el.tagName.toLowerCase(), got: bg, want: bodyBg });
    }
  });
  // 2. SHADOW CLIPPED: chỉ tính bóng LỚN (neumorphic, blur ≥ 8px) bị cha overflow:hidden cắt.
  //    Ngưỡng blur là BẮT BUỘC — không có nó thì bắt luôn `shadow-xs` gốc của app → kêu oan
  //    hàng chục lần/route → gate bị phớt lờ. (Bài học: gate noisy = gate chết.)
  const BLUR_MIN = 8;
  let clipped = 0;
  const sample = [];
  document.querySelectorAll("*").forEach((el) => {
    const cs = getComputedStyle(el);
    const sh = cs.boxShadow;
    if (!sh || sh === "none" || sh.includes("inset")) return;
    // lấy blur lớn nhất trong chuỗi box-shadow (px thứ 3 của mỗi lớp)
    const blurs = [...sh.matchAll(/(-?\d+(?:\.\d+)?)px\s+(-?\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px/g)].map((m) => parseFloat(m[3]));
    if (!blurs.length || Math.max(...blurs) < BLUR_MIN) return;   // bóng nhỏ → bỏ qua
    let p = el.parentElement, d = 0;
    while (p && d++ < 3) {
      const ps = getComputedStyle(p);
      if (ps.overflow === "hidden" || ps.overflowX === "hidden" || ps.overflowY === "hidden") {
        clipped++;
        if (sample.length < 4) sample.push(el.tagName.toLowerCase() + "." + String(el.className || "").slice(0, 24));
        break;
      }
      p = p.parentElement;
    }
  });
  if (clipped) issues.push({ rule: "shadow-clipped", count: clipped, sample });

  // 3. WCAG CONTRAST (BẮT BUỘC — bài học 13/07/26): tương phản chữ là CON SỐ TÍNH ĐƯỢC.
  //    Để nó cho mắt agent là sai thiết kế: rubric ghi "chữ đạt AA" mà không có bất biến ⇒
  //    evaluator KHÔNG detect nổi chữ mờ, kể cả ở trang đăng nhập. Máy phải tính, không đoán.
  const srgb = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const lum = ([r, g, b]) => 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b);
  // PARSE MÀU: KHÔNG chỉ rgb() — app hiện đại trả về oklch(). Regex chỉ bắt rgb ⇒ màu oklch bị
  // coi là TRONG SUỐT ⇒ leo lên nền body ⇒ BÁO OAN (nút đỏ oklch bị chấm 1.21:1 rồi FAIL).
  // Lỗi của THƯỚC, không phải của UI — mà gate báo oan = gate CHẾT. (canvas KHÔNG quy đổi hộ:
  // Chrome trả lại nguyên chuỗi oklch.) ⇒ tự quy đổi oklch → oklab → linear sRGB → sRGB.
  const oklchToRgb = (L, C, H, alpha) => {
    const h = (H * Math.PI) / 180;
    const a = C * Math.cos(h), bb = C * Math.sin(h);
    const l_ = L + 0.3963377774 * a + 0.2158037573 * bb;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * bb;
    const s_ = L - 0.0894841775 * a - 1.2914855480 * bb;
    const l = l_ ** 3, m = m_ ** 3, sC = s_ ** 3;
    const lin = [
      +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * sC,
      -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * sC,
      -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * sC,
    ];
    const g = (v) => { v = v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(Math.max(v, 0), 1 / 2.4) - 0.055;
      return Math.max(0, Math.min(255, Math.round(v * 255))); };
    return { rgb: lin.map(g), a: alpha };
  };
  const parse = (str) => {
    if (!str) return null;
    const m = str.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
    if (m) return { rgb: [ +m[1], +m[2], +m[3] ], a: m[4] === undefined ? 1 : +m[4] };
    const o = str.match(/oklch\(\s*([\d.]+%?)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+%?))?/i);
    if (o) {
      const L = o[1].endsWith("%") ? parseFloat(o[1]) / 100 : +o[1];
      const al = o[4] === undefined ? 1 : (o[4].endsWith("%") ? parseFloat(o[4]) / 100 : +o[4]);
      return oklchToRgb(L, +o[2], +o[3], al);
    }
    if (str === "transparent") return { rgb: [0, 0, 0], a: 0 };
    return null;
  };
  const ratio = (fg, bg) => { const L1 = lum(fg), L2 = lum(bg);
    return +(((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05))).toFixed(2); };
  const effBg = (el) => {                                   // nền hiệu dụng: leo cha tới khi có màu đục
    let q = el;
    while (q && q !== document.documentElement) {
      const c = parse(getComputedStyle(q).backgroundColor);
      if (c && c.a > 0.5) return c.rgb;
      q = q.parentElement;
    }
    const b = parse(getComputedStyle(document.body).backgroundColor);
    return b ? b.rgb : [255, 255, 255];
  };
  const fails = [];
  document.querySelectorAll("*").forEach((el) => {
    // chỉ xét phần tử có CHỮ TRỰC TIẾP (không tính chữ của con)
    const txt = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(" ").trim();
    if (!txt) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity < 0.15) return;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    const fg = parse(cs.color);
    if (!fg || fg.a < 0.15) return;
    const size = parseFloat(cs.fontSize), weight = +cs.fontWeight || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    // BAR = AAA (7:1), KHÔNG phải AA. Bài học 13/07/26: pass ở SÀN AA (4.5) vẫn ra giao diện
    // "chìm"/nhợt — user nhìn phát biết ngay. Sàn a11y ≠ đủ tương phản để đọc thoải mái.
    const need = large ? 4.5 : 7.0;                           // WCAG AAA
    const got = ratio(fg.rgb, effBg(el));
    if (got < need) fails.push({ text: txt.slice(0, 32), got, need, size: Math.round(size), color: cs.color });
  });
  if (fails.length) {
    fails.sort((a, b) => a.got - b.got);
    issues.push({ rule: "contrast-aa", count: fails.length, worst: fails.slice(0, 6) });
  }
  // 4. ROGUE SLAB (bài học 13/07/26 — user chỉ tận tay mảng ĐEN sau editor mà máy vẫn "design-ok"):
  //    `monochrome-surface` chỉ soi aside/nav/[class*=sidebar] ⇒ MÙ với mảng màu lạ là một <div>
  //    bất kỳ GIỮA TRANG. Mặt neumorphic là ĐƠN SẮC: mọi pane LỚN phải cùng độ sáng với nền.
  //    Đo bằng CONTRAST RATIO của nền-pane vs nền-body (con số, không đoán).
  const bodyRgb = parse(bodyBg)?.rgb ?? [255, 255, 255];
  const AREA_MIN = 0.02 * innerWidth * innerHeight;   // ≥2% viewport = "mảng", không phải chip/nút
  const SLAB_MAX = 1.6;                               // lệch nền > 1.6:1 = nhìn thấy rõ = lỗi
  const slabs = [];
  document.querySelectorAll("body *").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width * r.height < AREA_MIN || r.width < 120 || r.height < 60) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity < 0.15) return;
    const c = parse(cs.backgroundColor);
    if (!c || c.a < 0.5) return;                      // trong suốt → không phải mặt
    const got = ratio(c.rgb, bodyRgb);
    if (got > SLAB_MAX) {
      slabs.push({ el: el.tagName.toLowerCase() + "." + String(el.className || "").slice(0, 28),
                   bg: cs.backgroundColor, vsBody: got, w: Math.round(r.width), h: Math.round(r.height) });
    }
  });
  if (slabs.length) {
    slabs.sort((a, b) => b.vsBody - a.vsBody);
    issues.push({ rule: "rogue-slab", count: slabs.length, worst: slabs.slice(0, 5) });
  }

  // ── HÌNH HỌC (bài học 15/07/26 — 2 vòng /redesign + flywheel MÙ với lỗi này) ──
  // Contrast/rogue-slab kiểm MÀU, không kiểm TOẠ ĐỘ. Hai lỗi lọt: (1) nút position:fixed
  // với magic-offset đè lên nhau; (2) nút cạnh nhau lệch chiều cao. Cả hai chỉ lộ khi
  // ĐO rect thật — đọc CSS tĩnh không thấy. Hai rule dưới đo bằng getBoundingClientRect.
  const CTRL = "button, a[href], input, [role=button], .who, .back, #theme";
  const ctrls = [...document.querySelectorAll(CTRL)].filter((el) => {
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity < 0.15) return false;
    const r = el.getBoundingClientRect();
    return r.width >= 8 && r.height >= 8;
  });
  const isAnc = (a, b) => a.contains(b) || b.contains(a);       // cha-con thì đè nhau là bình thường
  const rectOf = (el) => el.getBoundingClientRect();

  // 5. OVERLAP — hai control KHÔNG phải cha-con mà rect chồng ≥4px CẢ HAI chiều = đè nhau.
  //    KHÔNG dùng ngưỡng %-diện-tích: bug thật chỉ là badge CLIP mép nút (19×37px = 18% dt),
  //    mọi ngưỡng % đều lọt. Đúng mô hình: 2 control độc lập chồng ≥ vài px = lỗi (bài học
  //    15/07/26 — ngưỡng 25% ban đầu MISS đúng bug đang muốn bắt, phát hiện khi chạy thật).
  const OVL = 4;   // px — hơn antialias/mép chạm, chưa tới mức "cố tình chồng nhẹ"
  const overlaps = [];
  for (let i = 0; i < ctrls.length; i++) for (let j = i + 1; j < ctrls.length; j++) {
    if (isAnc(ctrls[i], ctrls[j])) continue;
    const a = rectOf(ctrls[i]), b = rectOf(ctrls[j]);
    const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ix >= OVL && iy >= OVL) {
      overlaps.push({ a: (ctrls[i].id || ctrls[i].className || ctrls[i].tagName).toString().slice(0, 24),
                      b: (ctrls[j].id || ctrls[j].className || ctrls[j].tagName).toString().slice(0, 24),
                      chồng: `${Math.round(ix)}×${Math.round(iy)}px` });
    }
  }
  if (overlaps.length) issues.push({ rule: "overlap", count: overlaps.length, worst: overlaps.slice(0, 5) });

  // 6. ROW-MISALIGN — control CÙNG CHA (nhóm ngang) + gần cùng hàng (top lệch ≤ 6px) mà
  //    chiều cao lệch > 3px = "không cao bằng nhau". Đúng lỗi nút Sáng/Tối cao hơn badge.
  const byParent = new Map();
  ctrls.forEach((el) => {
    const p = el.parentElement; if (!p) return;
    (byParent.get(p) || byParent.set(p, []).get(p)).push(el);
  });
  const misaligns = [];
  byParent.forEach((group) => {
    if (group.length < 2) return;
    const rects = group.map(rectOf);
    // cùng hàng: mọi phần tử có top nằm trong dải 6px
    const tops = rects.map((r) => r.top);
    if (Math.max(...tops) - Math.min(...tops) > 6) return;      // khác hàng → bỏ (không so)
    const hs = rects.map((r) => r.height);
    const dh = Math.max(...hs) - Math.min(...hs);
    if (dh > 3) misaligns.push({ parent: (group[0].parentElement.className || group[0].parentElement.tagName).toString().slice(0, 24),
                                 heights: hs.map((h) => Math.round(h)), lệch: Math.round(dh) });
  });
  if (misaligns.length) issues.push({ rule: "row-misalign", count: misaligns.length, worst: misaligns.slice(0, 5) });

  // 7. TAP-TARGET — control tương tác < 24×24px CSS = dưới sàn WCAG 2.2 AA (2.5.8). ĐO rect thật.
  //    (khuyến nghị 44/48px cho mobile; 24 là sàn cứng — dưới nó là fail a11y đo được, không phải gu.)
  const tiny = [];
  ctrls.forEach((el) => {
    const r = rectOf(el);
    if (r.width < 24 || r.height < 24)
      tiny.push({ el: (el.id || el.className || el.tagName).toString().slice(0, 24),
                  size: `${Math.round(r.width)}×${Math.round(r.height)}px` });
  });
  if (tiny.length) issues.push({ rule: "tap-target", count: tiny.length, worst: tiny.slice(0, 6) });

  // 8. MISSING-LABEL — button/link/icon-button screen-reader đọc RỖNG (không tên truy cập được).
  //    Bỏ <input> (tên thường tới từ <label for> ngoài — cần resolve, dễ false-pos); bắt đúng
  //    ca kinh điển: nút-icon không aria-label/text. Đo trực tiếp DOM.
  const nameOf = (el) => (el.getAttribute("aria-label") || el.textContent.trim() ||
    el.getAttribute("title") || (el.querySelector("img") && el.querySelector("img").getAttribute("alt")) ||
    (el.getAttribute("aria-labelledby") ? "x" : "")).trim();
  const unlabeled = ctrls.filter((el) => el.tagName !== "INPUT" && !nameOf(el))
    .map((el) => (el.id || el.className || el.tagName).toString().slice(0, 24));
  if (unlabeled.length) issues.push({ rule: "missing-label", count: unlabeled.length, worst: unlabeled.slice(0, 6) });

  return issues;
}

// ── THEME là một TRẠNG THÁI, không phải tuỳ chọn (bài học 13/07/26) ──
// App bật dark bằng class `.dark` trên <html>` (theo setting app), KHÔNG theo prefers-color-scheme
// ⇒ headless mặc định chỉ bao giờ chụp LIGHT ⇒ dark mode là VÙNG MÙ TUYỆT ĐỐI: user mở app ở
// dark thấy UI vỡ mà gate vẫn xanh. Mỗi route phải chụp ĐỦ CẢ HAI theme.
// khoá localStorage app dùng để nhớ theme (memos: "memos-theme"). Đổi app khác thì đổi cờ này.
// lệnh JS đổi theme ĐÚNG CÁCH APP ĐỔI (chạy trong trang). {{theme}} = light|dark.
// Mặc định = memos/Lume: theme nằm ở SETTING TÀI KHOẢN trên server (localStorage bị ghi đè!).
const THEME_SET = arg("--theme-set", `fetch("/api/v1/users/-/settings/general?updateMask=theme",{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({setting:{name:"users/-/settings/general",generalSetting:{theme:"{{theme}}"==="dark"?"default-dark":"default"}}})})`);
// PHẢI PHỦ *MỌI* THEME APP CUNG CẤP, không phải danh sách tôi tự nghĩ ra (bài học 14/07/26:
// tôi hardcode "light,dark" ⇒ theme `paper` không ai đụng tới ⇒ nó vỡ y hệt dark, user tìm ra).
// Danh sách lấy từ CHÍNH APP (dropdown Theme trong Settings→Preferences), không đoán.
const THEMES = (process.argv.includes("--themes")
  ? process.argv[process.argv.indexOf("--themes") + 1] : "light,dark,paper").split(",");

// ── chụp từng route × từng theme + audit ──
for (const [name0, path] of ROUTES) {
 for (const theme of THEMES) {
  const name = theme === "light" ? name0 : `${name0}.${theme}`;
  try {
    const resp = await page.goto(BASE + path, { waitUntil: "domcontentloaded", timeout: 15000 });
    // ĐỔI THEME PHẢI ĐI QUA ĐÚNG ĐƯỜNG NGƯỜI DÙNG ĐI (bài học 14/07/26 — sai 2 tầng liên tiếp):
    //  ① gắn class `.dark` bằng tay ⇒ cơ chế KHÔNG TỒN TẠI (app dùng data-theme + inject CSS).
    //  ② set localStorage ⇒ app GHI ĐÈ lại từ SETTING TÀI KHOẢN trên server.
    // Cả 2 lần gate XANH trên trạng thái KHÔNG CÓ THẬT. Đường duy nhất chắc chắn đúng là đường
    // NGƯỜI DÙNG bấm: vào Settings → Preferences → chọn theme. Chậm hơn, nhưng THẬT.
    // theme lưu vào SETTING TÀI KHOẢN ⇒ dính lại giữa các route ⇒ phải đổi CẢ HAI CHIỀU,
    // và chỉ đổi khi khác theme đang bật (đỡ tốn thời gian).
    if (theme !== CUR_THEME) {
      try {
        await page.goto(BASE + "/setting", { waitUntil: "domcontentloaded" });
        await page.waitForTimeout(1500);
        await page.getByText("Preferences", { exact: true }).first().click();
        await page.waitForTimeout(1200);
        await page.locator("[data-slot='select-trigger']").first().click();   // dropdown Theme
        await page.waitForTimeout(600);
        await page.getByRole("option", { name: new RegExp("^" + theme + "$", "i") }).click();
        await page.waitForTimeout(1500);
        CUR_THEME = theme;
      } catch (e) { THEME_BROKEN.push(`${theme}: không bấm được UI đổi theme — ${e.message.split("\n")[0]}`); }
      await page.goto(BASE + path, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(1500);
      // VERIFY nền ĐÃ đổi thật — không có bước này thì "chụp dark" chỉ là chụp light lần 2.
      // VERIFY: mỗi theme phải có MẶT RIÊNG. Hai theme cùng màu nền ⇒ một trong hai chưa đổi
      // ⇒ ảnh là GIẢ (đã dính 2 lần: class .dark giả, rồi localStorage bị ghi đè).
      const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      const clash = Object.entries(THEME_BG).find(([t, v]) => v === bg && t !== theme);
      if (clash) THEME_BROKEN.push(`${theme}: nền y hệt theme "${clash[0]}" (${bg}) ⇒ ảnh "${theme}" là GIẢ`);
      THEME_BG[theme] = bg;
    }
    await page.waitForTimeout(2200);
    const file = `${OUT}/${name}.png`;
    await page.screenshot({ path: file });
    const issues = await page.evaluate(DESIGN_AUDIT).catch(() => []);

    // ── BASELINE DIFF: bắt thay đổi NGOÀI Ý MUỐN (thứ mắt agent + bất-biến-CSS đều mù) ──
    let diff = null;
    if (BASELINE) {
      mkdirSync(BASELINE, { recursive: true });
      const baseFile = `${BASELINE}/${name}.png`;
      if (UPDATE_BASELINE || !existsSync(baseFile)) {
        copyFileSync(file, baseFile);                       // lần đầu / cập nhật → ghi chuẩn
        diff = { pct: 0, note: UPDATE_BASELINE ? "baseline cập nhật" : "baseline mới tạo" };
      } else {
        diff = diffAgainstBaseline(file, baseFile, `${OUT}/${name}.diff.png`);
      }
    }

    results.push({ name, path: `${path} [${theme}]`, status: resp?.status() ?? 0, file, issues, diff });
    const bad = issues.filter((i) => i.rule === "monochrome-surface").length;
    const dtxt = diff ? (diff.note ? `  [baseline: ${diff.note}]`
      : `  [diff ${diff.pct}%${diff.pct > DIFF_MAX ? " ⚠ VƯỢT NGƯỠNG" : ""}]`) : "";
    console.log(`shot ${name} (${path}) → ${resp?.status()}` +
      (issues.length ? `  ⚑ ${issues.map((i) => i.rule + (i.count ? "×" + i.count : "")).join(", ")}` : "  ✓ design-ok") +
      (bad ? "  [VI PHẠM BẤT BIẾN]" : "") + dtxt);
  } catch (e) {
    results.push({ name, path: `${path} [${theme}]`, error: e.message.split("\n")[0], issues: [] });
    console.log(`shot ${name} FAIL — ${e.message.split("\n")[0]}`);
  }
 }
}

await browser.close();

// ── MANIFEST.json = BẰNG CHỨNG (chỉ tin file, không tin lời): mỗi route → file ảnh + bytes
//    thật trên đĩa. Không có file / bytes=0 = CHƯA TỪNG CHỤP = fail. ──
for (const r of results) {
  try {
    r.bytes = r.file ? statSync(r.file).size : 0;
  } catch { r.bytes = 0; }
  r.evidence = r.bytes > 0;
}
const manifest = { base: BASE, ts: Date.now(), shots: results };
const mpath = `${OUT}/MANIFEST.json`;
writeFileSync(mpath, JSON.stringify(manifest, null, 2));
console.log("\n=== BẰNG CHỨNG (route đã test → file ảnh) ===");
for (const r of results) console.log(`  ${r.evidence ? "✓" : "✗"} ${r.path}  ${r.file ?? "(no file)"}  ${r.bytes} bytes`);
console.log(`MANIFEST → ${mpath}`);
console.log("JSON " + JSON.stringify(results));

// ── BÁO BẤT BIẾN THIẾT KẾ (máy chấm, không dựa mắt) ──
const viol = results.flatMap((r) => (r.issues || []).filter((i) => i.rule === "monochrome-surface").map((i) => ({ ...i, path: r.path })));
const clip = results.flatMap((r) => (r.issues || []).filter((i) => i.rule === "shadow-clipped").map((i) => ({ ...i, path: r.path })));
if (viol.length) {
  console.log("\n=== ✗ VI PHẠM BẤT BIẾN: monochrome-surface (pane lệch màu nền) ===");
  viol.forEach((v) => console.log(`  ${v.path}: <${v.el}> bg=${v.got}  ≠ body=${v.want}`));
}
if (clip.length) {
  console.log("\n=== ⚠ shadow-clipped (bóng bị cắt bởi cha overflow:hidden) — PHẢI soi ảnh ===");
  clip.forEach((c) => console.log(`  ${c.path}: ${c.count} phần tử  vd ${(c.sample || []).join(", ")}`));
}
const slab = results.flatMap((r) => (r.issues || []).filter((i) => i.rule === "rogue-slab").map((i) => ({ ...i, path: r.path })));
if (slab.length) {
  console.log("\n=== ✗ VI PHẠM BẤT BIẾN: rogue-slab (mảng LỚN lệch sáng so với nền) ===");
  slab.forEach((s) => {
    console.log(`  ${s.path}: ${s.count} mảng`);
    (s.worst || []).forEach((w) =>
      console.log(`     <${w.el}>  ${w.w}×${w.h}px  bg=${w.bg}  lệch nền ${w.vsBody}:1`));
  });
}
const contrast = results.flatMap((r) => (r.issues || []).filter((i) => i.rule === "contrast-aa").map((i) => ({ ...i, path: r.path })));
if (contrast.length) {
  console.log("\n=== ✗ VI PHẠM WCAG AA: chữ không đủ tương phản (máy TÍNH, không đoán) ===");
  contrast.forEach((c) => {
    console.log(`  ${c.path}: ${c.count} chỗ`);
    (c.worst || []).forEach((w) =>
      console.log(`     "${w.text}"  ${w.got}:1 < cần ${w.need}:1  (${w.size}px, ${w.color})`));
  });
}

// ── assert gate: fail nếu route lỗi / thiếu ảnh / VI PHẠM BẤT BIẾN ──
if (ASSERT) {
  if (LOGIN_FAILED) {
    console.error(`ASSERT FAIL — LOGIN HỎNG (${LOGIN_FAILED}). Mọi route đã redirect về /auth ⇒ ` +
      "ảnh chụp là 8 bản sao trang sign-in, KHÔNG phải app. Xanh ở đây là xanh GIẢ.");
    process.exit(1);
  }
  if (THEME_BROKEN.length) {
    console.error("ASSERT FAIL — ĐỔI THEME KHÔNG ĂN:\n  " + [...new Set(THEME_BROKEN)].join("\n  ") +
      "\n  Gate đang chụp cùng một theme hai lần rồi tự khen. Sửa --theme-set cho đúng cách app đổi theme.");
    process.exit(1);
  }
  const bad = results.filter((r) => r.error || (r.status && r.status >= 400) || r.status === 0 || !r.evidence);
  if (bad.length) {
    console.error("ASSERT FAIL (thiếu bằng chứng/lỗi): " +
      bad.map((b) => `${b.path}=${b.evidence ? (b.status ?? b.error) : "NO-IMAGE"}`).join(", "));
    process.exit(1);
  }
  if (viol.length) {
    console.error(`ASSERT FAIL — ${viol.length} vi phạm bất biến monochrome-surface (UI vỡ, không được pass)`);
    process.exit(1);
  }
  if (slab.length) {
    const total = slab.reduce((s, c) => s + c.count, 0);
    console.error(`ASSERT FAIL — ${total} mảng lớn lệch sáng so với nền trên ${slab.length} route (mặt neumorphic phải ĐƠN SẮC)`);
    process.exit(1);
  }
  if (contrast.length) {
    const total = contrast.reduce((s, c) => s + c.count, 0);
    console.error(`ASSERT FAIL — ${total} chỗ chữ KHÔNG đạt WCAG AA trên ${contrast.length} route (a11y là luật, không phải sở thích)`);
    process.exit(1);
  }
  const regress = results.filter((r) => r.diff && !r.diff.note && r.diff.pct > DIFF_MAX);
  if (regress.length) {
    console.error(`\nASSERT FAIL — ${regress.length} route ĐỔI NGOÀI Ý MUỐN so baseline (> ${DIFF_MAX}%):`);
    regress.forEach((r) => console.error(`  ${r.path}: ${r.diff.pct}%  → xem ${r.diff.diffFile}`));
    console.error("  Cố ý đổi? chạy lại với --update-baseline. Không cố ý? ĐÂY LÀ REGRESSION.");
    process.exit(1);
  }
  console.log("\nASSERT OK — có ảnh + không vi phạm bất biến" +
    (BASELINE ? " + không lệch baseline" : "") +
    (clip.length ? ` (⚠ còn ${clip.length} route có shadow-clipped — soi ảnh)` : ""));
}
