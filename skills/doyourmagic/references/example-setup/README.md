# example-setup — một lượt chạy thật của /doyourmagic trên rheinmir/setup (overstack)

Bundle gốc nằm ở dự án tiêu thụ: `.overstack/doyourmagic/setup/` với `skills/<tên>/SKILL.md`. Trong reference này các file skill được lưu dạng `skills/<tên>.skill.md` để loader (`skills/*/SKILL.md`, `npx skills`) không quét nhầm chúng thành skill của repo.

Đọc theo thứ tự: `workflows.md` (chỉ mục + bảng "kiểm chứng thế nào" 30+ dòng) → `flow.html` (docs-site-macos: sidebar, mind map, sơ đồ luồng skill→sản phẩm→skill kế, nút gạt sáng/tối) → `skills/dym-setup.skill.md` (hub, 1 dòng context) → 6 sub-skill.

Cách sinh: 2 lần cài thật vào sandbox `HOME` cô lập + đối chiếu 1 bản cài thật trên máy → 5 lỗi thật tìm ra (vá ở PR #114–#117). Test phiên mới: `/dym-setup` không đọc file nào; `/dym-setup guardrail-cli` đọc đúng 1 file con và 4/4 lệnh cho rc như tài liệu ghi. `flow.html` mở thật bằng Playwright: 6 cạnh luồng, mind map, toggle lưu localStorage, mobile nav, 0 lỗi console.
