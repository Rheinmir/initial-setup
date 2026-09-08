// Đo scroll ngang ở 4 viewport (sàn mobile hallmark). Exit 1 nếu bất kỳ viewport nào scrollWidth > innerWidth.
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
// playwright lấy từ project đang chạy (cwd) trước, rồi mới tới cạnh script — skill cài ở ~/.claude không có node_modules riêng
let chromium;
for (const base of [resolve(process.cwd(), 'package.json'), import.meta.url]) {
  try { ({ chromium } = createRequire(base)('playwright')); break; } catch {}
}
if (!chromium) { console.error('viewport-check: playwright chưa cài (npm i -D playwright && npx playwright install chromium)'); process.exit(3); }
const targets = process.argv.slice(2).filter(t => t.endsWith('.html'));
const widths = [320, 375, 414, 768];
const b = await chromium.launch(); let bad = 0; const rows = [];
for (const t of targets) for (const w of widths) {
  const p = await b.newPage({ viewport: { width: w, height: 800 } });
  await p.goto(pathToFileURL(resolve(t)).href);
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  const ok = sw <= w; if (!ok) bad++;
  // GH#142: đỏ thì chỉ luôn THỦ PHẠM (phần tử sâu nhất tràn mép phải) — khỏi tự walk querySelectorAll('*')
  const culprit = ok ? null : await p.evaluate(() => {
    const W = innerWidth; let best = null;
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.right > W + 1 && (!best || r.right >= best.r)) best = { r: r.right, el };
    }
    if (!best) return null; const e = best.el;
    return { sel: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + [...e.classList].slice(0, 2).map(c => '.' + c).join(''), right: Math.round(best.r) };
  });
  rows.push({ file: t, w, scrollWidth: sw, ok, culprit });
  await p.close();
}
await b.close(); console.log(JSON.stringify(rows));
// GH#142: đỏ ở hẹp nhưng xanh ở rộng = chữ ký của bẫy min-content grid/flex (1fr thay vì minmax(0,1fr), thiếu min-width:0)
for (const t of targets) {
  const r = rows.filter(x => x.file === t), narrow = r.filter(x => x.w < 768 && !x.ok), wide = r.find(x => x.w === 768);
  if (narrow.length && wide?.ok) console.error(`viewport-check: ${t} đỏ ở ${narrow.map(x => x.w).join('/')} nhưng xanh ở 768 → bẫy min-content: thủ phạm ${narrow[0].culprit?.sel ?? '?'} — track grid dùng minmax(0,1fr) thay 1fr, con flex/grid thêm min-width:0, <pre>/bảng thêm overflow-x:auto`);
  else for (const x of narrow) if (x.culprit) console.error(`viewport-check: ${t}@${x.w} tràn tới ${x.culprit.right}px tại ${x.culprit.sel}`);
}
process.exit(bad ? 1 : 0);
