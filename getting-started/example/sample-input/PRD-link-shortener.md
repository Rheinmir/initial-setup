# PRD — Link Shortener (ví dụ để manual test dây chuyền /br)

> File THÔ mẫu. Ở bước `/br interview` bạn copy file này (hoặc tài liệu thật của bạn)
> vào `llmwiki/raw/` của project. Cố tình để VÀI CHỖ MƠ HỒ để thấy interview hỏi-bù.

## Mục tiêu
Dịch vụ rút gọn URL: người dùng dán một URL dài → nhận một mã ngắn; ai mở
`/<mã>` thì được chuyển hướng tới URL gốc. Có đếm số lượt click.

## Chức năng
1. **Tạo link:** nhập URL dài → sinh mã ngắn 6 ký tự (chữ+số) → trả về link ngắn.
2. **Chuyển hướng:** mở `/<mã>` → 302 tới URL gốc; mã không tồn tại → 404.
3. **Đếm click:** mỗi lần chuyển hướng tăng bộ đếm của mã đó.
4. **Danh sách:** trang liệt kê các link đã tạo + số click.

## Ràng buộc
- URL phải hợp lệ (http/https) — sai thì từ chối.
- Mã phải duy nhất.

## Chỗ chưa rõ (cố ý — để interview hỏi-bù, hoặc dùng /unknown ghi lại)
- Lưu ở đâu? (chưa quyết DB hay file)
- Mã có cho người dùng tự đặt (custom alias) không?
- Link có hạn dùng / hết hạn không?
- Có cần đăng nhập để tạo link không?
