# intake — ba nguồn thông số đổ về MỘT `design.md`

Đầu ra của cả ba route là `design.md` ở gốc project theo format hallmark (`skills/hallmark/references/design-md.md`): mục System · Tokens (block ```css :root{}```) · CTA voice · Motion stance · Exports, cộng § Provenance. Block `:root` phải có tối thiểu `--color-paper`, `--color-ink`, `--color-accent`, `--font-display`, `--font-body`, `--font-mono` (REQUIRED của `scripts/design-sync.py`). Sau khi ghi, luôn chạy `python3 skills/prd-grade-fe/scripts/design-sync.py` rồi `--check` rc 0.

## Route A — preset macOS glass (mặc định)
1. `cp skills/prd-grade-fe/references/presets/macos-glass.design.md ./design.md`
2. Đổi dòng `# Design — <Project name>` theo tên project; giữ nguyên token (đã qua detect rc 0, bằng chứng ở `presets/macos-glass.evidence.md`).
3. `design-sync.py` → frontmatter + `tokens.css`.

## Route B — tài liệu thiết kế (file hoặc folder)
1. Liệt kê nguồn: `find <path> -maxdepth 2 -type f \( -name '*.md' -o -name '*.css' -o -name '*.scss' -o -name '*.json' -o -name '*.pdf' -o -name '*.png' -o -name '*.fig' \)`. PDF và ảnh đọc bằng Read; `.fig` không đọc được thì xin export PNG.
2. Điền bảng schema, mỗi hàng ghi `giá trị | nguồn file:dòng | độ tin (chắc/suy)`:
   paper · paper-2 · ink · ink-2 · rule · accent · accent-ink · focus · font-display · font-body · font-mono · radius-card · radius-pill · radius-input · ease/dur · giọng CTA · motion stance.
   Màu hex/rgb trong tài liệu chép nguyên (impeccable parse được), không tự đổi sang OKLCH.
3. Hàng trống → gom thành MỘT câu hỏi bù duy nhất, mỗi hàng kèm đề xuất mặc định lấy từ preset macOS glass để user chỉ cần trả lời "ok" hoặc sửa từng dòng. Không hỏi nối đuôi.
4. Ghi `design.md`; § Provenance liệt kê từng file nguồn đã dùng và hàng nào là "suy".
5. `design-sync.py` → frontmatter + `tokens.css`.

## Route C — URL trang đích
1. Gọi hallmark `study <URL>` (URL mode). Lớp từ chối của `skills/hallmark/references/study.md` chạy TRƯỚC WebFetch: refuse list (themeforest, framer/webflow templates, gumroad UI-kit, dribbble, behance) và Remote URL Safety (không nội bộ/local). SPA shell, auth-wall, non-2xx, body < 1 KB → xin screenshot (image mode). Không suy giảm lặng lẽ.
2. Sau diagnosis, nói "lock the DNA". Hỏi attestation đúng một lần: (a) trang của chính user · (b) tham chiếu công khai cho brand của user · (c) khác. (c) → không emit design.md, chỉ giữ diagnosis và đề nghị route A/B.
3. `design.md` emit có § Provenance (URL, ngày, câu trả lời attestation) và § Notes ghi rõ "rhythm: không đọc được từ HTML" cùng danh sách anti-pattern của trang nguồn KHÔNG mang theo.
4. `design-sync.py` như route B.

## Khi project đã có `design.md`
Pre-flight thấy file → không chạy route nào, báo "hệ đã khoá" và đi thẳng pha 3; hallmark tự đảo chiều diversification (mọi màn hình chung hệ). Chỉ mở lại intake khi user nói rõ muốn đổi theme; khi đó AMEND `## Variants` thay vì ghi đè (no-overwrite policy của design-md.md).
