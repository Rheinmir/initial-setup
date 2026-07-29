# Bộ specs chuẩn — khung tham chiếu cho MỌI project (S1–S10)

> Đây là KHUNG (template) mà bước Interview đối chiếu tài liệu thô của user để biết
> "đã có gì / còn thiếu gì / mâu thuẫn ở đâu". Mỗi field có `id` cố định (vd `S4.2`)
> để câu hỏi hỏi-bù và điều khoản BR về sau truy ngược được. KHÔNG sửa id đã phát hành
> (chỉ thêm mới) — id là khoá travel xuyên vòng đời.
>
> `schema_version: 0`

Mỗi field khi được điền mang 4 thuộc tính: `required` (bắt buộc hay không), `status`
(`filled` | `missing` | `conflict` | `assumed`), `value` (nội dung), `provenance`
(`raw:<file>` | `user` | `lens:<tên>`). Interview CHỈ sinh câu hỏi cho field
`missing` hoặc `conflict` — không hỏi lại field đã `filled`.

---

## S1 · Tầm nhìn & bài toán (required)
- `S1.1` (required) Sản phẩm giải bài toán gì — một câu.
- `S1.2` (required) Đau hiện tại / vì sao cần — bằng chứng, không cảm tính.
- `S1.3` (required) "Thành công" trông thế nào — mô tả kiểm-chứng-được.
- `S1.4` (optional) Đối tượng KHÔNG phục vụ / phi-mục-tiêu ở tầm nhìn.

## S2 · Người dùng & vai trò (required)
- `S2.1` (required) Các nhóm người dùng chính.
- `S2.2` (required) Vai trò & quyền của mỗi nhóm.
- `S2.3` (optional) Quy mô (số người dùng, đồng thời).

## S3 · Luồng nghiệp vụ chính (required)
- `S3.1` (required) Danh sách flow đầu-cuối quan trọng nhất (đặt tên).
- `S3.2` (required) Với mỗi flow: bước khởi đầu → bước kết thúc → điều kiện thành công.
- `S3.3` (optional) Luồng ngoại lệ / lỗi cần xử lý.

## S4 · Chức năng (required)
- `S4.1` (required) Danh sách feature (đặt tên, 1 dòng mỗi feature).
- `S4.2` (required) Với MỖI feature: acceptance-criteria kiểm-chứng-được (điều kiện nghiệm thu).
- `S4.3` (optional) Ưu tiên feature (must / should / could).

## S5 · Dữ liệu (required)
- `S5.1` (required) Các entity nghiệp vụ (đặt tên).
- `S5.2` (required) Field chính của mỗi entity.
- `S5.3` (optional) Quan hệ giữa entity (1-n, n-n).
- `S5.4` (optional) Ràng buộc dữ liệu (unique, bắt buộc, định dạng).

## S6 · Tích hợp ngoài (optional)
- `S6.1` (optional) API / hệ thống bên thứ ba phải nối.
- `S6.2` (optional) Hệ thống nội bộ có sẵn phải tương thích.
- `S6.3` (optional) Định dạng trao đổi (REST/GraphQL/file/queue).

## S7 · Non-functional (required)
- `S7.1` (required) Yêu cầu hiệu năng (thời gian phản hồi, thông lượng).
- `S7.2` (required) Bảo mật & phân quyền (ai thấy/sửa được gì).
- `S7.3` (optional) Khối lượng dữ liệu / tải đỉnh.
- `S7.4` (optional) Khả dụng / sao lưu / phục hồi.
- `S7.5` (required) Giao diện & design system — sản phẩm có UI thì BẮT BUỘC theo `skills/br/assets/design-template.md` (khung Google design-doc + design system kế thừa `/high-end-visual-design`): chọn Vibe/Layout archetype, dark/light toggle + localStorage + chống FOUC. BR chốt một clause NFR trỏ tới `br/DESIGN.md`; KHÔNG chép luật vào BR.

## S8 · Ràng buộc (required)
- `S8.1` (required) Công nghệ bắt buộc / cấm (stack, hạ tầng).
- `S8.2` (optional) Deadline / mốc thời gian.
- `S8.3` (optional) Ngân sách / nguồn lực.

## S9 · Out-of-scope (required)
- `S9.1` (required) Những thứ DỨT KHOÁT không làm (chống phình).
- `S9.2` (optional) Hoãn sang giai đoạn sau.

## S10 · Acceptance tests tổng (required)
- `S10.1` (required) Tập kịch bản nghiệm thu toàn hệ, mỗi kịch bản **kiểm-chứng-được bằng máy**
  (điều kiện tiên quyết để bước Slice cắt được frame — frame chỉ "xong" khi test của nó xanh).
- `S10.2` (optional) Dữ liệu mẫu / môi trường để chạy nghiệm thu.
