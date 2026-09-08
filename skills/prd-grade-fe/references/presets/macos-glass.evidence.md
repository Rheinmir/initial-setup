# Bằng chứng preset macOS glass qua impeccable detect

Ngày 2026-09-08, `impeccable@3.6.1`, chạy từ `scratchpad/probe/` trong repo:

```
python3 ../../skills/prd-grade-fe/scripts/design-sync.py && bash ../../skills/prd-grade-fe/scripts/fe-gate.sh --no-viewport index.html; echo rc=$?
python3 ../../skills/prd-grade-fe/scripts/design-sync.py --check
```

| Vòng | Finding | rc |
|------|---------|----|
| 1 | 4 (2 low-contrast, 1 tight-leading, 1 cramped-padding) | 2 |
| 2 | 1 (tight-leading) | 2 |
| 3 | 0 | 0 |

Bảng finding dưới chép nguyên output của fe-gate (chỉ rút path về tương đối).

## Vòng 1
```
low-contrast	scratchpad/probe/index.html:0	4.2:1 (need 4.5:1) — text #fcfcfc on #0278e7
low-contrast	scratchpad/probe/index.html:0	4.2:1 (need 4.5:1) — text #fcfcfc on #0278e7
tight-leading	scratchpad/probe/index.html:0	line-height 1.20x (need >=1.3)
cramped-padding	scratchpad/probe/index.html:0	<div> "table-wrap": children flush against border+bg on all sides (no inset)
```
rc=2, 4 finding.
Đã sửa: accent `oklch(58% 0.19 255)` thành `oklch(50% 0.19 255)` trong design.md (focus theo accent) rồi design-sync lại; line-height heading 1.15 thành 1.3; `.table-wrap` thêm padding `var(--space-xs)`.

## Vòng 2
```
tight-leading	scratchpad/probe/index.html:0	line-height 1.20x (need >=1.3)
```
rc=2, 1 finding (2 low-contrast và cramped-padding đã hết).
Đã sửa: finding không phải heading (luật bỏ qua h1-h6). Truy trong `rules/checks.mjs` của impeccable: jsdom kế thừa line-height của body theo px (1.5 x 14 = 21px), đoạn hero cỡ `--text-md` 17.5px nên tỉ lệ 21/17.5 = 1.20. Khai `line-height: 1.5` trực tiếp trên `.hero p`.

## Vòng 3
```
0 finding
```
rc=0. `fe-gate: XANH (detect rc 0)`.

## Còn dư
Không.

## Viewport
- Viewport (chạy lại sau khi cài Playwright vào `scratchpad/probe`): `fe-gate.sh index.html` → 320/375/414/768 đều scrollWidth = innerWidth, `fe-gate: XANH (detect rc 0 + 4 viewport)`.

## design-sync --check
rc=0 (frontmatter + tokens.css khớp block :root trong design.md).
