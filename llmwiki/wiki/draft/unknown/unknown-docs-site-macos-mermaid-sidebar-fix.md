---
type: unknown-ledger
title: "unknown — docs-site-macos-mermaid-sidebar-fix"
status: open
source_task: T-260820-01
source_spec: wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md
timestamp: 2026-08-20
---

# Unknown ledger — docs-site-macos-mermaid-sidebar-fix

> **Nợ unknown** — model đã *fill-first* (điền default để không chặn việc), *find-out-later* (chờ thông tin thật để trả nợ). KHÔNG chặn cổng; hiện ra ở `/lint` để không chìm. Đóng khoảng hở giữa `(default)` và `[CẦN LÀM RÕ]`. Xem `[[150726-unknown-ledger]]`.
>
> Thêm/đóng mục bằng `python3 harness/scripts/unknown-ledger.py` — đừng sửa số U-NN bằng tay.

## U-01 — beautiful-mermaid (npm, dist/index.js ESM, deps elkjs+entities, unpacked 2.1MB) có cần bundler (esbuild/rollup) mới chạy được thẳng trong <script> trình duyệt self-contained, hay dist đã sẵn browser-ready?
- **Trace:** FR-004 · SPEC `propose T-260820-01` · task `T-260820-01`
- **Đã fill (default):** Giả định CẦN 1 bước build/bundle off-band (esbuild --bundle --format=iife) để ra 1 file JS vendor, build 1 lần lưu trong repo, không phải build lại mỗi lần sinh trang.
- **Cần verify:** Chạy thử esbuild trên package thật, đo kích thước output, xác nhận chạy được trong file:// không cần network
- **Rủi ro nếu default sai:** high
- **Status:** resolved
- **Resolved:** beautiful-mermaid@1.1.3 dist/index.js (327.7KB) co 2 import tran (entities, elkjs/lib/elk.bundled.js) - KHONG chay thang duoc trong <script type=module>, PHAI bundle. esbuild --bundle --format=iife --minify cho ra 1 file IIFE 1,558,820 bytes (~1.5MB), expose window.BeautifulMermaid.renderMermaidSVG(). PHAT HIEN MOI ngoai cau hoi goc: moi lan goi render() hard-code mot @import url(fonts.googleapis.com) vao SVG output, khong co option API tat - vi pham Self-Contained. Fix da verify: regex strip sau render, SVG van hop le, font fallback he thong. · fix: PoC that: llmwiki/html/200826-beautiful-mermaid-poc.html - verify bang Playwright/Chromium that (khong doan): 9-node flowchart render dung, theme toggle doi mau diagram song qua CSS custom property (khong re-render), wheel-zoom/pan camera hoat dong. Anh chup: /tmp/bm-poc/shot-{light,dark,zoomed}.png. Buoc strip font-import phai duoc dua vao vendor bundle that o Task 1/2 sau khi proposal duyet. · 2026-08-20

## Origin
- Sinh bởi `/propose` khi user chọn "fill-first, find-out-later" cho một unknown của SPEC nguồn.
- Trả nợ: `unknown-ledger.py --resolve <file> <U-id> --value … --fixed … --date …`.
- **Commit:** _(verify-before-commit điền)_
