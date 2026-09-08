---
name: dym-lieflat-charts-chart-request
description: "Xin biểu đồ (chế độ mặc định). đây là đường chính. Đưa dữ liệu + bối cảnh, nhận về HTML mở bằng double-click."
disable-model-invocation: true
---

# Skill: dym-lieflat-charts-chart-request — Xin biểu đồ (chế độ mặc định)

> **Toàn bộ file này là câu chat gửi cho agent, KHÔNG phải lệnh terminal.** Đừng dán vào shell.

**Vì sao dùng:** đây là đường chính. Đưa dữ liệu + bối cảnh, nhận về HTML mở bằng double-click.
**Sinh ra cái gì:** một hoặc vài file `.html` đơn (inline token, không cần build).

## Mẫu tối thiểu

```text
Dùng lieflat-charts. Đây là dữ liệu:

<dán CSV/bảng/số liệu>

Bối cảnh: <đăng bài blog / slide họp / báo cáo nội bộ>.
Ngôn ngữ: <tiếng Việt / English>.
```

Không cần nói tên kiểu biểu đồ. `SKILL.md` §1 bắt agent nhìn *hình dạng dữ liệu* trước, rồi mới chọn template.

## Số lượng biểu đồ agent sẽ trả (SKILL.md §1.2)

| Bạn đưa gì | Mặc định ra mấy hình |
|---|---:|
| Một câu hỏi / một chỉ số | 1 |
| Hai–ba kết luận rõ rệt | 2–3 |
| Cả một bài viết / paper / case study | 4–6 |
| Bạn chỉ định số | theo bạn (nhưng vẫn cắt hình trùng kết luận) |

Trần mặc định **6 hình một trang**; quá thì tách trang. Số hình do *số kết luận độc lập* quyết định, không do số cột dữ liệu.

## Lái agent khi cần

Thứ tự chọn cứng trong skill: **Lupi Editorial (L1–L15) → Lupi Basics (F1–F13) → mới tới Glance**. Muốn khác thì phải nói rõ:

```text
Đây là số liệu tuần, tôi cần đọc hiểu trong 10 giây — dùng Glance / dashboard.
```

```text
Vẽ bản đồ phân bố theo quốc gia.
```
↑ **Bắt buộc gọi đích danh "bản đồ".** Có cột quốc gia không tự bật M1/M2 (`SKILL.md` §7).

```text
Dùng preset porcelain, độ đậm nhạt thể hiện giá trị, giữ nguyên cấu trúc hình.
```

```text
Màu thương hiệu của tôi là #0B5FFF. Dựng custom palette theo luật role của skill.
```

```text
Tôi cần file chạy offline hoàn toàn — inline hết dependency, đừng nạp font/CDN.
```

## Ba câu trả lời "không" bạn sẽ gặp (và đó là đúng)

`SKILL.md` §7 cho phép agent từ chối, kèm phương án thay:

- Cột bị **cắt trục** (broken axis) → từ chối, đề xuất 3 cách trung thực.
- **Glow / glassmorphism / 3D** → từ chối, giữ nguyên ngữ pháp thị giác.
- **Trên 6 category mà vẫn đòi màu** → lùi về Mono thang xám.
- Dữ liệu quá mỏng cho kiểu hình đã chọn (3 node mà đòi force graph) → hạ cấp và giải thích.

Đây là tính năng, không phải agent bướng.

## Đòi agent trưng bằng chứng chọn hình

Checklist §8 của skill yêu cầu ghi lại tối thiểu 3 ứng viên và lý do loại. Bắt nó nộp:

```text
Trước khi vẽ, liệt kê 3 template ứng viên (mã hình + file gallery + tiêu đề thẻ),
nói rõ loại cái nào vì sao, rồi mới sinh HTML.
```

Trả lời phải có dạng `L13 Hourglass Stream · templates/lupi-gallery.html · "The funnel, poured"`. Nếu agent chỉ nói "tôi dùng biểu đồ cột" — nó đang bịa, không đọc gallery.

## Nghiệm thu file nhận về

1. Mở bằng double-click, không cần server.
2. Refresh hai lần → hình y hệt (skill cấm `Math.random`, dùng `MONO.rnd` tất định).
3. Tiêu đề là **kết luận**, không phải tên kiểu biểu đồ.
4. Dòng phụ đề giải thích được chú giải mà không cần đọc code.
5. Cả file chỉ một hệ màu (Mono, hoặc *một* preset, hoặc *một* custom) — trộn là phải làm lại.
6. Muốn offline: mở khi tắt mạng, chữ và hình vẫn đúng.
