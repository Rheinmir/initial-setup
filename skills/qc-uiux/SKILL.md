---
name: qc-uiux
description: >-
  Audit UI/UX phong cách SENIOR — bốn mục accessibility · visual-hierarchy · consistency · antipattern,
  mỗi mục cho ĐIỂM/10 + LỖI NẶNG NHẤT + CÁCH SỬA, rồi một kết luận PASS-sang-bước-kế hay CẦN-SỬA.
  Phần ĐO ĐƯỢC (contrast WCAG, tap-target, overlap/misalign hình học, missing-label) chạy tất định
  qua engine visual-qa (headless, 0-token, KHÔNG LLM); phần cần MẮT (hierarchy, drift design-system,
  dark-pattern) là LLM audit. Gọi khi user nói "qc uiux", "audit ui", "soi giao diện", "dẹp antipattern
  ui", "/qc-uiux", hoặc SAU khi có mockup/UI. NHÂN KHUÔN /qc-code (đắt=LLM tay, rẻ=test tất định auto).
  KHÁC /redesign (đổi mới thẩm mỹ) và /visual-qa (chụp+gác pixel) — qc-uiux là verdict senior 4-mục.
---

# Skill: qc-uiux

## When to use
- Vừa dựng/đổi UI (mockup `/br`, trang mới, component) và muốn một cặp mắt senior soi trước khi chốt.
- Trước commit thay đổi UI đáng kể — cắm tùy chọn vào `/orca-workflow` trước `verify-before-commit`, và tự-động sau mỗi `/br run` frame có UI.
- KHÔNG dùng cho: đổi mới thẩm mỹ tổng thể (đó là `/redesign-existing-projects`), hay chỉ chụp+so pixel (đó là `/visual-qa` — qc-uiux GỌI nó làm engine đo).

## Phạm vi audit (mặc định = mockup/route hiện có)
Mặc định soi **UI đang có** — các route/trang mockup vừa dựng. User chỉ định route/màn thì soi cái đó. Đọc DOM + đo rect thật (getBoundingClientRect) qua engine; KHÔNG đoán từ CSS tĩnh (đọc CSS MÙ lỗi render — bài học 15/07/26).

## Steps
1. **Xác định phạm vi** — route/màn nào. Chạy engine tất định trước để có DỮ KIỆN đo được (mục "Engine" dưới).
2. **Chấm bốn mục** (mục dưới). Mỗi mục: **điểm/10 · lỗi nặng nhất · cách sửa**. → Xong khi cả bốn mục đủ ba phần.
3. **Mục có lỗi ĐO ĐƯỢC: gắn dữ kiện engine** (contrast fail ở đâu, control nào <24px, cặp nào overlap…) — số đo là dữ kiện, verdict là ý kiến.
4. **Kết luận** — `PASS` (sang bước kế) hay `CẦN SỬA` (liệt kê phải sửa gì). → Xong khi verdict rõ + danh sách phải-sửa nếu CẦN SỬA.
5. **Chạy lại engine sau khi sửa** để chứng minh lỗi đo-được đã hết (đỏ→xanh), giống test tái hiện của qc-code.

## Bốn mục

### 1. Accessibility (a11y) — điểm/10 · lỗi nặng nhất · cách sửa
Soi (phần lớn ĐO ĐƯỢC — engine bắt): **contrast** (chữ thường ≥4.5:1, chữ lớn ≥3:1, control/viền/icon ≥3:1 — WCAG 2.2 AA) · **tap-target** (control tương tác ≥24×24px CSS là sàn AA 2.5.8; khuyến 44/48px mobile) · **focus-visible** (có vòng focus rõ, tương phản ≥3:1) · **missing-label** (nút/icon/link screen-reader đọc rỗng — thiếu aria-label/text). Đây là ranh giới tiếp cận — không lười (a11y là LUẬT, không phải gu). Lưu ý: chỉ ~30% tiêu chí WCAG tự-động được → phần còn lại (keyboard trap, thứ tự focus, alt có NGHĨA) là mắt người.

### 2. Visual hierarchy — điểm/10 · lỗi nặng nhất · cách sửa
Soi (mắt LLM): **nút trông như nút, link trông như link, heading phân cấp kích cỡ rõ** (bắt user phải "giải mã" giao diện = fail) · **CTA rõ ràng** (hành động chính nổi bật, không mơ hồ) · **content density** (không nhồi quá nhiều lên một màn — quá tải = mất hierarchy). Chỉ ra đâu là điểm mắt dừng ĐẦU TIÊN và nó có đúng là hành động chính không.

### 3. Consistency (design-system) — điểm/10 · lỗi nặng nhất · bảng drift
Soi (mắt LLM, vài phần đo được): **spacing theo token** (thang 4/8px — gap lộn xộn = mất nhịp) · **màu nhất quán** (không bảng màu chỏi/lẫn) · **shadow** (không lạm dụng/sai độ sâu — engine bắt `shadow-clipped`/`monochrome-surface`) · **typography** (cặp font/size nhất quán) · **đồng nhất xuyên trang** (cùng thứ gọi cùng kiểu ở mọi màn). **Trả bảng drift:**

| Chỗ | Lệch chuẩn | Sửa về |
|-----|-----------|--------|
| card padding | 14px / 20px / 17px lẫn lộn | token `--sp-4` (16px) |

### 4. Antipattern & interaction — điểm/10 · lỗi nặng nhất · bằng chứng đo
Soi: **dark-mode readability** (chữ washed-out quá nhạt/quá tối — lỗi dark-mode kinh điển, engine bắt qua contrast-aa ở theme tối) · **hình học vỡ** (overlap ≥4px, row-misalign — control chồng/không cao bằng nhau, engine ĐO rect) · **feedback thiếu** (hành động không có phản hồi hệ thống) · **responsive vỡ** (tràn ngang, chồng ở khổ hẹp) · **dark-pattern** (ép buộc, gài lựa chọn, khó thoát). Mỗi lỗi đo-được → **dẫn số từ engine** (route nào, cặp nào, chồng bao nhiêu px).

## Kết luận (verdict)
Một trong hai, kèm lý do:
- **PASS** — không lỗi nặng ở mục nào; a11y đo-được sạch; sang bước kế được.
- **CẦN SỬA** — liệt kê **cụ thể** phải sửa gì (ưu tiên a11y đo-được + hình học vỡ trước hierarchy/consistency).

> **Verdict là ADVISORY — người quyết, không chặn commit.** Thứ gác cứng là engine tất định (contrast/tap-target/overlap/misalign đỏ→xanh). Đừng để user tưởng "qc-uiux PASS = UI hoàn hảo"; nó là cặp mắt senior, không phải bằng chứng.

## Engine tất định (0-token, KHÔNG LLM) — reuse visual-qa
Phần ĐO ĐƯỢC dùng chung engine của `/visual-qa` (`skills/visual-qa/assets/route-shots.mjs`, headless playwright), hàm `DESIGN_AUDIT` đo rect thật trong trang và bắt các rule: `contrast-aa` · `tap-target` · `missing-label` · `overlap` · `row-misalign` · `shadow-clipped` · `monochrome-surface` · `rogue-slab`. Chạy:

```bash
node skills/visual-qa/assets/route-shots.mjs <base-url> --audit    # in issues theo route; exit ≠0 nếu a11y/hình học fail
```

Đây là phần "tự động hook khi UI đổi" — **chỉ hook phần rẻ tất định**, LLM audit (skill này, 4 mục) giữ gọi tay. Fail-open nếu chưa dựng được server/headless (không chặn). Giống `qc-regression.py --run` của qc-code: `verify-before-commit` bước 3b gọi nó; UI đổi → antipattern đo-được không âm thầm quay lại.

## Rules
- **Tách đắt/rẻ:** LLM audit (4 mục) = gọi tay / bước workflow tùy chọn. Đo tất định = auto qua engine visual-qa. KHÔNG gọi LLM trong hook (nguyên tắc hook-0-token).
- **Verdict advisory, engine đo gác cứng** — không để LLM verdict chặn commit; số đo (contrast/tap-target/geometry) mới là dữ kiện.
- **Đọc CSS là MÙ hình học** — mọi nhận định layout/kích cỡ/contrast phải ĐO rect thật qua engine, không suy từ CSS tĩnh.
- **Không dẫm:** `/redesign-existing-projects` = đổi mới thẩm mỹ · `/visual-qa` = chụp+gác pixel-diff · `/qc-code` = review CODE. `/qc-uiux` = verdict senior 4-mục UI/UX + reuse engine đo.
- **a11y là luật, không phải gu** — carve-out CLAUDE.md: không lười ở contrast/tap-target/label. Chỉ ~30% WCAG tự-động → phần còn lại ghi rõ "cần mắt người / nợ `[[150726-unknown-ledger]]`".

## Related
- `skills/visual-qa/assets/route-shots.mjs` — engine đo tất định (DESIGN_AUDIT) mà skill này reuse.
- `llmwiki/skills/dev-loop/qc-code.md` — skill anh em: cùng khuôn đắt-LLM / rẻ-tất-định, cho CODE.
- `harness/scripts/qc-regression.py` — runner test qc-* tất định (qc-code) chạy ở verify-before-commit.
- `llmwiki/skills/dev-loop/build-now-adapt-later.md` — quA khuôn tách quarantine đắt/rẻ.

## Output Report
Sau khi audit xong, ghi draft `llmwiki/wiki/sources/draft/DDMMYY-qc-uiux-<route>.md` (OKF frontmatter `type: draft`, `## Origin`) tóm: route đã soi · điểm 4 mục · lỗi đo-được từ engine · verdict + phải-sửa. Thêm dòng vào `index.md` + `log.md`. Bỏ qua nếu chỉ chạy engine đo (không có phán đoán mới).
