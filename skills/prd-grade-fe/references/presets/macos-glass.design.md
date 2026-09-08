---
# SINH từ block :root bởi design-sync.py — đừng sửa tay; sửa block rồi chạy lại
colors:
  paper: "oklch(97% 0.01 240)"
  paper-2: "oklch(93% 0.02 240)"
  ink: "oklch(22% 0.03 250)"
  ink-2: "oklch(42% 0.03 250)"
  rule: "oklch(85% 0.03 250 / 0.35)"
  accent: "oklch(50% 0.19 255)"
  accent-ink: "oklch(99% 0 0)"
  focus: "oklch(50% 0.19 255)"
typography:
  display:
    fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif"
  body:
    fontFamily: "'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif"
  mono:
    fontFamily: "'SF Mono', ui-monospace, Menlo, monospace"
  scale:
    xs: "11px"
    sm: "12.5px"
    base: "14px"
    md: "17.5px"
    lg: "22px"
    xl: "27px"
    2xl: "34px"
    display: "43px"
rounded:
  card: "16px"
  pill: "999px"
  input: "10px"
---
# Design — macOS Glass

Hệ thiết kế đã khoá. Các lần chạy Hallmark sau đọc file này trước; trang mới bám theo.
Muốn đổi thì sửa có chủ đích, file này là luật.

## System
- Genre · modern-minimal
- Macrostructure · theo brief
- Theme · custom (vibe: "macOS liquid glass, light-blue field, white glass")
- Axes · light-paper / sans-display / blue-accent

## Tokens (canonical · `tokens.css` là bản sinh từ block này)
```css
:root {
  --color-paper:      oklch(97% 0.01 240);
  --color-paper-2:    oklch(93% 0.02 240);
  --color-ink:        oklch(22% 0.03 250);
  --color-ink-2:      oklch(42% 0.03 250);
  --color-rule:       oklch(85% 0.03 250 / 0.35);
  --color-accent:     oklch(50% 0.19 255);
  --color-accent-ink: oklch(99% 0 0);
  --color-focus:      oklch(50% 0.19 255);

  --font-display: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  --font-body:    "SF Pro Text", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  --font-mono:    "SF Mono", ui-monospace, Menlo, monospace;

  /* Kính 3 tầng: 1 nền rộng, 2 card, 3 bảng/khối đặc */
  --glass-1: rgba(255,255,255,.55);
  --glass-2: rgba(255,255,255,.72);
  --glass-3: rgba(255,255,255,.88);
  --blur-1: 24px;  --blur-2: 8px;  --blur-3: 4px;
  --edge-hi: inset 0 1px 0 rgba(255,255,255,.85);
  --shadow-card: 0 4px 20px rgba(20,40,90,.08);

  /* Thang cách 4pt */
  --space-3xs: 2px;  --space-2xs: 4px;  --space-xs: 8px;  --space-sm: 12px;
  --space-md: 16px;  --space-lg: 24px;  --space-xl: 32px; --space-2xl: 48px;
  --space-3xl: 64px; --space-4xl: 96px;

  /* Thang chữ 1.25, gốc 14px */
  --text-xs: 11px;   --text-sm: 12.5px; --text-base: 14px;  --text-md: 17.5px;
  --text-lg: 22px;   --text-xl: 27px;   --text-2xl: 34px;   --text-display: 43px;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 180ms;  --dur-base: 240ms;  --dur-slow: 320ms;

  --radius-card: 16px;  --radius-pill: 999px;  --radius-input: 10px;
}
```

## CTA voice
- Primary · nền accent, chữ accent-ink · radius-pill · padding 12px 24px, min-height 44px
- Secondary · viền 1px rule trên glass-2 · cùng radius-pill

## Motion stance
- Lặng, một primitive reveal (fade + dịch 6px, dur-base, ease-out); hover chỉ đổi nền glass
- Reduced-motion fallback · opacity crossfade ≤150 ms, bỏ dịch chuyển

## Exports
`tokens.css` sinh từ block trên bằng `skills/prd-grade-fe/scripts/design-sync.py`. Cần Tailwind `@theme`, DTCG `tokens.json` hay biến shadcn thì yêu cầu Hallmark mở rộng file này.

## Evidence
Đã qua `impeccable@3.6.1 detect` rc 0 ngày 2026-09-08, 3 vòng, bằng chứng từng vòng tại [`macos-glass.evidence.md`](macos-glass.evidence.md). Trang mẫu: [`macos-glass.probe.html`](macos-glass.probe.html).
