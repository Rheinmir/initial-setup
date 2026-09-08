# 04 — Xem tận mắt kho template

**Vì sao dùng:** biết trong kho có gì thì hỏi agent trúng hơn nhiều, và bạn tự đối chiếu được sản phẩm nhận về có đúng "cùng một nhà" với template không (checklist §8 câu 14).
**Sinh ra cái gì:** không sinh gì. Chỉ đọc.

Chạy từ thư mục skill đã cài (`~/.claude/skills/lieflat-charts`) hoặc bản clone bất kỳ.

## Mở gallery

```bash
cd ~/.claude/skills/lieflat-charts

open templates/lupi-gallery.html     # 19 hình Lupi Editorial (L1–L20, không có L18)
open templates/basics-gallery.html   # 17 hình Basics (F1–F17)
open templates/glance-gallery.html   # 20 hình Glance (G3–G22)
open templates/maps-gallery.html     # 2 bản đồ (M1, M2) — cần mạng, GeoJSON online
open templates/reports/index.html    # chỉ mục 12 bộ báo cáo, bấm vào là mở bản zh/en
```

Ba hình lớn tương tác, mỗi hình một file nguyên trang:

```bash
open templates/big-circular.html   # B1 · mạng 60 node, dây cung
open templates/big-force.html      # B2 · mạng 180 node, force-directed
open templates/big-threads.html    # B3 · 100+ đường 3 chặng, hover/pin
```

Linux đổi `open` → `xdg-open`.

> Gallery dùng IntersectionObserver render lười — phải **cuộn tới** thì hình mới vẽ. Trang trắng ở giữa không phải hỏng.

## Bản đổi màu (chỉ để tra màu, không tra cấu trúc)

```bash
ls templates/color/
# basics|glance|lupi|maps × palm|porcelain|wire = 12 file
```

`templates/color/README.md` nói thẳng: **chính bản của code render/hình học/animation luôn là 4 gallery ở thư mục gốc.** Bản màu chỉ là bản thay da. Chép cấu trúc từ đây là đi đường vòng và dễ lệch.

Ba preset:

| Hậu tố | Hệ | Logic màu | Hợp với |
|---|---|---|---|
| `*-porcelain.html` | xanh men sứ | một tông, thang độ sáng | dữ liệu có thứ tự, một chuỗi |
| `*-palm.html` | xanh lá dừa | tông màu = category | category không thứ tự ≤4 (5–6 gượng) |
| `*-wire.html` | đỏ toà soạn | thang xám + một cam huỳnh quang | hầu hết, khi cần đúng một điểm rơi mắt |

Ba hình lớn **không có bản wire** (wire vốn đã là xám + một điểm nhấn, làm ra gần trùng bản Mono gốc).

## Đọc bản thành phẩm thật (quan trọng hơn gallery)

```bash
open examples/lenny-2026-survey.html                  # 1 bài báo → 8 hình, 8 template khác nhau
open examples/reports/r04-financial-report.zh.html    # R04 chuyển sang bối cảnh tài chính
cat examples/README.md
```

`examples/README.md` là chỗ đáng đọc nhất repo: nó ghi lại các bài học đã trả giá — làm tròn còn 98% thì ghi chú thẳng "rounding ate the other two" chứ không bịa cho đủ 100; dữ liệu không có thì để trống chứ không chế; nhãn category dựng đứng bị chê hai vòng, đổi sang nhãn nằm ngang mới xong.

## Tra code của một hình cụ thể

Quy trình 3 bước (`catalog.md` dòng mở đầu):

1. `catalog.md` → tìm mã hình (vd `L13`) → lấy cột "卡内标题" (tiêu đề trong thẻ, vd `The funnel, poured`).
2. Mở gallery tương ứng, tìm `<div class="card">` có tiêu đề đó.
3. Trong `<script>`, tìm khối chú thích cùng tên dạng `// ════ Hourglass Stream ════` để lấy code render.

```bash
grep -n 'The funnel, poured' templates/lupi-gallery.html
```

**Đừng bê nguyên cả trang gallery.** Gallery là trang gộp nhiều thẻ; giao phẩm luôn là file đơn dựng theo khung ở `SKILL.md` §9.
