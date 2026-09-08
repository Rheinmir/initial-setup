# impeccable-audit — rubric LLM cho pha 4 của /prd-grade-fe

Distill từ `pbakaus/impeccable@2bc2879` `plugin/skills/impeccable/reference/{audit,harden,polish}.md`. Không cài skill impeccable; bản tự chứa. License gốc: Apache License 2.0.

## A. Audit

| # | Trục | Kiểm gì | Mốc 0 | Mốc 4 |
|---|------|---------|-------|-------|
| 1 | Accessibility (A11y) | Contrast issues: Text contrast ratios < 4.5:1 (or 7:1 for AAA). Motion sensitivity: `prefers-reduced-motion` needs an intentional alternative that preserves state change and hierarchy; flag a global `0.01ms` kill that destroys useful feedback, flashing above threshold, and motion that blocks focus, reading, or task completion. Missing ARIA: Interactive elements without proper roles, labels, or states. Keyboard navigation: Missing focus indicators, illogical tab order, keyboard traps. Semantic HTML: Improper heading hierarchy, missing landmarks, divs instead of buttons. Alt text: Missing or poor image descriptions. Form issues: Inputs without labels, poor error messaging, missing required indicators. | Inaccessible (fails WCAG A) | Excellent (WCAG AA fully met, approaches AAA) |
| 2 | Performance | Layout thrashing: Reading/writing layout properties in loops. Expensive animations: Casual layout-property animation, unbounded blur/filter/shadow effects, or effects that visibly drop frames. Missing optimization: Images without lazy loading, unoptimized assets. `will-change` overuse: applied broadly or left on at rest (it is a targeted hint for known expensive animations, not a baseline requirement). Bundle size: Unnecessary imports, unused dependencies. Render performance: Unnecessary re-renders, missing memoization. | Severe issues (layout thrash, unoptimized everything) | Excellent (fast, lean, well-optimized) |
| 3 | Theming | Hard-coded colors: Colors not using design tokens. Broken dark mode: Missing dark mode variants, poor contrast in dark theme. Inconsistent tokens: Using wrong tokens, mixing token types. Theme switching issues: Values that don't update on theme change. | No theming (hard-coded everything) | Excellent (full token system, dark mode works perfectly) |
| 4 | Responsive Design | Fixed widths: Hard-coded widths that break on mobile. Touch targets: Interactive elements < 44x44px. Horizontal scroll: Content overflow on narrow viewports. Text scaling: Layouts that break when text size increases. Missing breakpoints: No mobile/tablet variants. | Desktop-only (breaks on mobile) | Excellent (fluid, all viewports, proper touch targets) |
| 5 | Implementation Integrity | Run the bundled detector and verify each finding in context. Look for repeated implementation shortcuts, design-system drift, misleading or decorative content, and structure that is interchangeable with an unrelated product. Keep deterministic findings separate from visual judgment and call out false positives. | systemic drift | coherent and intentional |

(nguồn: audit.md § 1. Accessibility (A11y), § 2. Performance, § 3. Theming, § 4. Responsive Design, § 5. Implementation Integrity (CRITICAL))

**Rating bands** (tổng điểm 5 trục, thang /20): 18-20 Excellent (minor polish); 14-17 Good (address weak dimensions); 10-13 Acceptable (significant work needed); 6-9 Poor (major overhaul); 0-5 Critical (fundamental issues). (nguồn: audit.md § Generate Report > Audit Health Score)

**Mức ưu tiên P0-P3** (gắn cho mỗi issue tìm được):
- **P0 Blocking**: Prevents task completion. Fix immediately.
- **P1 Major**: Significant difficulty or WCAG AA violation. Fix before release.
- **P2 Minor**: Annoyance, workaround exists. Fix in next pass.
- **P3 Polish**: Nice-to-fix, no real user impact. Fix if time permits.

(nguồn: audit.md § Generate Report > Detailed Findings by Severity)

## B. Harden

### Assess Hardening Needs
- [ ] Test very long text (names, descriptions, titles)
- [ ] Test very short text (empty, single character)
- [ ] Test special characters (emoji, RTL text, accents)
- [ ] Test large numbers (millions, billions)
- [ ] Test many items (1000+ list items, 50+ options)
- [ ] Test no data (empty states)
- [ ] Test network failures (offline, slow, timeout)
- [ ] Test API errors (400, 401, 403, 404, 500)
- [ ] Test validation errors
- [ ] Test permission errors
- [ ] Test rate limiting
- [ ] Test concurrent operations
- [ ] Test long translations (German is often 30% longer than English)
- [ ] Test RTL languages (Arabic, Hebrew)
- [ ] Test character sets (Chinese, Japanese, Korean, emoji)
- [ ] Test date/time formats
- [ ] Test number formats (1,000 vs 1.000)
- [ ] Test currency symbols

(nguồn: harden.md § Assess Hardening Needs)

### Hardening Dimensions — Text Overflow & Wrapping
- [ ] Long text handling: single-line ellipsis truncate, multi-line line-clamp, or wrap (word-wrap/overflow-wrap/hyphens)
- [ ] Flex/Grid overflow: `min-width: 0` (và `min-height: 0` cho grid item) để cho phép shrink, `overflow: hidden`
- [ ] Responsive text sizing: dùng `clamp()` cho fluid typography; đặt minimum readable size (floor 16px body trên mobile, 14px chỉ cho text phụ — iOS Safari force-zoom input dưới 16px); test zoom 200%; container phải giãn theo text

(nguồn: harden.md § Hardening Dimensions > Text Overflow & Wrapping)

### Hardening Dimensions — Internationalization (i18n)
- [ ] Text expansion: chừa 30-40% không gian cho bản dịch, dùng flexbox/grid co giãn theo nội dung, test với ngôn ngữ dài nhất (thường là tiếng Đức), tránh fixed width cho container chứa text
- [ ] RTL support: dùng logical properties (`margin-inline-start`, `padding-inline`, `border-inline-end`) thay vì physical (`margin-left`, `padding-left/right`, `border-right`), hoặc override qua `[dir="rtl"]`
- [ ] Character set support: UTF-8 mọi nơi, test CJK (Chinese/Japanese/Korean), test emoji (2-4 byte), xử lý được các script khác nhau (Latin, Cyrillic, Arabic, ...)
- [ ] Date/Time formatting: dùng `Intl.DateTimeFormat` và `Intl.NumberFormat` (currency) thay vì tự format tay
- [ ] Pluralization: dùng thư viện i18n đúng chuẩn thay vì `${count} item${count !== 1 ? 's' : ''}` kiểu tiếng Anh

(nguồn: harden.md § Hardening Dimensions > Internationalization (i18n))

### Hardening Dimensions — Error Handling
- [ ] Network errors: hiện thông báo lỗi rõ ràng, có nút retry, giải thích chuyện gì xảy ra, cho offline mode nếu phù hợp, xử lý timeout
- [ ] Form validation errors: lỗi inline gần field, thông điệp rõ và cụ thể, gợi ý cách sửa, không chặn submit khi không cần thiết, giữ lại input của user khi lỗi
- [ ] API errors xử lý theo status code: 400 hiện validation errors, 401 redirect login, 403 hiện permission error, 404 hiện not-found state, 429 hiện rate-limit message, 500 hiện generic error + offer support
- [ ] Graceful degradation: chức năng lõi chạy được không cần JavaScript, image có alt text, progressive enhancement, có fallback cho tính năng chưa được hỗ trợ

(nguồn: harden.md § Hardening Dimensions > Error Handling)

### Hardening Dimensions — Edge Cases & Boundary Conditions
- [ ] Empty states: không có item trong list, không có kết quả search, không có notification, không có data hiển thị, có next action rõ ràng
- [ ] Loading states: initial load, pagination load, refresh, hiện đang load cái gì ("Loading your projects..."), ước lượng thời gian cho thao tác dài
- [ ] Large datasets: pagination hoặc virtual scrolling, có search/filter, tối ưu hiệu năng, không load hết 10,000 item cùng lúc
- [ ] Concurrent operations: chặn double-submit (disable button khi đang load), xử lý race condition, optimistic update kèm rollback, conflict resolution
- [ ] Permission states: không có quyền xem, không có quyền sửa, chế độ read-only, giải thích rõ lý do
- [ ] Browser compatibility: polyfill cho tính năng mới, fallback cho CSS chưa hỗ trợ, feature detection (không phải browser detection), test trên browser mục tiêu

(nguồn: harden.md § Hardening Dimensions > Edge Cases & Boundary Conditions)

### Hardening Dimensions — Input Validation & Sanitization
- [ ] Client-side validation: required field, format validation (email, phone, URL), giới hạn độ dài, pattern matching, custom validation rule
- [ ] Server-side validation (luôn luôn): không bao giờ chỉ tin client-side, validate và sanitize mọi input, chống injection, rate limiting
- [ ] Constraint handling: đặt constraint rõ ràng (maxlength, pattern, required, aria-describedby hint)

(nguồn: harden.md § Hardening Dimensions > Input Validation & Sanitization)

### Hardening Dimensions — Accessibility Resilience
- [ ] Keyboard navigation: mọi chức năng dùng được bằng bàn phím, tab order hợp lý, quản lý focus trong modal, skip link cho nội dung dài
- [ ] Screen reader support: ARIA label đúng, thông báo thay đổi động (live region), alt text mô tả được, semantic HTML
- [ ] High contrast mode: test ở Windows high contrast mode, không chỉ dựa vào màu sắc, có visual cue thay thế

(nguồn: harden.md § Hardening Dimensions > Accessibility Resilience)

### Hardening Dimensions — Performance Resilience
- [ ] Slow connections: progressive image loading, skeleton screen, optimistic UI update, offline support (service worker)
- [ ] Memory leaks: dọn event listener, hủy subscription, clear timer/interval, abort request đang chờ khi unmount
- [ ] Throttling & Debouncing: debounce input search, throttle scroll handler

(nguồn: harden.md § Hardening Dimensions > Performance Resilience)

### Testing Strategies
- [ ] Manual testing: dữ liệu cực trị (rất dài, rất ngắn, rỗng), nhiều ngôn ngữ, offline, mạng chậm (throttle 3G), screen reader, chỉ dùng bàn phím, browser cũ
- [ ] Automated testing: unit test cho edge case, integration test cho error scenario, E2E test cho critical path, visual regression test, accessibility test (axe, WAVE)

(nguồn: harden.md § Testing Strategies)

### Verify Hardening
- [ ] Long text: thử tên 100+ ký tự
- [ ] Emoji: dùng emoji trong mọi field text
- [ ] RTL: test với tiếng Ả Rập hoặc Hebrew
- [ ] CJK: test với tiếng Trung/Nhật/Hàn
- [ ] Network issues: tắt mạng, throttle kết nối
- [ ] Large datasets: test với 1000+ item
- [ ] Concurrent actions: bấm submit 10 lần liên tiếp
- [ ] Errors: ép API lỗi, test hết mọi error state
- [ ] Empty: xóa hết dữ liệu, test empty state

(nguồn: harden.md § Verify Hardening)

### NEVER (harden)
- [ ] Không giả định input hoàn hảo (validate mọi thứ)
- [ ] Không bỏ qua internationalization (thiết kế cho toàn cầu)
- [ ] Không để thông báo lỗi generic ("Error occurred")
- [ ] Không quên kịch bản offline
- [ ] Không chỉ tin client-side validation
- [ ] Không dùng fixed width cho text
- [ ] Không giả định độ dài text kiểu tiếng Anh
- [ ] Không chặn cả interface khi một component lỗi

(nguồn: harden.md § NEVER)

## C. Polish

### 1. Establish the system
- [ ] Đọc DESIGN.md và các token, shared component, pattern, flow lân cận đại diện (hoặc theo coherent project conventions nếu chưa có formal system)
- [ ] Phân loại mỗi drift: missing token / one-off implementation / conceptual mismatch / local defect
- [ ] Sửa ở mức đúng hẹp nhất có thể; hỏi lại khi không suy ra được nguyên tắc hệ thống ràng buộc

(nguồn: polish.md § 1. Establish the system)

### 2. Gather the evidence
- [ ] Tự dùng thử feature ở kích thước đại diện: desktop và mobile trên web; device class đã ship (simulator/emulator/hardware) trên native
- [ ] Xác định: path đã functionally complete chưa
- [ ] Xác định: quality bar mong muốn và thời gian có sẵn
- [ ] Xác định: constraint đã biết hoặc phần cố tình chưa làm xong
- [ ] Xác định: các state, độ dài nội dung, role, input method mà user thật sự sẽ gặp
- [ ] Kiểm tra critique snapshot trước đó (`impeccable critique-storage latest`) và gộp finding P0/P1 liên quan nếu còn current

(nguồn: polish.md § 2. Gather the evidence)

### 3. Triage
- [ ] Sửa trước: broken/blocked task, mất dữ liệu, state gây hiểu lầm, path không truy cập được
- [ ] Sửa: thiếu loading, empty, error, success, disabled, permission state
- [ ] Sửa: drift về flow, hierarchy, responsive, design-system
- [ ] Sửa: bất nhất về visual và motion
- [ ] Sửa: dọn code và asset
- [ ] Không đánh bóng một góc trong khi phần còn lại vẫn dưới cùng quality bar

(nguồn: polish.md § 3. Triage)

### 4. Polish the whole path — Flow and hierarchy
- [ ] Khớp mental model, terminology, disclosure, routing, save behavior, optimistic/pessimistic pattern với khu vực lân cận
- [ ] Làm rõ primary task và current state mà không làm phẳng mọi phần tử về cùng một trọng số
- [ ] Đảm bảo arrival, transition, empty, recovery path nối liền nhau thay vì là màn hình cô lập

(nguồn: polish.md § 4. Polish the whole path > Flow and hierarchy)

### 4. Polish the whole path — Layout and type
- [ ] Căn theo grid và spacing scale của project; sửa cả optical lẫn mathematical alignment
- [ ] Nhóm nội dung liên quan sát nhau, tách nhóm khác biệt xa nhau
- [ ] Giữ nhất quán typography cùng vai trò; test measure, wrapping, localization expansion, zoom, font loading
- [ ] Kiểm tra mọi viewport được hỗ trợ, không chỉ sửa đúng ảnh chụp hiện tại

(nguồn: polish.md § 4. Polish the whole path > Layout and type)

### 4. Polish the whole path — Color, imagery, and icons
- [ ] Dùng semantic token, ý nghĩa màu ổn định xuyên theme
- [ ] Kiểm tra contrast của text, control, focus ở mọi state
- [ ] Giữ icon family, stroke/weight, sizing, optical alignment nhất quán
- [ ] Chặn layout shift do image; dùng đúng aspect ratio, responsive source, alt text hữu ích

(nguồn: polish.md § 4. Polish the whole path > Color, imagery, and icons)

### 4. Polish the whole path — Interaction and state
- [ ] Mỗi control cần đủ default, hover, focus, active, disabled, loading, error, success behavior
- [ ] Giữ visible keyboard focus, tab order hợp lý, label, touch target đúng chuẩn platform
- [ ] Giữ motion coherent, interruptible, performant; không thêm animation chỉ để show polish
- [ ] Kiểm tra nội dung dài, thiếu, đã dịch, offline, chậm, giới hạn quyền ở nơi sản phẩm có thể gặp

(nguồn: polish.md § 4. Polish the whole path > Interaction and state)

### 4. Polish the whole path — Content and code
- [ ] Giữ nhất quán terminology, viết hoa, dấu câu, nội dung factual; hỏi trước khi đổi claim
- [ ] Xóa debug output, dead code, unused import, style lỗi thời, và duplication do chính polish tạo ra
- [ ] Thay implementation tự chế bằng shared component/pattern nơi hệ thống đã sở hữu pattern đó
- [ ] Nâng giá trị thật sự tái dùng được thành token; không tạo abstraction hệ thống cho một ngoại lệ cục bộ

(nguồn: polish.md § 4. Polish the whole path > Content and code)

### 5. Verify and finish
- [ ] Đi lại toàn bộ path bằng chuột, bàn phím, và touch (nếu áp dụng)
- [ ] Kiểm layout mobile, intermediate, wide trên web; size class phone/tablet ở cả hai orientation trên native
- [ ] Kiểm state loading, empty, error, success, disabled, long-content, missing-content
- [ ] Kiểm zoom, contrast, focus, semantics, tên đọc bởi screen reader
- [ ] Kiểm console error, layout shift, độ trễ tương tác, image loading ở mọi nơi; browser hỗ trợ trên web; OS version, runtime warning, dropped frame trên native
- [ ] Kiểm khớp với DESIGN.md, feature lân cận, và scope của user
- [ ] Theo quality guidance từ `impeccable context` và hook; chạy các QA command liên quan khác
- [ ] Kết thúc bằng source diff: xóa churn ngẫu nhiên, code mồ côi, giá trị dư thừa, artifact tạm
- [ ] Chỉ ship khi feature functionally complete và nhất quán trên toàn path
- [ ] Chỉ đóng critique snapshot khi pass này đã dọn hết Priority Issue lấy từ snapshot đó

(nguồn: polish.md § 5. Verify and finish)

## Cách dùng trong /prd-grade-fe

1. Chấm mục A (Audit) ra thang điểm /20 theo 5 trục ở trên.
2. P0 phải = 0 thì mới được giao (deliver); còn P0 mở là chặn giao.
3. Mục B (Harden) và C (Polish) là pass sửa sau, chạy sau khi fe-gate rc = 0.
4. Ghi điểm A (?/20) cùng số lượng issue theo P0-P3 vào report.
