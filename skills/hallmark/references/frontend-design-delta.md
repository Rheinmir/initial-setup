# frontend-design (anthropics/skills) — delta so với sàn hallmark

Đối chiếu từng luật của skill `frontend-design` (Anthropic, 55 dòng) với sàn 6 discipline + slop-test (57 cổng). Chỉ absorb phần sàn CHƯA có; phần trùng ghi rõ để khỏi absorb lại lần sau.

## Luật sàn CHƯA có (absorb làm checkpoint)

| Luật | Nội dung (distill) | Áp khi nào |
|---|---|---|
| Ba cụm default-AI-look có tên | AI design hiện tụ về 3 look mặc định: (1) nền kem ấm ~#F4F1EA + serif tương phản cao + accent đất nung; (2) nền gần-đen + một accent acid-green/đỏ son; (3) layout kiểu báo khổ rộng — hairline rule, border-radius 0, cột dày đặc. Cả ba hợp lệ KHI brief yêu cầu; brief bỏ ngỏ trục nào thì KHÔNG tiêu trục đó vào một trong ba look này. | Mọi UI mới khi brief không ép hướng thẩm mỹ. Cộng hưởng với cổng Variety (trang mới phải khác cấu trúc trang trước). |
| Hero là THESIS | Mở trang bằng thứ đặc trưng nhất của thế giới chủ đề (headline/ảnh/demo/khoảnh khắc tương tác) — "con số to + nhãn nhỏ + gradient accent" là đáp án template, chỉ dùng khi thật sự tốt nhất. | Trang có hero/section mở đầu. |
| Signature element — tiêu boldness đúng MỘT chỗ | Mỗi trang có đúng một yếu tố để được nhớ; mọi thứ quanh nó giữ kỷ luật im lặng. Trước khi giao: soi gương bỏ bớt một "phụ kiện" (Chanel). Không dám mạo hiểm cũng là một loại rủi ro. | Bước plan (chọn signature trước khi code) + bước tự-soi trước khi trả kết quả. |
| UX-writing theo hành động | Nút nói đúng việc xảy ra ("Save changes", không "Submit"); một hành động giữ nguyên tên xuyên flow (nút "Publish" → toast "Published"); error chỉ đường sửa, không xin lỗi, không mơ hồ; empty-state là lời mời hành động; đặt tên theo thứ NGƯỜI DÙNG kiểm soát ("notifications"), không theo cách hệ thống build ("webhook config"). | Mọi UI có chữ — form, nút, error, empty state. |

## Luật trùng sàn (không absorb — đã có)

| Luật nguồn | Đã có ở |
|---|---|
| Token system đặt tên (palette 4-6 hex có tên, type theo role) | Discipline "Locked tokens" (mọi màu/font qua biến có tên) |
| Two-pass: plan → review-vs-brief → mới code | Discipline "Pre-emit self-critique" (6 trục, trục <3 phải revise trước) |
| CSS selector specificity cancel nhau | slop-test có cổng selector/specificity |
| Numbered markers chỉ khi nội dung THẬT là sequence | Nhóm cổng "structure is information" (eyebrow/numbered markers) |
| Quality floor: responsive mobile, focus visible, reduced motion | Discipline "Mobile bốn width" + a11y carve-out CLAUDE.md |
| Copy không bịa, cụ thể hơn là khéo | Discipline "Honest copy" (không bịa số liệu) |

## Origin
- **Source:** `anthropics/skills` skill `frontend-design` (clone depth-1 → `scratchpad/anthropic-skills/`, 2026-07-17; unknown U-01 resolved CÓ).
- **adapt_mode:** dissolve — đối chiếu từng luật với sàn [[design-foundation]], chỉ absorb 4 cụm thiếu; 6 cụm trùng ghi rõ vị trí đã có.
- **Task:** `T-260717-02` (SPEC `170726-absorb-six-sources`).
