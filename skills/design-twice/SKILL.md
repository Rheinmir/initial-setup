---
name: design-twice
description: >-
  Thiết kế MỘT thứ (interface, module, hoặc MÀN HÌNH/UI) bằng 2-3 phương án RADICALLY KHÁC NHAU
  chạy song song, rồi so sánh và tổng hợp — thay vì bổ thẳng vào ý tưởng đầu tiên. Gốc: "Design It
  Twice" (A Philosophy of Software Design) — ý đầu tiên hiếm khi là ý tốt nhất. Dùng TRƯỚC khi code
  một frame có UI, một API mới, hay khi đang bí/đi vòng. Trigger: "design it twice", "thiết kế 2 lần",
  "phác vài phương án", "so sánh thiết kế", "thiết kế interface", "UI nên trông thế nào", "/design-twice".
---

# Skill: design-twice — thiết kế 2 lần, chọn 1 (rồi ghép cái hay của cái còn lại)

> **Vì sao tồn tại:** ý tưởng đầu tiên là ý *dễ nghĩ nhất*, không phải ý *tốt nhất*. Agent (và người)
> mặc định bổ thẳng vào phương án đầu rồi vá dần — mỗi lần vá kéo theo một lỗi mới. Phác thêm 2
> phương án rẻ hơn nhiều so với sửa sai kiến trúc/UI sau khi đã code.
>
> **Bài học 14/07/26:** theme Lume vá **5 vòng** (accent chìm → accent lạc quẻ → hào quang bựa →
> mảng đen ở dark → paper vỡ) vì chưa bao giờ có 2 phương án để so — chỉ có MỘT phương án bị vá liên tục.

## When to use
- **BẮT BUỘC** trước khi code frame có `ui_role ≠ none` (xem skill `br` § Vòng thiết kế).
- Thiết kế API/module mới; hoặc đang vá lần thứ 2 cho cùng một chỗ (dấu hiệu **hình dạng sai**).
- User nói "xấu", "bựa", "không ưng" mà không chỉ được lỗi cụ thể → **đừng vá**, phác lại 3 hướng.

## Steps

### 1. Chốt yêu cầu (đừng thiết kế trong sương mù)
- Module/màn này giải bài toán gì? Ai gọi / ai dùng (module khác, user cuối, test)?
- Thao tác chính là gì? Ràng buộc gì (hiệu năng, tương thích, design system sẵn có)?
- Cái gì phải GIẤU bên trong, cái gì mới được lộ ra?

### 2. Sinh 2-3 phương án SONG SONG — ép chúng KHÁC NHAU TẬN GỐC
Spawn sub-agent song song (Agent tool), **mỗi agent một ràng buộc khác nhau** để chúng không hội tụ:

| | ràng buộc (code/API) | ràng buộc (UI/màn hình) |
|---|---|---|
| A | **Ít method nhất** (1–3), giấu tối đa | **Ít phần tử nhất** — bỏ được gì thì bỏ, còn lại là cốt lõi |
| B | **Linh hoạt nhất** — phủ nhiều use-case | **Dày thông tin** — cho thấy nhiều nhất trong 1 màn |
| C | **Tối ưu ca phổ biến nhất** | **Tối ưu thao tác lặp nhiều nhất** (đường tay ngắn nhất) |
| D | Cảm hứng từ **một paradigm/thư viện cụ thể** | Cảm hứng từ **một app tham chiếu cụ thể** |

Mỗi agent trả đúng 4 mục: ① chữ ký interface (hoặc wireframe + token/spacing/hierarchy)
② ví dụ dùng thật ③ nó GIẤU cái gì ④ đánh đổi.

### 3. Trình bày TUẦN TỰ — đọc xong cái này mới sang cái kế
Không trộn lẫn. **UI thì phải có HÌNH** (wireframe/ảnh) — tả suông là chưa thiết kế.

### 4. So sánh (văn xuôi, không bảng)
- **Đơn giản của interface**: ít method, tham số dễ hiểu.
- **Tổng quát vs chuyên biệt**: coi chừng tổng-quát-hoá quá đà.
- **ĐỘ SÂU**: interface nhỏ giấu nhiều phức tạp = **module sâu (tốt)**; interface to ruột mỏng = **nông (tránh)**.
- **Dễ dùng đúng** vs **dễ dùng sai**.
- Nêu rõ chỗ các phương án **phân kỳ mạnh nhất** — đó mới là quyết định thật.

### 5. Tổng hợp
Bản tốt nhất thường = bản thắng **+ ghép vài ý hay của bản thua**. Hỏi user: phương án nào hợp ca
dùng chính? Có ý nào của bản khác đáng bê sang?

### 6. Chốt vào FRAME (khi dùng trong dây chuyền `/br`)
Ghi vào frame mục `## Thiết kế (design-twice)`: 3 phương án tóm tắt + **phương án chọn** + **lý do**
+ ý đã ghép. Đó là bằng chứng đã thiết kế 2 lần. Frame UI thiếu mục này = **chưa xong**.

## Rules
- **Ép KHÁC NHAU TẬN GỐC.** 3 phương án na ná nhau = phí token; không có contrast thì không có giá trị.
- **Không code ở đây.** Chỉ HÌNH DẠNG. Chưa chọn xong thì chưa được viết implementation.
- **Không chấm theo "phương án nào dễ làm nhất"** — dễ làm ≠ đúng.
- **Vá lần thứ 2 cho cùng một chỗ = HÌNH DẠNG SAI** → dừng vá, chạy skill này.
- **Chốt xong phải ghi vào frame** — quyết định không ghi = quyết định sẽ thất lạc, rồi vá lại từ đầu.
- Thiết kế UI phải tuân design-system của dự án (`skills/br/assets/design-template.md`) — phương án
  khác nhau về **hình dạng/bố cục**, không phải khác nhau về **bảng màu tuỳ hứng**.
