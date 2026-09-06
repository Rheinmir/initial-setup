---
type: draft
title: "docs-site-macos — Mermaid diagram engine + fix vị trí sidebar/toggle"
status: implemented
tags: [docs-site-macos, mermaid, diagram, sidebar, css-bug, ui]
timestamp: 2026-08-20
task: T-260820-01
---

# 200826-docs-site-macos-mermaid-sidebar-fix

**Status:** implemented — user duyệt trực tiếp trong hội thoại (không qua orca gate CLI, phiên chat trực tiếp) và yêu cầu làm ngay + đẩy remote, không chờ `/plan` riêng vì cả 7 task đã có PoC verify đầy đủ trước khi vào SKILL.md thật.

## What

Nâng cấp skill `docs-site-macos` ở hai điểm user chỉ ra qua feedback trực tiếp: (1) thay engine diagram hiện tại — LLM tự tay viết toạ độ SVG rồi JS đoán node bằng heuristic thô — bằng render Mermaid thật có auto-layout, phủ một lớp tương tác (pan/zoom qua `viewBox`, ánh xạ node↔state, overlay HTML qua `getBBox`/`getScreenCTM`) theo đúng tài liệu kỹ thuật user cung cấp; và (2) vá lỗi rendering lệch vị trí ở cụm sidebar + nút toggle dark/light + nút đóng/mở sidebar, bắt nguồn từ một placeholder CSS chưa resolve và cấu trúc rải rác dễ rớt mảnh khi LLM sinh lại trang từ đầu.

## Context

Query wiki (Tầng 1–2 của `/query`) tìm thấy ba mảnh liên quan trực tiếp, không mảnh nào phủ được yêu cầu này:

``fdk/wiki/concepts/docs-site-macos-skill.md`` (fdk concept, stub) xác nhận file canonical là `skills/docs-site-macos/SKILL.md`, mirror `llmwiki/skills/utils/docs-site-macos.md`, và ghi rõ skill này là **chuẩn style của seq HTML** mà rule R11 enforce — nghĩa là thay đổi ở đây ảnh hưởng luôn tới chính trang HTML mà `/propose` sinh ra kèm draft này.

`wiki/draft/uiux/300626-audit-fix-docs-site-macos.md` là audit gần nhất trên chính skill này (2026-06-30): tám fix a11y/head (focus ring, viewport meta, collapse-clip, favicon inline, blue-tinted shadow, smooth scroll, `prefers-reduced-motion`). Audit đó **không đụng** tới engine diagram lẫn cụm positioning sidebar/toggle — hai vùng này chưa từng được rà kể từ khi skill ra đời. Audit cũng chốt "Parity strategy": canonical là nguồn chân lý, mirror generate-and-commit qua `harness/scripts/sync-skills.py`, enforce bằng `fdk-gate.py` + CI + hook `stop.py` — đề xuất này đi đúng khuôn đó, không mở lại quyết định.

`skills/cursor-animated-sites/SKILL.md` (dòng 9, 13, 156, 192) xác nhận nó là **layer trên `docs-site-macos`**, kế thừa tường minh "glass CSS, fonts, scrollbar, background plane" khi generate base page — nên thay đổi ở sidebar/nav-toggle của docs-site-macos có khả năng lan xuống nó (ghi ở Risks, không sửa trong lần này, theo Non-goals).

Đọc code thật (không suy đoán) ở `skills/docs-site-macos/SKILL.md`:

- **Engine diagram hiện tại** (dòng 418-582, mục "Animated SVG Diagrams"): LLM viết tay `<rect x y width height>`/`<line x1 y1 x2 y2>` cho từng node/edge; JS `initDraggableDiagrams()` (dòng 496-578) đoán "cái gì là node" bằng heuristic `rect.width>=70 && rect.height>=30` (dòng 521), gán text vào node bằng toạ độ rơi-vào-trong (dòng 524-528), và bind line vào node gần nhất bằng khoảng cách Euclid tới cạnh rect (hàm `nearest`, dòng 498-506). Không có layout engine thật nào tính toán vị trí — toàn bộ toạ độ là suy đoán tay của LLM lúc sinh trang.
- **Bug positioning cụ thể** ở dòng 807: `.theme-row{position:sticky;bottom:-<pad-nav>;margin-top:auto;...}` — `<pad-nav>` là một **placeholder chưa resolve** để nguyên trong khối CSS lẽ ra phải copy-paste được ngay. Giá trị đúng phải khớp `nav{padding:18px 12px}` (dòng 169) tức `bottom:-18px`, nhưng không có gì trong file buộc hai con số này đi cùng nhau — LLM sinh trang mỗi lần phải tự nhớ/suy ra lại, quên hoặc sai là hàng chứa nút gạt dark/light (`.theme-row`, dòng 805-824) lệch khỏi đáy sidebar.
- **Cảnh báo tự ghi đã tồn tại** ở dòng 193: *"⚠️ KHÔNG viết rule chung ép `position:relative` lên `.nav-toggle` — nó sẽ đè `position:fixed` (cùng specificity, rule sau thắng) làm nút rơi xuống cuối trang"* — xác nhận bằng chứng rằng lớp lỗi "CSS positioning bị đè/lệch quanh cụm nav-toggle" đã từng xảy ra thật, không phải suy đoán của đề xuất này.
- **Cấu trúc rải rác**: `.nav-toggle`/`.nav-close`/ripple nằm ở mục "Navigation" (dòng 161-274), còn `.theme-switch`/`.theme-row` nằm ở mục "Theme Toggle sáng/tối" cách xa 500+ dòng (782-826) — LLM sinh trang mới phải lắp ráp CSS+JS từ hai vị trí không liền mạch mỗi lần.

Prior art ngoài (đã đọc, không suy đoán):

- `github.com/lukilabs/beautiful-mermaid` — repo user chỉ đích danh, đọc README qua `gh api repos/lukilabs/beautiful-mermaid/readme` (fetch 2026-08-20). Xác nhận: render **đồng bộ** (`renderMermaidSVG()`, không async/không flash), zero DOM dependency, hệ theme **hai màu** `bg`/`fg` + enrichment tuỳ chọn (`line`/`accent`/`muted`/`surface`/`border`) qua `color-mix()`, và toàn bộ màu là **CSS custom property trên `<svg>`** nên đổi theme không cần re-render — README của chính họ phê bình đúng điểm yếu mà Mermaid chính thức có ("Complex theming — Customizing colors requires wrestling with CSS classes").
- `registry.npmjs.org/beautiful-mermaid` (fetch qua WebFetch 2026-08-20) — version 1.1.3, unpacked 2.1MB, deps `elkjs@^0.11.0` + `entities@^7.0.1`, main entry `dist/index.js` (ESM). Chưa xác nhận có bản browser-IIFE dựng sẵn hay phải tự bundle — ghi thành `[[unknown-docs-site-macos-mermaid-sidebar-fix]] U-01`.

## Global constraints

Chép nguyên văn giá trị thật từ SKILL.md và wiki — mỗi task ngầm mang theo toàn bộ mục này.

- **Self-Contained — CRITICAL** (chép nguyên văn dòng 885-887 của SKILL.md): *"The user opens these files directly (`file://`, offline, double-click). The output HTML must make ZERO external requests: no font/CSS/JS CDN links, no remote images, no `@import`, no `<script src>`. Everything (CSS, JS, SVG, icons) lives inline in the one file."* Mọi engine diagram mới PHẢI tuân luật này — không `<script src="https://cdn...">`.
- **Canonical + mirror byte-identical** (chốt ở audit 300626): `skills/docs-site-macos/SKILL.md` là nguồn chân lý; `llmwiki/skills/utils/docs-site-macos.md` phải giữ byte-identical qua `harness/scripts/sync-skills.py`, gác bởi `fdk-gate.py` ("skill mirror parity"), CI `.github/workflows/skills-sync.yml --check`, và hook `stop.py` tự sync cuối lượt.
- **Ladder chống over-engineering** (CLAUDE.md, bậc 1 YAGNI): không phải mọi diagram đều cần layout engine — diagram nhỏ/tuyến tính giữ nguyên hand-authored SVG, chỉ diagram phức tạp mới trả giá cho Mermaid.
- **R11 enforce style seq HTML** (fdk concept ``fdk/wiki/concepts/docs-site-macos-skill.md``): companion `.html` của chính draft này phải theo đúng docs-site-macos hiện hành — nên bản thân trang này vừa là spec vừa là bằng chứng sống của style đang áp dụng.
- **Wiki rules** (CLAUDE.md): mọi file wiki phải có `## Origin`; thêm file phải thêm dòng vào `wiki/index.md`; không ghi vào `raw/`; văn xuôi đầy đủ cho tài liệu người đọc (ADR/proposal/report/HTML) — không caveman.

## Non-goals

- **Không tự động hoá build/bundle mỗi lần sinh trang.** Vendor bundle của Mermaid engine được đóng gói **một lần** off-band, lưu như một khối copy-paste sẵn trong SKILL.md; LLM sinh trang chỉ copy khối đó, không chạy bundler.
- **Không bắt buộc mọi diagram đều qua Mermaid.** Giữ nguyên đường hand-authored SVG cho diagram đơn giản (ladder YAGNI) — đây là bổ sung engine thứ hai, không phải thay thế hoàn toàn engine thứ nhất.
- **Không đổi kiến trúc navigation.** Vẫn sidebar-only, không quay lại top bar, không redesign visual của sidebar (glass tier, gradient, specular sheen giữ nguyên) — chỉ sửa các rule positioning bị lệch.
- **Không sửa `cursor-animated-sites` trong lần này.** Ghi nhận rủi ro kế thừa ở Risks, chỉ xử lý nếu đo được ảnh hưởng thật sau khi docs-site-macos đã sửa xong.
- **Không hồi tố các trang `.html` đã sinh trước đây.** Áp cho lần sinh SAU khi skill được sửa, không quét sửa lại các file cũ trong `llmwiki/html/`.
- **Không xây pipeline Python hook vào Mermaid trong lần này.** User tiết lộ định hướng dài hạn: sau này có thể móc Mermaid vào một file Python để sinh chart, cùng phong cách glassmorphism. Đây là context ĐỊNH HƯỚNG cho việc chọn style ngay bây giờ (style phải nhất quán, không vẽ riêng cho HTML rồi làm lại cho Python), KHÔNG phải yêu cầu xây pipeline đó trong đề xuất này — ghi để phiên sau không hiểu nhầm thành scope đã cam kết.

## Approaches

**Trục 1 — chọn engine diagram:**

**Phương án A — vendor `beautiful-mermaid` (npm) làm engine, giữ hand-SVG làm fallback dưới ngưỡng.** Ưu điểm khớp trực tiếp yêu cầu user (gọi tên repo này), render đồng bộ (không async flash — hợp mô hình sinh HTML tĩnh của skill), hệ theme hai-màu `bg`/`fg` map thẳng vào token `--glass`/`data-theme` đã có sẵn (giải quyết luôn một phần đồng bộ dark/light cho riêng diagram gần như miễn phí), và output vẫn là SVG DOM thuần nên áp được nguyên vẹn kỹ thuật `getBBox`/`getScreenCTM` trong tài liệu user cung cấp. Nhược điểm: cần vendor ~vài trăm KB–1MB JS inline (elkjs là layout engine đầy đủ), và cách đóng gói thành browser-ready chưa xác nhận (U-01).

**Phương án B — vendor Mermaid.js chính thức (UMD browser build có sẵn).** Đúng API mà tài liệu user dán (`mermaid.render()`) không cần suy diễn lại cho khác API, có bản UMD dựng sẵn công khai nên không cần tự bundle. Nhược điểm: nặng hơn (Mermaid + toàn bộ dependency tree, được biết tới là lớn hơn beautiful-mermaid nhiều lần), theming phức tạp hơn — đúng điểm yếu mà chính README beautiful-mermaid nêu ra, và async API (`mermaid.render()` trả Promise trong bản mới) lệch với mô hình render-đồng-bộ hiện tại của skill.

**Phương án C — chỉ sửa heuristic rect-detection cho chính xác hơn, không đổi engine.** Rẻ nhất, không thêm dependency nào. Nhưng không giải quyết gốc: vẫn không có layout engine thật, LLM vẫn tự tay đoán toạ độ, sai hình dạng vẫn tái diễn — đây chính là loại "vá triệu chứng" mà CLAUDE.md cấm (mục 5-Why, "dừng ở *vì người ta quên* là chưa tới đáy").

**Chọn A.** Lý do chọn thay vì B: nhẹ hơn, đồng bộ theme gần như miễn phí qua CSS custom property, và đúng tên repo user chỉ định. Lý do không chọn C: không chạm gốc vấn đề. Rủi ro còn lại của A (cách vendor cụ thể) được ghi nợ ở U-01, không chặn việc bắt đầu — kỹ thuật SVG-DOM-manipulation từ tài liệu user áp được như nhau bất kể chọn A hay B, vì cả hai đều xuất SVG DOM chuẩn.

**Trục 2 — sửa positioning bug:**

**Phương án A — CSS custom property nối cứng nguồn↔đích, sửa tại chỗ.** Thay `bottom:-<pad-nav>` bằng `bottom:calc(-1 * var(--nav-pad-y))`, và `nav{padding:18px 12px}` đổi thành `nav{padding:var(--nav-pad-y) 12px}`. Từ đây hai giá trị không thể lệch nhau vì cùng đọc một biến. Rẻ, diff nhỏ, không đổi cấu trúc file.

**Phương án B — gộp toàn bộ cụm sidebar+toggle+theme thành MỘT mục H2 duy nhất, viết lại từ đầu.** Giải quyết luôn vấn đề "rải rác 3 vị trí xa nhau", nhưng đại tu cấu trúc một file 1025 dòng đang có nhiều chỗ khác trỏ tham chiếu chéo tới các mục hiện tại (vd audit 300626 trích dòng cụ thể) — rủi ro cao, diff lớn, không cân xứng với quy mô bug đã tìm được.

**Phương án C — chỉ sửa đúng chỗ bug cụ thể, không đụng cấu trúc.** An toàn nhất, nhưng bỏ qua yêu cầu "scout" mà user nêu rõ — không tìm thêm các placeholder tương tự khác có thể đang ẩn.

**Chọn A, mở rộng thành "A + scout có kỷ luật":** sửa bug cụ thể bằng CSS custom property (không đại tu cấu trúc như B), NHƯNG áp lại kỹ thuật đó cho MỌI chỗ tương tự tìm được khi scout toàn file (Task 4) — vừa rẻ vừa đúng yêu cầu "scout và xử lý nó luôn" của user, không cần đổi cấu trúc file như B.

## Requirements (FR)

**FR-001**: Hệ thống PHẢI thay heuristic rect-detection (`rect.width>=70 && rect.height>=30`, SKILL.md dòng 521) bằng một đường dẫn render Mermaid thật (auto-layout) cho diagram cần độ chính xác cao (nhiều node, có nhánh rẽ/hội tụ).

**FR-002**: Với diagram render qua Mermaid, hệ thống PHẢI cung cấp lớp tương tác gồm: (a) zoom qua wheel (camera scale, KHÔNG kèm pan-bằng-kéo-nền — xem quyết định cập nhật dưới), (b) ánh xạ SVG node id ↔ application state, (c) khả năng overlay HTML động lên node qua `getBBox()` + `getScreenCTM()` khi cần UI động (status card, nút bấm) — không dùng `foreignObject` làm mặc định, (d) kéo TỪNG node riêng lẻ (Level 1, tương đương `.dnode` của engine hand-SVG hiện tại, SKILL.md dòng 446-455) — kéo một node không được làm node khác xê dịch, mọi edge nối tới node đó phải tự re-route theo. Các kỹ thuật này đều đã verify bằng PoC thật (xem Risks), bao gồm phần (d): `beautiful-mermaid` xuất `data-id` trên mỗi `g.node` và `data-from`/`data-to` trên mỗi `polyline.edge`, cho phép bind edge↔node theo ID thật, không cần heuristic đoán-theo-khoảng-cách như engine cũ.

**Quyết định cập nhật (phản hồi user vòng verify thứ 3): KHÔNG cho kéo nền/canvas của Mermaid để pan.** Ban đầu (Approaches, Trục 1) dự định camera đủ cả pan-bằng-kéo lẫn zoom-bằng-cuộn, giống hệt engine hand-SVG cũ (SKILL.md dòng 451: "Drag empty background = pan the whole canvas"). User bác bỏ phần pan-bằng-kéo cho nhánh Mermaid — chỉ giữ zoom (wheel) + kéo từng node. Lý do suy ra được từ ngữ cảnh: kéo nền dễ nhầm với kéo node khi thao tác nhanh, và với nhánh Mermaid (đã có auto-layout đúng) nhu cầu pan-toàn-cảnh thấp hơn nhánh hand-SVG (nơi LLM tự vẽ toạ độ nên hay cần dịch chuyển cả khung để chỉnh). Đã verify bằng Playwright: kéo trên nền trống → `transform` của `<svg>` không đổi (`translate(0px,0px) scale(1)` trước/sau như nhau); kéo trên node → vẫn hoạt động bình thường; wheel zoom → vẫn hoạt động bình thường. Nhánh hand-SVG hiện tại (dòng 446-578, FR-003) giữ nguyên hành vi pan-bằng-kéo-nền cũ — quyết định này CHỈ áp cho nhánh Mermaid mới, không lùi lại sửa engine cũ.

**FR-003**: Hệ thống PHẢI giữ nguyên đường hand-authored SVG (dòng 418-491 hiện tại: styling nodes/arrows, keyframes) làm lựa chọn mặc định cho diagram dưới ngưỡng phức tạp — không bắt buộc mọi `.diagram-box` phải qua Mermaid.

**FR-004**: JS engine Mermaid (beautiful-mermaid theo Approaches) PHẢI được vendor một lần thành một khối copy-paste-verbatim duy nhất trong SKILL.md, không yêu cầu LLM chạy bước build/bundler khi sinh một trang HTML mới. Khối vendor này PHẢI kèm bước strip `@import url('https://fonts.googleapis.com/...')` khỏi mọi SVG do `renderMermaidSVG()` trả về trước khi chèn vào DOM — phát hiện thật (không phải giả thuyết): thư viện hard-code dòng này vào mọi output, không có tuỳ chọn API để tắt, và bỏ qua bước strip là vi phạm trực tiếp Self-Contained.

**FR-005**: Theme của diagram Mermaid PHẢI đổi theo `data-theme` toggle hiện có (dòng 794-795) mà không cần re-render toàn bộ SVG — tận dụng CSS custom property theo đúng cơ chế beautiful-mermaid mô tả.

**FR-006**: Hệ thống PHẢI sửa `.theme-row{bottom:-<pad-nav>}` (dòng 807) bằng một CSS custom property nối cứng với giá trị `padding` thật của `nav` (dòng 169), sao cho hai giá trị không thể lệch nhau khi một trong hai bị đổi.

**FR-007**: Hệ thống PHẢI scout toàn bộ SKILL.md tìm MỌI placeholder dạng `<...>` hoặc giá trị hard-code phải suy đoán tay khác trong cụm CSS/JS liên quan `nav`, `.nav-toggle`, `.nav-close`, `.theme-row`, `.theme-switch`, và sửa từng cái tìm được theo cùng kỹ thuật custom-property ở FR-006 — không chỉ sửa đúng một chỗ đã biết.

**FR-008**: Sau khi sửa, file canonical `skills/docs-site-macos/SKILL.md` và mirror `llmwiki/skills/utils/docs-site-macos.md` PHẢI byte-identical, xác nhận bằng `sync-skills.py --check`.

**FR-009**: Phải render được ít nhất một trang HTML mẫu bằng skill đã sửa (dùng nội dung thật, không phải trang rỗng) và xác nhận bằng mắt: (a) một diagram ≥6 node có nhánh rẽ layout cân đối qua Mermaid, pan/zoom/click hoạt động; (b) nút gạt dark/light, nút đóng `✕`, nút mở `☰` đều nằm đúng vị trí thiết kế ở CẢ hai theme sáng/tối và ở CẢ chế độ overlay màn hẹp <640px.

## Success criteria (SC)

**SC-001**: Người mở một trang docs-site-macos mới sinh thấy nút gạt dark/light nằm khít đáy sidebar, không tràn ra ngoài viền và không hụt vào trong, ở cả theme sáng lẫn tối — quan sát trực tiếp bằng mắt trên trình duyệt, không chỉ "chạy một lệnh ra exit 0".

**SC-002**: Người bấm nút mở/đóng sidebar (☰ ở góc trên-trái khi đóng, ✕ trong sidebar khi mở) trên màn hẹp <640px thấy nút luôn ở đúng vị trí quy định trong SKILL.md — không còn tái diễn triệu chứng "nút rơi xuống cuối trang" đã ghi ở dòng 193.

**SC-003**: Người xem một diagram nhiều-node (≥6 node, có nhánh rẽ) trên trang mới thấy khoảng cách/hình dạng cân đối, không đè lên nhau — so trực quan với một trang cũ dùng engine hand-SVG để thấy khác biệt rõ ràng.

**SC-004**: Người tương tác với diagram Mermaid mới kéo TỪNG node riêng lẻ được (node khác không xê dịch theo, edge tự bám theo node bị kéo), cuộn để zoom, nút reset trả cả node lẫn camera về gốc — nhưng kéo trên nền/canvas trống KHÔNG được làm gì cả (không pan). Không được chỉ có camera zoom/pan mà thiếu khả năng kéo từng node — đây là phản hồi user bác bỏ ở vòng verify đầu (PoC lần đầu chỉ có camera). Không được cho pan-bằng-kéo-nền — phản hồi user ở vòng verify thứ ba. Cả hai đã verify lại bằng Playwright đo toạ độ/transform thật, không chỉ xem ảnh chụp.

**SC-005**: Một dev khác mở SKILL.md sau này để hiểu cụm sidebar+toggle+theme-switch không phải lần theo 3 vị trí cách xa nhau trong file 1000+ dòng để ráp lại bức tranh đầy đủ — tìm được đường dẫn rõ ràng giữa các mục liên quan (bridging note), dù cấu trúc theo-chủ-đề hiện có được giữ nguyên.

## Plan

- [x] Task 1 — Xác nhận cách vendor `beautiful-mermaid` thành 1 file JS browser-ready (U-01 đã trả nợ bằng PoC thật: `esbuild --bundle --format=iife --minify` → 1.5MB IIFE, verify bằng Playwright), thêm bước strip `@import` Google Fonts bắt buộc (phát hiện mới), soạn bảng ánh xạ ĐỦ 7 biến theme (`bg`/`fg`/`line`/`accent`/`muted`/`surface`/`border`) sang token thật của docs-site-macos (SKILL.md dòng 28-29 text `#0f0f12`/`#4a4a55`, dòng 29 border `rgba(30,90,170,.14)`, dòng 103 accent `#0a84ff`) — verify bằng Playwright ở cả 2 theme, KHÔNG còn placeholder tạm. Đã thêm bước hậu-xử-lý DOM sau render (KHÔNG đụng toạ độ ELK.js đã tính — chỉ thêm filter/gradient/CSS): `<feDropShadow>` xanh mềm + `<linearGradient>` sheen kính + `rx=8` bo góc trên node hình chữ nhật (diamond chưa làm sheen, ladder v1) + flowing-dash animation trên edge (tái dùng đúng keyframe `flowArrow` đã có ở SKILL.md dòng 425, không bịa vocabulary mới) — đáp ứng yêu cầu "glassmorphism thật, không phải mặc định trơn" và "lively hơn". Ảnh chụp: `/tmp/bm-poc/shot-glass-crop-{light,dark}.png`.
- [x] Task 2 — Viết lại mục "Animated SVG Diagrams" trong SKILL.md: thêm nhánh Mermaid (vendor bundle từ Task 1 + code camera viewBox pan/zoom + node-id↔state mapping + overlay `getBBox`/`getScreenCTM` theo tài liệu user), giữ nguyên nhánh hand-SVG hiện có làm mặc định dưới ngưỡng phức tạp, ghi rõ ngưỡng chọn nhánh nào (≥6 node hoặc có nhánh rẽ → Mermaid).
- [x] Task 3 — Sửa bug `.theme-row{bottom:-<pad-nav>}` (dòng 807): thêm CSS custom property `--nav-pad-y`, đổi `nav{padding:18px 12px}` → `nav{padding:var(--nav-pad-y) 12px}`, đổi `.theme-row{bottom:-18px}` → `.theme-row{bottom:calc(-1 * var(--nav-pad-y))}`.
- [x] Task 4 — Scout toàn bộ SKILL.md (grep có hệ thống các rule `position:(fixed|absolute|sticky)` quanh selector `nav`/`.nav-toggle`/`.nav-close`/`.theme-switch`/`.theme-row`, và mọi placeholder dạng `<...>` còn sót) tìm thêm bug cùng lớp với Task 3, sửa từng cái bằng CSS custom property nối nguồn↔đích như FR-007 yêu cầu; ghi lại danh sách đã tìm + đã sửa vào Notes của trang wiki output-report.
- [x] Task 5 — Thêm bridging note ngắn ở cả hai mục "Navigation" (dòng 161-274) và "Theme Toggle" (dòng 782-826) trỏ chéo sang nhau, để một dev đọc một mục biết mục kia tồn tại và liên quan — không đại tu cấu trúc file.
- [x] Task 6 — Đồng bộ mirror: copy nguyên văn `skills/docs-site-macos/SKILL.md` đã sửa sang `llmwiki/skills/utils/docs-site-macos.md`, chạy `sync-skills.py --check` xác nhận byte-identical.
- [x] Task 7 — Sinh một trang HTML mẫu thật (không rỗng — dùng lại nội dung của chính draft này hoặc một topic có sẵn) bằng skill vừa sửa, mở bằng trình duyệt, xác nhận bằng mắt cả 5 điều ở FR-009/SC-001..004: diagram Mermaid layout đúng + tương tác được, và sidebar/toggle/theme-switch không còn lệch ở cả 2 theme và cả responsive.

## Assumptions

- Chọn `beautiful-mermaid` thay vì Mermaid.js chính thức `(default)` — lý do đã nêu ở Approaches: nhẹ hơn, render đồng bộ, theme hai-màu map thẳng token hiện có, đúng tên repo user chỉ định.
- Cách đóng gói `beautiful-mermaid` thành browser bundle `(default, find-out-later → [[unknown-docs-site-macos-mermaid-sidebar-fix]] U-01)` — giả định cần một bước `esbuild --bundle --format=iife` chạy MỘT LẦN off-band, chưa xác nhận package có sẵn bản browser-ready hay không.
- Ngưỡng chọn nhánh Mermaid vs hand-SVG là **≥6 node HOẶC có nhánh rẽ/hội tụ** `(default)` — dưới ngưỡng này giữ hand-authored SVG theo ladder YAGNI, vì diagram nhỏ đã đẹp sẵn với engine cũ.
- Bộ điều khiển draggable-per-node hiện có (dòng 446-578: kéo từng node, connector tự route lại) áp dụng cho nhánh hand-SVG như cũ; nhánh Mermaid dùng bộ điều khiển riêng theo tài liệu user (camera-based, không kéo từng node cá nhân) `(default)` — vì Mermaid tự quản lý layout, kéo lệch một node sẽ phá auto-layout mà chính engine vừa tính ra.
- Không mở rộng sửa `cursor-animated-sites` trong lần này dù nó kế thừa docs-site-macos `(default, find-out-later)` — chỉ xử lý nếu phát hiện nó cũng bị ảnh hưởng sau khi đo trên bản đã sửa.
- Trang HTML mẫu ở Task 7 dùng chính nội dung/topic của draft này (tận dụng luôn) thay vì dựng riêng một trang test rỗng `(default)` — tiết kiệm một vòng lặp, và cũng chính là companion HTML mà `/propose` bắt buộc phải sinh.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| Task 1 — vendor bundle + bảng ánh xạ theme | Claude | Quyết định kiến trúc (cách bundle, map màu vào token hiện có) cần phán đoán, không cơ học | pending |
| Task 2 — viết lại mục Animated SVG Diagrams | Claude | Viết code+prose theo sát tài liệu kỹ thuật dài user cung cấp, sai một chi tiết là lệch kiến trúc | pending |
| Task 3 — sửa bug `.theme-row` cụ thể | Claude | Đổi CSS custom property đụng vào rule đang chạy, cần hiểu đúng luồng cascade để không phá thứ khác | pending |
| Task 4 — scout toàn file tìm bug cùng lớp | Claude | Cần đọc-hiểu ngữ cảnh từng rule để phân biệt bug thật với giá trị cố ý hard-code, không phải việc grep máy móc | pending |
| Task 5 — bridging note giữa 2 mục | OpenCode (rẻ) | Thêm một câu trỏ chéo, thuần cơ học sau khi Task 3/4 đã chốt nội dung | pending |
| Task 6 — sync mirror + verify parity | OpenCode (rẻ) | Copy file + chạy script check, không cần phán đoán | pending |
| Task 7 — sinh trang mẫu + xác nhận bằng mắt | Claude | Cần tự đánh giá trực quan kết quả (đẹp/lệch), không phải việc chạy lệnh đơn thuần | pending |

**Sequence diagram:** [200826-docs-site-macos-mermaid-sidebar-fix-seq.html](../../../html/200826-docs-site-macos-mermaid-sidebar-fix-seq.html)

## Risks

- **Kích thước file vendor — ĐÃ ĐO THẬT, không còn suy đoán.** U-01 đã trả nợ (xem `[[unknown-docs-site-macos-mermaid-sidebar-fix]]`): cài `beautiful-mermaid@1.1.3` thật qua npm, `dist/index.js` (327.7KB) có 2 import trần (`entities`, `elkjs/lib/elk.bundled.js`) nên PHẢI bundle — `esbuild --bundle --format=iife --minify` cho ra đúng **1,558,820 bytes (~1.5MB)** một file IIFE duy nhất. Con số này lớn hơn ước lượng ban đầu ("vài trăm KB") nhưng đã verify chạy được thật trong Chromium qua Playwright (PoC: `llmwiki/html/200826-beautiful-mermaid-poc.html`), không phải giả thuyết.
- **Phát hiện MỚI (ngoài U-01 gốc): `beautiful-mermaid` hard-code `@import url('https://fonts.googleapis.com/...')` vào MỌI SVG nó sinh ra, không có option API để tắt** (đọc trực tiếp `buildStyleBlock()` trong `dist/index.js`). Đây là vi phạm thẳng luật Self-Contained (Global constraints) nếu không xử lý. Fix đã verify bằng thực nghiệm: strip dòng đó bằng regex `/@import url\('https:\/\/fonts\.googleapis\.com[^;]+;/g` ngay sau khi gọi `renderMermaidSVG()`, trước khi chèn SVG vào DOM — SVG vẫn hợp lệ, font fallback về hệ thống (đúng tinh thần dòng 779 của SKILL.md: "KHÔNG tải webfont"). Task 1/2 PHẢI đưa bước strip này vào khối vendor, không phải tuỳ chọn.
- **Rủi ro bundling (U-01) — đã đóng, không còn mở.** `beautiful-mermaid` bundle được xác nhận chạy đúng qua esbuild, không cần rơi về Phương án B (Mermaid.js chính thức). Bằng chứng: PoC render 9-node flowchart đúng layout, theme toggle đổi màu diagram sống qua CSS custom property (không re-render — verify bằng `getComputedStyle` trước/sau click, đo được `--bg` đổi từ `#eaf2fd` sang `#0d1a2c`), wheel-zoom/pan camera hoạt động (đo được `transform` đổi thật qua Playwright, không chỉ nhìn ảnh chụp).
- **Kéo từng node riêng lẻ — verify vòng 2, sau khi user bác bỏ vòng 1 (chỉ camera là chưa đủ).** Đã viết lại PoC: mỗi `g.node` bind theo `data-id` thật, mỗi `polyline.edge` bind theo `data-from`/`data-to` thật (không phải heuristic đoán-khoảng-cách của engine cũ). Verify bằng Playwright đo toạ độ: kéo node A → `transform` đổi đúng delta chuột, edge A→B có điểm đầu đổi ĐÚNG BẰNG delta đó, node B không đổi. Kéo cùng lúc 3 node khác (C, D, G) → cả 3 đổi transform độc lập, 6 node còn lại giữ nguyên `null`. Ảnh chụp: `/tmp/bm-poc/shot-drag.png`, `/tmp/bm-poc/shot-multi-drag.png`. Giới hạn đã biết, chưa xử lý: nhãn cạnh (`.edge-label`, vd "Single"/"Multi") KHÔNG tự di chuyển theo khi node bị kéo — lệch khỏi vị trí giữa đường nối. Chấp nhận được cho v1 (diagram hand-SVG cũ không có nhãn cạnh nên không phải regression), ghi nhận làm việc tiếp nếu cần.
- **Verify vòng 3: bỏ pan-bằng-kéo-nền khỏi nhánh Mermaid theo yêu cầu user.** Xoá nhánh `mode='pan'` khỏi pointerdown handler — kéo trên nền trống giờ không làm gì. Verify bằng Playwright: kéo nền → `transform` của `<svg>` giữ nguyên `translate(0px,0px) scale(1)` trước/sau; kéo node và wheel-zoom vẫn hoạt động bình thường sau khi xoá nhánh pan. Không đụng tới engine hand-SVG cũ (dòng 446-578) — nhánh đó vẫn giữ pan-bằng-kéo-nền như hành vi gốc, quyết định này chỉ áp cho nhánh Mermaid mới.
- **Bug thật thứ 2 bắt được lúc verify VERBATIM code trong SKILL.md (không phải bản PoC riêng): thiếu case "hệ điều hành dark, user chưa chọn".** Bản đầu viết vào SKILL.md chỉ có 1 rule `html[data-theme=dark]` cho token `--mm-*`, thiếu cặp `@media(prefers-color-scheme:dark){html:not([data-theme=light])}` mà chính §Theme Toggle đã định nghĩa là khuôn bắt buộc (4-rule, không phải 2). Hậu quả nếu không bắt: trang mở lần đầu trên máy đang ở dark mode (chưa từng bấm toggle) sẽ có card/nav tối nhưng diagram Mermaid vẫn sáng — lệch theme ngay từ lần xem đầu. Phát hiện bằng cách build lại trang test từ CHÍNH đoạn code trích ra từ SKILL.md (không phải bản PoC đã chỉnh tay), chạy Playwright với `colorScheme:'dark'` và KHÔNG set `data-theme` — bắt được `--mm-bg` vẫn trả về giá trị sáng. Đã sửa đúng theo khuôn 4-rule, verify lại: `--mm-bg` trả `#0d1a2c` khi `data-theme` là `null` và hệ đang dark.
- **Cạm bẫy CSS thật đã gặp và sửa: `height:100%` trên SVG không resolve khi div cha không có height tường minh.** `#mmOut` (div bọc SVG do `out.innerHTML = svg` tạo ra) mặc định `height:auto` — theo spec CSS, `%`-height trên một phần tử con bị coi là `auto` khi ancestor gần nhất không có height xác định. Hậu quả: SVG render ở kích thước GỐC (9-node cao ~1800-2000px) thay vì co vào khung 480px, và vì `overflow:hidden` chỉ ẩn HÌNH chứ không đổi toạ độ layout, các node phía dưới (C, D, G...) tồn tại ở toạ độ y=1300-2200px — ngoài tầm chuột thật, khiến 3/9 lần kéo đầu tiên không đăng ký được gì (`transform` vẫn `null` dù code kéo-thả không có bug). Fix: thêm `#mmOut{height:100%;display:block}` tường minh. Bài học cho Task 2: bất kỳ wrapper div nào giữa `.diagram-viewport` và `<svg>` cũng phải khai `height:100%` tường minh, không dựa vào kế thừa ngầm.
- **Lan xuống `cursor-animated-sites`.** Skill này kế thừa glass/scrollbar của docs-site-macos; nếu nó cũng dùng chung `.theme-row`/`.nav-toggle`, sửa xong docs-site-macos mà không note có thể để lại lệch tương tự ở đó — đã ghi rõ trong Non-goals + Assumptions để không quên, không phải để phớt lờ.
- **Diff lớn trên file 1025 dòng đang được nhiều nơi khác trích dẫn theo số dòng cụ thể** (vd audit 300626 trích "dòng 807"). Sửa xong cần rà xem có tài liệu wiki nào trích số dòng cũ của các đoạn bị dịch chuyển hay không, dù không bắt buộc sửa ngược các trích dẫn đó (chúng vẫn đúng về nội dung, chỉ số dòng có thể lệch).

## Self-review

- **Phủ yêu cầu.** Yêu cầu gốc gồm hai phần rõ ràng: (a) đổi engine diagram theo tài liệu Mermaid-SVG-tương-tác user dán nguyên văn — về Task 1, 2; (b) scout + sửa lệch vị trí sidebar/toggle dark-light/đóng-mở — về Task 3, 4, 5. Task 6 (parity) và Task 7 (verify bằng mắt) là hai bước bắt buộc theo Global constraints và FR-009, không phải task phát sinh ngoài yêu cầu.
- **Quét placeholder.** Đã rà lại toàn bộ draft, mọi mục mang nội dung cụ thể và đầy đủ ngay từ bây giờ. Cụm `<pad-nav>` xuất hiện trong draft là trích nguyên văn một bug đang tồn tại trong code thật, đưa vào Context làm bằng chứng — không phải một chỗ mơ hồ của chính draft này.
- **Nhất quán tên-kiểu.** Dùng thống nhất `beautiful-mermaid` (không viết hoa/viết tắt khác), `.theme-row`/`.theme-switch`/`.nav-toggle`/`.nav-close` đúng tên class hiện có trong SKILL.md xuyên suốt draft, `--nav-pad-y` là tên biến CSS mới duy nhất được đề xuất cho FR-006/FR-007.

## Origin

- **Yêu cầu gốc:** user, phiên hiện tại, 2026-08-20 — qua `/orca-workflow`, dán nguyên văn tài liệu kỹ thuật "Biến Mermaid SVG thành diagram tương tác" (9 mục: vấn đề giải quyết, zoom viewBox vs CSS transform, SVG thành component động, tách Render/Behavior, 3 cấp độ tương tác, `getBBox`+`getScreenCTM`, kiến trúc hoàn chỉnh, giới hạn của Mermaid, báo cáo tổng kết) làm căn cứ kỹ thuật cho Task 1-2, cộng yêu cầu "scouting và xử lý nó luôn" cho cụm sidebar/toggle.
- **Prior art đã đọc:** `skills/docs-site-macos/SKILL.md` (dòng 161-274, 418-582, 782-826), `wiki/draft/uiux/300626-audit-fix-docs-site-macos.md`, `skills/cursor-animated-sites/SKILL.md` (dòng 9, 13, 156, 192), `fdk/wiki/concepts/docs-site-macos-skill.md`.
- **Web đã đọc:** `github.com/lukilabs/beautiful-mermaid` README qua `gh api repos/lukilabs/beautiful-mermaid/readme` (fetch 2026-08-20); `registry.npmjs.org/beautiful-mermaid` qua WebFetch (fetch 2026-08-20).
- **Wiki đã query:** `fdk/wiki/concepts/docs-site-macos-skill.md`.
- **Unknown ghi nợ, đã trả:** [[unknown-docs-site-macos-mermaid-sidebar-fix]] U-01 — resolved 2026-08-20, bằng chứng là PoC thật `llmwiki/html/200826-beautiful-mermaid-poc.html` (verify bằng Playwright/Chromium: `node /tmp/bm-poc/verify.mjs`, ảnh chụp `/tmp/bm-poc/shot-{light,dark,zoomed}.png`).
- **Task ID:** `T-260820-01`.
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
