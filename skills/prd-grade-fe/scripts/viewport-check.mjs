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
  const ok = sw <= w; if (!ok) bad++; rows.push({ file: t, w, scrollWidth: sw, ok });
  await p.close();
}
await b.close(); console.log(JSON.stringify(rows)); process.exit(bad ? 1 : 0);
