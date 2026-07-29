---
# ── frame-template.md — TEMPLATE TẤT ĐỊNH cho mọi frame (/br slice bắt buộc dùng) ──
# frame-lint R1 gác frontmatter, R7 gác NỘI DUNG: muc_tieu phải mô tả nghiệp vụ
# thật (không được generic kiểu "F10 nghiệp vụ"), body phải đủ 4 section dưới.
schema_version: 0
frame_id: frame-NNN-<slug-nói-lên-nghiệp-vụ>   # vd: frame-010-ean13-checksum
created_by: slicer                              # human | slicer
parent_br: br/BR.md
clause_ids: [S?.?]                              # điều khoản BR mà frame này hiện thực
parent_br_hash: <sha256 của br/BR.md lúc slice>
muc_tieu: "<MỘT câu nghiệp vụ người-đọc-hiểu: hệ thống làm GÌ cho AI, vd: Kiểm mã vạch EAN-13 nhập tay — tính checksum digit 13, sai thì chặn lưu phiếu nhập kho>"
scope_code: ["app/<file>.py"]                   # ≤3 file frame ĐƯỢC sửa
scope_test: ["tests/test_<file>.py"]            # test bảo vệ — frame KHÔNG được sửa
acceptance_test: "python3 -m tests.test_<file>"
# depends_on — frame này KHÔNG chạy được cho tới khi các frame dưới đây xanh (dây chuyền
# là ĐỒ THỊ, không phải danh sách). Khai đúng thì: br-queue tự sắp thứ tự chạy · một frame
# đỏ tự CHẶN cả nhánh dưới nó (không đốt lượt model cho cái chắc chắn hỏng) · sửa một frame
# thì `br-queue.py affected <frame_id>` chỉ ra ĐÚNG nhánh phải chạy lại. Không phụ thuộc ai
# → để rỗng. Chu trình bị frame-lint R5 chặn.
depends_on: []                                  # vd: [frame-004-store-file-first]
# ── UI CONTRACT (điền nếu frame có mặt trên giao diện; frame logic thuần để mặc định) ──
ui_role: none            # none | screen | panel | widget | form | action
ui_screen:               # id màn hình frame này hiện (khớp br/ui-layout.yaml); trống nếu ui_role=none
guards:
  max_iter: 3
  budget_seconds: 60
  no_progress_k: 2
  escalate_after_iter: 3
run_log_ref: br/frames/frame-NNN-<slug>.run.json
---
# frame-NNN-<slug> — <tên nghiệp vụ ngắn>

## Nghiệp vụ
<3–6 câu cho NGƯỜI VỀ SAU đọc: bối cảnh nghiệp vụ, ai dùng, luồng xảy ra khi nào,
vì sao cần. Viết như giải thích cho đồng nghiệp mới — không chép lại frontmatter.>

## Input / Output
- **Input:** <dữ liệu vào — kiểu, nguồn, ví dụ cụ thể (vd: chuỗi 13 chữ số "8934588063050")>
- **Output:** <kết quả — kiểu, ý nghĩa từng giá trị (vd: True = checksum hợp lệ)>

## Spec (FR/SC)
<Học /orca-workflow: mỗi frame là MỘT spec rõ ràng, có id ổn định để truy vết frame→FR→clause.
- **FR (yêu cầu chức năng)** — id bền, mỗi dòng: `**FR-01**: Hệ thống PHẢI <hành vi cụ thể>`. Bao trọn muc_tieu, không mơ hồ.
- **SC (tiêu chí thành công, ĐO NGƯỜI không đo máy)** — `**SC-01**: <người dùng nhận được gì / ngưỡng đo được>`. Acceptance_test là BẰNG CHỨNG của SC, không thay thế SC.
Frame không có FR/SC rõ = chưa spec xong (như interview thiếu field). Mỗi FR phải về đúng ≥1 dòng "Tiêu chí nghiệm thu".>

## Tiêu chí nghiệm thu
<liệt kê hành vi acceptance_test kiểm — mỗi dòng một hành vi, gồm cả ca biên; mỗi dòng truy về một FR ở trên:
- <ca thường (FR-01): ...>
- <ca biên/lỗi (FR-02): chuỗi ngắn hơn 13 ký tự → ...>>

## Ngoài phạm vi
<những gì frame này CỐ TÌNH không làm (thuộc frame khác hoặc để sau) — chống scope creep.>

## Thiết kế (design-twice)
<CHỈ điền nếu ui_role≠none — và phải điền TRƯỚC KHI CODE. Chạy `/design-twice`:
- **PA-A / PA-B / PA-C:** mỗi phương án 1-2 dòng (khác nhau TẬN GỐC, kèm wireframe/ảnh — tả suông không tính).
- **CHỌN:** phương án nào + **VÌ SAO** (độ sâu, dễ dùng đúng, hợp ca dùng chính).
- **GHÉP:** ý hay bê từ phương án thua sang.
Không có mục này = chưa thiết kế = **frame chưa xong**. Đang vá lần 2 cho cùng một chỗ ⇒ quay lại đây.>

## UI hoạt động ra sao
<CHỈ điền nếu ui_role≠none — bỏ qua với frame logic thuần. Mô tả tương tác để CONTRACT chốt được:
- **Tương tác chính:** nhập gì / bấm gì → thấy gì.
- **Trạng thái:** rỗng / đang tải / lỗi / thành công (mỗi trạng thái hiển thị ra sao).
- **Cùng màn với:** những frame khác chia sẻ ui_screen này (nếu biết).
- **Token hệ (STREAM nhất quán — học hallmark):** frame này CHỈ dùng token khai trong `br/DESIGN.md`
  (`var(--color-…)`, `var(--font-…)`, thang spacing). **CẤM inline** hex/OKLCH/`font-family:"…"` — thiếu token
  thì thêm vào DESIGN.md rồi trỏ tên, KHÔNG tự chế tại frame. Luật ĐẢO NGƯỢC của design-system: các frame
  phải GIỐNG nhau (chia sẻ hệ), không mỗi frame một kiểu → mockup xuyên frame trông như MỘT sản phẩm.
  Drift token bị `/qc-uiux` (mục consistency) + visual-qa bắt.>

<!-- ══ VÒNG TỰ-KIỂM THỊ GIÁC — BẮT BUỘC với frame UI (ui_role≠none) ══
   Rút từ failure `ui-pass-without-full-visual-review` (13/07/26): frame theme từng khai
   ui_role:none + acceptance rỗng → UI vỡ mà frame vẫn "xanh". Không tái phạm:

   1) ui_role PHẢI đúng. Frame chạm theme/CSS/layout = UI, KHÔNG được khai `none`.
   2) acceptance_test PHẢI HIT UI (không phải unit-test cạnh bên):
        node skills/visual-qa/assets/route-shots.mjs --base http://localhost:<port> \
             --route <route của ui_screen> --assert --user <u> --pass <p> --out <dir>
      `--assert` FAIL khi: route không 200 · KHÔNG có ảnh bằng chứng · VI PHẠM BẤT BIẾN
      (monochrome-surface: pane lệch màu nền). → chạy lại frame = tự re-verify UI.
   3) Tiêu chí nghiệm thu của frame UI phải ghi RÕ (để người/agent chấm được, không cảm tính):
        - coverage: đọc HẾT route trong MANIFEST, mỗi route một dòng kết luận;
        - rubric: mặt đơn sắc · bóng không bị cắt · CTA phẳng accent · chữ AA · focus ring;
        - sau khi sửa: chụp LẠI + đọc lại ảnh rồi mới cho green.
   ══ -->


