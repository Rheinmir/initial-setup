---
type: draft
title: prd-grade-fe-PLAN
status: proposed
timestamp: 2026-09-08
task: T-260908-01
---

# /prd-grade-fe — PLAN thi hành

**Goal:** Skill hub `/prd-grade-fe` dựng một trang frontend production-grade: thông số khoá trong `design.md` (hallmark + impeccable đọc chung một file), build theo hallmark, cổng `fe-gate.sh` tất định trước khi giao.
**Architecture:** Hub mỏng (SKILL.md) điều phối 5 pha; hai script Python/bash nhỏ có `--self-test`; preset mặc định là một `design.md` đã qua `impeccable detect` rc 0; rubric LLM distill vào `references/`. Không sửa hallmark, không cài skill impeccable global.
**Tech stack:** Python 3.11 stdlib (re, json, pathlib, argparse) · bash · `npx -y impeccable@3.6.1` (pin) · Node 22 · Playwright qua skill `/playwright-verify` · test = `--self-test` assert trong chính script.
**SPEC nguồn:** `wiki/sources/draft/080926-prd-grade-fe.md` (đã duyệt 2026-09-08)

## Origin
- **SPEC:** `wiki/sources/draft/080926-prd-grade-fe.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints
- **Một nguồn chân lý thông số**: block token `:root{}` trong `design.md` (format hallmark references/design-md.md). Frontmatter YAML của chính file đó (impeccable đọc) và `tokens.css` đều SINH từ block bằng `design-sync.py`; sửa tay phần sinh là drift → `--check` đỏ.
- **Mọi màu/font trong output tham chiếu token** (`var(--color-*)`, `var(--font-*)`) — discipline 3 của hallmark; inline hex/oklch là fail.
- **Cổng giao hàng tất định**: `impeccable detect --json` rc phải = 0 trên mọi file output (rc 2 → sửa → chạy lại, tối đa 3 vòng, còn dư thì báo thẳng, không giấu); rc 1 là lỗi vận hành → dừng, không coi là sạch.
- **Mobile floor**: 320/375/414/768 px không scroll ngang (hallmark discipline 5), kiểm bằng `/playwright-verify`.
- **HTML cho người xem**: có toggle sáng/tối + localStorage + chống FOUC; thang chữ compact 13″; hiện path tương đối của chính nó (không path tuyệt đối — bài học #131).
- **Không ghi công AI** trong commit/file (R15). Skill sửa xong chạy `bash fdk/tools/sync-skill.sh prd-grade-fe`, không cp tay.
- Fail-open với công cụ thiếu: không có `node`/mạng thì bước detect ghi `skipped: <lý do>` trong report, KHÔNG được báo "sạch".
- Không bao giờ gọi `npx impeccable install` (bản 3.6.1 không có help, cài thật vào `$HOME`). `--scope` luôn viết dính (`--scope=type`). Đọc JSON ở stdout, không dựa vào stderr (npx gộp luồng).

## File structure
- Tạo `skills/prd-grade-fe/SKILL.md` — hub 5 pha, hợp đồng vào/ra từng pha, không chứa rubric.
- Tạo `skills/prd-grade-fe/scripts/design-sync.py` — parse block `:root{}` trong `design.md` → ghi frontmatter YAML vào chính file + `tokens.css`; `--check`, `--self-test`.
- Tạo `skills/prd-grade-fe/scripts/fe-gate.sh` — cổng tất định: assert path, detect --json, phân nhánh rc, gọi playwright; `--self-test`.
- Tạo `skills/prd-grade-fe/scripts/viewport-check.mjs` — Playwright đo `scrollWidth` 4 viewport, in JSON.
- Tạo `skills/prd-grade-fe/references/presets/macos-glass.design.md` — preset mặc định đã qua detect rc 0.
- Tạo `skills/prd-grade-fe/references/presets/macos-glass.evidence.md` — bảng finding trước/sau từng vòng.
- Tạo `skills/prd-grade-fe/references/intake.md` — route B (tài liệu) và C (URL) → schema design.md.
- Tạo `skills/prd-grade-fe/references/impeccable-audit.md` — rubric audit/harden/polish distill có nguồn.
- Sửa `llmwiki/skills/utils/prd-grade-fe.md` — mirror (sync-skill.sh sinh).
- Sửa `llmwiki/CLAUDE.md`, `llmwiki/AGENT.md`, `fdk/CAPABILITIES.md`, `llmwiki/wiki/index.md`, `llmwiki/wiki/log.md` — đăng ký.

### Task 1: `design-sync.py` — một nguồn sinh frontmatter + tokens.css

**Thoả:** FR-002

**Files:**
- Tạo: `skills/prd-grade-fe/scripts/design-sync.py`
- Test: chính file, `python3 skills/prd-grade-fe/scripts/design-sync.py --self-test`

**Interfaces:**
- Consumes: `design.md` có block ```` ```css\n:root{ --color-*: …; --font-*: …; --radius-*: …; --text-*: … } ```` (format hallmark `references/design-md.md`).
- Produces: CLI `design-sync.py [--root DIR] [--check] [--self-test]`; hàm `parse_tokens(md:str)->dict[str,str]`, `frontmatter_yaml(tokens:dict)->str`, `render(md:str)->tuple[str,str]` (md mới có frontmatter, nội dung tokens.css). Exit 0 sạch/đã ghi, 1 drift (`--check`), 2 thiếu token bắt buộc. Task 3 và Task 6 gọi CLI này.

- [ ] **Step 1: viết self-test fail (chưa có hàm)**

```python
def self_test():
    md = SAMPLE  # design.md mẫu có block :root với 8 màu + 3 font + 2 radius
    t = parse_tokens(md)
    assert {"color-paper","color-ink","color-accent","font-display","font-body","font-mono"} <= set(t), t.keys()
    assert t["color-accent"].startswith("oklch("), "OKLCH giữ nguyên, không đổi sang hex"
    md1, css1 = render(md); md2, css2 = render(md1)
    assert (md1, css1) == (md2, css2), "idempotent"
    assert "colors:" in md1.split("---")[1] and "typography:" in md1.split("---")[1]
    assert render(md1.replace("oklch(62% 0.19 250)", "oklch(50% 0.1 20)"))[1] != css1, "đổi 1 token → css đổi → --check bắt được"
    print("design-sync --self-test: 4/4 ok")
```

- [ ] **Step 2: chạy cho THẤY nó fail**

Chạy: `python3 skills/prd-grade-fe/scripts/design-sync.py --self-test`
Mong đợi: FAIL — `NameError: name 'parse_tokens' is not defined`

- [ ] **Step 3: code tối thiểu cho pass**

```python
#!/usr/bin/env python3
"""design-sync — design.md là nguồn chân lý; sinh frontmatter (impeccable đọc) + tokens.css từ block :root{}."""
import argparse, re, sys
from pathlib import Path

ROOT_RE = re.compile(r"```css\s*\n(:root\s*\{.*?\})\s*\n```", re.S)
DECL_RE = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);")
FM_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
REQUIRED = ["color-paper", "color-ink", "color-accent", "font-display", "font-body", "font-mono"]

def parse_tokens(md):
    m = ROOT_RE.search(md)
    if not m:
        sys.exit("design-sync: không thấy block ```css :root{} trong design.md")
    return {k: v.strip() for k, v in DECL_RE.findall(m.group(1))}

def frontmatter_yaml(t):
    q = lambda v: '"' + v.replace('"', "'") + '"'
    out = ["---", "# SINH từ block :root bởi design-sync.py — đừng sửa tay; sửa block rồi chạy lại", "colors:"]
    out += [f"  {k[6:]}: {q(v)}" for k, v in t.items() if k.startswith("color-")]
    out.append("typography:")
    for role in ("display", "body", "mono"):
        if f"font-{role}" in t:
            out += [f"  {role}:", f"    fontFamily: {q(t['font-'+role])}"]
    sizes = {k[5:]: v for k, v in t.items() if k.startswith("text-")}
    if sizes:
        out.append("  scale:")
        out += [f"    {k}: {q(v)}" for k, v in sizes.items()]
    radii = {k[7:]: v for k, v in t.items() if k.startswith("radius-")}
    if radii:
        out.append("rounded:")
        out += [f"  {k}: {q(v)}" for k, v in radii.items()]
    out.append("---\n")
    return "\n".join(out)

def render(md):
    t = parse_tokens(md)
    missing = [k for k in REQUIRED if k not in t]
    if missing:
        sys.exit(f"design-sync: thiếu token bắt buộc {missing}")
    body = FM_RE.sub("", md, count=1)
    css = "/* SINH từ design.md bởi design-sync.py — đừng sửa tay */\n" + ROOT_RE.search(md).group(1) + "\n"
    return frontmatter_yaml(t) + body, css

SAMPLE = """# Design — Sample

## Tokens
```css
:root {
  --color-paper: oklch(98% 0.005 250);  --color-paper-2: oklch(95% 0.01 250);
  --color-ink: oklch(20% 0.02 250);     --color-ink-2: oklch(40% 0.02 250);
  --color-rule: oklch(88% 0.01 250);    --color-accent: oklch(62% 0.19 250);
  --color-accent-ink: oklch(99% 0 0);   --color-focus: oklch(62% 0.19 250);
  --font-display: "SF Pro Display", -apple-system, sans-serif;
  --font-body: "SF Pro Text", -apple-system, sans-serif;
  --font-mono: "SF Mono", ui-monospace, monospace;
  --radius-card: 14px; --radius-pill: 999px;
  --text-base: 14px;
}
```
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    root = Path(a.root)
    src = next((root / n for n in ("design.md", "DESIGN.md") if (root / n).is_file()), None)
    if not src:
        sys.exit(f"design-sync: không có design.md ở {root}")
    md_new, css_new = render(src.read_text())
    css_p = root / "tokens.css"
    drift = [p.name for p, new in ((src, md_new), (css_p, css_new)) if not p.is_file() or p.read_text() != new]
    if a.check:
        print("design-sync --check:", "khớp đĩa" if not drift else f"DRIFT {drift}")
        sys.exit(1 if drift else 0)
    src.write_text(md_new); css_p.write_text(css_new)
    print(f"design-sync: đã ghi {src.name} (frontmatter) + tokens.css")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 skills/prd-grade-fe/scripts/design-sync.py --self-test`
Mong đợi: `design-sync --self-test: 4/4 ok`

- [ ] **Step 5: chạy thật trên thư mục tạm rồi --check**

Chạy:
```bash
d=$(mktemp -d); python3 -c "import sys;sys.path.insert(0,'skills/prd-grade-fe/scripts');import importlib;m=importlib.import_module('design-sync');open('$d/design.md','w').write(m.SAMPLE)"
python3 skills/prd-grade-fe/scripts/design-sync.py --root $d && python3 skills/prd-grade-fe/scripts/design-sync.py --root $d --check; echo rc=$?
head -3 $d/design.md
```
Mong đợi: `rc=0`, dòng đầu `design.md` là `---` rồi comment SINH.

### Task 2: `fe-gate.sh` + `viewport-check.mjs` — cổng tất định hiểu đúng rc

**Thoả:** FR-006

**Files:**
- Tạo: `skills/prd-grade-fe/scripts/fe-gate.sh`
- Tạo: `skills/prd-grade-fe/scripts/viewport-check.mjs`
- Test: `bash skills/prd-grade-fe/scripts/fe-gate.sh --self-test`

**Interfaces:**
- Consumes: danh sách file/thư mục output; `npx -y impeccable@3.6.1 detect --json --no-advisory <targets>`; Playwright đã cài theo `/playwright-verify` (`npm ls playwright` trong project hoặc global).
- Produces: `fe-gate.sh [--no-viewport] <target>...` → in bảng `rule | file | message`, ghi `fe-gate.report.json` tại cwd `{detect_rc, findings:[], viewports:[{w,ok,scrollWidth}], skipped:[]}`; exit 0 chỉ khi detect rc 0 VÀ 4 viewport ok; exit 3 khi skipped (thiếu node/mạng); exit 4 khi target thiếu. Task 3, Task 6 gọi.

- [ ] **Step 1: viết self-test fail**

```bash
# trong fe-gate.sh, nhánh --self-test (chưa có hàm gate → lỗi command not found)
self_test() {
  d=$(mktemp -d)
  printf '<html><body style="font-family:Georgia;color:#111;background:#fff"><h1>Sạch</h1><p>ok</p></body></html>' > "$d/clean.html"
  printf '<html><body style="font-family:Inter;color:#808080;background:linear-gradient(#667eea,#764ba2)"><h1>Hi</h1><h4>skip</h4></body></html>' > "$d/dirty.html"
  gate --no-viewport "$d/clean.html"; r1=$?
  gate --no-viewport "$d/dirty.html"; r2=$?
  gate --no-viewport "$d/nope.html"; r3=$?
  echo "clean=$r1 dirty=$r2 missing=$r3"
  [ "$r1" = 0 ] && [ "$r2" = 2 ] && [ "$r3" = 4 ] && echo "fe-gate --self-test: 3/3 ok" || { echo "fe-gate --self-test: FAIL"; exit 1; }
}
```

- [ ] **Step 2: chạy cho THẤY nó fail**

Chạy: `bash skills/prd-grade-fe/scripts/fe-gate.sh --self-test`
Mong đợi: FAIL — `gate: command not found`

- [ ] **Step 3: code tối thiểu cho pass**

```bash
#!/usr/bin/env bash
# fe-gate — cổng tất định trước khi giao UI. Exit: 0 xanh · 1 lỗi vận hành impeccable · 2 có finding · 3 skipped (thiếu node/mạng) · 4 target thiếu
set -u
IMP="npx -y impeccable@3.6.1"
HERE=$(cd "$(dirname "$0")" && pwd)

gate() {
  local noview=0; [ "${1:-}" = "--no-viewport" ] && { noview=1; shift; }
  local rep=fe-gate.report.json skipped='[]'
  for t in "$@"; do [ -e "$t" ] || { echo "fe-gate: target không tồn tại: $t (impeccable sẽ trả rc 0 giả — chặn ở đây)"; echo "{\"detect_rc\":4,\"missing\":\"$t\"}" > $rep; return 4; }; done
  command -v node >/dev/null || { echo '{"detect_rc":3,"skipped":["node không có"]}' > $rep; echo "fe-gate: skipped — không có node. KHÔNG phải sạch."; return 3; }
  local out; out=$($IMP detect --json --no-advisory "$@" 2>/dev/null); local rc=$?
  if [ $rc = 1 ] || [ -z "$out" ]; then echo "fe-gate: impeccable lỗi vận hành hoặc không tải được (rc=$rc). KHÔNG phải sạch."; echo "{\"detect_rc\":${rc:-3},\"skipped\":[\"impeccable không chạy\"]}" > $rep; [ $rc = 1 ] && return 1 || return 3; fi
  printf '%s' "$out" | node -e '
    let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);const f=(j.findings||j.results||[]).flatMap(x=>x.findings?x.findings.map(y=>({file:x.file,...y})):[x]);
    for(const x of f)console.log(`${x.rule||x.id}\t${x.file||""}\t${(x.message||x.summary||"").slice(0,90)}`);
    require("fs").writeFileSync("fe-gate.report.json",JSON.stringify({detect_rc:'"$rc"',findings:f},null,1));})'
  [ $rc = 2 ] && { echo "fe-gate: rc 2 — có finding, sửa rồi chạy lại (tối đa 3 vòng)"; return 2; }
  if [ $noview = 0 ]; then
    node "$HERE/viewport-check.mjs" "$@" || { echo "fe-gate: viewport đỏ (scroll ngang)"; return 2; }
  fi
  echo "fe-gate: XANH (detect rc 0$( [ $noview = 0 ] && echo ' + 4 viewport'))"; return 0
}

case "${1:-}" in --self-test) self_test ;; "") echo "usage: fe-gate.sh [--no-viewport] <target>..."; exit 4 ;; *) gate "$@" ;; esac
```

`viewport-check.mjs`:
```js
// Đo scroll ngang ở 4 viewport (sàn mobile hallmark). Exit 1 nếu bất kỳ viewport nào scrollWidth > innerWidth.
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
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
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `bash skills/prd-grade-fe/scripts/fe-gate.sh --self-test`
Mong đợi: `clean=0 dirty=2 missing=4` rồi `fe-gate --self-test: 3/3 ok` (cần mạng lần đầu để npx tải 3.6.1; offline thì clean/dirty trả 3 và self-test báo FAIL — đúng thiết kế fail-loud).

- [ ] **Step 5: kiểm ngữ nghĩa JSON của impeccable**

Chạy: `npx -y impeccable@3.6.1 detect --json --no-advisory /tmp/x/dirty.html | head -c 400`
Mong đợi: JSON có mảng finding với `rule`/`file`; nếu tên khoá khác (`id`, `results`) thì sửa đúng biểu thức `flatMap` ở Step 3 theo khoá thật — không đoán.

### Task 3: preset macOS glass qua vòng detect

**Thoả:** FR-003

**Files:**
- Tạo: `skills/prd-grade-fe/references/presets/macos-glass.design.md`
- Tạo: `skills/prd-grade-fe/references/presets/macos-glass.evidence.md`
- Tạo (tạm, scratchpad): `probe/index.html` + `probe/design.md`

**Interfaces:**
- Consumes: Task 1 `design-sync.py --root probe`, Task 2 `fe-gate.sh probe/index.html`; token glass từ skill `docs-site-macos` (opacity ladder, blur scale, `--edge-hi`, stack SF Pro).
- Produces: `macos-glass.design.md` đúng format hallmark design-md (System/Tokens/CTA voice/Motion stance/Exports) + frontmatter đã sync; Task 6 copy file này khi user chọn A.

- [ ] **Step 1: dựng trang probe đủ thành phần**

```html
<!-- probe/index.html — hero, card glass, nút primary/secondary, bảng, form, footer; MỌI màu/font qua var(--token) từ tokens.css -->
<link rel="stylesheet" href="tokens.css">
<style>
  body{background:linear-gradient(180deg,var(--color-paper),var(--color-paper-2));color:var(--color-ink);font-family:var(--font-body);margin:0}
  .glass{background:var(--glass-2);backdrop-filter:blur(var(--blur-2));border:1px solid var(--color-rule);border-radius:var(--radius-card);box-shadow:var(--edge-hi)}
  h1{font-family:var(--font-display);font-style:normal}
  .btn{background:var(--color-accent);color:var(--color-accent-ink);border-radius:var(--radius-pill);padding:10px 18px;min-height:44px}
</style>
```
Token khởi điểm (ghi vào `probe/design.md` block `:root`): paper `oklch(97% 0.01 240)`, paper-2 `oklch(93% 0.02 240)`, ink `oklch(22% 0.03 250)`, ink-2 `oklch(42% 0.03 250)`, rule `oklch(85% 0.03 250 / .35)`, accent `oklch(58% 0.19 255)` (Apple blue), accent-ink `oklch(99% 0 0)`, focus = accent; font display/body/mono theo stack SF Pro của docs-site-macos; `--glass-1..3: rgba(255,255,255,.55/.72/.85)`, `--blur-1..3: 12px/20px/28px`, `--edge-hi: inset 0 1px 0 rgba(255,255,255,.85)`, `--radius-card: 16px`, `--radius-pill: 999px`, `--radius-input: 10px`.

- [ ] **Step 2: chạy vòng 1, ghi số**

Chạy: `python3 skills/prd-grade-fe/scripts/design-sync.py --root probe && bash skills/prd-grade-fe/scripts/fe-gate.sh --no-viewport probe/index.html; echo rc=$?`
Mong đợi: `rc=2` với các luật dự kiến `low-contrast` (chữ ink-2 trên glass), `gpt-thin-border-wide-shadow` nếu có bóng rộng. Chép nguyên bảng finding vào `macos-glass.evidence.md` mục "Vòng 1".

- [ ] **Step 3: sửa token theo finding, lặp tới rc 0 (≤3 vòng)**

Quy tắc sửa, theo thứ tự: (1) ink-2 tối hơn tới khi contrast ≥4.5:1 trên `--glass-2` (đo bằng finding), (2) bỏ `box-shadow` rộng, chỉ giữ `--edge-hi`, (3) `--glass-2` ≥ .72 opacity nếu vẫn thiếu contrast, (4) không dùng font trong danh sách overused (Inter, Roboto…). Mỗi vòng ghi bảng vào evidence.
Chạy: `bash skills/prd-grade-fe/scripts/fe-gate.sh --no-viewport probe/index.html; echo rc=$?`
Mong đợi: `rc=0` ở vòng ≤3. Nếu vòng 3 vẫn còn finding: ghi waiver có lý do vào `probe/.impeccable/config.json` (`{"ignores":["<rule>"]}`) VÀ liệt kê trong evidence + preset mục "Waiver".

- [ ] **Step 4: chốt preset**

Chạy: `cp probe/design.md skills/prd-grade-fe/references/presets/macos-glass.design.md && python3 skills/prd-grade-fe/scripts/design-sync.py --root probe --check`
Mong đợi: `khớp đĩa`, rc 0. Preset có đủ 5 mục hallmark (System: genre modern-minimal · macrostructure theo brief · theme custom "macOS liquid glass" · Axes light/sans/blue) và mục "Evidence" trỏ `macos-glass.evidence.md`.

### Task 4: distill rubric impeccable → `references/impeccable-audit.md`

**Thoả:** FR-005

**Files:**
- Tạo: `skills/prd-grade-fe/references/impeccable-audit.md`
- Nguồn (scratchpad, đã sparse-clone): `imp-repo/plugin/skills/impeccable/reference/{audit,harden,polish}.md` @ `2bc2879`

**Interfaces:**
- Consumes: 3 file reference gốc.
- Produces: một checklist 3 phần (Audit 5 trục điểm 0–4 + bảng 20 điểm · Harden: error/empty/loading/i18n tràn chữ/edge · Polish: alignment/spacing/consistency/micro-detail), mỗi mục có `(nguồn: audit.md §<tiêu đề>)`; đầu file ghi `Distill từ pbakaus/impeccable@2bc2879 (LICENSE của repo áp dụng cho phần trích)`. Task 6 nạp file này ở pha 4.

- [ ] **Step 1: đọc 3 file gốc, liệt kê tiêu đề**

Chạy: `grep -nE '^#{2,3} ' $SCRATCH/imp-repo/plugin/skills/impeccable/reference/{audit,harden,polish}.md`
Mong đợi: danh sách section (audit: 5 Diagnostic dimensions + Generate Report; harden/polish: các mục checklist).

- [ ] **Step 2: viết file distill**

```markdown
# impeccable-audit — rubric LLM cho pha 4 của /prd-grade-fe
Distill từ `pbakaus/impeccable@2bc2879` `plugin/skills/impeccable/reference/{audit,harden,polish}.md`. Không cài skill impeccable; đây là bản tự chứa. LICENSE repo gốc áp dụng cho phần trích.

## A. Audit — 5 trục, mỗi trục 0–4 (nguồn: audit.md § Diagnostic Scan)
| # | Trục | Kiểm gì | 0 | 4 |
|---|------|---------|---|---|
| 1 | Accessibility | contrast ≥4.5:1 · reduced-motion có phương án thay · ARIA/role · focus ring · heading hierarchy · alt · label form | fails WCAG A | AA đủ, gần AAA |
| 2 | Performance | layout thrash · animation tốn · lazy-load · will-change lạm dụng · bundle | thrash khắp nơi | lean |
| 3 | Theming | màu hard-code · dark mode vỡ · token lẫn | không token | full token, dark ok |
| 4 | Responsive | width cứng · touch <44px · scroll ngang · text scale · thiếu breakpoint | chỉ desktop | fluid |
| 5 | Implementation integrity | chạy detector, soi từng finding trong ngữ cảnh, drift design-system, nội dung trang trí/gây hiểu nhầm | drift hệ thống | mạch lạc, có chủ đích |
Tổng /20: 18–20 Excellent · 14–17 Good · 10–13 Acceptable · 6–9 Poor · 0–5 Critical. Mức ưu tiên P0 (chặn giao) … P3 (nice-to-have) theo audit.md § Generate Report.

## B. Harden (nguồn: harden.md)
- [ ] mọi state: loading / empty / error / partial — có UI thật, không chỉ happy path
- [ ] chữ dài ×2 (i18n) không vỡ layout; số/ngày/tiền theo locale
- [ ] input biên: rỗng, quá dài, ký tự lạ, paste; nút không double-submit
- [ ] lỗi nói được "làm gì tiếp", không chỉ "có lỗi"

## C. Polish (nguồn: polish.md)
- [ ] căn lề theo một grid; spacing theo thang 4pt; không giá trị lẻ
- [ ] nhất quán: cùng loại nút/nhãn/độ dày viền xuyên trang
- [ ] micro-detail: focus/hover/active đủ 3 trạng thái; icon cùng bộ, cùng stroke
```
(bổ sung từng dòng đúng theo nội dung gốc khi đọc — không bịa mục không có trong nguồn).

- [ ] **Step 3: kiểm mỗi mục truy được nguồn**

Chạy: `grep -c '(nguồn:' skills/prd-grade-fe/references/impeccable-audit.md; grep -c '2bc2879' skills/prd-grade-fe/references/impeccable-audit.md`
Mong đợi: ≥3 và ≥1.

### Task 5: `references/intake.md` — route B và C

**Thoả:** FR-004

**Files:**
- Tạo: `skills/prd-grade-fe/references/intake.md`

**Interfaces:**
- Consumes: hallmark `references/study.md` (URL mode, refuse list, attestation), hallmark `references/design-md.md` (schema).
- Produces: hai thủ tục có bước đánh số; đầu ra cả hai là `design.md` ở gốc project đủ block `:root` theo REQUIRED của Task 1. Task 6 nạp file này ở pha 1–2.

- [ ] **Step 1: viết route B**

```markdown
## Route B — tài liệu thiết kế (file hoặc folder)
1. Liệt kê file: `find <path> -maxdepth 2 -type f \( -name '*.md' -o -name '*.css' -o -name '*.json' -o -name '*.pdf' -o -name '*.png' \)`; PDF/ảnh đọc bằng Read.
2. Điền bảng schema, mỗi hàng ghi `giá trị | nguồn file:dòng | độ tin`: paper, paper-2, ink, ink-2, rule, accent, accent-ink, focus, font-display, font-body, font-mono, radius-card/pill/input, ease/dur, giọng CTA, motion stance.
3. Hàng nào trống → gom thành MỘT câu hỏi bù duy nhất, kèm đề xuất mặc định cho từng hàng (lấy từ preset macOS glass) để user chỉ cần "ok".
4. Ghi `design.md` theo format hallmark design-md; § Provenance liệt kê file nguồn.
5. `python3 skills/prd-grade-fe/scripts/design-sync.py` → frontmatter + tokens.css.
```

- [ ] **Step 2: viết route C**

```markdown
## Route C — URL trang đích
1. Gọi hallmark `study <URL>` (URL mode). Refuse list + Remote URL Safety của study.md chạy TRƯỚC WebFetch; SPA shell/auth-wall/<1KB → xin screenshot (image mode), không suy giảm lặng lẽ.
2. Sau diagnosis, nói "lock the DNA" → hỏi attestation (a) của user / (b) tham chiếu công khai cho brand của user / (c) khác → (c) từ chối emit, chỉ giữ diagnosis.
3. `design.md` emit có § Provenance (URL, ngày, câu trả lời attestation) và § Notes ghi "rhythm: không đọc được từ HTML" + anti-pattern KHÔNG mang theo.
4. `design-sync.py` như Route B.
```

- [ ] **Step 3: kiểm tham chiếu đúng file hallmark tồn tại**

Chạy: `ls skills/hallmark/references/study.md skills/hallmark/references/design-md.md`
Mong đợi: cả hai tồn tại.

### Task 6: SKILL.md hub 5 pha

**Thoả:** FR-001, FR-007

**Files:**
- Tạo: `skills/prd-grade-fe/SKILL.md` (scaffold bằng `python3 fdk/tools/new-skill.py prd-grade-fe --loop utils --strict --desc "…"`)
- Tạo: `llmwiki/skills/utils/prd-grade-fe.md` (new-skill.py sinh mirror)

**Interfaces:**
- Consumes: Task 1 CLI `design-sync.py`, Task 2 CLI `fe-gate.sh` (exit 0/1/2/3/4), Task 3 preset path, Task 4 rubric, Task 5 intake.
- Produces: skill gọi được `/prd-grade-fe [brief]`; report cuối có 6 điểm pre-emit critique hallmark + bảng finding từng vòng + trạng thái gate.

- [ ] **Step 1: scaffold + kiểm trùng**

Chạy: `python3 fdk/tools/new-skill.py prd-grade-fe --loop utils --strict --desc "Dựng frontend production-grade MỘT CỬA: interview nguồn theme (mặc định macOS glassmorphism · trỏ tài liệu thiết kế · paste URL) → khoá thông số vào design.md (hallmark + impeccable đọc chung) → build kỷ luật → cổng impeccable detect + 4 viewport + rubric audit/harden/polish → mới giao. Gọi khi user nói 'frontend production', 'dựng UI chuẩn production', 'prd-grade-fe', 'giao diện kỷ luật', '/prd-grade-fe'."`
Mong đợi: scaffold thành công, in bước register; nếu `--strict` chặn vì trùng hallmark → đọc lý do, đổi description nhấn "một cửa + gate" rồi chạy lại.

- [ ] **Step 2: viết thân SKILL.md**

```markdown
## Steps
### Pha 0 — Pre-flight (không hỏi thứ máy tự thấy)
- `ls design.md DESIGN.md tokens.css .impeccable 2>/dev/null`; `command -v node`; `npx -y impeccable@3.6.1 --help >/dev/null 2>&1 && echo net-ok`.
- Đã có `design.md` → báo "hệ đã khoá, dùng lại" và nhảy pha 3 (trừ khi user đòi đổi theme).
### Pha 1 — Interview MỘT tin nhắn
> Trước khi dựng, cần 4 thứ — trả lời hoặc nói "go ahead":
> 1. **Nguồn theme** — [A] macOS glass mặc định · [B] path tài liệu thiết kế · [C] URL trang đích
> 2. **Audience** · 3. **Use case** · 4. **Tone** (editorial · brutalist · soft · utilitarian · luxury · playful · technical · austere)
"go ahead" → chọn A + suy luận 2–4, công bố một câu ở đầu reply.
### Pha 2 — Khoá biến
- A: `cp skills/prd-grade-fe/references/presets/macos-glass.design.md ./design.md` · B/C: theo `references/intake.md`.
- `python3 skills/prd-grade-fe/scripts/design-sync.py` rồi `--check` rc 0. Công bố Genre/Macrostructure/Theme (hallmark Step 2.5).
### Pha 3 — Build
- Chạy hallmark default flow với `design.md` locked (diversification đảo chiều); mọi màu/font qua `var(--token)`; stamp `<!-- design: macrostructure=… theme=… -->` + 6 điểm critique.
### Pha 4 — Gate
- `bash skills/prd-grade-fe/scripts/fe-gate.sh <output>`: rc 2 → sửa theo bảng finding → chạy lại, tối đa 3 vòng; rc 1/3/4 → dừng, ghi nguyên nhân.
- Nạp `references/impeccable-audit.md`: chấm 5 trục /20, làm Harden + Polish; P0 phải = 0.
- hallmark slop-test (references/slop-test.md) trên output.
### Pha 5 — Deliver
- Report: điểm critique 6 trục · bảng finding vòng 1..n · điểm audit /20 · viewport 4 · path output tương đối · `skipped` nếu có. KHÔNG nói "sạch" khi gate không rc 0.
## Rules
- Không chép rubric hallmark; không `npx impeccable install`; `--scope=` viết dính; JSON đọc ở stdout.
- Vòng sửa >3 mà còn finding → giao kèm bảng dư, hoặc waiver có lý do trong `.impeccable/config.json` — không ignore lén.
```

- [ ] **Step 3: test trigger**

Chạy: thử 2 câu trong phiên mới — "dựng frontend production cho app quản lý kho" và "/prd-grade-fe https://example.com" — quan sát router chọn `prd-grade-fe` (không rơi vào hallmark trần).
Mong đợi: cả hai câu nạp `skills/prd-grade-fe/SKILL.md`.

### Task 7: register + parity + chạy thử end-to-end

**Thoả:** FR-008

**Files:**
- Sửa: `llmwiki/CLAUDE.md` (bảng Skills), `llmwiki/AGENT.md`, `fdk/CAPABILITIES.md` (build), `llmwiki/wiki/index.md`, `llmwiki/wiki/log.md`, `llmwiki/html/fdk-problem-tree.html` (node p-50 → solved)
- Test: `python3 fdk/tools/medic.py --ci`

**Interfaces:**
- Consumes: mọi file Task 1–6.
- Produces: 3 bản parity (canonical · mirror · `~/.claude/skills`), CAPABILITIES cập nhật, một trang mẫu `scratchpad/prd-grade-fe-e2e/index.html` xanh gate.

- [ ] **Step 1: sync + build**

Chạy: `bash fdk/tools/sync-skill.sh prd-grade-fe && python3 fdk/tools/build-capabilities.py && python3 fdk/tools/build-capabilities.py --check`
Mong đợi: parity ok, `--check` rc 0.

- [ ] **Step 2: chạy thử end-to-end trên trang mẫu**

Chạy:
```bash
mkdir -p scratchpad/prd-grade-fe-e2e && cd scratchpad/prd-grade-fe-e2e
cp ../../skills/prd-grade-fe/references/presets/macos-glass.design.md design.md
python3 ../../skills/prd-grade-fe/scripts/design-sync.py && python3 ../../skills/prd-grade-fe/scripts/design-sync.py --check
# dựng index.html theo pha 3 (hallmark, token-only) rồi:
bash ../../skills/prd-grade-fe/scripts/fe-gate.sh index.html; echo rc=$?
```
Mong đợi: `rc=0` (detect 0 + 4 viewport ok) hoặc bảng finding cụ thể nếu chưa.

- [ ] **Step 3: cổng trước push**

Chạy: `python3 fdk/tools/medic.py --ci && python3 harness/validators/index_sync.py --wiki-dir llmwiki/wiki && python3 harness/validators/index_sync.py --wiki-dir fdk/wiki`
Mong đợi: medic xanh, index rc 0 cả hai. Cập nhật node p-50 `status: solved`, `scope: ["skills"]`, `solvedBy: "skill prd-grade-fe + R7 nhận archify"`.

## Self-review
1. **Phủ SPEC:** FR-001/007 → T6; FR-002 → T1; FR-003 → T3; FR-004 → T5; FR-005 → T4; FR-006 → T2; FR-008 → T7. Đủ 8/8.
2. **Placeholder:** không còn mẫu bị cấm; Step 5 của T2 nói rõ phải sửa theo khoá JSON thật thay vì đoán.
3. **Nhất quán tên:** `design-sync.py --root/--check/--self-test`, `fe-gate.sh [--no-viewport] <target>` exit 0/1/2/3/4, `viewport-check.mjs`, preset path `references/presets/macos-glass.design.md` — dùng thống nhất ở T3, T6, T7.
